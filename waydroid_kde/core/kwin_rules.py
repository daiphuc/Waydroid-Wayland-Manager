import os
import shutil
import subprocess
import configparser
from pathlib import Path
from typing import Dict, Any, Optional

def _get_default_kwin_rules_file() -> Path:
    xdg = os.getenv("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    target_file = base / "kwinrulesrc"
    try:
        base.mkdir(parents=True, exist_ok=True)
        return target_file
    except (OSError, PermissionError):
        local_dir = Path(__file__).resolve().parent.parent.parent / ".config"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir / "kwinrulesrc"

KWIN_RULES_FILE = _get_default_kwin_rules_file()
WAYDROID_RULE_ID = "waydroid_kde_manager_rule"
WAYDROID_RULE_DESC = "Waydroid Window (Waydroid KDE Manager)"


class KWinRulesManager:
    """Quản lý các quy tắc cửa sổ KWin (KWin Rules) cho Waydroid trên KDE Plasma 5/6."""

    def __init__(self, rules_file: Path = KWIN_RULES_FILE):
        self.rules_file = rules_file

    def _read_config(self) -> configparser.RawConfigParser:
        config = configparser.RawConfigParser()
        config.optionxform = str  # Giữ nguyên chữ hoa/thường của key trong KDE INI
        if self.rules_file.exists():
            try:
                config.read(self.rules_file, encoding="utf-8")
            except Exception as e:
                print(f"Cảnh báo: Không thể đọc {self.rules_file}: {e}")
        return config

    def _write_config(self, config: configparser.RawConfigParser) -> bool:
        try:
            self.rules_file.parent.mkdir(parents=True, exist_ok=True)
            # Tạo backup nhẹ trước khi ghi
            if self.rules_file.exists():
                backup_file = self.rules_file.with_suffix(".bak")
                try:
                    shutil.copy2(self.rules_file, backup_file)
                except Exception:
                    pass

            with open(self.rules_file, "w", encoding="utf-8") as f:
                config.write(f, space_around_delimiters=False)
            return True
        except (OSError, PermissionError) as e:
            # Nếu ~/.config bị read-only (ví dụ trong môi trường sandbox), thử ghi vào thư mục dự phòng
            try:
                fallback_file = Path(__file__).resolve().parent.parent.parent / ".config" / "kwinrulesrc"
                fallback_file.parent.mkdir(parents=True, exist_ok=True)
                with open(fallback_file, "w", encoding="utf-8") as f:
                    config.write(f, space_around_delimiters=False)
                return True
            except Exception:
                print(f"Lỗi khi ghi kwinrulesrc: {e}")
                return False
        except Exception as e:
            print(f"Lỗi khi ghi kwinrulesrc: {e}")
            return False

    def is_rule_applied(self) -> bool:
        if not self.rules_file.exists():
            return False
        config = self._read_config()
        if not config.has_section("General"):
            return False
        rules_list = [r.strip() for r in config.get("General", "rules", fallback="").split(",") if r.strip()]
        return WAYDROID_RULE_ID in rules_list and config.has_section(WAYDROID_RULE_ID)

    def apply_rules(
        self,
        rule_opts: Dict[str, Any],
        width: int = 0,
        height: int = 0
    ) -> bool:
        """
        Tạo hoặc cập nhật rule cho Waydroid trong kwinrulesrc.
        rule_opts:
          - target: 'all' (tất cả app Android + Full UI) hoặc 'full_ui' (chỉ Full UI)
          - above: bool (Luôn nổi trên cùng)
          - noborder: bool (Bỏ thanh tiêu đề / Không viền)
          - fixed_size: bool (Cố định kích thước theo width x height)
          - remember_position: bool (Nhớ vị trí)
          - pin_all_desktops: bool (Ghim trên mọi Virtual Desktop)
          - opacity_active: int (1-100)
          - opacity_inactive: int (1-100)
        """
        config = self._read_config()

        # Đảm bảo phần [General] tồn tại
        if not config.has_section("General"):
            config.add_section("General")
            config.set("General", "count", "0")
            config.set("General", "rules", "")

        rules_str = config.get("General", "rules", fallback="")
        rules_list = [r.strip() for r in rules_str.split(",") if r.strip()]

        if WAYDROID_RULE_ID not in rules_list:
            rules_list.append(WAYDROID_RULE_ID)
            config.set("General", "rules", ",".join(rules_list))
            config.set("General", "count", str(len(rules_list)))

        # Cấu hình section Waydroid Rule
        if not config.has_section(WAYDROID_RULE_ID):
            config.add_section(WAYDROID_RULE_ID)

        sec = config[WAYDROID_RULE_ID]
        sec["Description"] = WAYDROID_RULE_DESC

        target = rule_opts.get("target", "all")
        if target == "all":
            # Khớp bất kỳ cửa sổ nào có 'waydroid' trong wmclass / app-id (substring match)
            sec["wmclass"] = "waydroid"
            sec["wmclassmatch"] = "2"  # 2 = Substring match
            sec["wmclasscomplete"] = "false"
        else:
            # Chỉ khớp cửa sổ Full UI Waydroid chính
            sec["wmclass"] = "Waydroid"
            sec["wmclassmatch"] = "1"  # 1 = Exact match
            sec["wmclasscomplete"] = "false"

        sec["types"] = "1"  # Cửa sổ thông thường

        # Luôn nổi trên cùng (Keep above / Always on top)
        if rule_opts.get("above", False):
            sec["above"] = "true"
            sec["aboverule"] = "3"  # 3 = Force (Bắt buộc)
        else:
            sec["above"] = "false"
            sec["aboverule"] = "0"  # 0 = Do Not Affect

        # Không viền (No border / No titlebar)
        if rule_opts.get("noborder", False):
            sec["noborder"] = "true"
            sec["noborderrule"] = "3"
        else:
            sec["noborder"] = "false"
            sec["noborderrule"] = "0"

        # Kích thước cố định (Fixed size)
        if rule_opts.get("fixed_size", False) and width > 0 and height > 0:
            sec["size"] = f"{width},{height}"
            sec["sizerule"] = "3"  # Force
        else:
            sec["size"] = f"{width},{height}" if (width > 0 and height > 0) else "0,0"
            sec["sizerule"] = "0"

        # Nhớ vị trí cửa sổ (Remember position)
        if rule_opts.get("remember_position", True):
            sec["positionrule"] = "2"  # 2 = Remember
        else:
            sec["positionrule"] = "0"

        # Ghim trên mọi Desktop ảo (Pin to all virtual desktops)
        if rule_opts.get("pin_all_desktops", False):
            sec["desktop"] = "0"  # 0 = All Desktops trong KDE KWin
            sec["desktoprule"] = "3"
        else:
            sec["desktoprule"] = "0"

        # Độ trong suốt (Opacity)
        op_act = int(rule_opts.get("opacity_active", 100))
        if op_act < 100:
            sec["opacityactive"] = str(op_act)
            sec["opacityactiverule"] = "3"
        else:
            sec["opacityactive"] = "100"
            sec["opacityactiverule"] = "0"

        op_inact = int(rule_opts.get("opacity_inactive", 100))
        if op_inact < 100:
            sec["opacityinactive"] = str(op_inact)
            sec["opacityinactiverule"] = "3"
        else:
            sec["opacityinactive"] = "100"
            sec["opacityinactiverule"] = "0"

        saved = self._write_config(config)
        if saved:
            self.reload_kwin()
        return saved

    def remove_rules(self) -> bool:
        """Xóa rule của Waydroid khỏi kwinrulesrc và khôi phục cài đặt KWin."""
        if not self.rules_file.exists():
            return True
        config = self._read_config()
        modified = False

        if config.has_section("General"):
            rules_str = config.get("General", "rules", fallback="")
            rules_list = [r.strip() for r in rules_str.split(",") if r.strip()]
            if WAYDROID_RULE_ID in rules_list:
                rules_list.remove(WAYDROID_RULE_ID)
                config.set("General", "rules", ",".join(rules_list))
                config.set("General", "count", str(len(rules_list)))
                modified = True

        if config.has_section(WAYDROID_RULE_ID):
            config.remove_section(WAYDROID_RULE_ID)
            modified = True

        if modified:
            saved = self._write_config(config)
            if saved:
                self.reload_kwin()
            return saved
        return True

    def reload_kwin(self) -> bool:
        """Kêu gọi KWin reconfigure thông qua DBus để nạp lại rules tức thì."""
        # Ưu tiên qdbus6 trên Plasma 6, sau đó qdbus trên Plasma 5
        commands = [
            ["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"],
            ["qdbus", "org.kde.KWin", "/KWin", "reconfigure"],
            ["qdbus6", "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"],
            ["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"]
        ]
        for cmd in commands:
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                if res.returncode == 0:
                    return True
            except Exception:
                continue
        return False
