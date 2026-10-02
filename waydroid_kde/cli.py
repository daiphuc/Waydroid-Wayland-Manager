import sys
import argparse
from typing import List, Optional

from .core.config_manager import ConfigManager, RESOLUTION_PRESETS
from .core.kwin_rules import KWinRulesManager
from .core.waydroid_service import WaydroidService
from .core.app_manager import AppManager


def print_colored(text: str, color: str = "white", bold: bool = False):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    b = "\033[1m" if bold else ""
    c = colors.get(color, "")
    print(f"{b}{c}{text}{colors['reset']}")


def cmd_status(args):
    status = WaydroidService.get_status()
    print_colored("=== TRẠNG THÁI WAYDROID TRÊN KDE ===", "cyan", bold=True)
    s_col = "green" if status["session_status"] == "RUNNING" else "yellow" if "STARTING" in status["session_status"] else "red"
    print_colored(f"• Trạng thái phiên (Session): {status['session_status']}", s_col, bold=True)
    c_col = "green" if status["container_active"] else "red"
    print_colored(f"• Dịch vụ Container:         {status['container_status']} ({'Chạy' if status['container_active'] else 'Dừng'})", c_col)
    print(f"• Địa chỉ IP mạng:          {status['ip_address'] or 'Chưa kết nối'}")
    print(f"• Tiến trình liên quan:     {status['process_count']} tiến trình")
    if status["width"] > 0 and status["height"] > 0:
        print(f"• Độ phân giải hiện tại:    {status['width']} × {status['height']} (DPI: {status['dpi']})")
    print(f"• Chế độ cửa sổ:            {'Multi-window' if status['multi_windows'] else 'Single Full UI'}")

    km = KWinRulesManager()
    kwin_applied = km.is_rule_applied()
    print_colored(f"• Quy tắc KWin Plasma:      {'Đã áp dụng' if kwin_applied else 'Chưa áp dụng'}", "green" if kwin_applied else "white")


def cmd_start(args):
    cfg = ConfigManager()
    km = KWinRulesManager()

    mode = args.mode or cfg.get("display.mode", "multi_windows")
    w = args.width if args.width is not None else cfg.get("display.width", 0)
    h = args.height if args.height is not None else cfg.get("display.height", 0)
    dpi = args.dpi if args.dpi is not None else cfg.get("display.dpi", 0)

    # Tự động nạp rules nếu được bật
    if cfg.get("system.auto_apply_kwin_rules", True):
        km.apply_rules(cfg.get("kwin_rules", {}), width=w, height=h)

    print_colored(f"Đang khởi động Waydroid ({mode})...", "yellow")
    ok, msg = WaydroidService.start_session(mode=mode, width=w, height=h, dpi=dpi)
    if ok:
        print_colored(f"✓ {msg}", "green", bold=True)
    else:
        print_colored(f"✗ {msg}", "red", bold=True)
        sys.exit(1)


def cmd_stop(args):
    print_colored("Đang dừng Waydroid Session...", "yellow")
    ok, msg = WaydroidService.stop_session()
    if ok:
        print_colored(f"✓ {msg}", "green")
    else:
        print_colored(f"✗ {msg}", "red")

    if args.all:
        print_colored("Đang dừng Container service (giải phóng RAM)...", "yellow")
        ok_c, msg_c = WaydroidService.stop_container()
        if ok_c:
            print_colored(f"✓ {msg_c}", "green")
        else:
            print_colored(f"✗ {msg_c}", "red")


def cmd_clean(args):
    print_colored("🧹 Bắt đầu dọn dẹp Waydroid Session...", "yellow", bold=True)
    report = WaydroidService.cleanup_session(deep=args.deep)
    for m in report.get("messages", []):
        print(f"  • {m}")
    if report.get("success", True):
        print_colored("✓ Đã dọn dẹp session hoàn tất!", "green", bold=True)
    else:
        print_colored("✗ Có lỗi trong quá trình dọn dẹp.", "red", bold=True)


