import os
import json
from pathlib import Path
from typing import Any, Dict

def _get_default_config_file() -> Path:
    xdg = os.getenv("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    target_dir = base / "waydroid-kde"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / "config.json"
    except (OSError, PermissionError):
        # Fallback vào thư mục cấu hình cục bộ của project
        local_dir = Path(__file__).resolve().parent.parent.parent / ".config" / "waydroid-kde"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir / "config.json"

CONFIG_FILE = _get_default_config_file()

RESOLUTION_PRESETS = {
    "auto": {
        "name": "🖥️ Tự động (Theo màn hình Desktop)",
        "width": 0,
        "height": 0,
        "dpi": 0,
        "description": "Để Waydroid tự động điều chỉnh theo kích thước màn hình hiện tại."
    },
    "phone_compact": {
        "name": "📱 Điện thoại Nhỏ gọn (540 × 960)",
        "width": 540,
        "height": 960,
        "dpi": 200,
        "description": "Kích thước nhỏ gọn, ít tốn diện tích màn hình máy tính."
    },
    "phone_hd": {
        "name": "📱 Điện thoại Chuẩn HD (720 × 1280)",
        "width": 720,
        "height": 1280,
        "dpi": 260,
        "description": "Chuẩn tối ưu cho Zalo, TikTok, Facebook, tin nhắn điện thoại."
    },
    "phone_fhd": {
        "name": "📱 Điện thoại Full HD (1080 × 1920)",
        "width": 1080,
        "height": 1920,
        "dpi": 380,
        "description": "Độ nét cao sắc nét, hiển thị nhiều nội dung."
    },
    "phone_tall": {
        "name": "📱 Điện thoại Dọc 20:9 (720 × 1600)",
        "width": 720,
        "height": 1600,
        "dpi": 280,
        "description": "Tỉ lệ màn hình smartphone tràn viền hiện đại."
    },
    "tablet_small": {
        "name": "💻 Máy tính bảng Nhỏ (1280 × 800)",
        "width": 1280,
        "height": 800,
        "dpi": 200,
        "description": "Tỉ lệ 16:10 phù hợp đọc sách, làm việc màn ngang nhỏ."
    },
    "tablet_fhd": {
        "name": "💻 Máy tính bảng Full HD (1920 × 1080)",
        "width": 1920,
        "height": 1080,
        "dpi": 240,
        "description": "Màn hình ngang 16:9 tiêu chuẩn cho chơi game và đa nhiệm."
    },
    "tablet_2k": {
        "name": "💻 Máy tính bảng 2K (2560 × 1440)",
        "width": 2560,
        "height": 1440,
        "dpi": 280,
        "description": "Độ phân giải siêu cao cho màn hình rời hoặc tablet lớn."
    },
    "custom": {
        "name": "⚙️ Tùy chỉnh người dùng (Custom)",
        "width": 720,
        "height": 1280,
        "dpi": 260,
        "description": "Tự do điền kích thước và mật độ điểm ảnh tùy thích."
    }
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "display": {
        "mode": "multi_windows",  # "multi_windows" or "full_ui"
        "preset": "phone_hd",
        "width": 720,
        "height": 1280,
        "dpi": 260,
        "orientation": "portrait"
    },
    "kwin_rules": {
        "enabled": True,
        "target": "all",  # "all" or "full_ui"
        "above": False,
        "noborder": False,
        "fixed_size": False,
        "remember_position": True,
        "pin_all_desktops": False,
        "opacity_active": 100,
        "opacity_inactive": 100
    },
    "tweaks": {
        "disable_suspend": True,
        "cursor_subsurface": True,
        "fake_touch": False,
        "invert_colors": False
    },
    "system": {
        "auto_start_container": True,
        "auto_apply_kwin_rules": True,
        "minimize_to_tray": True
    }
}


class ConfigManager:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.config: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return json.loads(json.dumps(DEFAULT_CONFIG))
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_CONFIG))
            self._deep_update(merged, data)
            return merged
        except Exception:
            return json.loads(json.dumps(DEFAULT_CONFIG))

    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def save(self) -> bool:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            temp_path.replace(self.config_path)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        current = self.config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        current = self.config
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def apply_preset(self, preset_key: str) -> bool:
        if preset_key not in RESOLUTION_PRESETS:
            return False
        preset = RESOLUTION_PRESETS[preset_key]
        self.set("display.preset", preset_key)
        if preset_key != "custom":
            self.set("display.width", preset["width"])
            self.set("display.height", preset["height"])
            self.set("display.dpi", preset["dpi"])
            if preset["width"] > preset["height"] and preset["height"] > 0:
                self.set("display.orientation", "landscape")
            elif preset["height"] > 0:
                self.set("display.orientation", "portrait")
        self.save()
        return True
