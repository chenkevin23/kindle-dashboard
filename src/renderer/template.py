"""Jinja2 template rendering with base64 font embedding."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import settings

logger = logging.getLogger(__name__)


def _load_font_b64(filename: str) -> str:
    """Read a font file and return its base64 encoding."""
    path = settings.fonts_dir / filename
    if not path.exists():
        logger.warning(f"Font not found: {path}")
        return ""
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def _load_fonts() -> dict[str, str]:
    """Load all fonts as base64 strings."""
    return {
        "font_jbm_regular": _load_font_b64("JetBrainsMono-Regular.woff2"),
        "font_jbm_bold": _load_font_b64("JetBrainsMono-Bold.woff2"),
        "font_ibm_regular": _load_font_b64("IBMPlexSans-Regular.woff2"),
        "font_ibm_bold": _load_font_b64("IBMPlexSans-Bold.woff2"),
    }


def render_html(context: dict) -> str:
    """Render the dashboard template with data context and embedded fonts.

    Args:
        context: dict with keys: date_str, time_of_day, owner_name,
                 emails, events, tasks, tasks_done, news,
                 ai_message, last_updated

    Returns:
        Fully rendered HTML string with embedded fonts.
    """
    env = Environment(
        loader=FileSystemLoader(str(settings.templates_dir)),
        autoescape=False,
    )
    template = env.get_template("dashboard.html")

    # Merge font data into context
    full_context = {**_load_fonts(), **context}

    html = template.render(**full_context)
    logger.info(f"Rendered HTML template ({len(html):,} bytes)")
    return html
