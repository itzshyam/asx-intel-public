import streamlit as st
import json
from data.financials import get_company_data
from data.news import get_news
from prompts.analysis import build_analysis_prompt
from prompts.anomaly import build_anomaly_prompt
from claude_client import call_claude, call_claude_json

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="ASX Intel",
    page_icon="📈",
    layout="centered"
)

# ── Global CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f5f5f3;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main container */
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 860px;
}

/* App title */
.app-title {
    font-size: 1.9rem;
    font-weight: 600;
    color: #0a0a0a;
    letter-spacing: -0.5px;
    margin-bottom: 2px;
}

.app-subtitle {
    font-size: 0.85rem;
    color: #888;
    margin-bottom: 1.8rem;
    font-weight: 400;
}

/* Input area */
.stTextInput input {
    background: #ffffff;
    border: 1.5px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: #0a0a0a;
    transition: border-color 0.2s;
}
.stTextInput input:focus {
    border-color: #0a0a0a;
    box-shadow: none;
}

/* Button */
.stButton button {
    background: #0a0a0a;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background 0.2s, transform 0.1s;
    width: 100%;
}
.stButton button:hover {
    background: #2a2a2a;
    transform: translateY(-1px);
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="metric-container"] label {
    font-size: 0.72rem;
    font-weight: 500;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.15rem;
    font-weight: 600;
    color: #0a0a0a;
}

/* Verdict box */
.verdict-box {
    background: #0a0a0a;
    color: #ffffff;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 1.5rem 0;
    font-size: 1.0rem;
    font-weight: 400;
    line-height: 1.6;
}
.verdict-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 6px;
}

/* Company header */
.company-name {
    font-size: 1.5rem;
    font-weight: 600;
    color: #0a0a0a;
    letter-spacing: -0.3px;
    margin-bottom: 2px;
}
.company-meta {
    font-size: 0.82rem;
    color: #999;
    margin-bottom: 1.2rem;
}

/* Section headers */
.section-header {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #999;
    margin: 1.8rem 0 0.8rem 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #ebebeb;
}

/* Analysis cards */
.analysis-card {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.card-green {
    background: #f0faf4;
    border: 1px solid #c3e6cb;
}
.card-yellow {
    background: #fffdf0;
    border: 1px solid #ffeaa0;
}
.card-red {
    background: #fff5f5;
    border: 1px solid #ffc8c8;
}
.card-signal {
    font-size: 1.1rem;
    margin-top: 1px;
    flex-shrink: 0;
}
.card-content {
    flex: 1;
}
.card-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 4px;
}
.card-text {
    font-size: 0.88rem;
    color: #333;
    line-height: 1.55;
}

/* Progress bar for price position */
.progress-container {
    background: #e8e8e8;
    border-radius: 999px;
    height: 5px;
    margin-top: 8px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.6s ease;
}

/* Strength / Concern boxes */
.highlight-box {
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 0.86rem;
    line-height: 1.5;
    margin-bottom: 8px;
}
.highlight-strength {
    background: #f0faf4;
    border-left: 3px solid #28a745;
    color: #1a5c2a;
}
.highlight-concern {
    background: #fff5f5;
    border-left: 3px solid #dc3545;
    color: #7a1c1c;
}

