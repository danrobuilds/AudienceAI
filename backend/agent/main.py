from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from openai import OpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
import json
import asyncio 
from mcp import ClientSession
from mcp.client.sse import sse_client
import mcp.types 
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

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
        server_url = "http://localhost:8050/sse" 
        tool_output_content = "" 
        tool_name = tool_call["name"]

        await _log(f"Calling MCP tool '{tool_name}' with args: {tool_args} via SSE")

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
            
            await _log(f"MCP tool '{tool_name}' raw output preview: {str(tool_output_content)}")

        except Exception as e:
            log_msg = f"Error during MCP tool '{tool_name}' call: {e}"
            await _log(log_msg)
            tool_output_content = f"The '{tool_name}' tool failed. Please proceed with available information."
        
        if not isinstance(tool_output_content, str):
            tool_output_content = str(tool_output_content) if tool_output_content is not None else f"Tool '{tool_name}' resulted in a non-string output which has been converted."

        tool_messages.append(ToolMessage(content=tool_output_content, tool_call_id=tool_call["id"]))
    
    return tool_messages

# Agent 1: Gather information
async def gather_information(user_prompt_text: str, llm, async_log_callback=None):
   
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log("\n=== PHASE 1: INFORMATION GATHERING ===")
    
    # Bind information gathering tools including web search
    llm_with_info_tools = llm.bind_tools(
        [search_document_library_mcp_tool_def, search_recent_news_mcp_tool_def, web_search_mcp_tool_def],
        tool_choice="auto"
    )
    
    info_system_message = """You are a research assistant. Your task is to gather comprehensive information relevant to the user's request for creating a LinkedIn post.

    Use the available tools to:
    1. Search the document library for relevant company/internal information
    2. Search for recent news articles that relate to the topic
    3. Perform general web searches for broader context and information

    Be thorough in your information gathering. Call multiple tools with different queries to get a wide range of relevant information.
    Your goal is to collect as much relevant context as possible, not to create the post yet.

    After gathering information, provide a detailed summary INCLUDING KEY FACTS AND NUMBERS of all the relevant information you found in a loose, unstructured format.
    """
    
    messages = [
        SystemMessage(content=info_system_message),
        HumanMessage(content=f"Gather comprehensive information for creating a LinkedIn post about: {user_prompt_text}")
    ]
    
    # Initial LLM call for information gathering
    try:
        await _log("Invoking LLM for information gathering...")
        info_response = await asyncio.wait_for(llm_with_info_tools.ainvoke(messages), timeout=60.0)
        messages.append(info_response)
        
        # Process tool calls if any
        if info_response.tool_calls:
            tool_messages = await call_mcp_tools(info_response, async_log_callback)
            messages.extend(tool_messages)
            
            # Get final information summary
            final_info_response = await asyncio.wait_for(llm_with_info_tools.ainvoke(messages), timeout=60.0)
            gathered_info = final_info_response.content
        else:
            gathered_info = info_response.content
            
        await _log(f"Information gathering complete. Gathered info preview: {str(gathered_info)}...")
        return gathered_info
        
    except Exception as e:
        await _log(f"Error during information gathering: {e}")
        return f"Information gathering encountered an error: {e}. Proceeding with available information."

# AGENT 2: Create viral post ------------------------------------------------------------
async def create_viral_post(user_prompt_text: str, gathered_info: str, llm, async_log_callback=None):
    
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log("\n=== PHASE 2: VIRAL POST CREATION ===")
    
    # Bind only LinkedIn post search tool
    llm_with_post_tools = llm.bind_tools(
        [search_linkedin_posts_mcp_tool_def],
        tool_choice="auto"
    )
    
    post_system_message = """You are a social media marketing expert for the company ABLSoft. Your task is to create a single viral LinkedIn post using the provided information and examples of successful posts.

    1. Use the search_linkedin_posts tool to find examples of viral posts related to the topic.
    2. Create a compelling LinkedIn post that:
        1. Uses the gathered information as context and facts
        2. Follows the structure and style of successful viral posts, take inspiration from emojis and hashtags and use them in your post
        3. Is engaging, authentic, and likely to go viral

    YOUR FINAL RESPONSE MUST BE ONLY THE LINKEDIN POST AND A ONE-SENTENCE IMAGE MEDIA GUIDELINE.
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
        
        # Process tool calls if any
        if post_response.tool_calls:
            tool_messages = await call_mcp_tools(post_response, async_log_callback)
            messages.extend(tool_messages)
            
            # Get final post
            final_post_response = await asyncio.wait_for(llm_with_post_tools.ainvoke(messages), timeout=120.0)
            final_post = final_post_response.content
        else:
            final_post = post_response.content
            
        await _log("Viral post creation complete.")
        return final_post
        
    except Exception as e:
        await _log(f"Error during post creation: {e}")
        return f"Post creation encountered an error: {e}"
    

# MAIN FUNCTION FOR ORCHESTRATING AGENTS ------------------------------------------------------------
async def generate_post_for_prompt(user_prompt_text: str, async_log_callback: callable = None):
   
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    try:
        # llm = ChatOllama(model="llama3.1:8b", request_timeout=120.0)
        # await _log("LLM initialized successfully")
        llm = ChatOpenAI(
            model="gpt-4o", 
            request_timeout=120.0, 
            temperature=0.7,
            model_kwargs={"response_format": {"type": "text"}}
        )
        await _log("GPT-4o LLM initialized successfully with Responses API")
        
        # Agent 1: Information Gathering
        gathered_info = await gather_information(user_prompt_text, llm, async_log_callback)
        
        # Agent 2: Viral Post Creation
        final_post = await create_viral_post(user_prompt_text, gathered_info, llm, async_log_callback)
        
        return final_post
        
    except Exception as llm_error:
        await _log(f"Failed to create ChatOpenAI or process request: {llm_error}")
        raise llm_error
        
    

