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
    
    # Bind information gathering tools including web search
    llm_with_info_tools = llm.bind_tools(
        [search_document_library_mcp_tool_def, web_search_mcp_tool_def],
        tool_choice="auto"
    )
    
    info_system_message = f"""
    
    {company_context} 
    
    Your task is to gather comprehensive information relevant to the user's request for creating a social media post.

    USE ONLY WHAT IS STRICTLY NECESSARY TO REMAIN FOCUSED ON THE USER'S REQUEST.

    After gathering information, provide a detailed summary INCLUDING KEY FACTS AND NUMBERS of the most relevant information.
    """
    
    messages = [
        SystemMessage(content=info_system_message),
        HumanMessage(content=f"Gather comprehensive information for creating a social media post about: {user_prompt_text}")
    ]
    
    # Simple limits
    max_rounds = 5
    
    try:
        for round_num in range(max_rounds):
            await _log(f"Round {round_num + 1}: Gathering information...")
            
            response = await llm_with_info_tools.ainvoke(messages)
            messages.append(response)
            
            # If no tool calls, we're done
            if not response.tool_calls:
                return response.content
                
            # Execute tool calls
            tool_messages, _ = await call_mcp_tools(response, async_log_callback, tenant_id)
            messages.extend(tool_messages)
            
            # Call LLM again to process tool results
            await _log(f"Processing tool results...")
            follow_up_response = await llm_with_info_tools.ainvoke(messages + [
                HumanMessage(content="If this information does not fully satisfy the user's request, continue searching. Otherwise, provide a detailed summary.")
            ])
            messages.append(follow_up_response)
            
            # If no more tool calls, we're done
            if not follow_up_response.tool_calls:
                return follow_up_response.content
        
        # If we hit max rounds, get final summary
        final_response = await llm_with_info_tools.ainvoke(messages + [
            HumanMessage(content="Provide your final summary of the relevant information gathered.")
        ])
        
        return final_response.content
        
    except Exception as e:
        await _log(f"Error: {e}")
        return f"Information gathering error: {e}" 