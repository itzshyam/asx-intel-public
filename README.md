# ASX Intel — AI-Powered Financial Intelligence

> Two-agent AI pipeline that analyses any ASX-listed stock and returns a plain-English verdict — live at [asx-intel-fae3bah2chavbzc8.australiaeast-01.azurewebsites.net](https://asx-intel-fae3bah2chavbzc8.australiaeast-01.azurewebsites.net)

---

## What it does

Enter any ASX ticker. Two AI agents work in sequence — one analyses the financials and assigns colour-coded signals, the other stress-tests those conclusions using live Gemini web search before anything reaches the user. The result is a plain-English verdict covering business quality, valuation, dividend sustainability, and investor fit.

---

## Live demo

**[Try it here →](https://asx-intel-fae3bah2chavbzc8.australiaeast-01.azurewebsites.net)**

Works on desktop and mobile. Enter any ASX ticker — BHP, CBA, WES, NST, CSL.

---

## Architecture

See the full pipeline diagram and design decisions → **[How It Works](https://asx-intel-fae3bah2chavbzc8.australiaeast-01.azurewebsites.net/how-it-works)**

### Why two agents

Most AI tools use a single prompt to do everything. ASX Intel separates analysis from validation — Agent 1 forms a view from the data, Agent 2 stress-tests it against real-world context before the output reaches the user. The same pattern a senior analyst uses to pressure-test a junior's work before it goes to a client.

### Why native Python orchestration

CrewAI was evaluated and rejected. It makes 4-6 hidden API calls per execution on top of the two agent calls — this consistently hit the Anthropic rate limit. Native Python orchestration replaced it: exactly two Claude calls per analysis, full control over every API call, no hidden overhead.

---

## Tech stack

| Component | Technology | Notes |
|---|---|---|
| LLM — both agents | Anthropic Claude Haiku | Deterministic signal output |
| Web search | Gemini Flash + Google grounding | Batched — one call covers all flagged concerns |
| Financial data | yfinance | ASX-compatible via .AX suffix tickers |
| News | NewsAPI | Free tier, broad search — replacement planned |
| Orchestration | Native Python | CrewAI evaluated and rejected (see above) |
| Backend | FastAPI + Jinja2 | Decoupled from presentation layer |
| Deployment | Azure App Service B1 | Australia East · GitHub Actions CI/CD |
| Language | Python 3.11 | — |

---

## Known limitations

- **Analysis time:** 40–55 seconds. Two sequential Claude calls plus Gemini web search. Async parallelisation is the planned fix.
- **Fundamentals lag:** yfinance returns the most recent annual or semi-annual filing — up to 12 months old for some ASX companies.
- **News relevance:** NewsAPI free tier search is broad, not company-specific. A dedicated ASX announcements feed is planned.
- **Concurrency:** Single Azure B1 instance. Concurrent users queue. Four uvicorn workers partially mitigate this.

---

## Disclaimer

This tool provides general financial information only and does not constitute financial advice. Always verify against ASX announcements and consult a licensed financial adviser before making investment decisions.

---

## Author

Built by Shyam.

[Beyond the Config](https://open.substack.com/pub/itzshyam) · [LinkedIn](https://linkedin.com/in/itzshyam)
