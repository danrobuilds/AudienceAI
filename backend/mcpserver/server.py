from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_core.documents import Document
from .news import get_news
import os # Added for path manipulation
from langchain_ollama import OllamaEmbeddings # Added
from langchain_chroma import Chroma # Added


load_dotenv("../.env")

# --- Global Configurations for Vector Stores ---
# Determine the absolute path to the directory where server.py is located
SERVER_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_LOCATION will be backend/mcpserver/local_embeddings_db/
DB_LOCATION = os.path.join(SERVER_SCRIPT_DIR, "local_embeddings_db")

# Initialize embeddings model once
try:
    shared_embeddings = OllamaEmbeddings(model="nomic-embed-text")
except Exception as e:
    print(f"CRITICAL: Failed to initialize OllamaEmbeddings in server.py: {e}")
    print("Ensure Ollama is running and the model 'nomic-embed-text' is available.")
    # Depending on desired behavior, you might exit or disable tools that need embeddings
    shared_embeddings = None # Set to None so tools can check and fail gracefully

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
        content = article.get('content', 'No content available.')
        if not content: # Handle empty content string
            content = "No content available."
        url = article.get('url', 'N/A')
        
        
        formatted_article = (
            f"Article {i+1}:\n"
            f"  Title: {title}\n"
            f"  Source: {source_name}\n"
            f"  Description: {description}\n"
            f"  Content: {content}\n"
            f"  URL: {url}"
        )
        formatted_articles.append(formatted_article)
    
    return "\n\n---\n\n".join(formatted_articles) if formatted_articles else "No news articles could be formatted."


# Add the vector search tool for LinkedIn posts
@mcp.tool()
def search_linkedin_posts(query: str) -> str:
    """
    Search for viral LinkedIn posts using an embedding-based retriever.
    query (str): The topic or theme to search for in viral posts.
    Returns: str: Formatted examples of viral posts related to the query, or a message if no posts are found.
    """
    print(f"MCP Tool: Searching for viral posts with query: '{query}'")
    if shared_embeddings is None:
        return "Error: Embeddings model not available for LinkedIn post search."
    try:
        linkedin_vector_store = Chroma(
            collection_name="viral_post_data",
            persist_directory=DB_LOCATION,
            embedding_function=shared_embeddings
        )
        retriever = linkedin_vector_store.as_retriever(search_kwargs={"k": 10})
        retrieved_docs = retriever.invoke(query)
        
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


# Add the PDF document search tool
@mcp.tool()
def search_document_library(query: str) -> str:
    """
    Search the internal PDF document library using an embedding-based retriever.
    query (str): The topic or keywords to search for in the documents.
    Returns: str: Formatted text segments from relevant documents, or a message if no documents are found.
    """
    print(f"MCP Tool: Searching document library with query: '{query}'")
    if shared_embeddings is None:
        return "Error: Embeddings model not available for document library search."
    try:
        pdf_vector_store = Chroma(
            collection_name="pdf_text_content",
            persist_directory=DB_LOCATION,
            embedding_function=shared_embeddings
        )
        retriever = pdf_vector_store.as_retriever(search_kwargs={"k": 5})
        retrieved_docs = retriever.invoke(query)
        
        if not retrieved_docs:
            return "No relevant documents found in the library for this topic."
        
        results = []
        # Limit to top 3 for conciseness in the MCP tool response
        for i, doc in enumerate(retrieved_docs[:3]): 
            result_text = f"Document Segment {i+1}:\n"
            if doc.metadata and doc.metadata.get('source_filename'):
                result_text += f"Source PDF: {doc.metadata['source_filename']}\n"
            else:
                result_text += "Source PDF: Unknown\n"
            result_text += f"Content Snippet: ...{doc.page_content[:500]}...\n" # Show a snippet
            results.append(result_text)
        
        return "\n---\n".join(results) if results else "No relevant document segments found after formatting."

    except Exception as e:
        print(f"Error in MCP search_document_library tool: {e}")
        return f"Error retrieving documents from library: {str(e)}"


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
