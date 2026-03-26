from data.sources.yfinance_source import fetch_company_info, fetch_sector_change, fetch_market_change, fetch_price_history

def format_number(value):
    if value == "N/A" or value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.2f}"

def format_percent(value):
    if value == "N/A" or value is None:
        return "N/A"
    return f"{value * 100:.2f}%"

def _price_position(info):
    """Where is current price in the 52-week range? Expressed as a percentage."""
    try:
        low  = info.get("fiftyTwoWeekLow")
        high = info.get("fiftyTwoWeekHigh")
        current = info.get("currentPrice")
        if not all([low, high, current]) or high == low:
            return "N/A"
        position = ((current - low) / (high - low)) * 100
        if position <= 25:
            label = "Near 52-week LOW"
        elif position <= 50:
            label = "Lower half of 52-week range"
        elif position <= 75:
            label = "Upper half of 52-week range"
        else:
            label = "Near 52-week HIGH"
        return f"{position:.0f}% of 52-week range ({label})"
    except:
        return "N/A"

def _cashflow_quality(info):
    """Compare operating cash flow to net income. Flags if they diverge significantly."""
    try:
        ocf = info.get("operatingCashflow")
        net = info.get("netIncomeToCommon")
        if not ocf or not net or net == 0:
            return "N/A"
        ratio = ocf / net
        if ratio >= 1.2:
            quality = "STRONG — cash flow exceeds profit (high quality earnings)"
        elif ratio >= 0.8:
            quality = "HEALTHY — cash flow broadly in line with profit"
        elif ratio >= 0.5:
            quality = "MODERATE — cash flow trails profit, worth monitoring"
        else:
            quality = "WEAK — cash flow significantly below profit (potential earnings quality concern)"
        return f"Operating cash flow is {ratio:.1f}x net income — {quality}"
    except:
        return "N/A"

def _dividend_sustainability(info):
    """Check payout ratio against both earnings and free cash flow."""
    try:
        payout = info.get("payoutRatio")
        if not payout:
            return "No dividend paid"
        if payout <= 0.5:
            label = "SUSTAINABLE — well covered by earnings"
        elif payout <= 0.75:
            label = "MANAGEABLE — moderate payout, monitor if earnings fall"
        elif payout <= 1.0:
            label = "STRETCHED — paying out most of earnings, limited buffer"
        else:
            label = "UNSUSTAINABLE — paying out more than it earns, dividend at risk"
        return f"Payout ratio {payout*100:.0f}% — {label}"
    except:
        return "N/A"

def _short_interest(info):
    """Short interest as % of float — flags if unusually high."""
    try:
        short_pct = info.get("shortPercentOfFloat")
        if not short_pct:
            return "N/A"
        pct = short_pct * 100
        if pct < 2:
            label = "VERY LOW — minimal bearish positioning"
        elif pct < 5:
            label = "LOW — normal range"
        elif pct < 10:
            label = "MODERATE — some bearish conviction in market"
        elif pct < 20:
            label = "HIGH — significant short interest, smart money bearish"
        else:
            label = "VERY HIGH — heavily shorted, potential short squeeze OR serious concerns"
        return f"{pct:.1f}% of float shorted — {label}"
    except:
        return "N/A"

def _price_momentum(info, sector):
    """
    Compares stock 52w change vs sector and market.
    Returns dict with stock_pct, sector_pct, market_pct, classification.
    """
    try:
        stock_change = info.get("52WeekChange")
        if stock_change is None:
            return None

        stock_pct  = round(stock_change * 100, 1)
        sector_pct = fetch_sector_change(sector)
        market_pct = fetch_market_change()

        # Classify based on relative performance
        if sector_pct is not None:
            diff = stock_pct - sector_pct
            if diff < -15:
                classification = "Company-Specific"
            elif diff > 15:
                classification = "Relative Strength"
            else:
                # In line with sector — check vs market
                if market_pct is not None and sector_pct < market_pct - 10:
                    classification = "Sector-Driven"
                else:
                    classification = "Macro-Driven"
        else:
            classification = "Insufficient Data"

        return {
            "stock_pct":       stock_pct,
            "sector_pct":      sector_pct,
            "market_pct":      market_pct,
            "classification":  classification,
        }
    except:
        return None

