#!/usr/bin/env bash
set -e

BIN_FILE="$HOME/.local/bin/waydroid-kde"
DESKTOP_FILE="$HOME/.local/share/applications/waydroid-kde.desktop"
ICON_128="$HOME/.local/share/icons/hicolor/128x128/apps/waydroid-kde.png"
ICON_SVG="$HOME/.local/share/icons/hicolor/scalable/apps/waydroid-kde.svg"

echo -e "\033[1;33mĐang gỡ cài đặt Waydroid KDE Manager...\033[0m"

rm -f "$BIN_FILE"
rm -f "$DESKTOP_FILE"
rm -f "$ICON_128"
rm -f "$ICON_SVG"

# Gỡ rules khỏi kwinrulesrc
if [ -f "$HOME/.local/bin/waydroid-kde" ]; then
    waydroid-kde remove-rules 2>/dev/null || true
fi

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" &>/dev/null || true
fi

echo -e "\033[1;32m✓ Đã gỡ bỏ thành công khỏi hệ thống.\033[0m"
