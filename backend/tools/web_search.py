import os
from linkup_sdk import LinkupClient

def web_search(query: str) -> dict:
    """
    Search the web for general information using Linkup API.
    query (str): The search query to find relevant web content.
    Returns: dict: Dictionary containing web search results with titles, URLs, and content.
    """
    print(f"Tool: Searching web with query: '{query}'")
    
    try:
        # Initialize Linkup client with API key from environment
        linkup_api_key = os.getenv('LINKUP_API_KEY')
        if not linkup_api_key:
            return {"error": "LINKUP_API_KEY not found in environment variables. Please set your Linkup API key."}
        
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
            return {"error": f"No web search results found for query: '{query}'"}
        
        # Format the results
        web_results = []
        for i, result in enumerate(response.results[:5]):  # Limit to top 5 results
            try:
                # Handle both text and image results
                if hasattr(result, 'type') and result.type == 'image':
                    continue  # Skip image results for now
                
                title = getattr(result, 'name', '') or getattr(result, 'title', 'No title available')
                url = getattr(result, 'url', 'No URL available')
                content = getattr(result, 'content', '') or getattr(result, 'snippet', '') or 'No content available'
                
                web_result = {
                    "result_number": i + 1,
                    "title": title,
                    "url": url,
                    "content": content
                }
                
                web_results.append(web_result)
            except Exception as e:
                print(f"Error formatting result {i+1}: {e}")
                continue
        
        if not web_results:
            return {"error": f"No valid web search results could be formatted for query: '{query}'"}
        
        return {
            "success": True,
            "query": query,
            "total_results": len(web_results),
            "web_results": web_results
        }
        
    except Exception as e:
        error_message = f"Error performing web search: {str(e)}"
        print(f"Tool web_search error: {error_message}")
        return {"error": error_message} 