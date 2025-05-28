from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.documents import Document # For type hinting
import json

# Import the existing retriever from vector.py
from vector import retriever as RetrieverTool # Renamed to avoid conflict if any

@tool
def search_viral_posts_tool(query: str) -> str:
    """
    Search for viral LinkedIn posts using an embedding-based retriever.
    query (str): The topic or theme to search for in viral posts.
    Returns: str: Formatted examples of viral posts related to the query, or a message if no posts are found.
    """
    print(f"Tool: Searching for viral posts with query: '{query}'")
    try:
        # Use the retriever from vector.py
        retrieved_docs = RetrieverTool.invoke(query)
        
        if not retrieved_docs:
            return "No relevant viral posts found for this topic using the vector database."
        
        # Format the retrieved LangChain Documents into a string
        results = []
        for i, doc in enumerate(retrieved_docs[:3]): # Limit to top 3 for conciseness in prompt
            result_text = f"Viral Post Example {i+1}:\nPage Content: {doc.page_content}\n"
            if doc.metadata:
                result_text += f"Source: {doc.metadata.get('source', 'N/A')}, Views: {doc.metadata.get('views', 'N/A')}, Reactions: {doc.metadata.get('reactions', 'N/A')}\n"
            results.append(result_text)
        
        return "\n---\n".join(results) if results else "No relevant viral posts found after formatting."

    except Exception as e:
        print(f"Error in search_viral_posts_tool: {e}")
        return f"Error retrieving viral posts: {str(e)}"



def main():
    llm = ChatOllama(model="llama3.1:8b") 
    llm_with_tools = llm.bind_tools([search_viral_posts_tool])

    user_prompt_text = input("prompt: ")

    system_message_content = """You are a social media marketing employee. Your task is to write a single LinkedIn post for the user.

                            IMPORTANT INSTRUCTIONS:
                            1. First, use the 'search_viral_posts_tool' to find viral post examples related to the user's topic.
                            2. Then, write a LinkedIn post that draws inspiration from those viral examples.
                            3. Include a brief one-sentence guideline for media at the end of the post.
                            4. Do not provide guidelines or explanations beyond the post itself - write the post.

                            Company information to incorporate: "Don't let legacy processes hold you back. Harness ABLSoft to automate BBC Processing, simplify the borrower experience and track loan performance – all in one secure platform."

                            Follow this process:
                            1. Based on the user's prompt, decide if you need to search for viral posts. If so, call the 'search_viral_posts_tool' with an appropriate query.
                            2. Analyze the format and style of any successful posts returned by the tool.
                            3. Create a LinkedIn post incorporating these successful patterns and the provided company information.
                            """
    messages = [
        SystemMessage(content=system_message_content),
        HumanMessage(content=user_prompt_text),
    ]

    print("\nAnalyzing user prompt and potentially searching for viral posts...")

    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if ai_msg.tool_calls:
        print(f"\nLLM decided to use a tool: {ai_msg.tool_calls[0]['name']}")
        for tool_call in ai_msg.tool_calls:
            # The tool_call["args"] from ChatOllama with .bind_tools already comes as a dict
            # e.g. {'query': 'some search term'}
            tool_args = tool_call["args"]
            
            # Ensure the argument name matches what the tool expects (e.g., 'query')
            # If there's a mismatch or if args are nested, adjust parsing accordingly.
            # For a simple tool like ours, direct passing of args should work if names match.
            
            if tool_call["name"] == "search_viral_posts_tool":
                tool_output = search_viral_posts_tool.invoke(tool_args) 
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
            else:
                error_msg = f"Error: Tool {tool_call['name']} not found or not correctly mapped."
                print(error_msg)
                messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call["id"]))
        
        print("\nGenerating LinkedIn post based on tool output and user prompt...")
        final_response_msg = llm_with_tools.invoke(messages)
        generated_content = final_response_msg.content
    else:
        print("\nLLM decided not to use a tool. Generating post directly...")
        generated_content = ai_msg.content

    print("\n" + "="*50)
    print("GENERATED LINKEDIN POST:")
    print("="*50)
    print(generated_content)

if __name__ == "__main__":
    main()
