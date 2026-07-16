#!/bin/bash
# ==============================================================================
# 📱 Create InsightPulse Desktop App
# ==============================================================================
# This script creates a clickable macOS app for InsightPulse on your Desktop
# ==============================================================================

echo "📱 Creating InsightPulse Desktop App..."
echo ""

# Create the app structure
APP_PATH="$HOME/Desktop/InsightPulse.app"
CONTENTS_PATH="$APP_PATH/Contents"
MACOS_PATH="$CONTENTS_PATH/MacOS"
RESOURCES_PATH="$CONTENTS_PATH/Resources"

# Remove old app if exists
if [ -d "$APP_PATH" ]; then
    echo "🗑️  Removing old app..."
    rm -rf "$APP_PATH"
fi

# Create directories
mkdir -p "$MACOS_PATH"
mkdir -p "$RESOURCES_PATH"

# Create the executable script
cat > "$MACOS_PATH/InsightPulse" << 'EOF'
#!/bin/bash
cd /Users/rmtariq/Documents/InsightPulse

# Open Terminal and run the start script
osascript -e 'tell application "Terminal"
    do script "cd /Users/rmtariq/Documents/InsightPulse && ./start_insightpulse.sh"
    activate
end tell'
EOF

# Make it executable
chmod +x "$MACOS_PATH/InsightPulse"

# Create Info.plist
cat > "$CONTENTS_PATH/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>InsightPulse</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.maraliner.insightpulse</string>
    <key>CFBundleName</key>
    <string>InsightPulse</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create a simple icon (optional - you can replace with custom icon later)
# For now, we'll use the default Terminal icon

echo "✅ App created successfully!"
echo ""
echo "================================================"
echo "📱 InsightPulse.app is now on your Desktop!"
echo "================================================"
echo ""
echo "📍 Location: $HOME/Desktop/InsightPulse.app"
echo ""
echo "To use:"
echo "1. Double-click 'InsightPulse.app' on your Desktop"
echo "2. Terminal will open and start the server"
echo "3. Your browser will open to the dashboard"
echo ""
echo "✅ Done!"
