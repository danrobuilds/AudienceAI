from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import json
import logging
from agent.orchestrator import generate_post_for_prompt

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
    
    # Capture logs during generation
    captured_logs = []
    
    async def log_callback(message: str):
        """Callback to capture logs during generation"""
        captured_logs.append(message)
        logger.info(f"Generation log: {message}")
    
    try:
        logger.info(f"Processing query: {request.prompt[:100]}...")
        
        # Call the orchestrator to generate content with log capture
        result = await generate_post_for_prompt(request.prompt, async_log_callback=log_callback)
        
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
        import datetime
        import asyncio
        import queue
        
        # Create a queue to capture logs from the callback
        log_queue = asyncio.Queue()
        
        async def log_callback(message: str):
            """Callback to capture logs during generation"""
            timestamp = datetime.datetime.now().isoformat()
            
            log_entry = {
                "type": "log",
                "message": message,
                "timestamp": timestamp
            }
            
            # Put the log message in the queue
            await log_queue.put(log_entry)
        
        async def process_generation():
            """Run the generation in a separate task"""
            try:
                # Add timeout to the entire generation process (5 minutes)
                result = await asyncio.wait_for(
                    generate_post_for_prompt(request.prompt, async_log_callback=log_callback),
                    timeout=300.0
                )
                # Send final result
                final_response = {
                    'type': 'result', 
                    'content': result, 
                    'message': 'Content generation completed'
                }
                await log_queue.put(final_response)
            except asyncio.TimeoutError:
                logger.error("Generation process timed out after 5 minutes")
                error_message = {
                    "type": "error", 
                    "message": "Generation process timed out. Please try again."
                }
                await log_queue.put(error_message)
            except Exception as e:
                logger.error(f"Error in streaming generation: {str(e)}")
                error_message = {
                    "type": "error", 
                    "message": f"Error: {str(e)}"
                }
                await log_queue.put(error_message)
            finally:
                # Signal end of generation
                await log_queue.put({"type": "end", "message": "Stream ended"})
        
        try:
            # Send initial message
            yield f"data: {json.dumps({'type': 'progress', 'message': 'Starting content generation...'})}\n\n"
            
            # Start the generation task
            generation_task = asyncio.create_task(process_generation())
            
            # Stream logs as they come in
            stream_start_time = asyncio.get_event_loop().time()
            max_stream_duration = 360.0  # 6 minutes total timeout
            
            while True:
                try:
                    # Check for overall timeout
                    if asyncio.get_event_loop().time() - stream_start_time > max_stream_duration:
                        await log_queue.put({
                            "type": "error", 
                            "message": "Stream timeout - generation took too long"
                        })
                        break
                    
                    # Wait for next log message with timeout
                    log_entry = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                    
                    # Send the log message
                    yield f"data: {json.dumps(log_entry)}\n\n"
                    
                    # Check if this is the end signal
                    if log_entry.get('type') == 'end':
                        break
                        
                except asyncio.TimeoutError:
                    # Check if generation is still running
                    if generation_task.done():
                        break
                    # Send keep-alive
                    yield f"data: {json.dumps({'type': 'keepalive', 'message': 'Processing...'})}\n\n"
            
            # Ensure generation task completes
            if not generation_task.done():
                await generation_task
                
        except Exception as e:
            logger.error(f"Error in streaming generation: {str(e)}")
            error_message = {
                "type": "error",
                "message": f"Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_message)}\n\n"
        
        finally:
            # Send end signal
            yield f"data: {json.dumps({'type': 'end', 'message': 'Stream ended'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
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
