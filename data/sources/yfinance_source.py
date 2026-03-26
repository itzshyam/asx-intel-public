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

def fetch_price_history(ticker_symbol):
    """
    Fetches 3-year weekly price history for trend context.
    Returns a summary dict with key price points, not raw data.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="3y", interval="1mo")
        if hist.empty:
            return None

        prices = hist["Close"].dropna().tolist()
        if len(prices) < 6:
            return None

        current   = round(prices[-1], 2)
        one_yr    = round(prices[-12], 2) if len(prices) >= 12 else None
        two_yr    = round(prices[-24], 2) if len(prices) >= 24 else None
        three_yr  = round(prices[0], 2)

        def pct_change(old, new):
            if old and old != 0:
                return round(((new - old) / old) * 100, 1)
            return None

        return {
            "current":          current,
            "one_year_ago":     one_yr,
            "two_year_ago":     two_yr,
            "three_year_ago":   three_yr,
            "change_1yr_pct":   pct_change(one_yr, current),
            "change_2yr_pct":   pct_change(two_yr, current),
            "change_3yr_pct":   pct_change(three_yr, current),
        }
    except:
        return None