def detect_anomalies(info, data):
    """
    Checks calculated signals against thresholds.
    Returns a list of anomaly dicts for any triggered flags.
    Each dict has: metric, value, sector, industry
    """
    anomalies = []
    sector = info.get("sector", "")
    industry = info.get("industry", "")
    is_bank = "bank" in sector.lower() or "financial" in sector.lower()

    # Debt-to-equity anomaly — skip banks
    de = info.get("debtToEquity")
    if de and not is_bank:
        if de > 50:
            anomalies.append({
                "metric": "Debt-to-Equity",
                "value": f"{de:.1f}x",
                "sector": sector,
                "industry": industry,
                "threshold": "above 50x for a non-financial company"
            })
        elif de > 10:
            anomalies.append({
                "metric": "Debt-to-Equity",
                "value": f"{de:.1f}x",
                "sector": sector,
                "industry": industry,
                "threshold": "above 10x for a non-financial company"
            })

    # Cash flow quality anomaly
    ocf = info.get("operatingCashflow")
    net = info.get("netIncomeToCommon")
    if ocf and net and net != 0 and not is_bank:
        ratio = ocf / net
        if ratio < 0.5:
            anomalies.append({
                "metric": "Cash Flow Quality",
                "value": f"{ratio:.1f}x operating cash flow vs net income",
                "sector": sector,
                "industry": industry,
                "threshold": "cash flow below 0.3x net income for a non-financial company"
            })

    # Payout ratio anomaly
    payout = info.get("payoutRatio")
    if payout and payout > 1.0:
        anomalies.append({
            "metric": "Dividend Payout Ratio",
            "value": f"{payout*100:.0f}%",
            "sector": sector,
            "industry": industry,
            "threshold": "paying out more than 100% of earnings as dividends"
        })

    # P/E anomaly — extremely high
    pe = info.get("trailingPE")
    if pe and pe > 80:
        anomalies.append({
            "metric": "P/E Ratio",
            "value": f"{pe:.1f}x",
            "sector": sector,
            "industry": industry,
            "threshold": "above 80x trailing P/E"
        })

    return anomalies

def get_company_data(ticker_symbol):
    info = fetch_company_info(ticker_symbol)
    if not info:
        return {}

    # --- Base metrics ---
    data = {
        "name":             info.get("longName", "N/A"),
        "sector":           info.get("sector", "N/A"),
        "industry":         info.get("industry", "N/A"),
        "description":      info.get("longBusinessSummary", "N/A"),
        "employees":        f"{info.get('fullTimeEmployees', 0):,}",
        "country":          info.get("country", "N/A"),
        "current_price":    f"${info.get('currentPrice', 'N/A')} AUD",
        "market_cap":       format_number(info.get("marketCap", "N/A")),
        "revenue":          format_number(info.get("totalRevenue", "N/A")),
        "net_income":       format_number(info.get("netIncomeToCommon", "N/A")),
        "profit_margin":    format_percent(info.get("profitMargins", "N/A")),
        "pe_ratio":         f"{info.get('trailingPE', 'N/A'):.2f}x" if info.get('trailingPE') else "N/A",
        "forward_pe":       f"{info.get('forwardPE', 'N/A'):.2f}x" if info.get('forwardPE') else "N/A",
        "52w_low":          f"${info.get('fiftyTwoWeekLow', 'N/A')} AUD",
        "52w_high":         f"${info.get('fiftyTwoWeekHigh', 'N/A')} AUD",
        "current_vs_52w":   _price_position(info),
        "dividend_yield":   f"{info.get('dividendYield', 'N/A')}%",
        "return_on_equity": format_percent(info.get("returnOnEquity", "N/A")),
        "debt_to_equity":   f"{info.get('debtToEquity', 'N/A')}x" if info.get('debtToEquity') else "N/A",
        "analyst_rating":   info.get("recommendationKey", "N/A").upper(),
        "target_price":     f"${info.get('targetMeanPrice', 'N/A'):.2f} AUD" if info.get('targetMeanPrice') else "N/A",
    }

    # --- Signal 1: Cash flow quality ---
    data["cashflow_quality"] = _cashflow_quality(info)

    # --- Signal 2: Dividend sustainability ---
    data["dividend_sustainability"] = _dividend_sustainability(info)

    # --- Signal 3: Short interest ---
    data["short_interest"] = _short_interest(info)
    
    # --- Anomaly detection ---
    data["anomalies"] = detect_anomalies(info, data)

    data["price_momentum"] = _price_momentum(info, data["sector"])

    # --- 3 year price history ---
    data["price_history"]  = fetch_price_history(ticker_symbol)
    
    return data