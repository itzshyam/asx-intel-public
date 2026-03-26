from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from data.financials import get_company_data
from data.news import get_news
from claude_client import run_crew_analysis

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/analyse", response_class=HTMLResponse)
async def analyse(request: Request, ticker: str = Form(...)):
    """
    Receives ticker from the search form.
    Runs the full two-agent pipeline.
    Returns the results page as HTML.
    """

    # Normalise ticker — uppercase and add .AX suffix if missing
    ticker = ticker.upper().strip()
    if not ticker.endswith(".AX"):
        ticker = ticker + ".AX"

    try:
        # Fetch financial data and news (synchronous for now — Milestone 8 parallelises these)
        data = get_company_data(ticker)
        news = get_news(data["name"])

        # Run two-agent pipeline
        analysis = run_crew_analysis(data, news)

        # Preserve Agent 1 signals for summary cards — same logic as app.py
        agent1_signals = analysis.get("agent1_signals", {})
        bq  = agent1_signals.get("business_quality", analysis.get("business_quality", {}))
        val = agent1_signals.get("valuation",         analysis.get("valuation", {}))
        div = agent1_signals.get("dividend",           analysis.get("dividend", {}))

        # Calculate P/E signal directly in Python — removes Claude interpretation variance
        pe_signal = _calculate_pe_signal(data)

        # Aggregate Business Health signal from individual components
        health_signal, health_verdict = _aggregate_business_health(bq)

        # Calculate analyst signal and upside
        analyst_signal = val.get("analyst_view", {}).get("signal", "yellow")
        upside = _get_upside_pct(data["current_price"], data["target_price"])

        # Dividend signal
        div_signal = div.get("signal", "yellow") if div.get("has_dividend") else "yellow"
        div_label  = (
            "Sustainable" if div_signal == "green"
            else "At Risk"   if div_signal == "red"
            else "Stretched" if div.get("has_dividend")
            else "None"
        )

        # Pass everything the template needs as context
        context = {
            "request":        request,
            "data":           data,
            "analysis":       analysis,
            "bq":             bq,
            "val":            val,
            "div":            div,
            "fit":            analysis.get("investor_fit", {}),
            "health_signal":  health_signal,
            "health_verdict": health_verdict,
            "pe_signal":      pe_signal,
            "pe_label":       "Cheap" if pe_signal == "green" else "Expensive" if pe_signal == "red" else "Fair",
            "analyst_signal": analyst_signal,
            "upside":         upside,
            "div_signal":     div_signal,
            "div_label":      div_label,
            "div_yield":      data["dividend_yield"] if div.get("has_dividend") else "No dividend",
            "anomalies":      data.get("anomalies", []),
        }

        return templates.TemplateResponse("results.html", context)

    except Exception as e:
        # Return the homepage with an error message if anything fails
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error":   f"Analysis failed for {ticker}: {str(e)}"
        })


# ── Helper functions (ported from app.py) ─────────────────────────────────────

def _calculate_pe_signal(data: dict) -> str:
    """
    Calculate P/E signal directly from raw data.
    Same number always produces same colour — no Claude interpretation variance.
    """
    sector_pe_lower = {
        "Financial Services": 12, "Banks": 12,
        "Basic Materials": 10,    "Energy": 10,
        "Technology": 20,         "Healthcare": 20,
        "Consumer Cyclical": 12,  "Consumer Defensive": 12,
        "Industrials": 14,        "Real Estate": 15,
        "Communication Services": 14
    }
    sector_pe_upper = {
        "Financial Services": 20, "Banks": 20,
        "Basic Materials": 18,    "Energy": 18,
        "Technology": 40,         "Healthcare": 35,
        "Consumer Cyclical": 18,  "Consumer Defensive": 18,
        "Industrials": 22,        "Real Estate": 25,
        "Communication Services": 22
    }
    try:
        pe_raw = float(data["pe_ratio"].replace("x", "").strip())
        sector = data.get("sector", "")
        lower  = sector_pe_lower.get(sector, 14)
        upper  = sector_pe_upper.get(sector, 22)

        if pe_raw < lower * 0.9:
            return "green"
        elif pe_raw > upper:
            return "red"
        else:
            return "yellow"
    except Exception:
        return "yellow"


def _aggregate_business_health(bq: dict) -> tuple[str, str]:
    """
    Aggregate Business Health from profitability, earnings quality, and debt.
    Debt red = Mixed always — extreme leverage overrides operational strength.
    """
    profitability = bq.get("profitability",    {}).get("signal", "yellow")
    earnings      = bq.get("earnings_quality", {}).get("signal", "yellow")
    debt          = bq.get("debt",             {}).get("signal", "yellow")

    if debt == "red":
        return "yellow", "Mixed"
    if profitability == "green" and earnings == "green":
        return "green", "Strong"
    if profitability == "red" or earnings == "red":
        return "red", "Weak"
    return "yellow", "Mixed"


def _get_upside_pct(current_price_str: str, target_price_str: str) -> str:
    """Calculate % upside/downside from current price to analyst target."""
    try:
        current = float(current_price_str.replace("$", "").replace(" AUD", "").strip())
        target  = float(target_price_str.replace("$", "").replace(" AUD", "").strip())
        upside  = ((target - current) / current) * 100
        direction = "upside" if upside > 0 else "downside"
        return f"{abs(upside):.0f}% {direction}"
    except Exception:
        return "N/A"
