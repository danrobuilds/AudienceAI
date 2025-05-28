from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from .vector import retriever as RetrieverTool
from langchain_core.documents import Document

load_dotenv("../.env")

# Create an MCP server
mcp = FastMCP(
    name="AudienceAIServer",
    host="0.0.0.0",  # only used for SSE transport (localhost)
    port=8050,  # only used for SSE transport (set this to any port)
)


# Add a simple calculator tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

# Add the vector search tool
@mcp.tool()
def search_linkedin_posts(query: str) -> str:
    """
    Search for viral LinkedIn posts using an embedding-based retriever.
    query (str): The topic or theme to search for in viral posts.
    Returns: str: Formatted examples of viral posts related to the query, or a message if no posts are found.
    """
    print(f"MCP Tool: Searching for viral posts with query: '{query}'")
    try:
        retrieved_docs = RetrieverTool.invoke(query)
        
        if not retrieved_docs:
            return "No relevant viral posts found for this topic using the vector database."
        
        results = []
        for i, doc in enumerate(retrieved_docs[:3]): # Limit to top 3 for conciseness
            result_text = f"Viral Post Example {i+1}:\nPage Content: {doc.page_content}\n"
            if doc.metadata:
                result_text += f"Source: {doc.metadata.get('source', 'N/A')}, Views: {doc.metadata.get('views', 'N/A')}, Reactions: {doc.metadata.get('reactions', 'N/A')}\n"
            results.append(result_text)
        
        return "\n---\n".join(results) if results else "No relevant viral posts found after formatting."

    except Exception as e:
        print(f"Error in MCP search_linkedin_posts tool: {e}")
        return f"Error retrieving viral posts: {str(e)}"


# Run the server
if __name__ == "__main__":
    transport = "sse"  # Default to SSE
    # The host and port are defined in the FastMCP constructor if using SSE
    # mcp.run will use those.
    # Default path for SSE with mcp package is typically /mcp or /sse.
    # If you need a specific path, you might pass it to mcp.run, e.g., mcp.run(transport="sse", path="/custom_mcp")
    
    print(f"Running server with {transport} transport on http://{mcp.host}:{mcp.port}/mcp (or /sse)")
    mcp.run(transport=transport)

    # Older logic commented out for clarity:
    # if transport == "stdio":
    #     print("Running server with stdio transport")
    #     mcp.run(transport="stdio")
    # elif transport == "sse":
    #     print("Running server with SSE transport")
    #     mcp.run(transport="sse") # host and port are from mcp instance
    # else:
    #     raise ValueError(f"Unknown transport: {transport}")
