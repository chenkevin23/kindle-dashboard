"""Calendar fetcher — reads OpenClaw's icalBuddy cache file.

The cache at ~/.openclaw/cache/calendar-today.txt is updated every 5 min
by a LaunchAgent. Format: ANSI-colored icalBuddy output.

Fallback: call icalBuddy directly if cache is stale (>10 min old).
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)

# Strip ANSI escape sequences
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Match event title line: "• Title (Calendar)"
TITLE_RE = re.compile(r"^•\s+(.+?)\s+\(([^)]+)\)\s*$")

# Match time line: "10:00 AM - 11:30 AM"
TIME_RE = re.compile(r"^\s*(\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))\s*$")


@dataclass
class CalendarEvent:
    title: str
    calendar: str
    start_time: str = ""      # "10:00 AM"
    end_time: str = ""        # "11:30 AM"
    time_display: str = ""    # "10:00" (short form for dashboard)
    is_all_day: bool = False


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _read_cache() -> str:
    """Read the icalBuddy cache, with staleness check."""
    cache_path = settings.openclaw_calendar_cache

    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < 600:  # fresh enough (< 10 min)
            logger.info(f"Reading calendar cache (age: {age:.0f}s)")
            return cache_path.read_text(encoding="utf-8", errors="replace")
        else:
            logger.warning(f"Calendar cache is stale ({age:.0f}s old), trying direct icalBuddy")

    # Fallback: call icalBuddy directly
    try:
        result = subprocess.run(
            ["/opt/homebrew/bin/icalBuddy", "-f", "-iep", "title,datetime,location,notes,calendar", "eventsToday"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"icalBuddy fallback failed: {e}")

    return ""


def _parse_icalbuddy(raw: str) -> list[CalendarEvent]:
    """Parse icalBuddy output into structured events."""
    clean = _strip_ansi(raw)
    lines = clean.splitlines()

    events: list[CalendarEvent] = []
    current: CalendarEvent | None = None

    for line in lines:
        stripped = line.strip()

        # Title line
        title_match = TITLE_RE.match(stripped)
        if title_match:
            if current:
                events.append(current)
            current = CalendarEvent(
                title=title_match.group(1).strip(),
                calendar=title_match.group(2).strip(),
            )
            continue

        # Time line
        time_match = TIME_RE.match(stripped)
        if time_match and current:
            current.start_time = time_match.group(1).strip()
            current.end_time = time_match.group(2).strip()
            # Short display: "10:00" from "10:00 AM"
            current.time_display = current.start_time.replace(" AM", "").replace(" PM", "")
            continue

    # Don't forget the last event
    if current:
        events.append(current)

    return events


def fetch_calendar() -> list[CalendarEvent]:
    """Fetch today's calendar events, limited to settings.max_events."""
    raw = _read_cache()
    if not raw.strip():
        logger.warning("No calendar data available")
        return []

    events = _parse_icalbuddy(raw)
    logger.info(f"Parsed {len(events)} calendar events")

    # Limit and return
    return events[: settings.max_events]
