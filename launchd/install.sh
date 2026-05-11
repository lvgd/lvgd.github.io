#!/bin/bash
# Install / refresh the Scholar daily-update LaunchAgent.
set -e
DIR="$HOME/Library/LaunchAgents"
PLIST="com.lvgd.scholar.plist"
SRC="/Users/lvgd/Documents/lvgd.github.io/launchd/$PLIST"

mkdir -p "$DIR"
cp "$SRC" "$DIR/"
launchctl unload "$DIR/$PLIST" 2>/dev/null || true
launchctl load "$DIR/$PLIST"

echo "Installed $PLIST."
echo "Schedule: 03:17 and 15:17 local time daily."
echo "Manual fire:  launchctl start com.lvgd.scholar"
echo "Status:       launchctl list | grep com.lvgd.scholar"
echo "Tail log:     tail -f /Users/lvgd/Documents/lvgd.github.io/logs/scholar.log"
