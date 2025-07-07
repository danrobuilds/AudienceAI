import asyncio
from langchain_core.messages import ToolMessage

# Import the direct tool functions from individual files
from .search_document_library import search_document_library
from .search_linkedin_posts import search_linkedin_posts
from .search_recent_news import search_recent_news
from .web_search import web_search
from .generate_image import generate_image

# Tool Definitions (kept the same for compatibility)
search_document_library_mcp_tool_def = {
    "name": "search_document_library",
    "description": "Search the internal PDF document library on company information using an embedding-based retriever. Use this to find relevant information for the user's prompt about ABLSoft or related topics. These are not published sources, they are internal company documents for contextual information.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The topic or theme to search for in company information documents."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

search_linkedin_posts_mcp_tool_def = {
    "name": "search_linkedin_posts",
    "description": "Search for successful LinkedIn posts using an embedding-based retriever. Use this to find examples of successful posts that match the content type and themes you're creating. This helps you understand the structure, tone, and style of successful posts in similar categories.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A structured content brief that captures: The main message/key points you want to communicate, The content type - a detailed description of the structure and format of the post you want to create, The intended tone/style, The target audience context, and The desired outcome/call-to-action. This should be a clear, concise summary that represents the essence of your content for finding similar successful posts."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

search_recent_news_mcp_tool_def = {
    "name": "search_recent_news",
    "description": "Search for recent news articles based on a query. Use this to find recent, relevant information for use in the post. Prioritize relevancy for sorting if unsure.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Pick several keywords to search for. Use the OR operator to separate each single word or very short phrase (1-2 words). "
                    "For example: \'AI OR fintech OR \'payment processing\'\'. "
                    "Do not use over complicated queries or long phrases because they will not return any results."
                    "The complete value for q MUST be URL-encoded. Max length: 500 chars."
                )
            },
            "sort_by": {
                "type": "string",
                "description": "The sorting criteria for the news articles. Decide which is more relevant to the user's prompt. Can be 'publishedAt' or 'relevancy'. Default to 'relevancy' if unsure.",
                "enum": ["publishedAt", "relevancy"]
            }
        },
        "required": ["query", "sort_by"],
        "additionalProperties": False
    },
    "strict": True
}

web_search_mcp_tool_def = {
    "name": "web_search",
    "description": "Search the web for information on any topic. Use this to find comprehensive market research information including company information, industry insights, recent trends, and other relevant web content.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Use descriptive keywords and phrases to find relevant web content that complements and strengthens previous information in the context of making a successful, informative, and engaging social media post."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

generate_image_mcp_tool_def = {
    "name": "generate_image",
    "description": "Generate an image for provided content based on the media content and style. Use this when the text content would benefit from a visual element.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Detailed description of the image to generate, including style, composition, and key elements that align with the post content. Avoid generating images with repetitive imagery and excessive text."
            },
            "style": {
                "type": "string",
                "description": "Visual style for the image (e.g., 'professional', 'infographic', 'modern', 'minimalist', 'tech-focused')",
                "enum": ["professional", "infographic", "modern", "minimalist", "tech-focused", "corporate"]
            },
            "aspect_ratio": {
                "type": "string",
                "description": "Aspect ratio for content optimization",
                "enum": ["16:9", "1:1", "4:5"]
            }
        },
        "required": ["prompt", "style", "aspect_ratio"],
        "additionalProperties": False
    },
    "strict": True
}


# -------------------------- DIRECT TOOL CALLING LOGIC ------------------------------------------------------------

