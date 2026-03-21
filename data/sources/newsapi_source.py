from newsapi import NewsApiClient
from dotenv import load_dotenv
import os

load_dotenv()

_client = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))

def fetch_news(query, language="en", sort_by="publishedAt", page_size=5):
    """
    Raw NewsAPI fetch. Returns list of article dicts or empty list on failure.
    Swap this file out when replacing NewsAPI with a different news source.
    """
    try:
        response = _client.get_everything(
            q=query,
            language=language,
            sort_by=sort_by,
            page_size=page_size
        )
        return response.get("articles", [])
    except Exception as e:
        print(f"NewsAPI fetch failed: {e}")
        return []