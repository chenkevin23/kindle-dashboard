"""Todoist fetcher — pulls today's tasks via Todoist REST API.

Reads API token from ~/.config/todoist/api_token or TODOIST_API_TOKEN env var.
Returns tasks due today or overdue, sorted by priority.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)

TOKEN_PATH = Path.home() / ".config" / "todoist" / "api_token"


@dataclass
class TodoistTask:
    title: str
    done: bool = False
    priority: int = 1  # Todoist: 4=urgent, 3=high, 2=medium, 1=normal


def _get_token() -> str | None:
    """Get Todoist API token from file or env."""
    # 1. Check env var
    import os
    token = os.environ.get("TODOIST_API_TOKEN", "").strip()
    if token:
        return token

    # 2. Check settings
    token = getattr(settings, "todoist_api_token", "").strip()
    if token:
        return token

    # 3. Read from file (~/.config/todoist/api_token)
    if TOKEN_PATH.exists():
        token = TOKEN_PATH.read_text().strip()
        if token:
            return token

    return None


def fetch_todoist() -> list[TodoistTask]:
    """Fetch today's + overdue tasks from Todoist."""
    token = _get_token()
    if not token:
        logger.warning("No Todoist API token found — skipping tasks")
        return []

    try:
        from todoist_api_python.api import TodoistAPI
    except ImportError:
        logger.warning("todoist-api-python not installed — pip install todoist-api-python")
        return []

    try:
        api = TodoistAPI(token)

        # Paginator returns pages (lists) of Task objects
        all_tasks = []
        for page in api.get_tasks():
            if isinstance(page, list):
                all_tasks.extend(page)
            else:
                all_tasks.append(page)

        today = date.today()

        # Filter: has a due date, due today or overdue
        relevant = []
        for t in all_tasks:
            if t.completed_at:
                continue
            if not t.due:
                continue

            # t.due.date can be date or datetime
            due_date = t.due.date
            if isinstance(due_date, datetime):
                due_date = due_date.date()

            if due_date <= today:
                relevant.append((t, due_date))

        # Sort: higher priority first (Todoist 4=urgent, 1=normal), then by due date
        relevant.sort(key=lambda x: (-x[0].priority, x[1]))

        tasks = []
        for t, _ in relevant:
            # Clean up title: remove Spark deep links and other noise
            title = t.content
            if "[OPEN IN SPARK]" in title:
                title = title.split("[OPEN IN SPARK]")[0].strip()
            if "[OPEN IN" in title:
                title = title.split("[OPEN IN")[0].strip()

            tasks.append(TodoistTask(
                title=title,
                done=bool(t.completed_at),
                priority=t.priority,
            ))

        logger.info(f"Fetched {len(tasks)} Todoist tasks (today + overdue)")
        return tasks

    except Exception as e:
        logger.error(f"Todoist fetch failed: {e}")
        return []
