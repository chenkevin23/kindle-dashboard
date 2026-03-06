"""Centralized configuration — loads from .env and environment variables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenClaw integration ──
    openclaw_calendar_cache: Path = Path.home() / ".openclaw" / "cache" / "calendar-today.txt"
    gog_account: str = "chenk.ny@gmail.com"

    # ── Kindle connection (SCP mode) ──
    kindle_host: str = ""
    kindle_user: str = "root"
    kindle_ssh_key_path: Optional[str] = None
    kindle_ssh_key_b64: Optional[str] = None  # base64-encoded private key for Railway
    kindle_remote_path: str = "/mnt/us/dashboard/dashboard.png"

    # ── S3/R2 upload (cloud mode) ──
    s3_bucket: Optional[str] = None
    s3_key: str = "dashboard.png"
    s3_endpoint_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # ── RSS feeds ──
    rss_feeds: str = '[{"name":"TechCrunch","url":"https://techcrunch.com/feed/"},{"name":"Hacker News","url":"https://hnrss.org/frontpage?count=5"}]'

    # ── Display settings ──
    timezone: str = "America/Los_Angeles"
    owner_name: str = "KC"
    screen_width: int = 1072
    screen_height: int = 1448
    max_emails: int = 5
    max_events: int = 8
    max_news: int = 8

    # ── Todoist ──
    todoist_api_token: str = ""   # or auto-reads from ~/.config/todoist/api_token

    # ── Weather ──
    weather_lat: float = 47.61    # Seattle / Bellevue
    weather_lon: float = -122.33

    # ── Paths (auto-resolved) ──
    project_root: Path = Path(__file__).resolve().parent.parent
    output_dir: Path = Path(__file__).resolve().parent.parent / "output"
    fonts_dir: Path = Path(__file__).resolve().parent.parent / "fonts"
    templates_dir: Path = Path(__file__).resolve().parent.parent / "templates"

    @field_validator("openclaw_calendar_cache", mode="before")
    @classmethod
    def expand_home(cls, v: str | Path) -> Path:
        return Path(str(v)).expanduser()

    def get_rss_feeds(self) -> list[dict]:
        """Parse RSS_FEEDS JSON string into list of dicts."""
        return json.loads(self.rss_feeds)

    @property
    def output_png(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / "dashboard.png"

    @property
    def can_scp(self) -> bool:
        return bool(self.kindle_host)

    @property
    def can_s3(self) -> bool:
        return bool(self.s3_bucket)


# Singleton
settings = Settings()
