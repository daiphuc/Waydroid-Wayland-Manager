import os
import glob
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"
ICONS_DIR = Path.home() / ".local" / "share" / "waydroid" / "data" / "icons"


class AppManager:
    """Quản lý các ứng dụng Android cài đặt trong Waydroid."""

    @staticmethod
    def get_installed_apps() -> List[Dict[str, Any]]:
        """
        Lấy danh sách các ứng dụng Android đã cài.
        Đọc từ cả .desktop files trong ~/.local/share/applications và 'waydroid app list'.
        """
        apps: Dict[str, Dict[str, Any]] = {}

        # 1. Đọc từ desktop files của người dùng
        if APPLICATIONS_DIR.exists():
            for df in APPLICATIONS_DIR.glob("waydroid.*.desktop"):
                pkg_name = df.stem.replace("waydroid.", "", 1)
                app_name = pkg_name
                icon_path = ""
                try:
                    with open(df, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("Name=") and app_name == pkg_name:
                                app_name = line.strip().split("=", 1)[1]
                            elif line.startswith("Icon="):
                                icon_path = line.strip().split("=", 1)[1]
                except Exception:
                    pass

                # Nếu icon_path chưa có hoặc là đường dẫn tương đối, thử tìm trong ICONS_DIR
                if not icon_path or not os.path.exists(icon_path):
                    custom_icon = ICONS_DIR / f"{pkg_name}.png"
                    if custom_icon.exists():
                        icon_path = str(custom_icon)

                apps[pkg_name] = {
                    "name": app_name,
                    "package": pkg_name,
                    "icon": icon_path,
                    "desktop_file": str(df)
                }

        # 2. Thử truy vấn thêm từ 'waydroid app list' nếu container/session đang chạy
        try:
            res = subprocess.run(
                ["waydroid", "app", "list"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if res.returncode == 0:
                current_app: Dict[str, Any] = {}
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("Name:"):
                        current_app = {"name": line.split(":", 1)[1].strip()}
                    elif line.startswith("packageName:") and current_app:
                        pkg = line.split(":", 1)[1].strip()
                        current_app["package"] = pkg
                        if pkg not in apps:
                            icon_p = ICONS_DIR / f"{pkg}.png"
                            current_app["icon"] = str(icon_p) if icon_p.exists() else ""
                            current_app["desktop_file"] = ""
                            apps[pkg] = current_app
                        else:
                            # Cập nhật tên nếu desktop file chỉ có package name
                            if apps[pkg]["name"] == pkg:
                                apps[pkg]["name"] = current_app["name"]
                        current_app = {}
        except Exception:
            pass

        # Đảm bảo app Cài đặt (Settings) luôn có mặt trong danh sách nếu chưa có
        if "com.android.settings" not in apps:
            icon_settings = ICONS_DIR / "com.android.settings.png"
            apps["com.android.settings"] = {
                "name": "Cài đặt Android (Settings)",
                "package": "com.android.settings",
                "icon": str(icon_settings) if icon_settings.exists() else "",
                "desktop_file": ""
            }

        return sorted(list(apps.values()), key=lambda x: x["name"].lower())

    @staticmethod
    def launch_app(package_name: str) -> bool:
        """Khởi chạy 1 app Android."""
        try:
            subprocess.Popen(
                ["waydroid", "app", "launch", package_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception as e:
            print(f"Lỗi khi khởi chạy app {package_name}: {e}")
            return False

    @staticmethod
    def install_apk(apk_path: str) -> Tuple_result:
        """Cài đặt file APK vào Waydroid."""
        if not os.path.exists(apk_path):
            return False, "Tệp APK không tồn tại"
        try:
            res = subprocess.run(
                ["waydroid", "app", "install", apk_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if res.returncode == 0:
                return True, "Cài đặt APK thành công!"
            return False, res.stderr.strip() or res.stdout.strip()
        except Exception as e:
            return False, str(e)

    @staticmethod
    def uninstall_app(package_name: str) -> Tuple_result:
        """Gỡ cài đặt app khỏi Waydroid."""
        try:
            res = subprocess.run(
                ["waydroid", "app", "remove", package_name],
                capture_output=True,
                text=True,
                timeout=15
            )
            if res.returncode == 0:
                return True, f"Đã gỡ cài đặt {package_name}"
            return False, res.stderr.strip() or res.stdout.strip()
        except Exception as e:
            return False, str(e)

    @staticmethod
    def open_android_settings() -> bool:
        """Mở cài đặt hệ thống Android."""
        try:
            subprocess.Popen(
                ["waydroid", "app", "intent", "android.settings.SETTINGS"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception:
            return False


Tuple_result = tuple[bool, str]