/* Investor fit columns */
.fit-card {
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 10px;
    padding: 16px;
    height: 100%;
}
.fit-header {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.fit-suits { color: #28a745; }
.fit-not { color: #dc3545; }
.fit-item {
    font-size: 0.85rem;
    color: #444;
    padding: 5px 0;
    border-bottom: 1px solid #f0f0f0;
    line-height: 1.45;
}
.fit-item:last-child { border-bottom: none; }

/* Risk list */
.risk-item {
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-left: 3px solid #0a0a0a;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.86rem;
    color: #333;
    line-height: 1.5;
}
.risk-number {
    font-weight: 600;
    color: #0a0a0a;
    margin-right: 6px;
}

/* Anomaly cards */
.anomaly-card {
    background: #fffbf0;
    border: 1px solid #ffe0a0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
}

/* Disclaimer */
.disclaimer {
    font-size: 0.75rem;
    color: #aaa;
    line-height: 1.6;
    padding: 16px 0;
    border-top: 1px solid #ebebeb;
    margin-top: 1rem;
}

/* Divider */
hr {
    border: none;
    border-top: 1px solid #ebebeb;
    margin: 1.5rem 0;
}

/* Expander styling */
.streamlit-expanderHeader {
    font-size: 0.82rem;
    font-weight: 500;
    color: #555;
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────
def signal_icon(signal):
    return {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(signal, "⚪")

def signal_class(signal):
    return {"green": "card-green", "yellow": "card-yellow", "red": "card-red"}.get(signal, "card-yellow")

def analysis_card(label, signal, text):
    st.markdown(f"""
    <div class="analysis-card {signal_class(signal)}">
        <div class="card-signal">{signal_icon(signal)}</div>
        <div class="card-content">
            <div class="card-label">{label}</div>
            <div class="card-text">{text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def price_bar(position_str):
    """Extract percentage from position string and render a progress bar."""
    try:
        pct = int(position_str.split("%")[0])
        colour = "#28a745" if pct <= 30 else "#ffc107" if pct <= 70 else "#dc3545"
        st.markdown(f"""
        <div style="margin-top:6px;">
            <div style="font-size:0.72rem; color:#999; margin-bottom:4px;">
                52-WEEK POSITION
            </div>
            <div class="progress-container">
                <div class="progress-fill" style="width:{pct}%; background:{colour};"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.68rem; color:#bbb; margin-top:3px;">
                <span>52W Low</span>
                <span>{pct}%</span>
                <span>52W High</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except:
        pass

def aggregate_business_health(bq):
    """Combine profitability and earnings quality into one signal."""
    signals = [
        bq.get("profitability", {}).get("signal", "yellow"),
        bq.get("earnings_quality", {}).get("signal", "yellow"),
        bq.get("debt", {}).get("signal", "yellow")
    ]
    if "red" in signals:
        return "yellow", "Mixed"  # red debt doesn't mean weak business overall
    elif signals.count("green") >= 2:
        return "green", "Strong"
    else:
        return "yellow", "Mixed"

def get_upside_pct(current_price_str, target_price_str):
    """Calculate % upside from current price to analyst target."""
    try:
        current = float(current_price_str.replace("$", "").replace(" AUD", "").strip())
        target = float(target_price_str.replace("$", "").replace(" AUD", "").strip())
        upside = ((target - current) / current) * 100
        direction = "upside" if upside > 0 else "downside"
        return f"{abs(upside):.0f}% {direction}"
    except:
        return "N/A"

def get_52w_label(position_str, high_str, low_str):
    """Convert 52w position to plain English."""
    try:
        pct = int(position_str.split("%")[0])
        high = float(high_str.replace("$", "").replace(" AUD", "").strip())
        low = float(low_str.replace("$", "").replace(" AUD", "").strip())
        drop_from_high = ((high - float(position_str.split("(")[0].strip().split("%")[0]) / 100 * (high - low) + low - high) / high * -100)
        
        if pct <= 25:
            zone = "Near 52-week low"
        elif pct <= 50:
            zone = "Lower half of range"
        elif pct <= 75:
            zone = "Upper half of range"
        else:
            zone = "Near 52-week high"
        
        pct_from_high = ((high - (low + (pct/100) * (high - low))) / high * 100)
        return f"📍 {zone} — down {pct_from_high:.0f}% from high of {high_str}"
    except:
        return f"📍 {position_str}"

# ── App header ────────────────────────────────────────────
st.markdown('<div class="app-title">📈 ASX Intel</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">AI-powered company intelligence for ASX-listed stocks</div>', unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    ticker_input = st.text_input(
        "ticker",
        placeholder="Enter ASX ticker — e.g. CBA, BHP, WES, NST",
        label_visibility="collapsed"
    )
with col2:
    analyse_button = st.button("Analyse →", use_container_width=True)

# ── Main logic ────────────────────────────────────────────
if analyse_button and ticker_input:

    ticker = ticker_input.upper().strip()
    if not ticker.endswith(".AX"):
        ticker = ticker + ".AX"

    with st.spinner(f"Fetching live data for {ticker}..."):
        data = get_company_data(ticker)
        news = get_news(data["name"])

    # ── Company header ─────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f'<div class="company-name">{data["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{data["sector"]}  ·  {data["industry"]}  ·  {data["country"]}</div>', unsafe_allow_html=True)

    # ── Live metric strip ─────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Current Price", data["current_price"])
    with m2:
        st.metric("Market Cap", data["market_cap"])
    with m3:
        rating = data["analyst_rating"]
        emoji = "🟢" if rating in ["BUY", "STRONG_BUY"] else "🔴" if rating in ["SELL", "STRONG_SELL"] else "🟡"
        st.metric("Analyst Rating", f"{emoji} {rating}")
    with m4:
        st.metric("P/E Ratio", data["pe_ratio"])

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric("Revenue", data["revenue"])
    with m6:
        st.metric("Net Income", data["net_income"])
    with m7:
        st.metric("Dividend Yield", data["dividend_yield"])
    with m8:
        st.metric("ROE", data["return_on_equity"])

    # ── 52-week position ──────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.82rem; color:#888; margin:10px 0 20px 0;">'
        f'{get_52w_label(data["current_vs_52w"], data["52w_high"], data["52w_low"])}'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Claude analysis ───────────────────────────────────
    with st.spinner("Generating analysis..."):
        prompt = build_analysis_prompt(data, news)
        try:
            analysis = call_claude_json(prompt)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    # ── Four signal cards ─────────────────────────────────
    bq = analysis.get("business_quality", {})
    val = analysis.get("valuation", {})
    div = analysis.get("dividend", {})
    fit = analysis.get("investor_fit", {})

    health_signal, health_verdict = aggregate_business_health(bq)
    pe_signal = val.get("pe_assessment", {}).get("signal", "yellow")
    analyst_signal = val.get("analyst_view", {}).get("signal", "yellow")
    div_signal = div.get("signal", "yellow") if div.get("has_dividend") else "yellow"

    pm = analysis.get("price_momentum", {})
    pm_signal = pm.get("signal", "yellow")
    pm_class = pm.get("classification", "Unknown")
    pm_one_liner = pm.get("one_liner", "")
    momentum = data.get("price_momentum")

    # Map signal to card colours
    card_bg = {"green": "#f0faf4", "yellow": "#fffdf0", "red": "#fff5f5"}
    card_border = {"green": "#c3e6cb", "yellow": "#ffeaa0", "red": "#ffc8c8"}
    card_text = {"green": "#1a5c2a", "yellow": "#7a6000", "red": "#7a1c1c"}

    def signal_card_html(title, signal, verdict, supporting):
        bg = card_bg.get(signal, "#fffdf0")
        border = card_border.get(signal, "#ffeaa0")
        txt = card_text.get(signal, "#7a6000")
        icon = signal_icon(signal)
        return f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:10px;
                    padding:16px; text-align:center; height:100%;">
            <div style="font-size:0.65rem; font-weight:600; letter-spacing:1px;
                        text-transform:uppercase; color:#999; margin-bottom:8px;">
                {title}
            </div>
            <div style="font-size:1.6rem; margin-bottom:4px;">{icon}</div>
            <div style="font-size:1.0rem; font-weight:600; color:{txt};
                        margin-bottom:4px;">{verdict}</div>
            <div style="font-size:0.78rem; color:#666;">{supporting}</div>
        </div>
        """

    upside = get_upside_pct(data["current_price"], data["target_price"])
    profit_margin = data["profit_margin"]
    pe = data["pe_ratio"]
    div_yield = data["dividend_yield"] if div.get("has_dividend") else "No dividend"
    analyst_rating = data["analyst_rating"]

    def build_bar(label, pct, colour):
        if pct is None:
            return ""
        width = min(abs(pct) * 1.5, 80)
        direction = "▼" if pct < 0 else "▲"
        return f"""<div style="margin-bottom:5px;">
            <div style="font-size:0.62rem; color:#999; margin-bottom:2px;">{label}</div>
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="background:{colour}; height:6px; width:{width}px;
                            border-radius:3px; flex-shrink:0;"></div>
                <span style="font-size:0.72rem; color:#444; font-weight:500;">
                    {direction}{abs(pct)}%
                </span>
            </div>
        </div>"""

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    with sc1:
        st.markdown(signal_card_html(
            "Business Health", health_signal, health_verdict, profit_margin
        ), unsafe_allow_html=True)
    with sc2:
        st.markdown(signal_card_html(
            "Valuation", pe_signal,
            "Cheap" if pe_signal == "green" else "Expensive" if pe_signal == "red" else "Fair",
            pe
        ), unsafe_allow_html=True)
    with sc3:
        st.markdown(signal_card_html(
            "Analysts", analyst_signal, analyst_rating, upside
        ), unsafe_allow_html=True)
    with sc4:
        st.markdown(signal_card_html(
            "Dividend", div_signal,
            "Sustainable" if div_signal == "green" else "At Risk" if div_signal == "red" else "Stretched" if div.get("has_dividend") else "None",
            div_yield
        ), unsafe_allow_html=True)
    with sc5:
        if momentum:
            sp  = momentum["stock_pct"]
            scp = momentum.get("sector_pct")
            mp  = momentum.get("market_pct")

            stock_colour  = "#dc3545" if sp < 0 else "#28a745"
            sector_colour = "#ffc107" if scp and scp < 0 else "#28a745"
            market_colour = "#aaa"

            bars_html = (
                build_bar("STOCK",  sp,  stock_colour) +
                build_bar("SECTOR", scp, sector_colour) +
                build_bar("MARKET", mp,  market_colour)
            )

            bg     = {"green": "#f0faf4", "yellow": "#fffdf0", "red": "#fff5f5"}.get(pm_signal, "#fffdf0")
            border = {"green": "#c3e6cb", "yellow": "#ffeaa0", "red": "#ffc8c8"}.get(pm_signal, "#ffeaa0")
            txt    = {"green": "#1a5c2a", "yellow": "#7a6000", "red": "#7a1c1c"}.get(pm_signal, "#7a6000")

            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {border};
                        border-radius:10px; padding:14px 12px;">
                <div style="font-size:0.62rem; font-weight:600;
                            letter-spacing:1px; text-transform:uppercase;
                            color:#999; margin-bottom:10px;">
                    PRICE MOVEMENT
                </div>
                {bars_html}
                <div style="margin-top:10px; font-size:0.78rem;
                            font-weight:600; color:{txt};">
                    {pm_class}
                </div>
                <div style="font-size:0.72rem; color:#888; margin-top:2px;">
                    {pm_one_liner}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    # ── Verdict ───────────────────────────────────────────
    st.markdown(f"""
    <div class="verdict-box">
        <div class="verdict-label">Verdict</div>
        {analysis.get('verdict', '')}
    </div>
    """, unsafe_allow_html=True)

    # ── What they do ──────────────────────────────────────
    st.markdown('<div class="section-header">What This Company Does</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.9rem; color:#333; line-height:1.7;">{analysis.get("what_they_do", "")}</div>', unsafe_allow_html=True)

    # ── Business quality ──────────────────────────────────
    st.markdown('<div class="section-header">Business Quality</div>', unsafe_allow_html=True)
    bq = analysis.get("business_quality", {})

    for label, key in [
        ("Profitability", "profitability"),
        ("Capital Efficiency (ROE)", "roe"),
        ("Earnings Quality", "earnings_quality"),
        ("Debt", "debt"),
    ]:
        metric = bq.get(key, {})
        analysis_card(label, metric.get("signal", "yellow"), metric.get("text", ""))

    col_s, col_c = st.columns(2)
    with col_s:
        st.markdown(f"""
        <div class="highlight-box highlight-strength">
            <strong>✅ Strength</strong><br>{bq.get('strength', '')}
        </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown(f"""
        <div class="highlight-box highlight-concern">
            <strong>⚠️ Concern</strong><br>{bq.get('concern', '')}
        </div>
        """, unsafe_allow_html=True)

    # ── Valuation ─────────────────────────────────────────
    st.markdown('<div class="section-header">Valuation</div>', unsafe_allow_html=True)
    val = analysis.get("valuation", {})

    for label, key in [
        ("P/E Assessment", "pe_assessment"),
        ("Price Position", "price_position"),
        ("Analyst View", "analyst_view"),
    ]:
        metric = val.get(key, {})
        analysis_card(label, metric.get("signal", "yellow"), metric.get("text", ""))

    # ── Dividend ──────────────────────────────────────────
    div = analysis.get("dividend", {})
    if div.get("has_dividend"):
        st.markdown('<div class="section-header">Dividend</div>', unsafe_allow_html=True)
        analysis_card("Dividend", div.get("signal", "yellow"), div.get("text", ""))

    # ── Investor fit ──────────────────────────────────────
    st.markdown('<div class="section-header">Investor Fit</div>', unsafe_allow_html=True)
    fit = analysis.get("investor_fit", {})

    col_suits, col_not = st.columns(2)
    with col_suits:
        suits_items = "".join([f'<div class="fit-item">✅ {item}</div>' for item in fit.get("suits", [])])
        st.markdown(f"""
        <div class="fit-card">
            <div class="fit-header fit-suits">Suits</div>
            {suits_items}
        </div>
        """, unsafe_allow_html=True)
    with col_not:
        not_items = "".join([f'<div class="fit-item">❌ {item}</div>' for item in fit.get("doesnt_suit", [])])
        st.markdown(f"""
        <div class="fit-card">
            <div class="fit-header fit-not">Doesn't Suit</div>
            {not_items}
        </div>
        """, unsafe_allow_html=True)

    # ── Risks ─────────────────────────────────────────────
    st.markdown('<div class="section-header">Top Risks</div>', unsafe_allow_html=True)
    for i, risk in enumerate(fit.get("risks", []), 1):
        st.markdown(f"""
        <div class="risk-item">
            <span class="risk-number">{i}.</span>{risk}
        </div>
        """, unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────
    st.markdown(f'<div class="disclaimer">⚠️ {analysis.get("disclaimer", "")}</div>',
                unsafe_allow_html=True)

    # ── Anomaly cards ─────────────────────────────────────
    anomalies = data.get("anomalies", [])
    if anomalies:
        st.markdown('<div class="section-header">Anomaly Deep Dives</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.82rem; color:#999; margin-bottom:12px;">These metrics were flagged as unusual. Click each one to understand what it means.</div>', unsafe_allow_html=True)

        for anomaly in anomalies:
            with st.expander(f"⚠️ {anomaly['metric']} — {anomaly['value']}"):
                with st.spinner("Researching this anomaly..."):
                    anomaly_prompt = build_anomaly_prompt(
                        metric=anomaly["metric"],
                        value=anomaly["value"],
                        sector=anomaly["sector"],
                        industry=anomaly["industry"],
                        threshold=anomaly["threshold"]
                    )
                    anomaly_analysis = call_claude(anomaly_prompt, max_tokens=400)
                st.markdown(anomaly_analysis)

elif analyse_button and not ticker_input:
    st.warning("Please enter an ASX ticker symbol first.")