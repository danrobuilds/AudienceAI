import asyncio
import os  # Added for environment variable access
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_core.messages import ToolMessage

# MCP Tool Definitions
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
    "description": "Search for viral LinkedIn posts using an embedding-based retriever. Use this to find examples of successful posts on a given topic to understand their structure and style for creating a new viral post.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The topic or theme to search for in viral post structures."
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
    "description": "Search the web for general information on any topic. Use this to find comprehensive market researchinformation beyond just news articles, including company information, industry insights, trends, and other relevant web content.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Use descriptive keywords and phrases to find relevant web content."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

generate_image_mcp_tool_def = {
    "name": "generate_image",
    "description": "Generate an image for the LinkedIn post based on the post content and style. Use this when the post would benefit from a visual element.",
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


# -------------------------- MCP TOOLS CALLING LOGIC ------------------------------------------------------------

async def call_mcp_tools(llm_response, async_log_callback=None):
    """
    Separate function to handle MCP tool calling logic.
    
    Args:
        llm_response: The LLM response containing tool calls
        async_log_callback: Optional logging callback function
    
    Returns:
        List of ToolMessage objects with tool results
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    tool_messages = []
    
    if not llm_response.tool_calls:
        return tool_messages
        
    await _log(f"\nLLM decided to use {len(llm_response.tool_calls)} tool(s): {[tc.get('name', 'unknown') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown') for tc in llm_response.tool_calls]}")
    
    for tool_call in llm_response.tool_calls:
        tool_args = tool_call["args"]
        # Make MCP server URL configurable for Railway deployment
        mcp_host = os.getenv("MCP_SERVER_HOST", "localhost")
        mcp_port = os.getenv("MCP_SERVER_PORT", "8050")
        server_url = f"http://{mcp_host}:{mcp_port}/sse"
        tool_output_content = "" 
        tool_name = tool_call["name"]

        await _log(f"Calling MCP tool '{tool_name}' with args: {tool_args} via SSE")
        await _log(f"MCP Server URL: {server_url}")  # Added for debugging

        try:
            async with sse_client(server_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    response = await session.call_tool(tool_name, arguments=tool_args)
                    
                    if hasattr(response, 'error') and response.error:
                        error_message = getattr(response.error, 'message', str(response.error))
                        tool_output_content = f"Tool Error from '{tool_name}': {error_message}"
                        await _log(f"MCP Tool Error: {tool_output_content}")
                    elif hasattr(response, 'content') and response.content is not None:
                        if isinstance(response.content, list) and len(response.content) > 0 and hasattr(response.content[0], 'text'):
                            tool_output_content = response.content[0].text
                        elif hasattr(response.content, 'text'):
                            tool_output_content = response.content.text
                        else:
                            tool_output_content = str(response.content)
                        
                        if not isinstance(tool_output_content, str):
                            tool_output_content = str(tool_output_content)
                    else:
                        tool_output_content = f"Tool '{tool_name}' returned no usable content."
                        await _log(tool_output_content)
            
            # Avoid printing base64 data for image generation
            if tool_name == "generate_image" and "IMAGE_GENERATED|" in str(tool_output_content):
                await _log(f"MCP tool '{tool_name}' completed successfully - image data ready")
            else:
                await _log(f"MCP tool '{tool_name}' raw output preview: {str(tool_output_content)}")

        except Exception as e:
            log_msg = f"Error during MCP tool '{tool_name}' call: {e}"
            await _log(log_msg)
            tool_output_content = f"The '{tool_name}' tool failed. Please proceed with available information."
        
        if not isinstance(tool_output_content, str):
            tool_output_content = str(tool_output_content) if tool_output_content is not None else f"Tool '{tool_name}' resulted in a non-string output which has been converted."

        tool_messages.append(ToolMessage(content=tool_output_content, tool_call_id=tool_call["id"]))
    
    return tool_messages 