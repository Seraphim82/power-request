#!/bin/zsh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$PROJECT_DIR/Power Request.app"

rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources"

cat << PLIST > "$APP_PATH/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Power Request</string>
    <key>CFBundleDisplayName</key>
    <string>Power Request</string>
    <key>CFBundleIdentifier</key>
    <string>br.com.seraphim.powerrequest</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
PLIST

cat << LAUNCHER > "$APP_PATH/Contents/MacOS/launcher"
#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:\$HOME/.local/bin:\$HOME/.npm-global/bin:\$PATH"
cd "$PROJECT_DIR/backend"
if lsof -i :8765 -sTCP:LISTEN >/dev/null 2>&1; then
    open "http://127.0.0.1:8765"
    exit 0
fi
exec "$PROJECT_DIR/backend/venv/bin/python" "$PROJECT_DIR/backend/desktop_app.py"
LAUNCHER

chmod +x "$APP_PATH/Contents/MacOS/launcher"
echo "Power Request.app criado com sucesso em: $APP_PATH"
