import asyncio
import uuid
from langchain_core.messages import SystemMessage, HumanMessage
from .tools import (
    search_linkedin_posts_mcp_tool_def, 
    generate_image_mcp_tool_def,
    call_mcp_tools
)

async def create_viral_post(user_prompt_text: str, gathered_info: str, llm, async_log_callback=None):
    """
    Agent 2: Create a viral LinkedIn post using the provided information and examples.
    
    Args:
        user_prompt_text: The original user request
        gathered_info: Information gathered by the info gathering agent
        llm: The language model instance
        async_log_callback: Optional logging callback function
    
    Returns:
        Dictionary containing post content and any generated images
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log("\n=== PHASE 2: VIRAL POST CREATION ===")
    
    # Bind LinkedIn post search and image generation tools
    llm_with_post_tools = llm.bind_tools(
        [search_linkedin_posts_mcp_tool_def, generate_image_mcp_tool_def],
        tool_choice="auto"
    )
    
    post_system_message = """You are a social media marketing expert for the company ABLSoft. Your task is to create a single viral LinkedIn post using the provided information and examples of successful posts.

    1. Use the search_linkedin_posts tool to find examples of viral posts related to the topic.
    2. Optionally use the generate_image tool if the post would benefit from a compelling visual element. The image should have no text.
    3. Create a compelling LinkedIn post that:
        - Uses the gathered information as context and facts. Describes entities if their name is not known. Does not include direct quotes in the post unless they exist directly in gathered information.
        - Follows the structure and style of successful viral posts, take inspiration from emojis and hashtags and use them in your post. Avoid astericks.
        - Is engaging, authentic, and likely to go viral
        - Includes an image if one was generated

    YOUR FINAL RESPONSE MUST BE ONLY THE LINKEDIN POST CONTENT.
    If an image was generated, include a note at the end: "Image: [brief description of generated image]"
    ABSOLUTELY NO PRE-AMBLE, EXPLANATIONS, APOLOGIES, OR CONVERSATIONAL FILLER.
    """
    
    messages = [
        SystemMessage(content=post_system_message),
        HumanMessage(content=f"""Original request: {user_prompt_text}, Gathered Information: {gathered_info},Create a viral LinkedIn post using this information and examples from successful posts.""")
    ]
    
    try:
        await _log("Invoking LLM for post creation...")
        post_response = await asyncio.wait_for(llm_with_post_tools.ainvoke(messages), timeout=60.0)
        messages.append(post_response)
        
        # Track generated images
        generated_images = []
        
        # Process tool calls if any
        if post_response.tool_calls:
            tool_messages = await call_mcp_tools(post_response, async_log_callback)
            
            # Extract and process any generated images BEFORE sending to LLM
            for i, tool_msg in enumerate(tool_messages):
                if "IMAGE_GENERATED|" in tool_msg.content:
                    try:
                        # Parse the structured response
                        content = tool_msg.content
                        parts = content.split("|")
                        
                        # Extract metadata
                        filename = parts[1].split(":")[1] if len(parts) > 1 else f"generated_{uuid.uuid4().hex[:8]}.png"
                        size = parts[2].split(":")[1] if len(parts) > 2 else "Unknown"
                        style = parts[3].split(":")[1] if len(parts) > 3 else "Unknown"
                        base64_data = parts[4].split(":", 1)[1] if len(parts) > 4 else None
                        
                        if base64_data:
                            generated_images.append({
                                "filename": filename,
                                "base64_data": base64_data,
                                "size": size,
                                "style": style
                            })
                            
                            # Replace the tool message with a clean version for LLM (no base64)
                            tool_messages[i].content = f"Image generated successfully. Filename: {filename}, Size: {size}, Style: {style}. The image has been prepared for display."
                            
                            await _log(f"Image generated and prepared for frontend: {filename}")
                        else:
                            await _log(f"Warning: Could not extract base64 data from image generation")
                        
                    except Exception as e:
                        await _log(f"Error processing generated image: {e}")
            
            messages.extend(tool_messages)
            
            # Get final post
            final_post_response = await asyncio.wait_for(llm_with_post_tools.ainvoke(messages), timeout=120.0)
            final_post = final_post_response.content
        else:
            final_post = post_response.content
            
        await _log("Viral post creation complete.")
        
        # Return both post and image info
        result = {
            "post_content": final_post,
            "generated_images": generated_images
        }
        
        return result
        
    except Exception as e:
        await _log(f"Error during post creation: {e}")
        return {
            "post_content": f"Post creation encountered an error: {e}",
            "generated_images": []
        } 