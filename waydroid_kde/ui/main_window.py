import sys
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui

from ..core.config_manager import ConfigManager
from ..core.kwin_rules import KWinRulesManager
from ..core.waydroid_service import WaydroidService
from .session_tab import SessionTab
from .window_tab import WindowTab
from .apps_tab import AppsTab
from .logs_tab import LogsTab
from .tray_icon import WaydroidTrayIcon

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "waydroid-kde.png"


class MainWindow(QtWidgets.QMainWindow):
    """Cửa sổ chính của Waydroid KDE Manager."""

    def __init__(self, config_mgr: ConfigManager, kwin_mgr: KWinRulesManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.kwin_mgr = kwin_mgr

        self.setWindowTitle("Waydroid Manager - KDE Plasma")
        self.resize(860, 660)
        self.setMinimumSize(720, 520)

        if ICON_PATH.exists():
            self.setWindowIcon(QtGui.QIcon(str(ICON_PATH)))

        self._init_ui()

        # Tạo khay hệ thống (System Tray Icon)
        self.tray_icon = WaydroidTrayIcon(self, self.config_mgr, self)
        self.tray_icon.show()

        # Timer cập nhật trạng thái định kỳ
        self.status_timer = QtCore.QTimer(self)
        self.status_timer.timeout.connect(self._periodic_status_update)
        self.status_timer.start(2500)

        # Cập nhật ngay lần đầu
        self.session_tab.update_status_ui()

    def _init_ui(self):
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Tabs Widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setIconSize(QtCore.QSize(20, 20))
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 13px;
                font-weight: 500;
                padding: 8px 18px;
            }
        """)

        # 1. Tab Phiên & Trạng thái
        self.session_tab = SessionTab(self.config_mgr, self.kwin_mgr, self)
        self.session_tab.status_changed.connect(self._on_status_changed)
        self.session_tab.status_message.connect(self._show_status_message)
        self.tabs.addTab(
            self.session_tab,
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DriveHDIcon),
            "🕹️ Điều Khiển & Phiên"
        )

        # 2. Tab Tùy Biến Cửa Sổ
        self.window_tab = WindowTab(self.config_mgr, self.kwin_mgr, self)
        self.tabs.addTab(
            self.window_tab,
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DesktopIcon),
            "🪟 Tùy Biến Cửa Sổ"
        )

        # 3. Tab Ứng Dụng Android
        self.apps_tab = AppsTab(self)
        self.tabs.addTab(
            self.apps_tab,
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView),
            "📱 Ứng Dụng Android"
        )

        # 4. Tab Nhật Ký & Chẩn Đoán
        self.logs_tab = LogsTab(self)
        self.tabs.addTab(
            self.logs_tab,
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView),
            "📋 Nhật Ký & Công Cụ"
        )

        main_layout.addWidget(self.tabs)

        # Status Bar
        self.status_bar = self.statusBar()
        self.lbl_sb_status = QtWidgets.QLabel("Waydroid: Sẵn sàng")
        self.status_bar.addPermanentWidget(self.lbl_sb_status)

    def _periodic_status_update(self):
        # Chỉ cập nhật tự động nếu cửa sổ đang hiển thị
        if self.isVisible():
            self.session_tab.update_status_ui()

    def _on_status_changed(self, status: dict):
        self.tray_icon.update_status(status)
        s_state = status.get("session_status", "STOPPED")
        ip = status.get("ip_address", "")
        ip_txt = f" | IP: {ip}" if ip else ""
        self.lbl_sb_status.setText(f"Waydroid: {s_state}{ip_txt}")

    def _show_status_message(self, message: str, timeout: int = 5000):
        if self.status_bar:
            self.status_bar.showMessage(message, timeout)

    def closeEvent(self, event: QtGui.QCloseEvent):
        # Nếu bật chế độ thu nhỏ vào khay hệ thống
        if self.config_mgr.get("system.minimize_to_tray", True) and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Waydroid Manager",
                "Ứng dụng vẫn đang chạy ở khay hệ thống KDE.",
                QtWidgets.QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
