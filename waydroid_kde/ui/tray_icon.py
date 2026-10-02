import os
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui
from typing import Optional

from ..core.waydroid_service import WaydroidService
from ..core.config_manager import ConfigManager

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "waydroid-kde.png"


class WaydroidTrayIcon(QtWidgets.QSystemTrayIcon):
    """System Tray Icon cho KDE Plasma."""

    def __init__(self, main_window, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.config_mgr = config_mgr

        if ICON_PATH.exists():
            self.setIcon(QtGui.QIcon(str(ICON_PATH)))
        else:
            self.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon))

        self.setToolTip("Waydroid KDE Manager")
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _build_menu(self):
        self.menu = QtWidgets.QMenu()

        self.action_status = self.menu.addAction("Waydroid: Đang kiểm tra...")
        self.action_status.setEnabled(False)
        self.menu.addSeparator()

        self.action_start_multi = self.menu.addAction("🚀 Bật Multi-Window")
        self.action_start_multi.triggered.connect(lambda: self.main_window.session_tab._start_session("multi_windows"))

        self.action_start_full = self.menu.addAction("📱 Mở Full UI")
        self.action_start_full.triggered.connect(lambda: self.main_window.session_tab._start_session("full_ui"))

        self.action_stop = self.menu.addAction("⏹️ Tắt Waydroid Session")
        self.action_stop.triggered.connect(self.main_window.session_tab._stop_session)

        self.action_restart = self.menu.addAction("🔄 Khởi động lại")
        self.action_restart.triggered.connect(self.main_window.session_tab._restart_session)

        self.action_clean = self.menu.addAction("🧹 Dọn dẹp Session (Clean)")
        self.action_clean.triggered.connect(lambda: self.main_window.session_tab._cleanup_session(deep=False))

        self.menu.addSeparator()

        self.action_settings = self.menu.addAction("⚙️ Cài đặt Android")
        from ..core.app_manager import AppManager
        self.action_settings.triggered.connect(AppManager.open_android_settings)

        self.action_toggle_window = self.menu.addAction("🪟 Mở Cửa sổ Quản lý")
        self.action_toggle_window.triggered.connect(self.toggle_window)

        self.menu.addSeparator()

        self.action_quit = self.menu.addAction("❌ Thoát ứng dụng")
        self.action_quit.triggered.connect(QtWidgets.QApplication.quit)

        self.setContextMenu(self.menu)

    def update_status(self, status: dict):
        s_state = status.get("session_status", "STOPPED")
        if s_state == "RUNNING":
            self.action_status.setText("● Trạng thái: ĐANG CHẠY")
            self.setToolTip("Waydroid: Đang hoạt động")
            self.action_start_multi.setEnabled(False)
            self.action_stop.setEnabled(True)
        elif "STARTING" in s_state or "BUSY" in s_state:
            self.action_status.setText("⏳ Trạng thái: Đang khởi động")
            self.setToolTip("Waydroid: Đang khởi động...")
            self.action_start_multi.setEnabled(False)
            self.action_stop.setEnabled(True)
        else:
            self.action_status.setText("○ Trạng thái: ĐÃ TẮT")
            self.setToolTip("Waydroid: Đã tắt")
            self.action_start_multi.setEnabled(True)
            self.action_stop.setEnabled(False)

    def _on_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()

    def toggle_window(self):
        if self.main_window.isVisible():
            if self.main_window.isMinimized():
                self.main_window.showNormal()
                self.main_window.activateWindow()
            else:
                self.main_window.hide()
        else:
            self.main_window.showNormal()
            self.main_window.activateWindow()
