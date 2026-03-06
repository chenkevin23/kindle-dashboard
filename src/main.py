"""kindle-dashboard entry point.

Usage:
    python -m src.main                          # Render only (save to output/)
    python -m src.main --push                   # Render + push to Kindle
    python -m src.main --message "Today's focus: ..."   # Custom AI message
    python -m src.main --push --message "..."   # Full pipeline

Luka (OpenClaw) calls this via exec to generate and push dashboard updates.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import datetime

from dateutil import tz

from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("kindle-dashboard")


@dataclass
class TaskItem:
    """Simple task item for dashboard display."""
    title: str
    done: bool = False


def _get_time_of_day(hour: int) -> str:
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"


def _build_context(args: argparse.Namespace) -> dict:
    """Fetch all data sources and build template context."""
    local_tz = tz.gettz(settings.timezone)
    now = datetime.now(local_tz)

    # ── Fetch data ──
    logger.info("Fetching calendar…")
    from src.fetchers.calendar import fetch_calendar
    events = fetch_calendar()

    logger.info("Fetching email…")
    from src.fetchers.gmail import fetch_gmail
    emails = fetch_gmail()

    logger.info("Fetching news…")
    from src.fetchers.news import fetch_news
    news = fetch_news()

    logger.info("Fetching weather…")
    from src.fetchers.weather import fetch_weather
    weather = fetch_weather()

    # ── Tasks: Todoist first, fall back to --tasks-json ──
    tasks: list[TaskItem] = []
    if args.tasks_json:
        import json
        try:
            raw_tasks = json.loads(args.tasks_json)
            tasks = [TaskItem(title=t.get("title", ""), done=t.get("done", False)) for t in raw_tasks]
        except json.JSONDecodeError:
            logger.warning("Invalid --tasks-json, ignoring")

    if not tasks:
        logger.info("Fetching tasks from Todoist…")
        from src.fetchers.todoist import fetch_todoist
        todoist_tasks = fetch_todoist()
        tasks = [TaskItem(title=t.title, done=t.done) for t in todoist_tasks]

    tasks_done = sum(1 for t in tasks if t.done)

    context = {
        "date_str": now.strftime("%a %b %d, %Y").upper(),
        "date_long": now.strftime("%A, %B %-d, %Y"),
        "time_of_day": _get_time_of_day(now.hour),
        "owner_name": settings.owner_name,
        "emails": emails,
        "events": events,
        "tasks": tasks,
        "tasks_done": tasks_done,
        "news": news,
        "weather": weather,
        "ai_message": args.message or "",
        "last_updated": now.strftime("%I:%M %p %Z").lstrip("0"),
    }

    return context


def main() -> None:
    parser = argparse.ArgumentParser(description="Kindle E-Ink Dashboard Generator")
    parser.add_argument("--push", action="store_true", help="Push PNG to Kindle after rendering")
    parser.add_argument("--message", "-m", type=str, default="", help="AI summary message for dashboard")
    parser.add_argument("--tasks-json", type=str, default="", help='Tasks JSON: [{"title":"...", "done":true}]')
    parser.add_argument("--output", "-o", type=str, default="", help="Custom output path for PNG")
    args = parser.parse_args()

    logger.info("═══ Kindle Dashboard ═══")

    # 1. Build context
    context = _build_context(args)
    logger.info(f"Data: {len(context['emails'])} emails, {len(context['events'])} events, {len(context['news'])} news")

    # 2. Render HTML
    from src.renderer.template import render_html
    html = render_html(context)

    # 3. Screenshot to PNG
    from src.renderer.screenshot import render_png
    output_path = args.output or None
    png_path = render_png(html, output_path)
    logger.info(f"Dashboard rendered: {png_path}")

    # 4. Push to Kindle (if requested)
    if args.push:
        from src.delivery.push import deliver
        success = deliver(png_path)
        if success:
            logger.info("✓ Dashboard delivered to Kindle")
        else:
            logger.warning("⚠ Delivery failed — PNG saved locally")

    logger.info("═══ Done ═══")
    sys.exit(0)


if __name__ == "__main__":
    main()
