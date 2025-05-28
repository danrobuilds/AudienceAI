from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
# from langchain_core.tools import tool # No longer defining local tools
# from langchain_core.documents import Document # Not directly used here anymore
import json
import asyncio # For async operations
# import os # No longer needed for path to server script

# MCP Client imports from the 'mcp' package
from mcp import ClientSession, SSEClientParameters, types # Changed to SSEClientParameters
from mcp.client.sse import sse_client # Changed to sse_client

# Define the tool for the LLM, which will now call the MCP server
# The definition for the LLM needs to match the MCP tool's signature
search_linkedin_posts_mcp_tool_def = {
    "name": "search_linkedin_posts",
    "description": "Search for viral LinkedIn posts using an embedding-based retriever. Use this to find examples of successful posts on a given topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The topic or theme to search for in viral posts."
            }
        },
        "required": ["query"]
    }
}

async def main(): # Changed to async
    llm = ChatOllama(model="llama3.1:8b") 
    # Pass the MCP tool definition to the LLM
    llm_with_tools = llm.bind_tools([search_linkedin_posts_mcp_tool_def], tool_choice=True) # Added tool_choice=True

    user_prompt_text = input("prompt: ")

    system_message_content = """You are a social media marketing employee. Your task is to write a single LinkedIn post for the user.

                            IMPORTANT INSTRUCTIONS:
                            1. First, use the 'search_linkedin_posts' tool to find viral post examples related to the user's topic. This tool is remotely hosted.
                            2. Then, write a LinkedIn post that draws inspiration from those viral examples.
                            3. Include a brief one-sentence guideline for media at the end of the post.
                            4. Do not provide guidelines or explanations beyond the post itself - write the post.

                            Company information to incorporate: "Don't let legacy processes hold you back. Harness ABLSoft to automate BBC Processing, simplify the borrower experience and track loan performance – all in one secure platform."

                            Follow this process:
                            1. Based on the user's prompt, decide if you need to search for viral posts. If so, call the 'search_linkedin_posts' tool with an appropriate query.
                            2. Analyze the format and style of any successful posts returned by the tool.
                            3. Create a LinkedIn post incorporating these successful patterns and the provided company information.
                            """
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content=user_prompt_text),
    ]

    print("\nAnalyzing user prompt and potentially searching for viral posts via MCP (SSE)...")

    ai_msg = await llm_with_tools.ainvoke(messages) # Changed to ainvoke
    messages.append(ai_msg)

    if ai_msg.tool_calls:
        print(f"\nLLM decided to use a tool: {ai_msg.tool_calls[0]['name']}")
        for tool_call in ai_msg.tool_calls:
            tool_args = tool_call["args"]
            
            if tool_call["name"] == "search_linkedin_posts":
                print(f"Calling MCP tool 'search_linkedin_posts' with args: {tool_args} via SSE")
                
                # SSE Client Parameters - assumes server.py runs on localhost:8050 with /mcp path
                # The port 8050 and path /mcp are common defaults but might need adjustment
                # based on how server.py is run with mcp.run(transport="sse", ...)
                server_params = SSEClientParameters(url="http://localhost:8050/mcp")
                
                tool_output = ""
                try:
                    # Using sse_client context manager
                    async with sse_client(server_params) as (read_stream, write_stream, _): # sse_client returns a 3rd element
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            response = await session.call_tool(
                                "search_linkedin_posts", 
                                arguments=tool_args
                            )
                            if response.type == types.ToolResultType.TOOL_RESULT:
                                tool_output = response.content.text if response.content else ""
                            elif response.type == types.ToolResultType.TOOL_ERROR:
                                tool_output = f"Tool Error: {response.error.message if response.error else 'Unknown MCP tool error'}"
                                print(f"MCP Tool Error: {tool_output}")
                            else:
                                tool_output = f"Unknown MCP response type: {response.type}"
                                print(tool_output)
                            
                    print(f"MCP tool output: {tool_output}")
                except ConnectionRefusedError:
                    print(f"Error calling MCP tool: Connection refused. Is the MCP server running at {server_params.url}?")
                    tool_output = f"Error: Could not connect to MCP server at {server_params.url}. Please ensure it is running with SSE transport."
                except Exception as e:
                    print(f"Error calling MCP tool: {e}")
                    tool_output = f"Error executing tool via MCP (SSE): {str(e)}"
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
            else:
                error_msg = f"Error: Tool {tool_call['name']} not found or not correctly mapped."
                print(error_msg)
                messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call["id"]))
        
        print("\nGenerating LinkedIn post based on tool output and user prompt...")
        # The LLM needs to be invoked again with the tool results
        # Ensure the tool definition is still available if llm.bind_tools is used for subsequent calls
        final_response_msg = await llm.bind_tools([search_linkedin_posts_mcp_tool_def]).ainvoke(messages) # Changed to ainvoke
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
