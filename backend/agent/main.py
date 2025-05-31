from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
# from langchain_core.tools import tool # No longer defining local tools
# from langchain_core.documents import Document # Not directly used here anymore
import json
import asyncio # For async operations
# import os # No longer needed for path to server script

# MCP Client imports from the 'mcp' package
from mcp import ClientSession
from mcp.client.sse import sse_client
import mcp.types # Import mcp.types directly

# Define the tool for the LLM, which will now call the MCP server
# The definition for the LLM needs to match the MCP tool's signature
search_document_library_mcp_tool_def = {
    "name": "search_document_library",
    "description": "Search the internal PDF document library on company information using an embedding-based retriever. Use this to find relevant information for the user's prompt about ABLSoft or related topics.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The topic or theme to search for in company information documents."
            }
        },
        "required": ["query"]
    }
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
        "required": ["query"]
    }
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
                "description": "The sorting criteria for the news articles. Decide which is more relevant to the user's prompt. Can be 'publishedAt' or 'relevancy'. Default to 'relevancy' if unsure."
            }
        },
        "required": ["query", "sort_by"]
    }
}

# Renamed and refactored main function
async def generate_post_for_prompt(user_prompt_text: str, async_log_callback: callable = None):
    # logs = [] # No longer collecting logs here, will use callback
    async def _log(message):
        if async_log_callback:
            await async_log_callback(message)
        # else:
            # Optionally print to console if no callback is provided (for backend debugging)
            # print(message)

    llm = ChatOllama(model="llama3.1:8b") 
    llm_with_tools = llm.bind_tools([search_linkedin_posts_mcp_tool_def, search_recent_news_mcp_tool_def, search_document_library_mcp_tool_def]) 

    # user_prompt_text = input("prompt: ") # Removed input

    system_message_content = """You are a social media marketing employee. Your task is to write a single viral LinkedIn post for the user.

                            YOUR RESPONSE MUST BE ONLY THE LINKEDIN POST AND A ONE-SENTENCE MEDIA GUIDELINE.
                            ABSOLUTELY NO PRE-AMBLE, EXPLANATIONS, APOLOGIES, OR CONVERSATIONAL FILLER.

                            Follow this process internally, but do not describe it in your output:
                            1. To help make the post VIRAL, you SHOULD strongly prioritize using the 'search_linkedin_posts' tool to find viral post examples related to the user's query. Analyze the structure, style, and common elements of these successful posts.
                            2. Use the 'search_document_library' tool to find relevant contextual information from the company's internal documents to incorporate into the post, if applicable to the user's request.
                            3. Based on the user's query AND the content of potential viral posts, determine if you also need to use the 'search_recent_news' tool to gather current, relevant information.
                            4. Silently analyze the results from any tools used. If a tool returns an error, an empty result, or irrelevant information, acknowledge this internally and proceed to write the best post possible using any other successfully retrieved information and the original prompt. Do not mention the tool's failure or shortcomings in your final output. Your goal is to create a compelling post regardless of tool issues.
                            5. Write a LinkedIn post that draws inspiration from viral examples (if found) and incorporates relevant news (if found and relevant) and company information.
                            6. Conclude your response with a single, brief one-sentence guideline for media on a new line after the post. Example: "Media: A dynamic image representing innovation in finance."

                            Company information to draw from if necessary given the user's query (use this information silently):
                                - ABLSoft is a software company providing asset based lending solutions. 
                                - Don't let legacy processes hold you back. Harness ABLSoft to automate BBC Processing, simplify the borrower experience and track loan performance – all in one secure platform.
                                - Lend with Confidence. ABL Expertise. Personalized Service.
                                - Effortless Borrowing Base. Save time and automate your BBC intake process. Standardize and map data from Excel, PDFs, online BBC entry, even directly from borrowers' accounting systems.
                                - Intelligent Processing Onboard any deal (AR, inventory, term) and customize as needed (sublimits, ineligibles, lockbox). Instantly calculate availability and streamline advance approvals.
                                - Seamless Insights. Get immediate visibility with real-time dashboards and 30+ standard reports. Design your own reports in minutes to track borrower performance and compliance.
                            """
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content=user_prompt_text),
    ]

    await _log("\nAnalyzing user prompt and potentially using tools via MCP (SSE)...")

    ai_msg = await llm_with_tools.ainvoke(messages) 
    messages.append(ai_msg)

    if ai_msg.tool_calls:
        await _log(f"\nLLM decided to use a tool: {ai_msg.tool_calls[0]['name']}")
        for tool_call in ai_msg.tool_calls:
            tool_args = tool_call["args"]
            server_url = "http://localhost:8050/sse" 
            tool_output_content = "" # Initialize to empty string
            
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
                        elif hasattr(response, 'content') and response.content is not None: # Check content is not None
                            if isinstance(response.content, list) and len(response.content) > 0 and hasattr(response.content[0], 'text'):
                                tool_output_content = response.content[0].text
                            elif hasattr(response.content, 'text'): # Check if content itself has text
                                tool_output_content = response.content.text
                            else:
                                tool_output_content = str(response.content) # Fallback to string representation
                            
                            # Ensure tool_output_content is a string if it was derived from response.content
                            if not isinstance(tool_output_content, str):
                                tool_output_content = str(tool_output_content)

                        elif response.content is None and not (hasattr(response, 'error') and response.error):
                             tool_output_content = f"Tool '{tool_name}' returned no specific content or error. This might indicate no results found or an issue."
                             await _log(tool_output_content)
                        else:
                            tool_output_content = f"Unknown MCP tool response structure or empty result for '{tool_name}'."
                            await _log(tool_output_content)
                
                await _log(f"MCP tool '{tool_name}' raw output preview: {str(tool_output_content)[:200]}...") # Log a preview

            except ConnectionRefusedError:
                log_msg = f"Error calling MCP tool '{tool_name}': Connection refused. Is the MCP server running at {server_url}?"
                await _log(log_msg)
                tool_output_content = f"Error: Could not connect to MCP server for tool '{tool_name}'. Please ensure it is running with SSE transport."
            except Exception as e:
                import traceback 
                log_msg = f"Error during MCP tool '{tool_name}' call (client-side full traceback): {e}"
                await _log(log_msg)
                # await _log(traceback.format_exc()) # Optionally add full traceback to logs
                tool_output_content = f"The '{tool_name}' tool failed to execute or return valid data due to a client-side or communication error: {str(e)}. Please proceed based on other available information and the user's original request."
            
            # Ensure tool_output_content is always a string before appending to ToolMessage
            if not isinstance(tool_output_content, str):
                tool_output_content = str(tool_output_content) if tool_output_content is not None else f"Tool '{tool_name}' resulted in a non-string output which has been converted."

            messages.append(ToolMessage(content=tool_output_content, tool_call_id=tool_call["id"]))
        
        await _log("\nGenerating LinkedIn post based on tool output and user prompt...")
        # Bind tools again for the final response generation, in case LLM needs to re-evaluate or summarize.
        final_response_msg = await llm.bind_tools([search_document_library_mcp_tool_def, search_linkedin_posts_mcp_tool_def, search_recent_news_mcp_tool_def]).ainvoke(messages) 
        generated_content_final = final_response_msg.content
    else:
        await _log("\nLLM decided not to use a tool. Generating post directly...")
        generated_content_final = ai_msg.content

    return generated_content_final

# Removed: if __name__ == "__main__":
# Removed:     asyncio.run(main())
