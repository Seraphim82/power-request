#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SVG_FILE="$ROOT_DIR/assets/logo-power-request.svg"
ICONSET_DIR="$ROOT_DIR/assets/AppIcon.iconset"
ICNS_FILE="$ROOT_DIR/assets/AppIcon.icns"
TMP_PNG="$ROOT_DIR/assets/logo-1024.png"

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

if command -v qlmanage >/dev/null 2>&1; then
  qlmanage -t -s 1024 -o "$ROOT_DIR/assets" "$SVG_FILE" >/dev/null 2>&1 || true
  if [ -f "$ROOT_DIR/assets/logo-power-request.svg.png" ]; then
    mv "$ROOT_DIR/assets/logo-power-request.svg.png" "$TMP_PNG"
  fi
fi

if [ ! -f "$TMP_PNG" ] && command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 1024 -h 1024 "$SVG_FILE" -o "$TMP_PNG"
fi

if [ -f "$TMP_PNG" ] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  for sz in 16 32 128 256 512; do
    sips -z $sz $sz "$TMP_PNG" --out "$ICONSET_DIR/icon_${sz}x${sz}.png" >/dev/null 2>&1
    d=$((sz * 2))
    sips -z $d $d "$TMP_PNG" --out "$ICONSET_DIR/icon_${sz}x${sz}@2x.png" >/dev/null 2>&1
  done
  iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE"
  rm -rf "$ICONSET_DIR" "$TMP_PNG"
  echo "Ícone AppIcon.icns gerado com sucesso."
else
  echo "SVG do logo salvo em assets/logo-power-request.svg (conversor PNG/ICNS não encontrado)."
fi
