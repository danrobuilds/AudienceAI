from services.embeddings_service import shared_embeddings
from services.supabase_service import supabase

def search_linkedin_posts(query: str) -> dict:
    """
    Search for viral LinkedIn posts using Supabase vector similarity search.
    query (str): The topic or theme to search for in viral posts.
    Returns: dict: Dictionary containing viral post examples with metadata and content.
    """
    print(f"Tool: Searching for viral posts with query: '{query}'")
    
    if shared_embeddings is None:
        return {"error": "Embeddings model not available for LinkedIn post search."}
    
    if supabase is None:
        return {"error": "Supabase client not available for LinkedIn post search."}
    
    try:
        # Generate embedding for the query
        query_embedding = shared_embeddings.embed_query(query)
        
        # Use specific RPC function for viral content search
        response = supabase.rpc(
            'search_viral_content',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'type': 'linkedin'
            }
        ).execute()
        
        if not response.data:
            return {"error": "No relevant viral posts found for this topic using the vector database."}
        
        viral_posts = []
        for i, doc in enumerate(response.data[:1]):  # Limit to top 3 for conciseness
            content = doc.get('content', 'No content available')
            similarity = doc.get('similarity', 0)
            target_audience = doc.get('target_audience', 'No target audience available')
            media_description = doc.get('media_description', 'No media description available')
            content_url = doc.get('content_url', 'No content URL available')
            
            post = {
                "example_number": i + 1,
                "content": content,
                "similarity_score": similarity,
                "target_audience": target_audience,
                "media_description": media_description,
                "content_url": content_url
            }
            
            viral_posts.append(post)
        
        return {
            "success": True,
            "query": query,
            "total_posts": len(viral_posts),
            "viral_posts": viral_posts
        }

    except Exception as e:
        print(f"Error in search_linkedin_posts tool: {e}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {"error": f"Error retrieving viral posts: {str(e)} (Type: {type(e).__name__})"} 