# Tingly

Lightweight self-hosted push notification bus. Any local project POSTs to Tingly's HTTP API; Tingly routes to ntfy.sh; your phone gets a push notification anywhere.

## Architecture

```
caller → POST /notify → Tingly :7654 → ntfy.sh → phone
```

- **Tingly** — auth layer and topic router (~70 lines of Flask), runs on your Mac Mini
- **ntfy.sh** — open-source push notification relay (free, no account required)

Topics are prefixed with a unique string (`NTFY_TOPIC_PREFIX`) to prevent collisions with other ntfy.sh users.

## Topics

| Topic | Purpose |
|---|---|
| `threshold` | Motion detection, doorbell press |
| `trading` | Trade fills, Kalshi/Bitunix alerts |
| `system` | Catch-all, service events |

## Setup

### 1. Configure Tingly

```bash
cp .env.example .env
```

Edit `.env`:
- `TINGLY_TOKEN` — generate a random string: `openssl rand -hex 20`
- `NTFY_TOPIC_PREFIX` — pick something unique and hard to guess (e.g. `openssl rand -hex 8`)
- `NTFY_URL` — leave as `https://ntfy.sh`
- `PORT` — leave as `7654`

### 2. Install as a login service

```bash
chmod +x launchd/install.sh
./launchd/install.sh
```

This creates a Python venv, installs dependencies, generates a LaunchAgent plist, and starts Tingly. It will restart automatically on login.

Verify:
```bash
curl -s http://localhost:7654/health
# → {"ok": true}
```

### 3. Set up the ntfy iOS app

1. Install ntfy from the App Store
2. Leave the default server (`https://ntfy.sh`)
3. Subscribe to each prefixed topic — replace `<prefix>` with your `NTFY_TOPIC_PREFIX`:
   - `<prefix>-threshold`
   - `<prefix>-trading`
   - `<prefix>-system`

## API

```
POST /notify
Authorization: Bearer <TINGLY_TOKEN>
Content-Type: application/json

{
  "title":    "Doorbell pressed",
  "body":     "Front door — 7:42 PM",
  "topic":    "threshold",
  "priority": "urgent",
  "tags":     ["bell"],
  "source":   "threshold"
}
```

| Field | Required | Values |
|---|---|---|
| `title` | yes | any string |
| `body` | yes | any string |
| `topic` | yes | `threshold`, `trading`, `system` |
| `priority` | no | `urgent`, `high`, `default` (default), `low` |
| `tags` | no | list of ntfy emoji shortcodes |
| `source` | no | logged but not forwarded — identify the caller |

Priority → iOS behavior:
- `urgent` — bypasses Do Not Disturb (doorbell press)
- `high` — loud alert (after-hours motion)
- `default` — normal notification
- `low` — silent

## Caller snippet

Drop this into any project that should send notifications:

```python
import requests

def tingly(title, body, topic, priority="default", tags=[], source=""):
    try:
        requests.post(
            "http://localhost:7654/notify",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={"title": title, "body": body, "topic": topic,
                  "priority": priority, "tags": tags, "source": source},
            timeout=3,
        )
    except requests.RequestException:
        pass  # notifications are best-effort — never block the caller
```

## Logs

```bash
tail -f /tmp/tingly.log
```

## Stopping / restarting

```bash
launchctl unload ~/Library/LaunchAgents/com.kris.tingly.plist
launchctl load   ~/Library/LaunchAgents/com.kris.tingly.plist
```
