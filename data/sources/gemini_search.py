from google import genai
from google.genai import types
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

# Model constant — safe to define at module level
GEMINI_SEARCH_MODEL = "gemini-2.5-flash"

def search_web(query: str) -> str:
    """
    Performs a web search using Gemini with Google Search grounding.
    Injects today's date into every query to force recent results.
    Returns plain text summary of findings.
    """
    # Initialise client inside function — ensures Azure env vars are loaded
    # Module-level initialisation fails on Azure as vars aren't injected yet
    gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # Anchor every search to today's date — prevents stale cached results
    today = date.today().strftime("%d %B %Y")
    dated_query = f"{query} as of {today}"

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_SEARCH_MODEL,
            contents=dated_query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=500
            )
        )
        return response.text
    except Exception as e:
        print(f"Gemini search failed for query '{query}': {e}")
        return ""