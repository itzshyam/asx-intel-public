import yfinance as yf

def fetch_company_info(ticker_symbol):
    """
    Fetches raw company info dict from Yahoo Finance via yfinance.
    Returns the raw info dictionary or empty dict on failure.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        return ticker.info
    except Exception as e:
        print(f"yfinance fetch failed for {ticker_symbol}: {e}")
        return {}

SECTOR_INDEX_MAP = {
    "Basic Materials":        "^AXMJ",
    "Financial Services":     "^AXFJ",
    "Healthcare":             "^AXHJ",
    "Technology":             "^AXTJ",
    "Energy":                 "^AXEJ",
    "Consumer Cyclical":      "^AXDJ",
    "Consumer Defensive":     "^AXSJ",
    "Industrials":            "^AXNJ",
    "Real Estate":            "^AXPJ",
    "Utilities":              "^AXUJ",
    "Communication Services": "^AXKJ",
}

def fetch_sector_change(sector_name):
    """
    Returns 52-week % change for the ASX sector index
    matching the company's GICS sector. Returns None if unavailable.
    """
    try:
        index_ticker = SECTOR_INDEX_MAP.get(sector_name)
        if not index_ticker:
            return None
        info = yf.Ticker(index_ticker).info
        change = info.get("52WeekChange")
        return round(change, 1) if change is not None else None # already a percentage
    except:
        return None

def fetch_market_change():
    """
    Returns ASX200 52-week % change as macro baseline.
    Returns None if unavailable.
    """
    try:
        info = yf.Ticker("^AXJO").info
        change = info.get("52WeekChange")
        return round(change, 1) if change is not None else None # already a percentage
    except:
        return None