def cmd_restart(args):
    print_colored("Đang khởi động lại Waydroid...", "yellow")
    WaydroidService.stop_session()
    WaydroidService.cleanup_session(deep=False)
    cmd_start(args)


def cmd_preset(args):
    preset_name = args.name.lower()
    cfg = ConfigManager()
    if preset_name not in RESOLUTION_PRESETS:
        print_colored(f"✗ Không tìm thấy preset '{preset_name}'. Các preset khả dụng:", "red")
        for k, v in RESOLUTION_PRESETS.items():
            print(f"  • {k:15}: {v['name']}")
        sys.exit(1)

    cfg.apply_preset(preset_name)
    p = RESOLUTION_PRESETS[preset_name]
    print_colored(f"✓ Đã áp dụng preset '{preset_name}': {p['width']} × {p['height']} @ {p['dpi']} DPI", "green")

    # Nếu Waydroid đang chạy, đồng bộ luôn
    status = WaydroidService.get_status()
    if status["session_status"] == "RUNNING" and p["width"] > 0 and p["height"] > 0:
        WaydroidService.set_prop("persist.waydroid.width", str(p["width"]))
        WaydroidService.set_prop("persist.waydroid.height", str(p["height"]))
        if p["dpi"] > 0:
            WaydroidService.set_prop("persist.waydroid.dpi", str(p["dpi"]))
        print_colored("  (Đã đồng bộ sang phiên đang chạy. Hãy restart session nếu cần áp dụng kích thước mới.)", "yellow")


def cmd_apply_rules(args):
    cfg = ConfigManager()
    km = KWinRulesManager()

    opts = cfg.get("kwin_rules", {})
    if args.above is not None:
        opts["above"] = args.above
    if args.noborder is not None:
        opts["noborder"] = args.noborder
    if args.fixed_size is not None:
        opts["fixed_size"] = args.fixed_size

    w = cfg.get("display.width", 0)
    h = cfg.get("display.height", 0)

    ok = km.apply_rules(opts, width=w, height=h)
    if ok:
        print_colored("✓ Đã áp dụng KWin Rules vào ~/.config/kwinrulesrc và reload KWin!", "green")
    else:
        print_colored("✗ Lỗi khi áp dụng KWin Rules.", "red")


def cmd_remove_rules(args):
    km = KWinRulesManager()
    ok = km.remove_rules()
    if ok:
        print_colored("✓ Đã gỡ bỏ KWin Rules của Waydroid khỏi KDE Plasma.", "green")
    else:
        print_colored("✗ Lỗi khi gỡ KWin Rules.", "red")


def cmd_app(args):
    sub = args.app_action
    if sub == "list":
        apps = AppManager.get_installed_apps()
        print_colored(f"Danh sách ứng dụng Android ({len(apps)} apps):", "cyan", bold=True)
        for a in apps:
            print(f"  • {a['name']:<30} [{a['package']}]")
    elif sub == "launch":
        if not args.package:
            print_colored("Lỗi: Cần cung cấp package name để mở (ví dụ: com.android.settings)", "red")
            sys.exit(1)
        ok = AppManager.launch_app(args.package)
        if ok:
            print_colored(f"✓ Đã gửi lệnh mở {args.package}", "green")
    elif sub == "install":
        if not args.apk:
            print_colored("Lỗi: Cần cung cấp đường dẫn file .apk", "red")
            sys.exit(1)
        print_colored(f"Đang cài đặt {args.apk}...", "yellow")
        ok, msg = AppManager.install_apk(args.apk)
        if ok:
            print_colored(f"✓ {msg}", "green")
        else:
            print_colored(f"✗ {msg}", "red")


