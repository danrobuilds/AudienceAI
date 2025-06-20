from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_core.documents import Document
from .news import get_news
import os # Added for path manipulation
from langchain_ollama import OllamaEmbeddings # Added
from langchain_chroma import Chroma # Added
from linkup import LinkupClient # Added for web search
from openai import OpenAI # Added for image generation
import base64
import uuid


load_dotenv("../.env")

# --- Global Configurations for Vector Stores ---
# Determine the absolute path to the directory where server.py is located
SERVER_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_LOCATION will be backend/local_embeddings_db/
DB_LOCATION = os.path.join(SERVER_SCRIPT_DIR, "..", "local_embeddings_db")

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
    
    # Updated error handling based on the new structure from get_news()
    if not isinstance(news_data, dict) or news_data.get('status') != 'ok':
        error_message = "Could not retrieve news articles or an API error occurred."
        if isinstance(news_data, dict) and news_data.get('message'):
            error_message = f"NewsAPI Error: {news_data['message']}" # Use the message from get_news
        elif not isinstance(news_data, dict):
            error_message = f"NewsAPI Error: Unexpected response type from get_news: {type(news_data)}"
        print(f"MCP Tool search_recent_news error: {error_message}")
        return error_message

    articles = news_data.get('articles', [])
    if not articles:
        return "No news articles found for your query."

    formatted_articles = []
    for i, article in enumerate(articles[:5]): # Ensure we only process up to 5
        title = str(article.get('title', 'N/A'))
        source_name = str(article.get('source', {}).get('name', 'N/A'))
        
        description = article.get('description')
        if not description: # Handles None and empty string
            description = "No description available."
        else:
            description = str(description)

        content = article.get('content')
        if not content: # Handles None and empty string
            content = "No content available."
        else:
            content = str(content)
            
        url = str(article.get('url', 'N/A'))
        
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
    
    max_retries = 2
    for attempt in range(max_retries):
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
                    
                    # Add chunk information if available
                    if doc.metadata.get('chunk_index') is not None:
                        chunk_idx = doc.metadata.get('chunk_index')
                        total_chunks = doc.metadata.get('total_chunks', '?')
                        result_text += f"Chunk: {chunk_idx + 1} of {total_chunks}\n"
                        
                    if doc.metadata.get('chunk_size'):
                        result_text += f"Chunk Size: {doc.metadata['chunk_size']} chars\n"
                else:
                    result_text += "Source PDF: Unknown\n"
                    
                result_text += f"Content: {doc.page_content}\n"  # Return full content instead of snippet
                results.append(result_text)
            
            return "\n---\n".join(results) if results else "No relevant document segments found after formatting."

        except Exception as e:
            error_str = str(e).lower()
            print(f"Error in MCP search_document_library tool (attempt {attempt + 1}): {e}")
            
            # Check for specific HNSW index errors
            if "nothing found on disk" in error_str or "hnsw" in error_str:
                if attempt < max_retries - 1:
                    print(f"HNSW index error detected, retrying... (attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(0.5)  # Brief delay before retry
                    continue
                else:
                    return "Error: Vector database index is temporarily unavailable. Please try uploading PDFs again or contact support if the issue persists."
            else:
                # For other errors, don't retry
                break
    
    return f"Error retrieving documents from library: {str(e)}"


# Add the web search tool using Linkup
@mcp.tool()
def web_search(query: str) -> str:
    """
    Search the web for general information using Linkup API.
    query (str): The search query to find relevant web content.
    Returns: str: Formatted web search results with titles, URLs, and snippets, or an error message.
    """
    print(f"MCP Tool: Searching web with query: '{query}'")
    
    try:
        # Initialize Linkup client with API key from environment
        linkup_api_key = os.getenv('LINKUP_API_KEY')
        if not linkup_api_key:
            return "Error: LINKUP_API_KEY not found in environment variables. Please set your Linkup API key."
        
        client = LinkupClient(api_key=linkup_api_key)
        
        # Perform the search
        response = client.search(
            query=query,
            depth="standard",
            output_type="searchResults",
            include_images=False,
        )
        
        # Check if response has results
        if not response or not hasattr(response, 'results') or not response.results:
            return f"No web search results found for query: '{query}'"
        
        # Format the results
        formatted_results = []
        for i, result in enumerate(response.results[:5]):  # Limit to top 5 results
            try:
                # Handle both text and image results
                if hasattr(result, 'type') and result.type == 'image':
                    continue  # Skip image results for now
                
                title = getattr(result, 'name', '') or getattr(result, 'title', 'No title available')
                url = getattr(result, 'url', 'No URL available')
                content = getattr(result, 'content', '') or getattr(result, 'snippet', '') or 'No content available'
                
                formatted_result = (
                    f"Web Result {i+1}:\n"
                    f"  Title: {title}\n"
                    f"  URL: {url}\n"
                    f"  Content: {content[:500]}{'...' if len(content) > 500 else ''}"
                )
                formatted_results.append(formatted_result)
            except Exception as e:
                print(f"Error formatting result {i+1}: {e}")
                continue
        
        if not formatted_results:
            return f"No valid web search results could be formatted for query: '{query}'"
        
        return "\n\n---\n\n".join(formatted_results)
        
    except Exception as e:
        error_message = f"Error performing web search: {str(e)}"
        print(f"MCP Tool web_search error: {error_message}")
        return error_message


# Add the image generation tool using OpenAI DALL-E 3
@mcp.tool()
def generate_image(prompt: str, style: str = "professional", aspect_ratio: str = "16:9") -> str:
    """
    Generate an image using OpenAI's GPT-Image-1 API based on the prompt and style.
    prompt (str): Detailed description of the image to generate.
    style (str): Visual style for the image (professional, infographic, modern, minimalist, tech-focused, corporate).
    aspect_ratio (str): Aspect ratio for the image (16:9, 1:1, 4:5).
    Returns: str: Base64 encoded image data with metadata.
    """
    print(f"MCP Tool: Generating image with prompt: '{prompt}', style: '{style}', aspect_ratio: '{aspect_ratio}'")
    
    try:
        # Get OpenAI API key from environment
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return "Error: OPENAI_API_KEY not found in environment variables. Please set your OpenAI API key."
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Map aspect ratios to supported sizes
        size_mapping = {
            "1:1": "1024x1024",
            "16:9": "1536x1024",  # Landscape
            "4:5": "1024x1536"    # Portrait (closest to 4:5)
        }
        
        # Get the appropriate size, default to 16:9 if not found
        image_size = size_mapping.get(aspect_ratio, "1536x1024")
        
        # Enhance prompt with style guidelines
        style_enhancements = {
            "professional": "professional, clean, business-appropriate, high-quality",
            "infographic": "infographic style, data visualization, charts, clean design, informative",
            "modern": "modern, contemporary, sleek design, trendy",
            "minimalist": "minimalist, simple, clean lines, uncluttered, elegant",
            "tech-focused": "technology-focused, digital, innovation, high-tech, futuristic",
            "corporate": "corporate, business, professional, formal, enterprise"
        }
        
        enhanced_prompt = f"{prompt}. Style: {style_enhancements.get(style, 'professional')}"
        
        # Generate image using gpt-image-1 (returns base64 by default)
        response = client.images.generate(
            model="gpt-image-1",
            prompt=enhanced_prompt,
            size=image_size,
            quality="low",  # Use low quality for cost efficiency
            n=1,
        )
        
        # Return base64 data for frontend use
        if response.data and len(response.data) > 0:
            image_base64 = response.data[0].b64_json
            
            # Generate unique filename for frontend
            image_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            
            print(f"MCP Tool: Image generated successfully")
            
            # Return base64 with metadata markers for parsing
            return f"IMAGE_GENERATED|filename:{image_filename}|size:{image_size}|style:{style}|base64:{image_base64}"
        else:
            return "Error: No image was generated by gpt-image-1."
            
    except Exception as e:
        error_message = f"Error generating image: {str(e)}"
        print(f"MCP Tool generate_image error: {error_message}")
        return error_message


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
