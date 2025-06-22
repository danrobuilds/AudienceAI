import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .tools import (
    search_document_library_mcp_tool_def, 
    search_recent_news_mcp_tool_def, 
    web_search_mcp_tool_def,
    call_mcp_tools
)

async def gather_information(user_prompt_text: str, llm, async_log_callback=None):
    """
    Agent 1: Gather comprehensive information relevant to the user's request.
    
    Args:
        user_prompt_text: The user's request for creating a LinkedIn post
        llm: The language model instance
        async_log_callback: Optional logging callback function
    
    Returns:
        String containing gathered information
    """
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