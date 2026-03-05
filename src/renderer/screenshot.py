"""Playwright-based HTML → PNG screenshot renderer.

Produces a 1072×1448 pixel grayscale PNG optimized for Kindle PW3 e-ink.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from src.config import settings

logger = logging.getLogger(__name__)


def render_png(html_content: str, output_path: Path | str | None = None) -> Path:
    """Render HTML string to a 1072×1448 grayscale PNG.

    Args:
        html_content: Full HTML string (with embedded fonts).
        output_path: Where to save the PNG. Defaults to settings.output_png.

    Returns:
        Path to the generated PNG file.
    """
    output = Path(output_path) if output_path else settings.output_png
    output.parent.mkdir(parents=True, exist_ok=True)

    width = settings.screen_width
    height = settings.screen_height

    logger.info(f"Launching Playwright for {width}×{height} screenshot…")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=1,  # 1:1 CSS px → device px
        )

        page.set_content(html_content, wait_until="networkidle")

        # Small wait for fonts to fully rasterize
        page.wait_for_timeout(500)

        # Screenshot
        png_bytes = page.screenshot(
            path=str(output),
            full_page=False,  # Clip to viewport
            type="png",
        )

        browser.close()

    # Post-process: convert to 8-bit grayscale for optimal e-ink display
    _convert_to_grayscale(output)

    file_size = output.stat().st_size
    logger.info(f"PNG saved: {output} ({file_size:,} bytes)")
    return output


def _convert_to_grayscale(path: Path) -> None:
    """Convert PNG to 8-bit grayscale (optimal for e-ink)."""
    with Image.open(path) as img:
        if img.mode != "L":
            gray = img.convert("L")
            gray.save(path, "PNG", optimize=True)
            logger.info(f"Converted to grayscale: {img.mode} → L")
