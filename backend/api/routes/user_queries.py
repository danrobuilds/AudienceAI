from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import json
import logging
from ...agent.orchestrator import generate_post_for_prompt

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="User prompt for generating content")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")

class QueryResponse(BaseModel):
    success: bool
    content: Optional[Dict[str, Any]] = None
    message: str
    execution_time: Optional[float] = None

class StreamMessage(BaseModel):
    type: str  # "log", "progress", "result", "error"
    message: str
    timestamp: Optional[str] = None

@router.post("/generate", response_model=QueryResponse)
async def generate_content(request: QueryRequest):
    """
    Generate LinkedIn post content based on user prompt.
    Uses the orchestrator to gather information and create viral posts.
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.prompt[:100]}...")
        
        # Call the orchestrator to generate content
        result = await generate_post_for_prompt(request.prompt)
        
        execution_time = time.time() - start_time
        
        return QueryResponse(
            success=True,
            content=result,
            message="Content generated successfully",
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error generating content: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )

@router.post("/generate-stream")
async def generate_content_stream(request: QueryRequest):
    """
    Generate LinkedIn post content with streaming logs.
    Provides real-time updates on the generation process.
    """
    async def event_generator():
        logs_buffer = []
        
        async def log_callback(message: str):
            """Callback to capture logs during generation"""
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            
            log_entry = StreamMessage(
                type="log",
                message=message,
                timestamp=timestamp
            )
            
            # Add to buffer and yield
            logs_buffer.append(log_entry.dict())
            yield f"data: {json.dumps(log_entry.dict())}\n\n"
        
        try:
            # Send initial message
            yield f"data: {json.dumps({'type': 'progress', 'message': 'Starting content generation...'})}\n\n"
            
            # Call the orchestrator with streaming callback
            result = await generate_post_for_prompt(request.prompt, log_callback)
            
            # Send final result
            final_message = StreamMessage(
                type="result",
                message="Content generation completed",
            )
            yield f"data: {json.dumps({'type': 'result', 'content': result, 'message': 'Content generation completed'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {str(e)}")
            error_message = StreamMessage(
                type="error",
                message=f"Error: {str(e)}"
            )
            yield f"data: {json.dumps(error_message.dict())}\n\n"
        
        finally:
            # Send end signal
            yield f"data: {json.dumps({'type': 'end', 'message': 'Stream ended'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@router.get("/status")
async def get_query_status():
    """
    Check the status of the query processing system.
    """
    try:
        # Test if we can import and access the orchestrator
        from ...agent.orchestrator import generate_post_for_prompt
        from ...services.openai_service import initialize_llm
        
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
