# ASX Intel 📊

**AI-powered company intelligence for ASX-listed stocks.**

Live demo: https://asx-intel-fae3bah2chavbzc8.australiaeast-01.azurewebsites.net

---

## What It Does

Enter any ASX ticker symbol and get a plain-English intelligence report on the company — not raw numbers, but meaning. Built for investors who want to understand a business quickly without wading through annual reports.

**Example output for NST (Northern Star Resources):**
- Verdict: *Gold miner trading near 52-week lows with strong earnings and cash generation, but extreme leverage and sector-wide weakness create material risks despite attractive valuation.*
- Colour-coded business quality signals across profitability, ROE, earnings quality, and debt
- Valuation assessment with sector P/E context
- Dividend sustainability analysis
- Investor fit — who this stock suits and who it doesn't
- Top 3 ranked risks

---

## Why I Built This

I'm a network engineer who researches ASX companies obsessively. The problem: financial data is everywhere but meaning is hard to find. P/E of 15x — is that cheap or expensive? Depends entirely on the sector, the business model, and what's happening in the market right now.

This tool solves that. It combines live financial data, recent news, and a carefully engineered LLM prompt layer to produce analysis that reads like a knowledgeable friend explaining a stock — not a Bloomberg terminal.

---

## Architecture
```
asx-intel/
├── app.py                        ← Streamlit UI coordinator
├── claude_client.py              ← Anthropic Claude API handler
├── data/
│   ├── financials.py             ← Signal calculations + anomaly detection
│   ├── news.py                   ← News search + formatting
│   └── sources/
│       ├── yfinance_source.py    ← Yahoo Finance data connector
│       └── newsapi_source.py     ← NewsAPI connector
└── prompts/                      ← Prompt engineering layer (private IP)
```

**One file, one job.** Each component is independently replaceable — swap yfinance for a better data source, add a new feature, change the LLM — without touching the rest of the system.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Language | Python 3.11 | Industry standard for AI/LLM tooling |
| Financial Data | yfinance | Live ASX data via Yahoo Finance |
| News | NewsAPI | Recent headlines for context |
| LLM | Anthropic Claude API | Best-in-class narrative generation |
| Frontend | Streamlit | Fast interactive UI without frontend overhead |
| Deployment | Azure App Service (B1) | Production cloud deployment, CI/CD via GitHub Actions |

---

## Key Engineering Decisions

**Structured JSON output from Claude** — Claude returns structured JSON, not markdown text. The app controls every design decision independently. Same data could power a mobile app or PDF report without changing the analysis layer.

**Modular architecture** — Adding a new feature means adding new files, not editing existing ones. The Claude client never changes regardless of how many features are added.

**Anomaly detection** — A separate detection layer flags unusual metrics (D/E above 10x for non-banks, cashflow below 0.5x net income, P/E above 80x) and triggers a second Claude call for deep-dive research.

**Prompt engineering** — The analysis prompt uses conditional sector context (only explain norms when a metric would mislead without it), transient distortion handling (cross-reference news before flagging concerns), and hard word limits per section.

---

## Live Features

- 8 live metric cards (price, market cap, analyst rating, P/E, revenue, net income, dividend yield, ROE)
- 52-week price position in plain English
- 5 signal cards: Business Health, Valuation, Analysts, Dividend, Price Movement
- Price movement vs sector index vs ASX200 (relative performance bars)
- Colour-coded analysis cards (green/yellow/red per metric)
- Two-column Investor Fit layout
- Anomaly Deep Dive expandable cards

---

## Deployment

Hosted on Azure App Service (Australia East, B1 tier). Auto-deploys via GitHub Actions on every push to main.

---

## About

Built by Shyam — network engineer (CCNP, DevAsc, AZ-700) based in Melbourne, exploring the intersection of infrastructure thinking and AI application development.

Substack: [Beyond the Config](https://substack.com/@itzshyam) — where network engineering meets business and financial thinking.

---

*This tool provides general financial information only and does not constitute financial advice.*