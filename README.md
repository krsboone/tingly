# Tingly

Lightweight self-hosted push notification bus. Any local project POSTs to Tingly's HTTP API; Tingly routes to an ntfy server; your phone gets a push notification.

## Architecture

```
caller → POST /notify → Tingly :7654 → ntfy :8080 → phone (via Tailscale)
```

- **Tingly** — auth layer and topic router (~70 lines of Flask)
- **ntfy** — open-source push notification server (binwiederhier/ntfy)
- **Tailscale** — encrypted mesh VPN so your phone reaches the Mac Mini from anywhere

## Topics

| Topic | Purpose |
|---|---|
| `threshold` | Motion detection, doorbell press |
| `trading` | Trade fills, Kalshi/Bitunix alerts |
| `system` | Catch-all, service events |

## Setup

### 1. Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the post-install instructions to add brew to your PATH (printed at the end of the installer).

### 2. Install ntfy server

```bash
brew install ntfy
```

### 3. Install Tailscale

Download the Tailscale macOS app from https://tailscale.com/download and sign in.
Install Tailscale on your iPhone from the App Store and sign in to the same account.
Both devices now share a private network — find the Mac Mini's Tailscale IP in the Tailscale menu bar app (e.g. `100.x.x.x`) or use its MagicDNS hostname (e.g. `mac-mini.ts.net`).

### 4. Configure Tingly

```bash
cp .env.example .env
```

Edit `.env`:
- `TINGLY_TOKEN` — generate a random string: `openssl rand -hex 20`
- `NTFY_URL` — leave as `http://localhost:8080`
- `PORT` — leave as `7654`

### 5. Install services

```bash
chmod +x launchd/install.sh
./launchd/install.sh
```

This creates a Python venv, installs dependencies, generates LaunchAgent plists with the correct paths, and starts both services. Both will restart automatically on login.

Verify:
```bash
curl -s http://localhost:7654/health
# → {"ok": true}
```

### 6. Set up the ntfy iOS app

1. Open the ntfy app → Settings → Default server → enter `http://<tailscale-ip>:8080`
2. Subscribe to each topic: `threshold`, `trading`, `system`

You'll now receive notifications on your phone from anywhere, routed through your Tailscale network.

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
tail -f /tmp/tingly.log   # Tingly request log
tail -f /tmp/ntfy.log     # ntfy server log
```

## Stopping / restarting

```bash
launchctl unload ~/Library/LaunchAgents/com.kris.tingly.plist
launchctl load   ~/Library/LaunchAgents/com.kris.tingly.plist
```
