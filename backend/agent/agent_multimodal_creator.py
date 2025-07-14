import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from tools.tool_calling import generate_image_mcp_tool_def, call_mcp_tools, image_web_search_mcp_tool_def, create_diagram_mcp_tool_def

async def create_media_for_post(post_content: str, modality: str, llm, async_log_callback=None, tenant_id: str = "", image_description: str = ""):
    """
    Agent: Create images for social media posts using the generated content.
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log(f"\n=== PHASE 3: VISUAL CONTENT CREATION FOR {modality.upper()} ===")
    
    # Bind image generation and diagram creation tools
    llm_with_image_tool = llm.bind_tools([image_web_search_mcp_tool_def, create_diagram_mcp_tool_def, generate_image_mcp_tool_def], tool_choice="auto")
    
    # Get platform-specific visual content creation instructions
    system_message = get_image_system_message(modality)
    
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=f"""
                     
        Generated {modality} post content: {post_content}

        Image description: {image_description}

        Create ONE visual element that enhances this post's engagement. 

        Choose the most appropriate visual approach based on the content and image description.

        """)
    ]
    
    try:
        await _log(f"Invoking LLM for {modality} visual content creation...")
        response = await asyncio.wait_for(llm_with_image_tool.ainvoke(messages), timeout=60.0)
        
        # Track generated images/diagrams
        generated_images = []
        
        # Process tool calls if any
        if response.tool_calls:
            await _log(f"LLM requesting visual content creation for {modality} post")
            
            tool_messages, generated_images = await call_mcp_tools(response, async_log_callback, tenant_id)
            
            # Log any generated visual content
            if generated_images:
                await _log(f"Generated {len(generated_images)} visual elements for the {modality} post")
                for img in generated_images:
                    if 'style' in img:
                        await _log(f"Image: {img['filename']} ({img['size']}, {img['style']} style)")
                    elif 'diagram_type' in img:
                        await _log(f"Diagram: {img['filename']} ({img['size']}, {img['diagram_type']} type)")
                    else:
                        await _log(f"Visual: {img['filename']} ({img['size']})")
        
        await _log(f"{modality.title()} visual content creation complete.")
        return generated_images
        
    except Exception as e:
        await _log(f"Error during {modality} visual content creation: {e}")
        return []

def get_image_system_message(modality: str):
    """
    Get platform-specific visual content creation instructions.
    """
    base_context = "You are an expert visual content creator for social media. You can generate images, create diagrams, or search for images. Only create ONE visual element per request. "
    
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
