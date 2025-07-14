import os
from linkup import LinkupClient

def image_web_search(query: str) -> dict:
    """
    Search the web for images using Linkup API.
    query (str): The search query to find relevant images.
    Returns: dict: Dictionary containing image search results with URLs, titles, and truncated content.
    """
    print(f"Tool: Searching web for images with query: '{query}'")
    
    try:
        # Initialize Linkup client with API key from environment
        linkup_api_key = os.getenv('LINKUP_API_KEY')
        if not linkup_api_key:
            return {"error": "LINKUP_API_KEY not found in environment variables. Please set your Linkup API key."}
        
        client = LinkupClient(api_key=linkup_api_key)
        
        # Perform the search with images enabled
        response = client.search(
            query=query,
            depth="standard",
            output_type="searchResults",
            include_images=True,
        )
        
        # Check if response has results
        if not response or not hasattr(response, 'results') or not response.results:
            return {"error": f"No image search results found for query: '{query}'"}
        
        # Format the results - only include image results
        image_results = []
        for i, result in enumerate(response.results):
            try:
                # Only process image results
                if hasattr(result, 'type') and result.type == 'image':
                    title = getattr(result, 'name', '') 
                    url = getattr(result, 'url', 'No URL available')
                    
                    image_result = {
                        "result_number": len(image_results) + 1,
                        "title": title,
                        "url": url,
                    }
                    
                    image_results.append(image_result)
                    
            except Exception as e:
                print(f"Error formatting result {i+1}: {e}")
                continue
        
        if not image_results:
            return {"error": f"No valid image search results could be formatted for query: '{query}'"}
        
        return {
            "success": True,
            "query": query,
            "total_results": len(image_results),
            "image_results": image_results[:10]
        }
        
    except Exception as e:
        error_message = f"Error performing image search: {str(e)}"
        print(f"Tool image_web_search error: {error_message}")
        return {"error": error_message}
