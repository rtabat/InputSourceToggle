#!/bin/bash
# Setup script for InputSourceToggle

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.inputsourcetoggle.plist"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "==================================="
echo "  Input Source Toggle Setup"
echo "==================================="
echo ""
echo "App directory: $APP_DIR"
echo ""

# Create LaunchAgents directory if needed
mkdir -p "$LAUNCH_AGENTS_DIR"

# Create the LaunchAgent plist
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.inputsourcetoggle</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$APP_DIR/input_source_toggle.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/tmp/inputsourcetoggle.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/inputsourcetoggle.out</string>
</dict>
</plist>
EOF

echo "LaunchAgent created at: $PLIST_PATH"
echo ""

# Load the agent
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "==================================="
echo "  Setup Complete!"
echo "==================================="
echo ""
echo "The app is now running and will start automatically on login."
echo ""
echo "IMPORTANT: You need to grant Accessibility permissions!"
echo "  1. Go to System Preferences > Privacy & Security > Accessibility"
echo "  2. Click the + button"
echo "  3. Add 'Terminal' or 'python3' to the list"
echo "  4. Make sure it's checked/enabled"
echo ""
echo "Commands:"
echo "  To stop:   launchctl unload $PLIST_PATH"
echo "  To start:  launchctl load $PLIST_PATH"
echo "  To uninstall: rm $PLIST_PATH"
echo ""
echo "You should see a keyboard icon in your menu bar."
echo "Press Ctrl+Left Shift to toggle input sources!"
