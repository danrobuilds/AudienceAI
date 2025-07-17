import asyncio
from langchain_core.messages import ToolMessage

# Import the direct tool functions from individual files
from .search_document_library import search_document_library
from .search_linkedin_posts import search_linkedin_posts
from .web_search import web_search
from .image_web_search import image_web_search
from .generate_image import generate_image
from .create_diagram import create_diagram
from .search_blog_posts import search_blog_posts

# Tool Definitions (kept the same for compatibility)
search_document_library_mcp_tool_def = {
    "name": "search_document_library",
    "description": "Search the internal company knowledge base using an embedding-based retriever. Use this to find specific data or contextual information needed for the user's request.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The specific information or data to search for in company information documents."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

search_blog_posts_mcp_tool_def = {
    "name": "search_blog_posts",
    "description": "Search for successful blog posts using an embedding-based retriever. Use this to find examples of successful content structures that match the content type and themes you're creating.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A structured content brief of at least 50 words: The main message/key points you want to communicate, The content type - a detailed description of the structure and format of the post you want to create, The intended tone/style, The target audience context. "
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

search_linkedin_posts_mcp_tool_def = {
    "name": "search_linkedin_posts",
    "description": "Search for successful LinkedIn posts using an embedding-based retriever. Use this to find examples of successful posts that match the content type and themes you're creating.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A structured content brief of at least 50 words: The main message/key points you want to communicate, The content type - a detailed description of the structure and format of the post you want to create, The intended tone/style, The target audience context. "
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

web_search_mcp_tool_def = {
    "name": "web_search",
    "description": "Search the internet for information. Use this to find information that you wouldn't be able to find internally.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A structured content brief of at least 50 words containing: What SPECIFIC information do you want to find or understand? If about a specific company or person, what is the name? Where should the system look? What type of information and analytical depth should the system apply? How should the response be structured or returned?"
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

image_web_search_mcp_tool_def = {
    "name": "image_web_search",
    "description": "Search the web for specific images. Use to this to find generic, external images of places or organizations. Returns only image results with URLs and brief descriptions.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query for finding images. Describe what type of images, visual content, or visual references you're looking for."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

generate_image_mcp_tool_def = {
    "name": "generate_image",
    "description": "Create an AI-generated image. Use this if a more generic image is needed.",
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

create_diagram_mcp_tool_def = {
    "name": "create_diagram",
    "description": "Create custom tables, diagrams, charts, and visualizations using Mermaid syntax. Generate the complete, valid Mermaid code for the diagram. Use this to create tables, flowcharts, sequence diagrams, pie charts, mindmaps, and timelines that enhance post content with structured visual information.",
    "parameters": {
        "type": "object",
        "properties": {
            "mermaid_code": {
                "type": "string",
                "description": "Complete, valid Mermaid diagram code. Include the diagram type declaration (e.g., 'flowchart TD', 'pie title My Chart', 'mindmap', 'sequenceDiagram', 'timeline'). Ensure proper syntax and formatting for the specific diagram type."
            }
        },
        "required": ["mermaid_code"],
        "additionalProperties": False
    },
    "strict": True
}


# -------------------------- DIRECT TOOL CALLING LOGIC ------------------------------------------------------------

async def call_mcp_tools(llm_response, async_log_callback=None, tenant_id: str = ""):
    """
    Run all requested tool calls concurrently and return formatted results.
    This streamlined version removes verbose logging and excessive error handling.
    """

    if not llm_response.tool_calls:
        return [], []

    # Map tool names to callables
    tool_function_map = {
        "search_document_library": search_document_library,
        "search_linkedin_posts": search_linkedin_posts,
        "web_search": web_search,
        "image_web_search": image_web_search,
        "generate_image": generate_image,
        "create_diagram": create_diagram,
        "search_blog_posts": search_blog_posts,
    }

    generated_images = []

    async def run_tool(tool_call):
        tool_name = tool_call["name"]
        args = tool_call["args"]
        func = tool_function_map.get(tool_name)

        if func is None:
            return ToolMessage(content=f"Unknown tool '{tool_name}'", tool_call_id=tool_call["id"])

        # Build kwargs based on tool signature
        if tool_name == "generate_image":
            kwargs = {
                "prompt": args["prompt"],
                "style": args.get("style", "professional"),
                "aspect_ratio": args.get("aspect_ratio", "16:9"),
            }
        elif tool_name == "create_diagram":
            kwargs = {"mermaid_code": args["mermaid_code"]}
        elif tool_name == "search_document_library":
            kwargs = {"query": args["query"], "tenant_id": tenant_id}
        else:
            kwargs = {"query": args["query"]}

        try:
            if asyncio.iscoroutinefunction(func):
                output = await func(**kwargs)
            else:
                output = await asyncio.to_thread(func, **kwargs)
        except Exception as e:
            return ToolMessage(content=f"Error running '{tool_name}': {e}", tool_call_id=tool_call["id"])

        if isinstance(output, dict) and "base64_data" in output:
            generated_images.append(output)

        formatted = format_output_for_llm(tool_name, output) if isinstance(output, dict) else str(output)
        log_output = format_output_for_log(tool_name, output) if isinstance(output, dict) else str(output)
        if async_log_callback:
            await async_log_callback(log_output)

        return ToolMessage(content=formatted, tool_call_id=tool_call["id"])

    # Execute all tools in parallel
    tool_messages = await asyncio.gather(*(run_tool(tc) for tc in llm_response.tool_calls))

    return list(tool_messages), generated_images


def format_output_for_log(tool_name: str, tool_output_content: dict) -> str:
    
    lines = []

    if "error" in tool_output_content:
        return tool_output_content["error"]
    
    if tool_name == "generate_image" or tool_name == "create_diagram":
        lines.append("Image/Diagram generated successfully")
        lines.append(f"Filename: {tool_output_content['filename']}") 
        lines.append(f"Size: {tool_output_content['size']}") 
        lines.append("")
        return "\n".join(lines)
    
    if tool_name == "search_linkedin_posts":
        lines.append("Successfully found viral posts")
        lines.append("")  # Add consistent spacing
        for post in tool_output_content['viral_posts']:
            lines.append(f"Post Content: {post['content'][:50]}...")
            lines.append(f"Similarity Score: {post['similarity_score']}")
            lines.append("")
        return "\n".join(lines)
    
    if tool_name == "search_blog_posts":
        lines.append("Successfully found blog posts")
        lines.append("")  # Add consistent spacing
        for post in tool_output_content['blog_posts']:
            lines.append(f"Post Content: {post['content'][:50]}...")
            lines.append(f"Similarity Score: {post['similarity_score']}")
            lines.append("")
        return "\n".join(lines)

    if tool_name == "search_document_library":
        lines.append("Successfully found documents")
        lines.append("")  # Add consistent spacing
        for segment in tool_output_content['document_segments']:
            lines.append(f"Document Title: {segment['filename']}")
            lines.append(f"Document Content: {segment['content'][:50]}...")
            lines.append(f"Document URL: {segment['document_url']}")
            lines.append("")  # Separator between documents
        return "\n".join(lines)
    
    if tool_name == "web_search":
        lines.append("Successfully found web results")
        lines.append("")  # Add consistent spacing
        for result in tool_output_content['web_results']:
            lines.append(f"Web Title: {result['title'][:50]}...")
            lines.append(f"Web Content: {result['content'][:50]}...")
            lines.append(f"WebURL: {result['url']}")
            lines.append("")  # Separator between results
        return "\n".join(lines)
    
    if tool_name == "image_web_search":
        lines.append("Successfully found image results")
        lines.append("")  # Add consistent spacing
        for result in tool_output_content['image_results']:
            lines.append(f"Image URL: {result['url']}")
            lines.append(f"Image description: {result['title']}")
            lines.append("")  # Separator between images
        return "\n".join(lines)
    
    return "I don't know how to log this tool."


def format_output_for_llm(tool_name: str, tool_output_content: dict) -> str:
    lines = []

    if "error" in tool_output_content:
        return tool_output_content["error"]
    
    if tool_name == "generate_image" or tool_name == "create_diagram": #exclude base64 data for LLM
        lines.append("Image generated successfully")
        lines.append(f"Filename: {tool_output_content['filename']}") 
        lines.append(f"Size: {tool_output_content['size']}") 
        lines.append("")
        return "\n".join(lines)
    
    if tool_name == "search_linkedin_posts":
        lines.append("Successfully found viral posts")
        lines.append(f"Total posts: {tool_output_content['total_posts']}")
        for post in tool_output_content['viral_posts']:
            lines.append(f"Content: {post['content']}")
            lines.append(f"Target audience: {post['target_audience']}")
            lines.append(f"Media description: {post['media_description']}")
            lines.append("")
        lines.append("")
        return "\n".join(lines)

    if tool_name == "search_document_library":
        lines.append("Successfully found documents")
        for segment in tool_output_content['document_segments']:
            lines.append(f"Content: {segment['content']}")
            lines.append("")
        lines.append("")
        return "\n".join(lines)
    
    if tool_name == "web_search":
        lines.append("Successfully found web results")
        for result in tool_output_content['web_results']:
            lines.append(f"Title: {result['title']}")
            lines.append(f"Content: {result['content']}")
            lines.append("")
        lines.append("")
        return "\n".join(lines)
    
    if tool_name == "image_web_search":
        lines.append("Successfully found image results")
        for result in tool_output_content['image_results']:
            lines.append(f"Image description: {result['title']}")
            lines.append("")
        lines.append("")
        return "\n".join(lines)
    
    return "I don't know how to format this tool for the LLM."