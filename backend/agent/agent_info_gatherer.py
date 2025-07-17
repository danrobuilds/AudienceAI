import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from tools.tool_calling import (
    search_document_library_mcp_tool_def, 
    web_search_mcp_tool_def,
    call_mcp_tools
)

async def gather_information(user_prompt_text: str, llm, async_log_callback=None, company_context: str = "", tenant_id: str = ""):
    """
    Agent 1: Gather comprehensive information relevant to the user's request.
    """
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[LOG] {message}") 

    await _log("\n=== PHASE 1: INFORMATION GATHERING ===")
    
    llm_with_info_tools = llm.bind_tools(
        [search_document_library_mcp_tool_def, web_search_mcp_tool_def],
        tool_choice="auto"
    )
    
    info_system_message = f"""
        {company_context} 
        
        Your task is to act as a researcher. You will be given a user's request for a marketing post, and your goal is to gather comprehensive information for that post.

        - You MUST use the available tools to find relevant information. Do not answer from your own knowledge.
        - If a tool returns no relevant information, try searching again with a different, more specific, or broader query.
        - After you have finished calling tools and believe you have enough information, provide a detailed summary of your findings. List all of the KEY FACTS, CONCEPTS, AND NUMBERS.
        
        Example flow:
        1. User asks for a post about a new feature.
        2. You use `search_document_library` to find company specific documents about the feature.
        3. You use `web_search` to find market data or competitor information related to this feature.
        4. After gathering sufficient information, you stop using tools and provide a summary of what you found.
    """

    info_human_message = f"Please gather information for this request: '{user_prompt_text}'"
    
    messages = [SystemMessage(content=info_system_message), HumanMessage(content=info_human_message)]
    
    max_rounds = 2
    
    try:
        final_content = "Information gathering was inconclusive."
        for round_num in range(max_rounds):
            await _log(f"Round {round_num + 1}/{max_rounds}: Calling model...")
            
            response = await llm_with_info_tools.ainvoke(messages)
            
            if not response.tool_calls:
                await _log("Model finished gathering information.")
                final_content = response.content
                break
            
            messages.append(response)
            
            await _log(f"Executing tools: {[tc['name'] for tc in response.tool_calls]}")
            tool_messages, _ = await call_mcp_tools(response, async_log_callback, tenant_id)
            messages.extend(tool_messages)

            follow_up_response = await llm_with_info_tools.ainvoke(messages + [
                HumanMessage(content=f"""
                             Decide if you have gathered enough information. 
                             If you have, provide a detailed summary of your findings and do not call anymore tools.
                             List all of the KEY FACTS, CONCEPTS, AND NUMBERS.
                             """)])
            
            return follow_up_response

        return final_content
        
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        await _log(f"Error in information gathering: {e}\n{tb_str}")
        return f"Information gathering error: {e}" 