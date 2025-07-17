import asyncio
import uuid
from langchain_core.messages import SystemMessage, HumanMessage
from tools.tool_calling import (search_linkedin_posts_mcp_tool_def, search_blog_posts_mcp_tool_def, call_mcp_tools)


# AGENT 2: Create viral social media content using modality-specific tools and strategies.

async def create_viral_post(user_prompt_text: str, gathered_info: str, llm, async_log_callback=None, company_context: str = "", modality: str = "linkedin", tenant_id: str = ""):
   
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
        SystemMessage(content= f"""
            {system_message}

            {company_context}

            You are a social media marketing expert who makes content for this company's social media accounts.

            """),
        
        HumanMessage(content=f"""
                     
            Original request: {user_prompt_text}

            Gathered Information: {gathered_info}

            Find an example of a successful post and copy the format exactly. This will lay the groundwork for creating the text and image for marketing content that satisfies the user's original request.
            
            After gathering examples, I'll ask you to create the final structured content.

            """)
    ]
    
    # Phase 1 – research
    response = await llm_with_tools.ainvoke(messages)
    messages.append(response)

    # Handle any tool calls returned from the first pass
    if response.tool_calls:
        tool_messages, _ = await call_mcp_tools(response, async_log_callback, tenant_id)
        messages.extend(tool_messages)

    # Phase 2 – generate structured content
    structured_schema = {
        "name": "social_media_content",
        "schema": {
            "type": "object",
            "properties": {
                "post_content": {
                    "type": "string",
                    "description": f"The viral {modality} post content that satisfies the user's original request according to the examples of successful {modality} posts. Post content should complement the image, not be a duplicate of it."
                },
                "image_description": {
                    "type": "string", 
                    "description": f"Detailed description for generating a compelling image for this {modality} post, including the purpose of the image, data, words, and information, type, visual elements, style, composition, colors, and any other relevant details."
                }
            },
            "required": ["post_content", "image_description"],
            "additionalProperties": False
        }
    }

    llm_structured = llm.with_structured_output(structured_schema)

    # Add final instruction for structured output
    messages.append(HumanMessage(content=f"""

        Now create the final viral {modality} content that satisfies the user's original request exactly using all the information gathered.
    
        IMPORTANT: Format the content and image in tandem based on the provided examples of successful {modality} posts. They should complement each other and not be repetitive.
        """))

    structured_response = await llm_structured.ainvoke(messages)

    await _log(f"{modality.title()} content creation complete.")
    return structured_response

def get_tools_for_modality(modality: str):
    """
    Get the appropriate toolset for the specified content modality.
    Each platform gets optimized tools for content creation.
    """
    if modality == "linkedin":
        return [search_linkedin_posts_mcp_tool_def]
    elif modality == "twitter":
        return [search_linkedin_posts_mcp_tool_def]  # Temporary fallback
    elif modality == "tiktok":
        return [search_linkedin_posts_mcp_tool_def]  # Temporary fallback
    elif modality == "instagram":
        return [search_linkedin_posts_mcp_tool_def]  # Temporary fallback
    elif modality == "blog":
        return [search_blog_posts_mcp_tool_def]  # Blog posts can reference LinkedIn content for professional insights
    else:
        return [search_linkedin_posts_mcp_tool_def]

def get_system_message_for_modality(modality: str, company_context: str):
    """
    Get modality-specific system message with platform-optimized instructions.
    """
    
    if modality == "linkedin":
        return """
        
        YOUR TASK is to create a single viral LinkedIn post exactly as specified in the ORIGINAL QUERY using the provided information and tools.

        Use the provided tools to find examples of successful LinkedIn posts based on the type of information provided 
        (a post about a leader should be based on the format of a successful posts about leaders)
        
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

    elif modality == "blog":
        return """YOUR TASK is to create a comprehensive blog post using the provided information and research.

        1. Research relevant content and examples to inform your blog post structure and style.
        2. Create a compelling blog post that:
        - Has an engaging, SEO-friendly title
        - Includes a compelling introduction that hooks the reader
        - Uses clear headings and subheadings for structure
        - Provides valuable, actionable insights
        - Includes relevant examples and case studies
        - Has a strong conclusion with key takeaways
        - Uses professional, informative tone
        - Incorporates relevant keywords naturally
        - Is 800-2000 words in length
        - Includes calls-to-action where appropriate

        Focus on providing value to the reader while maintaining professional credibility.
        """

    else:
        # Fallback to LinkedIn
        return get_system_message_for_modality("linkedin", company_context) 