def run_gui():
    import traceback
    from PyQt6 import QtWidgets
    from .ui.main_window import MainWindow

    # Ngăn PyQt6 gọi qFatal() gây coredump khi có ngoại lệ Python
    def qt_excepthook(exc_type, exc_value, exc_traceback):
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = qt_excepthook

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Waydroid KDE Manager")
    app.setOrganizationName("WaydroidKDE")

    cfg = ConfigManager()
    km = KWinRulesManager()
    win = MainWindow(cfg, km)
    win.show()
    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(
        prog="waydroid-kde",
        description="Công cụ quản lý Waydroid, phiên làm việc và tùy biến cửa sổ trên KDE Plasma."
    )
    subparsers = parser.add_subparsers(dest="command")

    # GUI
    subparsers.add_parser("gui", help="Mở giao diện đồ họa (mặc định nếu không truyền tham số)")

    # Status
    subparsers.add_parser("status", help="Xem trạng thái phiên, container và KWin")

    # Start
    p_start = subparsers.add_parser("start", help="Khởi động Waydroid")
    p_start.add_argument("--mode", choices=["multi_windows", "full_ui"], help="Chế độ cửa sổ")
    p_start.add_argument("--width", type=int, help="Chiều rộng (px)")
    p_start.add_argument("--height", type=int, help="Chiều cao (px)")
    p_start.add_argument("--dpi", type=int, help="Mật độ điểm ảnh DPI")

    # Stop
    p_stop = subparsers.add_parser("stop", help="Tắt Waydroid session")
    p_stop.add_argument("--all", action="store_true", help="Dừng cả Container để giải phóng RAM hoàn toàn")

    # Restart
    p_restart = subparsers.add_parser("restart", help="Dọn dẹp và khởi động lại phiên")
    p_restart.add_argument("--mode", choices=["multi_windows", "full_ui"])
    p_restart.add_argument("--width", type=int)
    p_restart.add_argument("--height", type=int)
    p_restart.add_argument("--dpi", type=int)

    # Clean
    p_clean = subparsers.add_parser("clean", help="Dọn dẹp session, diệt zombie processes và dọn socket lock")
    p_clean.add_argument("--deep", action="store_true", help="Dọn dẹp sâu cấp root (restart container)")

    # Preset
    p_preset = subparsers.add_parser("preset", help="Áp dụng cấu hình kích thước màn hình sẵn")
    p_preset.add_argument("name", help="Tên preset (phone_hd, phone_fhd, phone_compact, tablet_fhd, auto...)")

    # KWin Rules
    p_rules = subparsers.add_parser("apply-rules", help="Áp dụng KWin Window Rules vào KDE")
    p_rules.add_argument("--above", type=lambda x: x.lower() == 'true', help="Nổi trên cùng (true/false)")
    p_rules.add_argument("--noborder", type=lambda x: x.lower() == 'true', help="Không viền (true/false)")
    p_rules.add_argument("--fixed-size", type=lambda x: x.lower() == 'true', help="Cố định kích thước (true/false)")

    subparsers.add_parser("remove-rules", help="Gỡ bỏ KWin Rules của Waydroid")

    # App
    p_app = subparsers.add_parser("app", help="Quản lý ứng dụng Android")
    p_app_sub = p_app.add_subparsers(dest="app_action")
    p_app_sub.add_parser("list", help="Liệt kê ứng dụng đã cài")
    p_launch = p_app_sub.add_parser("launch", help="Khởi chạy ứng dụng")
    p_launch.add_argument("package", help="Package name của app")
    p_inst = p_app_sub.add_parser("install", help="Cài file APK")
    p_inst.add_argument("apk", help="Đường dẫn tới file .apk")

    args = parser.parse_args()

    if not args.command or args.command == "gui":
        run_gui()
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "restart":
        cmd_restart(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "preset":
        cmd_preset(args)
    elif args.command == "apply-rules":
        cmd_apply_rules(args)
    elif args.command == "remove-rules":
        cmd_remove_rules(args)
    elif args.command == "app":
        cmd_app(args)
