from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from .vector import retriever as RetrieverTool
from langchain_core.documents import Document
from .news import get_news


load_dotenv("../.env")

# These are the intended host and port for the SSE server
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8050

# Create an MCP server
mcp = FastMCP(
    name="AudienceAIServer",
    host=SERVER_HOST,  # Pass to FastMCP constructor
    port=SERVER_PORT,  # Pass to FastMCP constructor
)


# Add a news search tool
@mcp.tool()
def search_recent_news(query: str, sort_by: str = "publishedAt") -> str:
    """Use NewsAPI to search for recent news articles based on a query."""
    print(f"MCP Tool: Searching for recent news with query: '{query}', sort_by: '{sort_by}'")

    news_data = get_news(query, sort_by)
    
    if news_data.get('status') != 'ok' or not news_data.get('articles'):
        return "Could not retrieve news articles or no articles found."

    articles = news_data.get('articles', [])
    if not articles:
        return "No news articles found for your query."

    formatted_articles = []
    for i, article in enumerate(articles[:5]): # Ensure we only process up to 5
        title = article.get('title', 'N/A')
        source_name = article.get('source', {}).get('name', 'N/A')
        description = article.get('description', 'No description available.')
        if not description: # Handle empty description string
            description = "No description available."
        url = article.get('url', 'N/A')
        
        formatted_article = (
            f"Article {i+1}:\n"
            f"  Title: {title}\n"
            f"  Source: {source_name}\n"
            f"  Description: {description}\n"
            f"  URL: {url}"
        )
        formatted_articles.append(formatted_article)
    
    return "\n\n---\n\n".join(formatted_articles) if formatted_articles else "No news articles could be formatted."


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


def start_mcp_server():
    """Initializes and runs the MCP server."""
    transport = "sse"  # Default to SSE
    # The host and port are defined in the FastMCP constructor and used by mcp.run()
    
    # Use the locally defined SERVER_HOST and SERVER_PORT for the print statement
    print(f"Attempting to run server with {transport} transport on http://{SERVER_HOST}:{SERVER_PORT}/mcp (or /sse)")
    # The mcp.run() method will use the host and port passed to the FastMCP constructor
    mcp.run(transport=transport)

# Run the server
if __name__ == "__main__":
    start_mcp_server()

    # Older logic commented out for clarity:
    # if transport == "stdio":
    #     print("Running server with stdio transport")
    #     mcp.run(transport="stdio")
    # elif transport == "sse":
    #     print("Running server with SSE transport")
    #     mcp.run(transport="sse") # host and port are from mcp instance
    # else:
    #     raise ValueError(f"Unknown transport: {transport}")