async def call_mcp_tools(llm_response, async_log_callback=None, tenant_id: str = ""):
    """
    Updated function to handle direct tool calling instead of MCP.
    
    Args:
        llm_response: The LLM response containing tool calls
        async_log_callback: Optional logging callback function
        tenant_id: Tenant ID for multi-tenant operations
    
    Returns:
        Tuple of (List of ToolMessage objects with tool results, List of generated images)
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    tool_messages = []
    generated_images = []  # Track generated images separately
    
    if not llm_response.tool_calls:
        return tool_messages, generated_images
        
    await _log(f"\nLLM decided to use {len(llm_response.tool_calls)} tool(s): {[tc.get('name', 'unknown') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown') for tc in llm_response.tool_calls]}")
    
    # Map tool names to functions
    tool_function_map = {
        "search_document_library": search_document_library,
        "search_linkedin_posts": search_linkedin_posts,
        "search_recent_news": search_recent_news,
        "web_search": web_search,
        "generate_image": generate_image
    }
    
    for tool_call in llm_response.tool_calls:
        tool_args = tool_call["args"]
        tool_output_content = "" 
        tool_name = tool_call["name"]

        await _log(f"Calling tool '{tool_name}' with args: {tool_args}")

        try:
            # Get the function for this tool
            tool_function = tool_function_map.get(tool_name)
            
            if not tool_function:
                tool_output_content = f"Error: Unknown tool '{tool_name}'"
                await _log(tool_output_content)
            else:
                # Call the tool function directly
                if tool_name == "search_recent_news":
                    # Handle the two-argument case
                    tool_output_content = tool_function(
                        query=tool_args["query"],
                        sort_by=tool_args.get("sort_by", "publishedAt")
                    )
                elif tool_name == "generate_image":
                    # Handle the three-argument case
                    tool_output_content = tool_function(
                        prompt=tool_args["prompt"],
                        style=tool_args.get("style", "professional"),
                        aspect_ratio=tool_args.get("aspect_ratio", "16:9")
                    )
                    
                    # If image generation was successful, preserve the complete image object
                    if isinstance(tool_output_content, dict) and "base64_data" in tool_output_content:
                        generated_images.append(tool_output_content)
                        await _log(f"Image generated and stored: {tool_output_content['filename']}")
                        
                elif tool_name == "search_document_library":
                    # Handle search_document_library with tenant_id
                    tool_output_content = tool_function(
                        query=tool_args["query"],
                        tenant_id=tenant_id
                    )
                else:
                    # Handle other single-argument tools
                    tool_output_content = tool_function(query=tool_args["query"])
            
            # Create truncated log based on tool type and response format
            if isinstance(tool_output_content, dict):
                truncated_log = _create_truncated_log_from_dict(tool_name, tool_output_content)
                await _log(f"Tool '{tool_name}' results:\n{truncated_log}")
            else:
                # Fallback for tools that still return strings (like search_recent_news)
                truncated_log = str(tool_output_content)[:500] + ("..." if len(str(tool_output_content)) > 500 else "")
                await _log(f"Tool '{tool_name}' results:\n{truncated_log}")

        except Exception as e:
            log_msg = f"Error during tool '{tool_name}' call: {e}"
            await _log(log_msg)
            tool_output_content = f"The '{tool_name}' tool failed. Please proceed with available information."
        
        # Convert dict responses back to strings for LLM compatibility
        if isinstance(tool_output_content, dict):
            tool_output_content = _convert_dict_to_llm_string(tool_name, tool_output_content)
        elif not isinstance(tool_output_content, str):
            tool_output_content = str(tool_output_content) if tool_output_content is not None else f"Tool '{tool_name}' resulted in a non-string output which has been converted."

        tool_messages.append(ToolMessage(content=tool_output_content, tool_call_id=tool_call["id"]))
    
    return tool_messages, generated_images

def _create_truncated_log_from_dict(tool_name: str, result_dict: dict) -> str:
    """Create truncated log message from dictionary response."""
    if "error" in result_dict:
        return f"Error: {result_dict['error']}"
    
    if tool_name == "search_document_library":
        return _truncate_document_library_dict(result_dict)
    elif tool_name == "search_linkedin_posts":
        return _truncate_linkedin_posts_dict(result_dict)
    elif tool_name == "web_search":
        return _truncate_web_search_dict(result_dict)
    elif tool_name == "generate_image":
        return _truncate_generate_image_dict(result_dict)
    else:
        return str(result_dict)[:500] + ("..." if len(str(result_dict)) > 500 else "")

def _truncate_document_library_dict(result: dict) -> str:
    """Create truncated log for document library results."""
    lines = [f"Found {result['total_segments']} document segments"]
    lines.append(f"Source files: {', '.join(result['source_files'])}")
    
    for segment in result['document_segments']:
        lines.append(f"\nSegment {segment['segment_number']}:")
        lines.append(f"  File: {segment['filename']}")
        lines.append(f"  Similarity: {segment['similarity_score']:.3f}")
        lines.append(f"  Document URL: {segment['document_url']}")
        # Truncate content
        content = segment['content'][:150] + ("..." if len(segment['content']) > 150 else "")
        lines.append(f"  Content: {content}")
    
    return "\n".join(lines)

def _truncate_linkedin_posts_dict(result: dict) -> str:
    """Create truncated log for LinkedIn posts results."""
    lines = [f"Found {result['total_posts']} viral post examples"]
    
    for post in result['viral_posts']:
        lines.append(f"\nExample {post['example_number']}:")
        lines.append(f"  Similarity: {post['similarity_score']:.3f}")
        # Truncate content
        content = post['content'][:100] + ("..." if len(post['content']) > 100 else "")
        lines.append(f"  Content: {content}")
    
    return "\n".join(lines)

def _truncate_web_search_dict(result: dict) -> str:
    """Create truncated log for web search results."""
    lines = [f"Found {result['total_results']} web results"]
    
    for web_result in result['web_results']:
        lines.append(f"\nResult {web_result['result_number']}:")
        lines.append(f"  Title: {web_result['title']}")
        lines.append(f"  URL: {web_result['url']}")
        # Truncate content
        content = web_result['content'][:100] + ("..." if len(web_result['content']) > 100 else "")
        lines.append(f"  Content: {content}")
    
    return "\n".join(lines)

def _truncate_generate_image_dict(result: dict) -> str:
    return f"Image generated: {result['filename']} ({result['size']}, {result['style']} style)"

def _convert_dict_to_llm_string(tool_name: str, result_dict: dict) -> str:
    """Convert any dictionary response to string format for LLM using a generic approach."""
    if "error" in result_dict:
        return result_dict["error"]
    
    if tool_name == "generate_image":
        # Special case for image generation - exclude base64 data for LLM
        return f"Image generated successfully. Filename: {result_dict['filename']}, Size: {result_dict['size']}, Style: {result_dict['style']}. The image has been prepared for display."
    
    # Generic conversion for all other tools
    return _dict_to_formatted_string(result_dict)

def _dict_to_formatted_string(data: dict, indent: int = 0) -> str:
    """Recursively convert dictionary to formatted string."""
    lines = []
    prefix = "  " * indent
    
    for key, value in data.items():
        if key in ['success', 'query', 'total_segments', 'total_posts', 'total_results', 'base64_data']:
            # Skip metadata fields and base64 data that aren't needed for LLM
            continue
            
        if isinstance(value, list):
            # Handle arrays of results
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    # Add a separator for readability
                    if i > 0:
                        lines.append("---")
                    lines.append(_dict_to_formatted_string(item, indent))
                else:
                    lines.append(f"{prefix}{key}: {item}")
        elif isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dict_to_formatted_string(value, indent + 1))
        else:
            # Handle simple key-value pairs with readable formatting
            formatted_key = key.replace('_', ' ').title()
            if key == 'segment_number':
                lines.append(f"\nDocument Segment {value}:")
            elif key == 'example_number':
                lines.append(f"\nViral Post Example {value}:")
            elif key == 'result_number':
                lines.append(f"\nWeb Result {value}:")
            elif key == 'similarity_score':
                lines.append(f"{prefix}Similarity Score: {value:.3f}")
            elif key == 'document_url' and not value:
                lines.append(f"{prefix}Document URL: Not available")
            elif key == 'url_error':
                # Skip url_error if document_url is present
                continue
            else:
                lines.append(f"{prefix}{formatted_key}: {value}")
    
    return "\n".join(lines)

