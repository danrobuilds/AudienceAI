import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from tools.tool_calling import generate_image_mcp_tool_def, call_mcp_tools

async def create_media_for_post(post_content: str, modality: str, llm, async_log_callback=None, tenant_id: str = "", image_description: str = ""):
    """
    Agent: Create images for social media posts using the generated content.
    
    Args:
        post_content: The generated post content
        modality: Social media platform (linkedin, twitter, tiktok, instagram)
        llm: The language model instance
        async_log_callback: Optional logging callback function
    
    Returns:
        List of generated image objects
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log(f"\n=== PHASE 3: IMAGE GENERATION FOR {modality.upper()} ===")
    
    # Bind image generation tool
    llm_with_image_tool = llm.bind_tools([generate_image_mcp_tool_def], tool_choice="auto")
    
    # Get platform-specific image generation instructions
    system_message = get_image_system_message(modality)
    
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=f"""Generated {modality} post content: {post_content}, with the following image description: {image_description}.

        Generate ONE professional image that enhances this post's engagement based on provided information and image description. There should be no text in the image.""")
    ]
    
    try:
        await _log(f"Invoking LLM for {modality} image generation...")
        response = await asyncio.wait_for(llm_with_image_tool.ainvoke(messages), timeout=60.0)
        
        # Track generated images
        generated_images = []
        
        # Process tool calls if any
        if response.tool_calls:
            await _log(f"LLM requesting image generation for {modality} post")
            
            tool_messages, generated_images = await call_mcp_tools(response, async_log_callback, tenant_id)
            
            # Log any generated images
            if generated_images:
                await _log(f"Generated {len(generated_images)} images for the {modality} post")
                for img in generated_images:
                    await _log(f"Image: {img['filename']} ({img['size']}, {img['style']} style)")
        
        await _log(f"{modality.title()} image generation complete.")
        return generated_images
        
    except Exception as e:
        await _log(f"Error during {modality} image generation: {e}")
        return []

def get_image_system_message(modality: str):
    """
    Get platform-specific image generation instructions.
    """
    base_context = "You are an expert visual content creator for social media. Only call generate_image one time. "
    
    if modality == "linkedin":
        return base_context
        
    elif modality == "twitter":
        return base_context + """Create an engaging, eye-catching image for Twitter posts.
        - Use bold, attention-grabbing visuals
        - Keep designs simple and clear for small screens
        - Use trending color schemes and modern design
        - Focus on visual impact and shareability"""
        
    elif modality == "tiktok":
        return base_context + """Create vibrant, dynamic images for TikTok content.
        - Use bright, energetic colors
        - Include dynamic elements and modern aesthetics
        - Focus on youth-oriented, trendy visual styles
        - Create visuals that would work as video thumbnails or backgrounds"""
        
    elif modality == "instagram":
        return base_context + """Create aesthetically pleasing images for Instagram posts.
        - Use Instagram-native visual styles and trends
        - Focus on beauty, lifestyle, and visual appeal
        - Use popular color palettes and compositions
        - Ensure high visual quality and aesthetic coherence"""
        
    else:
        # Default to LinkedIn
        return get_image_system_message("linkedin")
