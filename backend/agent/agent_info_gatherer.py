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
        
        Your task is to gather comprehensive information relevant to the user's request for creating a marketing post.

        USE ONLY WHAT IS STRICTLY NECESSARY TO REMAIN FOCUSED ON THE USER'S REQUEST.

        YOU MUST ALWAYS USE AT LEAST ONE OF THE AVAILABLE TOOLS TO GATHER INFORMATION - DO NOT RELY ON YOUR TRAINING DATA.

        For example:
        - "Make a post about Jim Johnson" -> search document library for information about Jim Johnson
        - "Make a post about how we're revolutionizing the real estate industry" -> search document library for features, search the web for how the industry is lagging behind
        - "Make a post about client success stories" -> search document library for information about client success stories
        - "Make a post about the latest trends in AI" -> search the web for the latest trends in AI in the company's industry
        - "Make a post comparing us to one of our competitors, Solifi" -> search document library for info about our features, search the web for Solifi features.

        After gathering information, list all of the KEY FACTS, CONCEPTS, AND NUMBERS pertaining to the most relevant information.
        When users indicate that current information is wrong or incomplete, you MUST search for accurate information using the available tools.
    """
    
    messages = [
        SystemMessage(content=info_system_message),
        HumanMessage(content=f"Gather comprehensive information for creating a social media post about: {user_prompt_text}\n\nIMPORTANT: You must start by using the available tools to search for current and accurate information. Do not provide any response until you have gathered information using the tools.")
    ]
    
    # Simple limits
    max_rounds = 2
    
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
                HumanMessage(content="Original prompt: {user_prompt_text}. If not relevant information, continue searching with completely different prompts. Otherwise, provide a detailed summary. Example: Original prompt: make a post about jim johnson. Returns: no info on jim johnson. -> query web tool again")
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