---
name: kindle-dashboard
description: Generate and push e-ink dashboard to Kindle PW3. Renders calendar, email, news into a 1072×1448 PNG.
homepage: https://github.com/chenkevin23/kindle-dashboard
metadata:
  {
    "openclaw":
      {
        "emoji": "📟",
        "requires": { "bins": ["python3", "playwright"] },
      },
  }
---

# kindle-dashboard

Generate and push an e-ink dashboard image to the Kindle PW3.

The dashboard pulls data from OpenClaw's calendar cache, gog CLI (Gmail), and RSS feeds,
then renders a terminal-style PNG via Playwright and pushes to Kindle over SCP.

## Project Location

`~/Documents/development/kindle-dashboard/`

## Commands

**Render only (save to output/):**
```bash
cd ~/Documents/development/kindle-dashboard && python -m src.main
```

**Render + push to Kindle:**
```bash
cd ~/Documents/development/kindle-dashboard && python -m src.main --push
```

**With custom AI message (from Luka):**
```bash
cd ~/Documents/development/kindle-dashboard && python -m src.main --push --message "Today's focus: Intuit escalation is top priority. Roadmap review at 10:30."
```

**With tasks (Luka can inject from Todoist/Notion):**
```bash
cd ~/Documents/development/kindle-dashboard && python -m src.main --push \
  --message "3 meetings today, prep CFA slides by noon." \
  --tasks-json '[{"title":"Finalize CFA roadmap draft","done":false},{"title":"Review Jira backlog","done":false},{"title":"Update Intuit escalation doc","done":true}]'
```

## When to Use

- User says "刷新 dashboard" / "refresh kindle" / "update dashboard"
- As part of a morning briefing routine (cron at 6:30 AM, 12:00 PM, 6:00 PM)
- When user asks "show my schedule on kindle"
- After significant calendar or email changes

## Tips

- The `--message` flag lets you inject your own AI-generated daily briefing
- Pull tasks from Todoist via `todoist` skill, format as JSON, pass to `--tasks-json`
- Calendar data comes from `~/.openclaw/cache/calendar-today.txt` (auto-updated every 5 min)
- Gmail comes from `gog gmail` (existing OAuth, no extra setup)
- Output PNG is at `~/Documents/development/kindle-dashboard/output/dashboard.png`
- Kindle must be on the same WiFi network for SCP push to work

## Cron Integration

Luka can set up a cron to auto-refresh:
```
openclaw cron create kindle-morning \
  --cron "30 6 * * *" \
  --prompt "Refresh the Kindle dashboard with today's briefing" \
  --session isolated
```
