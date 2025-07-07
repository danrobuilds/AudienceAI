from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Literal
import asyncio
import json
import logging
import uuid
from agent.orchestrator import generate_post_for_prompt
import time


router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="User prompt for generating content")
    modality: Literal["linkedin", "twitter", "blog", "instagram"] = Field(default="linkedin", description="Social media platform to generate content for")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")
    tenant_id: str = Field(..., description="Tenant ID for company context (required UUID)")
    generate_image: Optional[bool] = Field(default=False, description="Whether to generate an image for the post")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Tenant ID is required')
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError('Tenant ID must be a valid UUID format')
        
        return v.strip()

class QueryResponse(BaseModel):
    success: bool
    content: Optional[Dict[str, Any]] = None
    message: str
    modality: str
    execution_time: Optional[float] = None

class StreamMessage(BaseModel):
    type: str  # "log", "progress", "result", "error"
    message: str
    timestamp: Optional[str] = None


@router.post("/generate", response_model=QueryResponse)
async def generate_content(request: QueryRequest):
    """
    Generate social media content based on user prompt and specified modality.
    Supports LinkedIn posts, Twitter posts, TikTok videos, and Instagram posts.
    """
    start_time = time.time()
    
    # Capture logs during generation
    captured_logs = []
    
    async def log_callback(message: str):
        """Callback to capture logs during generation"""
        captured_logs.append(message)
        logger.info(f"Generation log: {message}")
    
    try:
        logger.info(f"Processing {request.modality} query: {request.prompt[:100]}...")
        
        # Call the orchestrator with modality, tenant_id, and generate_image
        result = await generate_post_for_prompt(
            user_prompt_text=request.prompt, 
            async_log_callback=log_callback,
            modality=request.modality,
            tenant_id=request.tenant_id,
            generate_image=request.generate_image
        )
        
        execution_time = time.time() - start_time
        
        # Include logs in the response
        if isinstance(result, dict):
            result['logs'] = captured_logs
        else:
            # If result is not a dict, wrap it
            result = {
                'post_content': result,
                'generated_images': [],
                'logs': captured_logs
            }
        
        return QueryResponse(
            success=True,
            content=result,
            message=f"{request.modality.title()} content generated successfully",
            modality=request.modality,
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error generating {request.modality} content: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate {request.modality} content: {str(e)}"
        )
    


@router.get("/status")
async def get_query_status():
    """
    Check the status of the query processing system.
    """
    try:
        # Test if we can import and access the orchestrator
        from agent.orchestrator import generate_post_for_prompt
        from services.openai_service import initialize_llm
        
        # Try to initialize LLM to check if services are available
        llm = initialize_llm()
        
        return {
            "status": "healthy",
            "service": "user_queries",
            "llm_initialized": True,
            "orchestrator_available": True
        }
    except Exception as e:
        logger.warning(f"Service health check failed: {str(e)}")
        return {
            "status": "degraded",
            "service": "user_queries",
            "error": str(e),
            "llm_initialized": False,
            "orchestrator_available": False
        }
