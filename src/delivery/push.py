"""Kindle delivery — SCP push (local) and S3 upload (cloud).

SCP mode: Push PNG directly to Kindle over WiFi (requires same network).
S3 mode: Upload to S3/R2 bucket; Kindle pulls via cron wget.
"""

from __future__ import annotations

import base64
import io
import logging
import time
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)


def push_scp(png_path: Path) -> bool:
    """Push PNG to Kindle via SCP, then trigger eips display refresh.

    Returns True on success, False on failure.
    """
    if not settings.can_scp:
        logger.warning("SCP not configured (KINDLE_HOST not set)")
        return False

    try:
        import paramiko
        from scp import SCPClient
    except ImportError:
        logger.error("paramiko/scp not installed")
        return False

    try:
        # Load SSH key
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict = {
            "hostname": settings.kindle_host,
            "username": settings.kindle_user,
            "timeout": 10,
        }

        if settings.kindle_ssh_key_b64:
            # Key from env var (base64-encoded) — for Railway
            key_data = base64.b64decode(settings.kindle_ssh_key_b64)
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(key_data.decode()))
            connect_kwargs["pkey"] = private_key
        elif settings.kindle_ssh_key_path:
            # Key from file path — for local
            connect_kwargs["key_filename"] = str(Path(settings.kindle_ssh_key_path).expanduser())
        else:
            # Try default SSH key
            connect_kwargs["key_filename"] = str(Path.home() / ".ssh" / "id_rsa")

        logger.info(f"Connecting to Kindle at {settings.kindle_host}…")
        ssh.connect(**connect_kwargs)

        # SCP the PNG
        with SCPClient(ssh.get_transport()) as scp_client:
            scp_client.put(str(png_path), settings.kindle_remote_path)
        logger.info(f"SCP uploaded: {png_path.name} → {settings.kindle_remote_path}")

        # Trigger display refresh via eips
        commands = [
            "eips -c",                                           # clear screen
            "eips -c",                                           # double-clear (reduce ghosting)
            f"eips -f -g {settings.kindle_remote_path}",         # full refresh display
        ]
        for cmd in commands:
            ssh.exec_command(cmd)
            time.sleep(0.5)

        logger.info("Kindle display refreshed ✓")
        ssh.close()
        return True

    except Exception as e:
        logger.error(f"SCP push failed: {e}")
        return False


def upload_s3(png_path: Path) -> bool:
    """Upload PNG to S3/R2 bucket.

    Returns True on success, False on failure.
    """
    if not settings.can_s3:
        logger.warning("S3 not configured (S3_BUCKET not set)")
        return False

    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed")
        return False

    try:
        client_kwargs: dict = {}
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url
        if settings.aws_access_key_id:
            client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

        s3 = boto3.client("s3", **client_kwargs)
        s3.upload_file(
            str(png_path),
            settings.s3_bucket,
            settings.s3_key,
            ExtraArgs={"ContentType": "image/png", "CacheControl": "max-age=0"},
        )
        logger.info(f"S3 uploaded: {settings.s3_bucket}/{settings.s3_key}")
        return True

    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return False


def deliver(png_path: Path) -> bool:
    """Deliver PNG via best available method.

    Tries SCP first (local), then S3 (cloud). Returns True if any succeeded.
    """
    success = False

    if settings.can_scp:
        success = push_scp(png_path) or success

    if settings.can_s3:
        success = upload_s3(png_path) or success

    if not success:
        logger.warning("No delivery method succeeded (PNG still in output/)")

    return success
