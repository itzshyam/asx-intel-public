import json
import time
import anthropic
from dotenv import load_dotenv
from datetime import date
import os

load_dotenv()

# Single Anthropic client for both agents
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _call_agent(prompt: str, max_tokens: int = 4000) -> str:
    """
    Single Claude API call with retry logic for rate limits.
    Used by both agents — same model, same client, full control.
    """
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                temperature=0,  # Deterministic — same data always produces same signals
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except anthropic.RateLimitError:
            if attempt < 2:
                wait = (attempt + 1) * 20  # 20s, 40s
                print(f"Rate limit — waiting {wait}s before retry {attempt + 2}/3")
                time.sleep(wait)
            else:
                raise


def _parse_json(raw: str) -> dict:
    """
    Robustly parse JSON from Claude's response.
    Handles markdown fences and any preamble text.
    """
    raw = raw.strip()

    # Strip markdown code fences if present
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    # Find outermost JSON object — handles any leading/trailing text
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}")
        print(f"Raw output (first 500 chars): {raw[:500]}")
        raise


def _run_agent2_searches(concerns: list) -> str:
    """
    Batches all concern research into a single Gemini call.
    Gemini handles multiple internal searches automatically.
    One network round trip instead of one per concern — faster and cleaner.
    """
    from data.sources.gemini_search import search_web

    if not concerns:
        return "No concerns flagged by Agent 1 — no searches performed."

    # Filter to only concerns Agent 1 flagged as needing web verification
    searchable = [c for c in concerns if c.get("needs_search", False)]
    if not searchable:
        return "No concerns required web search."

    # Build one batched query covering all concerns
    # Gemini's grounding handles multiple internal searches automatically —
    # no need to call it once per concern like we did before
    today = date.today().strftime("%d %B %Y")
    concern_lines = "\n".join([
        f"- {c.get('metric')}: {c.get('search_hint', c.get('metric', ''))}"
        for c in searchable
    ])

    batched_query = (
        f"Research the following concerns about an ASX-listed company "
        f"as of {today}. For each concern, find recent news, ASX "
        f"announcements, or market context that explains whether it is "
        f"a temporary issue or a structural problem:\n\n"
        f"{concern_lines}"
    )

    print(f"Agent 2 running batched search for {len(searchable)} concerns...")
    result = search_web(batched_query)

    # Return findings with date header so Agent 2 knows how fresh the data is
    return (
        f"=== AGENT 2 RESEARCH FINDINGS (as of {today}) ===\n\n"
        f"{result}"
    ) if result else "Search returned no results."


def run_analysis_crew(agent1_prompt: str, agent2_prompt_template: str) -> dict:
    """
    Native two-agent pipeline with Gemini web search.

    Agent 1: Financial Analyst
    Receives financial data, writes analysis, triages concerns.

    Agent 2: Devil's Advocate
    Receives Agent 1 output + real web search findings,
    stress tests conclusions, adjusts signals, runs compliance check.

    API calls: 2 Claude + up to 4 Gemini searches.
    Context passed manually — no framework overhead.
    """

    # ── Agent 1 — Financial Analyst ───────────────────────────────────
    print("Running Agent 1 — Financial Analyst...")
    agent1_raw    = _call_agent(agent1_prompt, max_tokens=3000)
    agent1_output = _parse_json(agent1_raw)

    # ── Extract concerns and run targeted web searches ─────────────────
    # Agent 2 gets both Agent 1's analysis AND real search findings
    concerns       = agent1_output.get("concerns", [])
    
    # Log what Agent 1 flagged so we can see triage decisions in terminal
    if concerns:
        print(f"Agent 1 flagged {len(concerns)} concern(s):")
        for c in concerns:
            print(f"  → {c.get('metric')} | {c.get('value')} | "
              f"Category: {c.get('initial_category')} | "
              f"Confidence: {c.get('confidence')}")
    else:
        print("Agent 1 flagged no concerns")

    search_results = _run_agent2_searches(concerns)

    # ── Agent 2 — Devil's Advocate ────────────────────────────────────
    print("Running Agent 2 — Devil's Advocate...")
    agent2_prompt = agent2_prompt_template.replace(
        "{agent1_output}",
        json.dumps(agent1_output, indent=2)
    )

    # Inject search findings into Agent 2 prompt
    agent2_prompt = agent2_prompt + f"\n\n{search_results}"

    agent2_raw   = _call_agent(agent2_prompt, max_tokens=3000)
    final_output = _parse_json(agent2_raw)

    # Preserve Agent 1's original signals so the Business Health summary cards
    # always reflect the base financial analysis. Agent 2 may adjust these
    # signals during its devil's advocate review, which would cause the summary
    # cards to change unpredictably between runs on the same data.
    final_output["agent1_signals"] = {
        "business_quality": agent1_output.get("business_quality", {}),
        "valuation":        agent1_output.get("valuation", {}),
        "dividend":         agent1_output.get("dividend", {})
    }

    return final_output