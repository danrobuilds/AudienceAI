import asyncio
import uuid
from langchain_core.messages import SystemMessage, HumanMessage
from tools.tool_calling import (
    search_linkedin_posts_mcp_tool_def, 
    call_mcp_tools
)

async def create_viral_post(user_prompt_text: str, gathered_info: str, llm, async_log_callback=None, company_context: str = "", modality: str = "linkedin", tenant_id: str = ""):
    """
    Agent 2: Create viral social media content using modality-specific tools and strategies.
    
    Args:
        user_prompt_text: The original user request
        gathered_info: Information gathered by the info gathering agent
        llm: The language model instance
        async_log_callback: Optional logging callback function
        company_context: Company context from orchestrator
        modality: Social media platform (linkedin, twitter, tiktok, instagram)
    
    Returns:
        Dict containing post content and image description
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log(f"\n=== PHASE 2: {modality.upper()} VIRAL CONTENT CREATION ===")
    
    # Step 1: Use regular LLM with tools for research
    tools = get_tools_for_modality(modality)
    await _log(f"Using {len(tools)} {modality}-optimized tools for viral content creation")
    
    llm_with_tools = llm.bind_tools(tools, tool_choice="auto")
    
    # Get modality-specific system message
    system_message = get_system_message_for_modality(modality, company_context)
    
    messages = [
        SystemMessage(content=system_message + "You are a social media marketing expert for a company. Here is context about the company: " + company_context),
        HumanMessage(content=f"""Original request: {user_prompt_text}

        Gathered Information: {gathered_info}

        First, create a comprehensive content brief that captures the essence of what you're communicating, then use the {modality} post search tool to find relevant examples of successful posts.
        
        After gathering examples, I'll ask you to create the final structured content.

        """)
    ]
    
    try:
        await _log(f"Invoking LLM for {modality} content research...")
        response = await asyncio.wait_for(llm_with_tools.ainvoke(messages), timeout=60.0)
        messages.append(response)
        
        tool_call_count = 0
        
        # Process tool calls if any
        if response.tool_calls:
            tool_call_count = len(response.tool_calls)
            await _log(f"LLM requesting {tool_call_count} tool calls for {modality} content research")
            
            tool_messages, _ = await call_mcp_tools(response, async_log_callback, tenant_id)
            messages.extend(tool_messages)
            
        # Step 2: Use structured output LLM to create final content
        structured_schema = {
            "name": "social_media_content",
            "schema": {
                "type": "object",
                "properties": {
                    "post_content": {
                        "type": "string",
                        "description": f"The viral {modality} post content that satisfies the user's original request"
                    },
                    "image_description": {
                        "type": "string", 
                        "description": f"Detailed description for generating a compelling image for this {modality} post, including style, composition, colors, and visual elements"
                    }
                },
                "required": ["post_content", "image_description"],
                "additionalProperties": False
            }
        }
        
        llm_structured = llm.with_structured_output(structured_schema)
        
        # Add final instruction for structured output
        messages.append(HumanMessage(content=f"""Now create the final viral {modality} content that satisfies the user's original request exactly using all the information gathered.
        
        IMPORTANT: Format the content based on the provided examples of successful {modality} posts.

        YOUR RESPONSE MUST INCLUDE:
        1. post_content: The viral {modality} post content that satisfies the user's original request
        2. image_description: A detailed description for generating a compelling image that would enhance this post's engagement
        
        Focus on creating both high-quality post content and a vivid image description that complements the post.
        """))
        
        await _log(f"Invoking LLM for structured {modality} content creation...")
        structured_response = await asyncio.wait_for(llm_structured.ainvoke(messages), timeout=120.0)
        
        await _log(f"{modality.title()} viral content creation complete. Used {tool_call_count} tool calls.")
        
        return structured_response
        
    except Exception as e:
        await _log(f"Error during {modality} content creation: {e}")
        return {
            "post_content": f"{modality.title()} content creation encountered an error: {e}",
            "image_description": f"Professional image complementing this {modality} post"
        }

def get_tools_for_modality(modality: str):
    """
    Get the appropriate toolset for the specified social media modality.
    Each platform gets optimized tools for viral content creation.
    """
    if modality == "linkedin":
        return [search_linkedin_posts_mcp_tool_def]
    elif modality == "twitter":
        return [search_linkedin_posts_mcp_tool_def]  # Temporary fallback
    elif modality == "tiktok":
        return [search_linkedin_posts_mcp_tool_def]  # Temporary fallback
    elif modality == "instagram":
        return [search_linkedin_posts_mcp_tool_def]  # Temporary fallback
    else:
        return [search_linkedin_posts_mcp_tool_def]

def get_system_message_for_modality(modality: str, company_context: str):
    """
    Get modality-specific system message with platform-optimized instructions.
    """
    
    if modality == "linkedin":
        return """
        
        YOUR TASK is to create a single viral LinkedIn post exactly as specified in the ORIGINAL QUERY using the provided information and tools.

        Use the provided tools to find examples of successful LinkedIn posts based on the type of information provided (a post about a leader should be based on the format of a successful posts about leaders)
        
        """

    elif modality == "twitter":
        return """YOUR TASK is to create a viral Twitter post using the provided information and trending examples.

        1. Search for trending Twitter content related to the topic (using available tools).
        2. Create a compelling Twitter post that:
        - Stays within 280 characters (or create a thread if needed)
        - Uses Twitter-native language and tone
        - Includes trending hashtags and mentions
        - Has a strong hook in the first line
        - Encourages retweets and replies
        - Uses emojis strategically

        If creating a thread, number each tweet (1/x format).
        """

    elif modality == "tiktok":
        return """YOUR TASK is to create a viral TikTok video script using the provided information and trending elements.

        1. Research trending TikTok content, sounds, and effects related to the topic.
        2. Create a compelling TikTok video script that:
        - Has a strong hook in the first 3 seconds
        - Uses trending sounds or audio cues
        - Includes visual direction and text overlays
        - Leverages popular TikTok formats (day in the life, behind the scenes, etc.)
        - Uses trending hashtags (#fyp #viral #business)
        - Is 15-60 seconds in length
        - Includes calls-to-action for follows/engagement

        Format: [SCENE] - [ACTION] - [TEXT OVERLAY] - [AUDIO/SOUND]
        If suggesting specific trending sounds, include: "Suggested Sound: [description]"
        """

    elif modality == "instagram":
        return """YOUR TASK is to create a viral Instagram post using the provided information and visual trends.

        1. Research trending Instagram content and visual styles related to the topic.
        2. Create a compelling Instagram post that:
        - Uses Instagram-native caption style
        - Includes compelling visual elements
        - Uses strategic hashtags (mix of popular and niche)
        - Includes Instagram-specific CTAs (Save, Share, DM)
        - Leverages Instagram features (polls, questions, etc.)
        - Uses emojis and line breaks for readability

        Include suggestions for Instagram Stories or Reels if applicable.
        """

    else:
        # Fallback to LinkedIn
        return get_system_message_for_modality("linkedin", company_context) 