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
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
PLIST

if [ -f "$PROJECT_DIR/assets/AppIcon.icns" ]; then
    cp "$PROJECT_DIR/assets/AppIcon.icns" "$APP_PATH/Contents/Resources/AppIcon.icns"
fi

cat << LAUNCHER > "$APP_PATH/Contents/MacOS/launcher"
#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:\$HOME/.local/bin:\$HOME/.npm-global/bin:\$PATH"
PROJECT_DIR="$PROJECT_DIR"
PYTHON_BIN="\$PROJECT_DIR/backend/venv/bin/python"

aviso() {
    osascript -e "display dialog \"\$1\" buttons {\"OK\"} default button \"OK\" with title \"Power Request\" with icon caution" >/dev/null 2>&1
}

if [ ! -x "\$PYTHON_BIN" ]; then
    aviso "Ambiente Python não encontrado. Abra o Terminal na pasta do projeto e rode: make setup"
    exit 1
fi
if [ ! -f "\$PROJECT_DIR/frontend/dist/index.html" ]; then
    aviso "Interface ainda não compilada. Abra o Terminal na pasta do projeto e rode: make build"
    exit 1
fi

cd "\$PROJECT_DIR/backend"
# Se o Power Request já estiver rodando, só abre a janela (confere o /api/health para não confundir com outro programa na porta)
if curl -fs --max-time 1 http://127.0.0.1:8765/api/health 2>/dev/null | grep -q '"status"'; then
    open "http://127.0.0.1:8765"
    exit 0
fi
exec "\$PYTHON_BIN" desktop_app.py
LAUNCHER

chmod +x "$APP_PATH/Contents/MacOS/launcher"
echo "Power Request.app criado com sucesso em: $APP_PATH"
