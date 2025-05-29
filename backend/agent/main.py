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
    "description": "Search the internal PDF document library on company information using an embedding-based retriever. Use this to find relevant information for the user's prompt.",
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
    "description": "Search for viral LinkedIn posts using an embedding-based retriever. Use this to find examples of successful posts on a given topic.",
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
    "description": "Search for recent news articles based on a query. Use this to find recent, relevant information for use in the post.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Pick several keywords to search for in the article title and body. "
                    "Separate each single word with the OR operator. "
                    "Only use common words and OR operator. Do not use over complicated queries because they will not return any results."
                    "The complete value for q must be URL-encoded. Max length: 500 chars."
                )
            },
            "sort_by": {
                "type": "string",
                "description": "The sorting criteria for the news articles. Decide which is more relevant to the user's prompt. Can be 'publishedAt' or 'relevancy'."
            }
        },
        "required": ["query", "sort_by"]
    }
}

async def main(): # Changed to async
    llm = ChatOllama(model="llama3.1:8b") 
    # Pass the MCP tool definitions to the LLM
    llm_with_tools = llm.bind_tools([search_linkedin_posts_mcp_tool_def, search_recent_news_mcp_tool_def, search_document_library_mcp_tool_def]) 

    user_prompt_text = input("prompt: ")

    system_message_content = """You are a social media marketing employee. Your task is to write a single LinkedIn post for the user.

                            IMPORTANT INSTRUCTIONS:
                            1. Use the 'search_document_library' tool to find relevant contextual information from the company's internal documents.
                            2. Determine whether to use the 'search_linkedin_posts' tool to find viral post examples related to the user's query.
                            3. Determine based on the user's query if you need to use the 'search_recent_news' tool to gather current information or news relevant to the user's topic. This tool is remotely hosted.
                            4. Then, write a LinkedIn post that draws inspiration from viral examples (if found) and incorporates relevant news (if found).
                            5. Include a brief one-sentence guideline for media at the end of the post.
                            6. Do not provide guidelines or explanations beyond the post itself - write the post.

                            Company information to draw from if necessary given the user's query: 
                                - ABLSoft is a software company providing asset based lending solutions. 
                                - Don't let legacy processes hold you back. Harness ABLSoft to automate BBC Processing, simplify the borrower experience and track loan performance – all in one secure platform.
                                - Lend with Confidence. ABL Expertise. Personalized Service.
                                - Effortless Borrowing Base. Save time and automate your BBC intake process. Standardize and map data from Excel, PDFs, online BBC entry, even directly from borrowers’ accounting systems.
                                - Intelligent Processing Onboard any deal (AR, inventory, term) and customize as needed (sublimits, ineligibles, lockbox). Instantly calculate availability and streamline advance approvals.
                                - Seamless Insights. Get immediate visibility with real-time dashboards and 30+ standard reports. Design your own reports in minutes to track borrower performance and compliance.
                                

                            Follow this process:
                            1. Based on the user's prompt, decide if you need to search for viral posts and/or recent news. If so, call the appropriate tool(s) with relevant queries.
                            2. Analyze the format and style of any successful posts and the content of any news articles returned by the tool(s).
                            3. Create a LinkedIn post incorporating these successful patterns, relevant news, and the provided company information.
                            """
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content=user_prompt_text),
    ]

    print("\nAnalyzing user prompt and potentially using tools via MCP (SSE)...")

    ai_msg = await llm_with_tools.ainvoke(messages) 
    messages.append(ai_msg)

    if ai_msg.tool_calls:
        print(f"\nLLM decided to use a tool: {ai_msg.tool_calls[0]['name']}")
        for tool_call in ai_msg.tool_calls:
            tool_args = tool_call["args"]

            # local server url
            server_url = "http://localhost:8050/sse" 
            tool_output = ""
            
            # MCP tool for company information
            if tool_call["name"] == "search_document_library":
                print(f"Calling MCP tool 'search_document_library' with args: {tool_args} via SSE")
                
                try:
                    async with sse_client(server_url) as (read_stream, write_stream):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            response = await session.call_tool(
                                "search_document_library", 
                                arguments=tool_args
                            )
                            if hasattr(response, 'error') and response.error:
                                error_message = getattr(response.error, 'message', str(response.error))
                                tool_output = f"Tool Error: {error_message}"
                                print(f"MCP Tool Error: {tool_output}")
                            elif hasattr(response, 'content') and response.content:
                                if isinstance(response.content, list) and len(response.content) > 0 and hasattr(response.content[0], 'text'):
                                    tool_output = response.content[0].text
                                elif hasattr(response.content, 'text'):
                                    tool_output = response.content.text
                                else:
                                    tool_output = str(response.content) 
                            else:
                                tool_output = "Unknown MCP tool response structure or empty result."
                                print(tool_output)
                            
                    print(f"MCP tool output: {tool_output}")
                except ConnectionRefusedError:
                    print(f"Error calling MCP tool: Connection refused. Is the MCP server running at {server_url}?")
                    tool_output = f"Error: Could not connect to MCP server at {server_url}. Please ensure it is running with SSE transport."
                except Exception as e:
                    import traceback # Add for more detailed client-side error
                    print(f"Error calling MCP tool (client-side full traceback): {e}")
                    traceback.print_exc()
                    tool_output = f"Error executing tool via MCP (SSE): {str(e)}"
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

            # MCP tool for viral posts
            if tool_call["name"] == "search_linkedin_posts":
                print(f"Calling MCP tool 'search_linkedin_posts' with args: {tool_args} via SSE")
                
                try:
                    async with sse_client(server_url) as (read_stream, write_stream):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            response = await session.call_tool(
                                "search_linkedin_posts", 
                                arguments=tool_args
                            )
                            if hasattr(response, 'error') and response.error:
                                error_message = getattr(response.error, 'message', str(response.error))
                                tool_output = f"Tool Error: {error_message}"
                                print(f"MCP Tool Error: {tool_output}")
                            elif hasattr(response, 'content') and response.content:
                                # Handle response format
                                if isinstance(response.content, list) and len(response.content) > 0 and hasattr(response.content[0], 'text'):
                                    tool_output = response.content[0].text
                                elif hasattr(response.content, 'text'):
                                    tool_output = response.content.text
                                else:
                                    tool_output = str(response.content) 
                            else:
                                tool_output = "Unknown MCP tool response structure or empty result."
                                print(tool_output)
                            
                    print(f"MCP tool output: {tool_output}")
                except ConnectionRefusedError:
                    print(f"Error calling MCP tool: Connection refused. Is the MCP server running at {server_url}?")
                    tool_output = f"Error: Could not connect to MCP server at {server_url}. Please ensure it is running with SSE transport."
                except Exception as e:
                    import traceback # Add for more detailed client-side error
                    print(f"Error calling MCP tool (client-side full traceback): {e}")
                    traceback.print_exc()
                    tool_output = f"Error executing tool via MCP (SSE): {str(e)}"
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
            
            # MCP tool for recent news
            elif tool_call["name"] == "search_recent_news":
                print(f"Calling MCP tool 'search_recent_news' with args: {tool_args} via SSE")
                
                try:
                    async with sse_client(server_url) as (read_stream, write_stream):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            response = await session.call_tool(
                                "search_recent_news", 
                                arguments=tool_args
                            )
                            if hasattr(response, 'error') and response.error:
                                error_message = getattr(response.error, 'message', str(response.error))
                                tool_output = f"Tool Error: {error_message}"
                                print(f"MCP Tool Error: {tool_output}")
                            elif hasattr(response, 'content') and response.content:
                                if isinstance(response.content, list) and len(response.content) > 0 and hasattr(response.content[0], 'text'):
                                    tool_output = response.content[0].text
                                elif hasattr(response.content, 'text'):
                                    tool_output = response.content.text
                                else:
                                    tool_output = str(response.content) 
                            else:
                                tool_output = "Unknown MCP tool response structure or empty result for news search."
                                print(tool_output)

                    print(f"MCP tool 'search_recent_news' output: {tool_output}")
                except ConnectionRefusedError:
                    print(f"Error calling MCP tool: Connection refused. Is the MCP server running at {server_url}?")
                    tool_output = f"Error: Could not connect to MCP server at {server_url}. Please ensure it is running with SSE transport."
                except Exception as e:
                    import traceback 
                    print(f"Error calling MCP tool 'search_recent_news' (client-side full traceback): {e}")
                    traceback.print_exc()
                    tool_output = f"Error executing tool 'search_recent_news' via MCP (SSE): {str(e)}"
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])) # Ensure this uses str(tool_output)
                
            else:
                error_msg = f"Error: Tool {tool_call['name']} not found or not correctly mapped."
                print(error_msg)
                messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call["id"]))
        
        print("\nGenerating LinkedIn post based on tool output and user prompt...")
        # The LLM needs to be invoked again with the tool results
        # Ensure all tool definitions are available if llm.bind_tools is used for subsequent calls
        final_response_msg = await llm.bind_tools([search_document_library_mcp_tool_def, search_linkedin_posts_mcp_tool_def, search_recent_news_mcp_tool_def]).ainvoke(messages) 
        generated_content = final_response_msg.content
    else:
        print("\nLLM decided not to use a tool. Generating post directly...")
        generated_content = ai_msg.content

    print("\n" + "="*50)
    print("GENERATED LINKEDIN POST:")
    print("="*50)
    print(generated_content)

if __name__ == "__main__":
    asyncio.run(main()) # Run the async main function
