"""Gmail fetcher — uses gog CLI to query emails.

Leverages OpenClaw's existing OAuth credentials via the `gog` CLI tool.
No need to manage Google API tokens ourselves.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailSummary:
    sender: str           # "Matt Shimizu" or "matt@example.com"
    subject: str          # truncated to ~60 chars
    snippet: str          # first line preview
    priority: str         # "P1", "P2", "P3"
    is_unread: bool = True


def _run_gog(args: list[str], timeout: int = 15) -> str | None:
    """Run a gog CLI command and return stdout."""
    cmd = ["gog"] + args
    if settings.gog_account:
        cmd.extend(["--account", settings.gog_account])

    import os
    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env.get("PATH", "")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode != 0:
            logger.error(f"gog failed: {result.stderr.strip()}")
            return None
        return result.stdout
    except FileNotFoundError:
        logger.error("gog CLI not found — install via: brew install steipete/tap/gogcli")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"gog timed out after {timeout}s")
        return None


def _classify_priority(labels: list[str], subject: str) -> str:
    """Simple priority classification based on Gmail labels."""
    labels_lower = [l.lower() for l in labels]

    if "important" in labels_lower or "starred" in labels_lower:
        return "P1"
    if "category_updates" in labels_lower or "category_social" in labels_lower:
        return "P3"
    return "P2"


def _truncate(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _extract_sender_name(from_str: str) -> str:
    """Extract readable name from 'Name <email>' format."""
    if "<" in from_str:
        name = from_str.split("<")[0].strip().strip('"')
        if name:
            return name
    # Fallback: use email prefix
    return from_str.split("@")[0].strip("<>").strip()


def fetch_gmail() -> list[EmailSummary]:
    """Fetch recent important/unread emails via gog CLI."""

    # Try JSON mode first
    raw = _run_gog([
        "gmail", "messages", "search",
        "in:inbox newer_than:1d",
        "--max", str(settings.max_emails * 2),  # fetch extra, then filter
        "--json",
    ])

    if raw is None:
        logger.warning("Gmail fetch failed, returning empty")
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # gog might not support --json for all commands; parse text
        logger.warning("gog JSON parse failed, attempting text parse")
        return _parse_text_output(raw)

    emails: list[EmailSummary] = []
    items = data if isinstance(data, list) else data.get("messages", data.get("threads", []))

    for item in items:
        # gog JSON structure varies; handle gracefully
        sender = item.get("from", item.get("sender", "Unknown"))
        subject = item.get("subject", "(no subject)")
        snippet = item.get("snippet", "")
        labels = item.get("labels", item.get("labelIds", []))
        if isinstance(labels, str):
            labels = [labels]

        emails.append(EmailSummary(
            sender=_extract_sender_name(sender),
            subject=_truncate(subject),
            snippet=_truncate(snippet, 80),
            priority=_classify_priority(labels, subject),
            is_unread="UNREAD" in [l.upper() for l in labels],
        ))

    # Sort by priority, take top N
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    emails.sort(key=lambda e: priority_order.get(e.priority, 9))
    return emails[: settings.max_emails]


def _parse_text_output(raw: str) -> list[EmailSummary]:
    """Fallback: parse gog plain-text output."""
    emails: list[EmailSummary] = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or line.startswith(("─", "=", "-")):
            continue
        # Simple heuristic: each line is a thread/message summary
        emails.append(EmailSummary(
            sender="",
            subject=_truncate(line),
            snippet="",
            priority="P2",
        ))
    return emails[: settings.max_emails]
