from services.embeddings_service import shared_embeddings
from services.supabase_service import supabase

def search_blog_posts(query: str) -> dict:
    """
    Search for successful blog posts using Supabase vector similarity search.
    query (str): The topic or theme to search for in blog posts.
    Returns: dict: Dictionary containing blog post examples with metadata and content.
    """
    print(f"Tool: Searching for blog posts with query: '{query}'")
    
    if shared_embeddings is None:
        return {"error": "Embeddings model not available for blog post search."}
    
    if supabase is None:
        return {"error": "Supabase client not available for blog post search."}
    
    try:
        # Generate embedding for the query
        query_embedding = shared_embeddings.embed_query(query)
        
        # Use specific RPC function for viral content search
        response = supabase.rpc(
            'search_viral_content',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'type': 'blog'
            }
        ).execute()
        
        if not response.data:
            return {"error": "No relevant blog posts found for this topic using the vector database."}
        
        blog_posts = []
        for i, doc in enumerate(response.data[:3]):  # Limit to top 3 for conciseness
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
            
            blog_posts.append(post)
        
        return {
            "success": True,
            "query": query,
            "total_posts": len(blog_posts),
            "blog_posts": blog_posts
        }

    except Exception as e:
        print(f"Error in search_blog_posts tool: {e}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {"error": f"Error retrieving blog posts: {str(e)} (Type: {type(e).__name__})"} 