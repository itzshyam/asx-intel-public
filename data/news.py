from newsapi import NewsApiClient
from dotenv import load_dotenv
import os

load_dotenv()
news_api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))

def get_news(company_name):
    try:
        search_name = company_name.split(" ")[0:3]
        search_query = " ".join(search_name)

        response = news_api.get_everything(
            q=f'"{search_query}" AND (ASX OR shares OR stock OR investor)',
            language="en",
            sort_by="publishedAt",
            page_size=5
        )
        articles = response.get("articles", [])
        headlines = [
            f"- {a['title']} ({a['source']['name']})"
            for a in articles
            if a.get("title")
        ]
        return headlines if headlines else ["No recent news found"]
    except Exception as e:
        return [f"News fetch failed: {str(e)}"]