from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
loaded_correctly = load_dotenv(dotenv_path=dotenv_path, verbose=True)

print(f"[news_service.py DEBUG] dotenv_path being checked: {dotenv_path}")
print(f"[news_service.py DEBUG] load_dotenv reported successful load: {loaded_correctly}")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
key_is_loaded = NEWS_API_KEY is not None and NEWS_API_KEY != ""
print(f"[news_service.py DEBUG] NEWS_API_KEY is loaded: {key_is_loaded}")

newsapi_client = None

if NEWS_API_KEY:
    newsapi_client = NewsApiClient(api_key=NEWS_API_KEY)
else:
    print("WARNING: NEWS_API_KEY not found in environment. News search functionality will be impaired.")

def get_news(query, sort_by):
    if not newsapi_client:
        print("Error in get_news: NewsApiClient not initialized due to missing API key.")
        return {
            'status': 'error',
            'code': 'apiKeyMissing',
            'message': 'NewsAPI key is not configured. Cannot fetch news.',
            'articles': []
        }
    
    # Calculate dates for the past month
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    try:
        all_articles = newsapi_client.get_everything(
            q=query,
            from_param=from_date,
            to=to_date,
            language='en',
            sort_by=sort_by,
            page_size=10,  # Limiting page size
            page=1
        )
        # Basic check on the response structure from NewsAPI
        if not isinstance(all_articles, dict) or 'status' not in all_articles:
            print(f"Error in get_news: Unexpected response structure from NewsAPI: {type(all_articles)}")
            return {
                'status': 'error',
                'code': 'apiResponseError',
                'message': 'Unexpected response structure from NewsAPI.',
                'articles': []
            }
        return all_articles
    except Exception as e:
        print(f"Error during NewsAPI call in get_news: {e}")
        # Return an error structure 
        return {
            'status': 'error',
            'code': 'apiCallError',
            'message': f'Error calling NewsAPI: {str(e)}',
            'articles': []
        } 