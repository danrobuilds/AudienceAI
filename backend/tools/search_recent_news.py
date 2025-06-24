from services.news_service import get_news

def search_recent_news(query: str, sort_by: str = "publishedAt") -> str:
    """Use NewsAPI to search for recent news articles based on a query."""
    print(f"Tool: Searching for recent news with query: '{query}', sort_by: '{sort_by}'")

    news_data = get_news(query, sort_by)
    
    # Updated error handling based on the new structure from get_news()
    if not isinstance(news_data, dict) or news_data.get('status') != 'ok':
        error_message = "Could not retrieve news articles or an API error occurred."
        if isinstance(news_data, dict) and news_data.get('message'):
            error_message = f"NewsAPI Error: {news_data['message']}" # Use the message from get_news
        elif not isinstance(news_data, dict):
            error_message = f"NewsAPI Error: Unexpected response type from get_news: {type(news_data)}"
        print(f"Tool search_recent_news error: {error_message}")
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