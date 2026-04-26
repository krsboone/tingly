#!/bin/bash
# Installs Tingly as a macOS login service.
# Run once after setup. Re-run to apply config changes.
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCHD="$HOME/Library/LaunchAgents"

if [ ! -f "$REPO/.env" ]; then
    echo ".env not found — copy .env.example to .env and fill in values"
    exit 1
fi

# Create venv and install dependencies
if [ ! -d "$REPO/.venv" ]; then
    python3 -m venv "$REPO/.venv"
fi
"$REPO/.venv/bin/pip" install -q -r "$REPO/requirements.txt"

mkdir -p "$LAUNCHD"

# Tingly plist
cat > "$LAUNCHD/com.kris.tingly.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kris.tingly</string>
    <key>ProgramArguments</key>
    <array>
        <string>$REPO/.venv/bin/python3</string>
        <string>$REPO/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$REPO</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/tingly.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/tingly.log</string>
</dict>
</plist>
EOF

launchctl unload "$LAUNCHD/com.kris.tingly.plist" 2>/dev/null || true
launchctl load "$LAUNCHD/com.kris.tingly.plist"

echo ""
echo "Done. Tingly is running."
echo ""
echo "Check status:  curl -s http://localhost:7654/health"
echo "Tingly logs:   tail -f /tmp/tingly.log"
