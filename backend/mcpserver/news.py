from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env
load_dotenv("../.env")

newsapi_client = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))

def get_news(query, sort_by):
    
    # Calculate dates for the past month
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # /v2/everything
    all_articles = newsapi_client.get_everything(q=query,
                                        from_param=from_date,
                                        to=to_date,
                                        language='en',
                                        sort_by=sort_by,
                                        page_size=10,
                                        page=1)
    
    return all_articles



# if __name__ == "__main__":
#     print(get_news("AI OR loan OR lending OR asset based lending OR asset based lending software", "publishedAt"))




# /v2/top-headlines
# top_headlines = newsapi_client.get_top_headlines(q='bitcoin',
#                                           sources='bbc-news,the-verge',
#                                           category='business',
#                                           language='en',
#                                           country='us')