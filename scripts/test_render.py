#!/usr/bin/env python3
"""Local test: render dashboard with sample data (no API calls needed).

Usage: python scripts/test_render.py
Output: output/dashboard.png
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.renderer.template import render_html
from src.renderer.screenshot import render_png


def main():
    # Sample data matching the screenshot design
    context = {
        "date_str": "WED MAR 05, 2026",
        "date_long": "Wednesday, March 5, 2026",
        "time_of_day": "morning",
        "owner_name": "KC",
        "weather": {
            "temp_current": 48,
            "temp_high": 54,
            "temp_low": 39,
            "description": "Partly Cloudy",
            "description_short": "PARTLY CLOUDY",
            "wind_mph": 8,
            "humidity": 72,
        },
        "emails": [
            {"sender": "Intuit SA Team", "subject": "Cache warmup timeout — need config update", "priority": "p1"},
            {"sender": "Demandbase", "subject": "Cluster scaling request for Q1 load", "priority": "p1"},
            {"sender": "Product Team", "subject": "Roadmap review slides — feedback needed", "priority": "p2"},
            {"sender": "GitHub", "subject": "inbox-os-digest: 2 new issues opened", "priority": "p3"},
        ],
        "events": [
            {"time_display": "09:00", "title": "Standup — Product & Eng"},
            {"time_display": "10:30", "title": "Product Sync — Roadmap Review", "highlight": True},
            {"time_display": "13:00", "title": "Lunch"},
            {"time_display": "14:00", "title": "Customer Call — Intuit Escalation"},
            {"time_display": "16:30", "title": "1:1 with Manager"},
        ],
        "tasks": [
            {"title": "Update Intuit escalation doc", "done": True},
            {"title": "Review Demandbase cluster config", "done": True},
            {"title": "Finalize CFA roadmap draft", "done": False},
            {"title": "Prep AI strategy deck for Intuit", "done": False},
            {"title": "Review Jira backlog — P0 triage", "done": False},
        ],
        "tasks_done": 2,
        "news": [
            {"title": "Databricks launches serverless real-time analytics", "source": "TECHCRUNCH"},
            {"title": "Snowflake acquires AI startup for $400M", "source": "REUTERS"},
            {"title": "Enterprise OLAP market projected $18B by 2028", "source": "GARTNER"},
            {"title": "Open-source DB adoption up 40% YoY", "source": "DB-ENGINES"},
            {"title": "Google Cloud adds vector search to BigQuery", "source": "GOOGLE BLOG"},
            {"title": "ClickHouse raises $250M Series C at $4B valuation", "source": "BLOOMBERG"},
        ],
        "ai_message": "Intuit escalation is top priority — cache warmup config param exists but needs BYOC exposure. Roadmap review at 10:30, prep CFA slides. Inbox OS digest had 2 new issues overnight.",
        "last_updated": "07:45 AM PST",
    }

    print("Rendering HTML template…")
    html = render_html(context)

    print(f"HTML size: {len(html):,} bytes")
    print("Taking screenshot…")
    output = render_png(html)

    print(f"\n✓ Dashboard rendered: {output}")
    print(f"  Size: {output.stat().st_size:,} bytes")
    print(f"  Open: open {output}")


if __name__ == "__main__":
    main()
