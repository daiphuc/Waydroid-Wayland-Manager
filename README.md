# Waydroid KDE Manager 🚀

Công cụ quản lý toàn diện **Waydroid** dành riêng cho môi trường **KDE Plasma (Wayland)**.

Tối ưu hóa trải nghiệm Android trên KDE với khả năng **tắt/mở phiên, dọn dẹp triệt để session bị treo, tùy biến kích thước độ phân giải (Presets)** và **tích hợp sâu với KWin Window Rules**.

---

## 🌟 Tính Năng Nổi Bật

### 1. 🕹️ Quản Lý Phiên & Điều Khiển Toàn Diện (Session Control)
- **Tắt / Mở nhẹ nhàng**: Khởi chạy phiên Waydroid ở chế độ **Multi-window** (từng app thành cửa sổ riêng) hoặc **Single Full UI** (nguyên khối Android).
- **Dọn dẹp Session (Clean Session)**:
  - Tự động diệt các tiến trình zombie, giải phóng lockfile và socket treo trong `/run/user/UID` và `/tmp`.
  - Khắc phục triệt để lỗi kinh điển `Session is already running` hoặc màn hình đen không thể mở lại Waydroid.
- **Dọn dẹp sâu (Deep Clean - Root)**: Tùy chọn dừng và khởi động lại dịch vụ `waydroid-container.service` ở cấp hệ thống.
- **Dừng Container (Giải phóng RAM)**: Một chạm để tắt hoàn toàn dịch vụ container chạy ngầm, trả lại 1–2 GB RAM cho KDE Plasma.
- **Giám sát thời gian thực**: Trạng thái phiên (RUNNING/STOPPED), trạng thái dịch vụ container, địa chỉ IP mạng bridge `waydroid0`, và danh sách các tiến trình chạy ngầm.

### 2. 🪟 Tùy Biến Cửa Sổ & Màn Hình (Window Customization & KWin Rules)
- **Cấu hình sẵn kích thước chuẩn (Resolution Presets)**:
  - 📱 **Điện thoại Nhỏ gọn**: `540 × 960` (DPI: 200) – Phù hợp để góc màn hình xem thông báo.
  - 📱 **Điện thoại Chuẩn HD**: `720 × 1280` (DPI: 260) – Tối ưu cho Zalo, TikTok, Facebook, Messenger.
  - 📱 **Điện thoại Full HD**: `1080 × 1920` (DPI: 380) – Độ nét cao, hiển thị nhiều nội dung.
  - 📱 **Điện thoại Màn hình dài 20:9**: `720 × 1600` (DPI: 280) – Tỉ lệ smartphone hiện đại.
  - 💻 **Máy tính bảng Nhỏ**: `1280 × 800` (DPI: 200).
  - 💻 **Máy tính bảng Full HD 16:9**: `1920 × 1080` (DPI: 240).
  - 💻 **Máy tính bảng 2K**: `2560 × 1440` (DPI: 280).
  - 🖥️ **Tự động theo màn hình máy tính (Auto / Native Desktop)**.
  - ⚙️ **Tùy chỉnh tự do (Custom)**: Chiều rộng, chiều cao, mật độ điểm ảnh DPI theo ý muốn.
  - 🔄 **Nút đảo chiều nhanh (Portrait ↔ Landscape)** xoay 90° tức thì.
- **Tích hợp sâu KWin Window Rules (KDE Plasma 5 & 6)**:
  - 📌 **Luôn nổi trên cùng (Keep Above / Always on Top)**: Giữ app Android luôn hiển thị trên các cửa sổ khác khi làm việc.
  - 🔲 **Bỏ viền & thanh tiêu đề (Borderless / No Titlebar)**: Giao diện tràn viền như smartphone thực tế.
  - 📏 **Cố định kích thước cửa sổ (Fixed Size)**: Ngăn không cho kéo giãn làm méo tỉ lệ khung hình Android.
  - 🧠 **Ghi nhớ vị trí (Remember Position)**: Mở lại đúng vị trí người dùng đã đặt.
  - 🌐 **Ghim trên tất cả Desktop ảo (Pin to all Virtual Desktops)**.
  - 🎨 **Độ mờ / Trong suốt (Opacity)**: Tùy chỉnh độ mờ khi Active và Inactive.
  - ⚡ **Nạp KWin tức thì**: Đồng bộ trực tiếp qua DBus (`org.kde.KWin reconfigure`), có tác dụng ngay lập tức mà không cần khởi động lại máy hay logout.

