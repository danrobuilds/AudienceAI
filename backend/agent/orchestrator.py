import asyncio
from services.openai_service import initialize_llm
from agent.agent_info_gatherer import gather_information
from agent.agent_post_creator import create_viral_post
from agent.agent_multimodal_creator import create_media_for_post
from agent.context import get_company_context

async def generate_post_for_prompt(user_prompt_text: str, async_log_callback: callable = None, modality: str = "linkedin", tenant_id: str = "", generate_image: bool = False):
    """
    Main orchestration function for generating social media content.
    
    Args:
        user_prompt_text: The user's request for creating social media content
        async_log_callback: Optional logging callback function
        modality: Social media platform (linkedin, twitter, tiktok, instagram)
        tenant_id: The tenant ID to fetch company context for
        generate_image: Whether to generate images for the post
    
    Returns:
        Dictionary containing post content and any generated images
    """

    # Only run if tenant_id is provided
    if tenant_id == "":
        return "No tenant ID provided"

    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    try:
        # Initialize the LLM
        llm = initialize_llm()
        await _log("GPT-4o LLM initialized successfully with Responses API")
        
        # Fetch company context once for both agents
        await _log("Fetching company context...")
        company_context = await get_company_context(tenant_id)
        if not company_context: await _log(f"No company context found for tenant")
        
        # Agent 1: Information Gathering
        gathered_info = await gather_information(user_prompt_text, llm, async_log_callback, company_context, tenant_id)
        
        # Agent 2: Viral Post Creation (returns structured response)
        post_response = await create_viral_post(user_prompt_text, gathered_info, llm, async_log_callback, company_context, modality, tenant_id)
        
        # Extract structured content
        post_content = post_response.get("post_content", "")
        image_description = post_response.get("image_description", "")
        await _log(f"Structured response received - Post: {len(post_content)} chars, Image desc: {len(image_description)} chars")
    
        # Agent 3: Image Generation (conditional)
        generated_images = []
        if generate_image and image_description:
            generated_images = await create_media_for_post(post_content, modality, llm, async_log_callback, tenant_id, image_description)
        
        # Return complete result
        result = {
            "post_content": post_content,
            "generated_images": generated_images,
            "modality": modality
        }
        
        return result

    except Exception as llm_error:
        await _log(f"Failed to create ChatOpenAI or process request: {llm_error}")
        raise llm_error
        
    

