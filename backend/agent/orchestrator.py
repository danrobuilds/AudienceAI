import asyncio
from ..services.openai_service import initialize_llm
from .agent_info_gatherer import gather_information
from .agent_post_creator import create_viral_post

async def generate_post_for_prompt(user_prompt_text: str, async_log_callback: callable = None):
    """
    Main orchestration function for generating LinkedIn posts.
    
    Args:
        user_prompt_text: The user's request for creating a LinkedIn post
        async_log_callback: Optional logging callback function
    
    Returns:
        Dictionary containing post content and any generated images
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    try:
        # Initialize the LLM
        llm = initialize_llm()
        await _log("GPT-4o LLM initialized successfully with Responses API")
        
        # Agent 1: Information Gathering
        gathered_info = await gather_information(user_prompt_text, llm, async_log_callback)
        
        # Agent 2: Viral Post Creation
        result = await create_viral_post(user_prompt_text, gathered_info, llm, async_log_callback)
        
        return result

    except Exception as llm_error:
        await _log(f"Failed to create ChatOpenAI or process request: {llm_error}")
        raise llm_error
        
    