### 3. 📱 Quản Lý Ứng Dụng Android (App Manager)
- Xem danh sách toàn bộ ứng dụng Android đã cài đặt kèm icon chính chủ.
- Tìm kiếm nhanh ứng dụng theo tên hoặc package name.
- Khởi chạy app với 1 click hoặc click đúp.
- 📦 **Cài đặt file APK trực tiếp**: Hộp thoại chọn file `.apk` và cài ngầm không đơ máy.
- ⚙️ Mở nhanh Cài đặt hệ thống Android (Android Settings).
- 🗑️ Gỡ cài đặt ứng dụng Android dễ dàng.

### 4. 📋 Nhật Ký & Công Cụ Chẩn Đoán (Logs & Diagnostics)
- Xem nhật ký trực tiếp từ `/var/lib/waydroid/waydroid.log` với chế độ tự động cuộn.
- Mở **Android Shell** trực tiếp trong Konsole (`waydroid shell`).
- Mở luồng **Logcat** trực tiếp trong Konsole (`waydroid logcat`).
- Mở thư mục dữ liệu Waydroid trong Dolphin file manager.

### 5. 🛡️ Khay Hệ Thống & Desktop Actions (KDE Integration)
- **System Tray Icon**:
  - Đổi màu/tooltip theo trạng thái hoạt động của Waydroid.
  - Menu chuột phải thao tác nhanh: Bật/Tắt, Mở Full UI, Dọn dẹp session, Mở Settings, Thoát.
  - Click vào icon khay để ẩn / hiện cửa sổ quản lý.
- **Desktop Entry với Quick Actions**:
  - Tích hợp vào KDE Application Launcher (Kickoff) và KRunner.
  - Chuột phải vào biểu tượng trên Taskbar KDE để kích hoạt nhanh các hành động (Multi-Window, Full UI, Stop, Clean).

---

## 📥 Hướng Dẫn Cài Đặt

### 1. Yêu cầu hệ thống
- Hệ điều hành Linux (Kubuntu, Ubuntu, Arch, Fedora, openSUSE...) đang chạy phiên **KDE Plasma trên Wayland**.
- Python 3 và PyQt6:
  ```bash
  sudo apt install python3-pyqt6
  # Hoặc trên Arch: sudo pacman -S python-pyqt6
  # Hoặc trên Fedora: sudo dnf install python3-pyqt6
  ```
- Waydroid đã được cài đặt và khởi tạo (`waydroid init`).

### 2. Cài đặt tự động vào KDE
Chạy file cài đặt có sẵn trong thư mục dự án:
```bash
./install.sh
```
Script sẽ tự động:
1. Đăng ký lệnh `waydroid-kde` vào `~/.local/bin/`.
2. Cài đặt icon và file `.desktop` vào menu ứng dụng KDE Plasma.
3. Kích hoạt tính năng tìm kiếm qua KRunner (`Alt + Space` -> gõ `Waydroid`).

*(Để gỡ cài đặt, bạn chỉ cần chạy `./uninstall.sh`)*.

---

## 🚀 Hướng Dẫn Sử Dụng

### A. Sử dụng Giao diện Đồ họa (GUI)
- Mở từ Menu ứng dụng KDE: Tìm **Waydroid KDE Manager**.
- Hoặc gõ lệnh trong terminal:
  ```bash
  waydroid-kde
  ```

### B. Sử dụng Giao diện Dòng lệnh (CLI) & Phím Tắt KDE
Bạn có thể dùng lệnh CLI hoặc gán phím tắt tùy chỉnh trong **KDE System Settings -> Shortcuts**:

