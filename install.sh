#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR_128="$HOME/.local/share/icons/hicolor/128x128/apps"
ICON_DIR_SCALABLE="$HOME/.local/share/icons/hicolor/scalable/apps"

echo -e "\033[1;36m=== CÀI ĐẶT WAYDROID KDE MANAGER ===\033[0m"

# 1. Kiểm tra Python và PyQt6
if ! command -v python3 &>/dev/null; then
    echo -e "\033[1;31m✗ Lỗi: Python 3 chưa được cài đặt!\033[0m"
    exit 1
fi

if ! python3 -c "import PyQt6" &>/dev/null; then
    echo -e "\033[1;33m⚠ Cảnh báo: PyQt6 chưa có sẵn trong Python. Đang kiểm tra cài đặt...\033[0m"
    echo -e "Bạn có thể cài đặt bằng lệnh: \033[1m sudo apt install python3-pyqt6\033[0m"
fi

# 2. Tạo symlink trong ~/.local/bin
mkdir -p "$BIN_DIR"
chmod +x "$PROJECT_DIR/waydroid-kde"
ln -sf "$PROJECT_DIR/waydroid-kde" "$BIN_DIR/waydroid-kde"
echo -e "\033[1;32m✓ Đã tạo lệnh thực thi:\033[0m $BIN_DIR/waydroid-kde"

# 3. Cài đặt Icon
mkdir -p "$ICON_DIR_128" "$ICON_DIR_SCALABLE"
if [ -f "$PROJECT_DIR/waydroid_kde/assets/waydroid-kde.png" ]; then
    cp "$PROJECT_DIR/waydroid_kde/assets/waydroid-kde.png" "$ICON_DIR_128/waydroid-kde.png"
fi
if [ -f "$PROJECT_DIR/waydroid_kde/assets/waydroid-kde.svg" ]; then
    cp "$PROJECT_DIR/waydroid_kde/assets/waydroid-kde.svg" "$ICON_DIR_SCALABLE/waydroid-kde.svg"
fi
echo -e "\033[1;32m✓ Đã cài đặt Icon vào hệ thống KDE\033[0m"

# 4. Cài đặt .desktop entry
mkdir -p "$DESKTOP_DIR"
sed -e "s|/run/media/daiphuc/DATA/Projects/Waydroid-Wayland|$PROJECT_DIR|g" \
    "$PROJECT_DIR/waydroid-kde.desktop" > "$DESKTOP_DIR/waydroid-kde.desktop"
chmod +x "$DESKTOP_DIR/waydroid-kde.desktop"
echo -e "\033[1;32m✓ Đã thêm vào Application Menu KDE:\033[0m $DESKTOP_DIR/waydroid-kde.desktop"

# 5. Cập nhật cache ứng dụng
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" &>/dev/null || true
fi
if command -v kbuildsycoca6 &>/dev/null; then
    kbuildsycoca6 &>/dev/null || true
elif command -v kbuildsycoca5 &>/dev/null; then
    kbuildsycoca5 &>/dev/null || true
fi

echo -e "\n\033[1;32m🎉 CÀI ĐẶT THÀNH CÔNG!\033[0m"
echo -e "Bạn có thể khởi động công cụ bằng:"
echo -e "  1. Tìm \033[1m'Waydroid KDE Manager'\033[0m trong menu ứng dụng Kickoff hoặc KRunner (Alt + Space)."
echo -e "  2. Chạy lệnh: \033[1mwaydroid-kde\033[0m (hoặc \033[1m$PROJECT_DIR/waydroid-kde\033[0m)"
echo -e "  3. Các lệnh nhanh CLI:"
echo -e "     • \033[1mwaydroid-kde status\033[0m     (Kiểm tra trạng thái)"
echo -e "     • \033[1mwaydroid-kde clean\033[0m      (Dọn dẹp session treo)"
echo -e "     • \033[1mwaydroid-kde preset phone_hd\033[0m (Chuyển nhanh màn hình điện thoại)"
echo -e "     • \033[1mwaydroid-kde apply-rules\033[0m (Nạp lại KWin rules)"
