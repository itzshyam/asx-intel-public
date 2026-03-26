import anthropic
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def call_claude(prompt, max_tokens=1500):
    """Single Claude call returning plain text. Used by anomaly deep dive."""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def call_claude_json(prompt, max_tokens=2000):
    """
    Single Claude call returning parsed JSON.
    Kept for fallback — anomaly deep dive uses this directly.
    """
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text.strip()

    # Strip markdown code blocks if Claude wraps response despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


def run_crew_analysis(data: dict, news: list) -> dict:
    """
    Runs the two-agent pipeline via native Python orchestration.
    Agent 1 analyses and triages concerns.
    Agent 2 stress tests and runs compliance check.
    Returns final enriched JSON dict.
    """
    from pipeline import run_analysis_crew
    from prompts.agent1 import build_agent1_prompt
    from prompts.agent2 import build_agent2_prompt

    # Build Agent 1 prompt with all financial data
    agent1_prompt = build_agent1_prompt(data, news)

    # Build Agent 2 prompt template — pipeline.py injects Agent 1 output at runtime
    # {agent1_output} is the placeholder that gets replaced with actual Agent 1 JSON
    agent2_prompt_template = build_agent2_prompt()

    return run_analysis_crew(agent1_prompt, agent2_prompt_template)