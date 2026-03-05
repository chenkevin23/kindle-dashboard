#!/bin/sh
# ── Kindle-side cron script ──
# Downloads dashboard PNG from S3/R2 and displays on e-ink screen.
# Install on Kindle: add to /etc/crontab/root or use KUAL extension.
#
# Usage: sh /mnt/us/dashboard/refresh.sh
#
# Crontab entry (every 30 min):
#   */30 * * * * /bin/sh /mnt/us/dashboard/refresh.sh

IMAGE_URL="${DASHBOARD_URL:-https://your-bucket.s3.amazonaws.com/dashboard.png}"
LOCAL_PATH="/mnt/us/dashboard/dashboard.png"
TEMP_PATH="/tmp/dashboard_new.png"
LOG="/mnt/us/dashboard/refresh.log"

echo "$(date): Starting refresh" >> "$LOG"

# Download new image
wget -q -O "$TEMP_PATH" "$IMAGE_URL" 2>/dev/null

if [ $? -eq 0 ] && [ -s "$TEMP_PATH" ]; then
    mv "$TEMP_PATH" "$LOCAL_PATH"
    # Full e-ink refresh
    eips -c
    sleep 0.3
    eips -c
    sleep 0.3
    eips -f -g "$LOCAL_PATH"
    echo "$(date): Refresh OK ($(wc -c < "$LOCAL_PATH") bytes)" >> "$LOG"
else
    echo "$(date): Download failed" >> "$LOG"
    rm -f "$TEMP_PATH"
fi

# Keep log small
tail -50 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