| Thao tác | Lệnh Terminal | Gợi ý phím tắt |
| :--- | :--- | :--- |
| **Xem trạng thái chi tiết** | `waydroid-kde status` | |
| **Khởi động Multi-Window** | `waydroid-kde start --mode multi_windows` | `Meta + Alt + W` |
| **Khởi động Full UI** | `waydroid-kde start --mode full_ui` | |
| **Tắt phiên Waydroid** | `waydroid-kde stop` | `Meta + Alt + Q` |
| **Tắt cả Container (giải phóng RAM)** | `waydroid-kde stop --all` | |
| **Dọn dẹp session treo** | `waydroid-kde clean` | `Meta + Alt + C` |
| **Dọn dẹp sâu cấp root** | `waydroid-kde clean --deep` | |
| **Chuyển preset Điện thoại HD** | `waydroid-kde preset phone_hd` | |
| **Chuyển preset Tablet Full HD** | `waydroid-kde preset tablet_fhd` | |
| **Áp dụng KWin Rules** | `waydroid-kde apply-rules` | |
| **Gỡ bỏ KWin Rules** | `waydroid-kde remove-rules` | |
| **Xem danh sách app Android** | `waydroid-kde app list` | |
| **Cài đặt file APK** | `waydroid-kde app install <duong_dan.apk>` | |

---

## 🛠️ Cấu Trúc Mã Nguồn

```
Waydroid-Wayland/
├── waydroid_kde/
│   ├── core/
│   │   ├── waydroid_service.py   # Điều khiển Waydroid session, container, process & deep cleanup
│   │   ├── kwin_rules.py         # Quản lý KWin rules (~/.config/kwinrulesrc & DBus reload)
│   │   ├── config_manager.py     # Quản lý cấu hình & Presets độ phân giải
│   │   └── app_manager.py        # Quét app, cài đặt APK, mở ứng dụng
│   ├── ui/
│   │   ├── main_window.py        # Cửa sổ chính PyQt6
│   │   ├── session_tab.py        # Tab Điều khiển phiên & Dọn dẹp
│   │   ├── window_tab.py         # Tab Tùy biến cửa sổ & KWin Rules
│   │   ├── apps_tab.py           # Tab Quản lý ứng dụng Android & APK
│   │   ├── logs_tab.py           # Tab Xem Log & Chẩn đoán hệ thống
│   │   └── tray_icon.py          # System Tray Icon cho KDE Plasma
│   ├── assets/
│   │   ├── waydroid-kde.svg      # Icon ứng dụng định dạng SVG
│   │   └── waydroid-kde.png      # Icon ứng dụng định dạng PNG
│   ├── cli.py                    # Giao diện dòng lệnh CLI đầy đủ
│   ├── __init__.py
│   └── __main__.py
├── waydroid-kde                  # File thực thi chính
├── waydroid-kde.desktop          # Tệp tích hợp Desktop Menu KDE
├── install.sh                    # Script cài đặt tự động
├── uninstall.sh                  # Script gỡ cài đặt
└── README.md                     # Tài liệu hướng dẫn sử dụng
```

---

## 💡 Mẹo & Khắc Phục Sự Cố Thường Gặp

1. **Waydroid báo lỗi "Session is already running" nhưng không hiện cửa sổ:**
   - Nhấn nút **"🧹 Dọn dẹp Session (Clean)"** trong ứng dụng hoặc chạy `waydroid-kde clean`. Lệnh này sẽ diệt toàn bộ process treo và socket tồn đọng.
2. **Cửa sổ Android bị kéo dãn méo hình:**
   - Vào tab **Tùy Biến Cửa Sổ**, chọn preset mong muốn (ví dụ: Điện thoại HD 720x1280), tích chọn **"Cố định kích thước cửa sổ"**, sau đó nhấn **"Lưu tất cả Cấu hình"**.
3. **Muốn app Android luôn nổi trên màn hình khi làm việc:**
   - Vào tab **Tùy Biến Cửa Sổ**, bật **"Luôn nổi trên cùng (Always on Top)"** và nhấn **"Áp dụng KWin Rules ngay"**.
4. **Giải phóng RAM khi không dùng Waydroid:**
   - Nhấn **"Dừng hoàn toàn Container (Giải phóng RAM)"** hoặc chạy `waydroid-kde stop --all`.
