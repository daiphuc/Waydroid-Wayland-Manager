import os
from PyQt6 import QtWidgets, QtCore, QtGui
from typing import List, Dict, Any, Optional

from ..core.app_manager import AppManager
from ..core.waydroid_service import WaydroidService


class InstallWorker(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(bool, str)

    def __init__(self, apk_path: str):
        super().__init__()
        self.apk_path = apk_path

    def run(self):
        ok, msg = AppManager.install_apk(self.apk_path)
        self.finished_signal.emit(ok, msg)


class AppsTab(QtWidgets.QWidget):
    """Tab quản lý và khởi chạy các ứng dụng Android trong Waydroid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.apps_data: List[Dict[str, Any]] = []
        self.install_worker: Optional[InstallWorker] = None
        self._init_ui()
        self.refresh_apps()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Thanh công cụ tìm kiếm và các nút thao tác trên cùng
        top_bar = QtWidgets.QHBoxLayout()

        self.txt_search = QtWidgets.QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Tìm kiếm ứng dụng...")
        self.txt_search.textChanged.connect(self._filter_apps)
        top_bar.addWidget(self.txt_search, stretch=2)

        self.btn_install_apk = QtWidgets.QPushButton("📦 Cài đặt file APK...")
        self.btn_install_apk.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        self.btn_install_apk.clicked.connect(self._choose_and_install_apk)
        top_bar.addWidget(self.btn_install_apk)

        self.btn_settings = QtWidgets.QPushButton("⚙️ Cài đặt Android")
        self.btn_settings.clicked.connect(AppManager.open_android_settings)
        top_bar.addWidget(self.btn_settings)

        self.btn_refresh = QtWidgets.QPushButton("🔄 Làm mới")
        self.btn_refresh.clicked.connect(self.refresh_apps)
        top_bar.addWidget(self.btn_refresh)

        layout.addLayout(top_bar)

        # 2. Danh sách ứng dụng (ListWidget with custom items)
        self.app_list = QtWidgets.QListWidget()
        self.app_list.setIconSize(QtCore.QSize(48, 48))
        self.app_list.setSpacing(6)
        self.app_list.setStyleSheet("""
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid palette(midlight);
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
            QListWidget::item:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.app_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.app_list)

        # 3. Thanh thao tác cho ứng dụng đã chọn
        bottom_bar = QtWidgets.QHBoxLayout()

        self.btn_launch = QtWidgets.QPushButton("🚀 Mở ứng dụng")
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #3498db; }
        """)
        self.btn_launch.clicked.connect(self._launch_selected)
        bottom_bar.addWidget(self.btn_launch)

        self.btn_uninstall = QtWidgets.QPushButton("🗑️ Gỡ cài đặt")
        self.btn_uninstall.setStyleSheet("""
            QPushButton {
                color: #c0392b;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #fadbd8; }
        """)
        self.btn_uninstall.clicked.connect(self._uninstall_selected)
        bottom_bar.addWidget(self.btn_uninstall)

        bottom_bar.addStretch()
        self.lbl_app_count = QtWidgets.QLabel("0 ứng dụng")
        self.lbl_app_count.setStyleSheet("color: #7f8c8d;")
        bottom_bar.addWidget(self.lbl_app_count)

        layout.addLayout(bottom_bar)

        # Progress bar khi đang cài đặt APK
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def refresh_apps(self):
        """Quét và nạp lại danh sách ứng dụng."""
        self.apps_data = AppManager.get_installed_apps()
        self._populate_list(self.apps_data)

    def _populate_list(self, apps: List[Dict[str, Any]]):
        self.app_list.clear()
        default_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView)

        for app in apps:
            item = QtWidgets.QListWidgetItem()
            item.setText(f"{app['name']}\n{app['package']}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, app)

            icon_path = app.get("icon", "")
            if icon_path and os.path.exists(icon_path):
                pixmap = QtGui.QPixmap(icon_path)
                item.setIcon(QtGui.QIcon(pixmap))
            else:
                item.setIcon(default_icon)

            self.app_list.addItem(item)

        self.lbl_app_count.setText(f"{len(apps)} ứng dụng")

    def _filter_apps(self, query: str):
        query = query.strip().lower()
        if not query:
            self._populate_list(self.apps_data)
            return

        filtered = [
            a for a in self.apps_data
            if query in a["name"].lower() or query in a["package"].lower()
        ]
        self._populate_list(filtered)

    def _get_selected_app(self) -> Optional[Dict[str, Any]]:
        items = self.app_list.selectedItems()
        if not items:
            return None
        return items[0].data(QtCore.Qt.ItemDataRole.UserRole)

    def _on_item_double_clicked(self, item: QtWidgets.QListWidgetItem):
        app = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if app:
            AppManager.launch_app(app["package"])

    def _launch_selected(self):
        app = self._get_selected_app()
        if not app:
            QtWidgets.QMessageBox.information(self, "Thông báo", "Vui lòng chọn một ứng dụng để mở!")
            return
        AppManager.launch_app(app["package"])

    def _uninstall_selected(self):
        app = self._get_selected_app()
        if not app:
            QtWidgets.QMessageBox.information(self, "Thông báo", "Vui lòng chọn một ứng dụng để gỡ cài đặt!")
            return

        pkg = app["package"]
        if pkg == "com.android.settings":
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Không thể gỡ ứng dụng Cài đặt của hệ thống!")
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Xác nhận gỡ cài đặt",
            f"Bạn có chắc muốn gỡ ứng dụng:\n{app['name']} ({pkg})?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            ok, msg = AppManager.uninstall_app(pkg)
            if ok:
                QtWidgets.QMessageBox.information(self, "Thành công", msg)
                self.refresh_apps()
            else:
                QtWidgets.QMessageBox.warning(self, "Lỗi", f"Không thể gỡ cài đặt: {msg}")

    def _choose_and_install_apk(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Chọn file APK cần cài đặt",
            str(Path.home()),
            "Tệp APK Android (*.apk)"
        )
        if not file_path:
            return

        self.progress_bar.setVisible(True)
        self.btn_install_apk.setEnabled(False)

        self.install_worker = InstallWorker(file_path)
        self.install_worker.finished_signal.connect(self._on_install_finished)
        self.install_worker.start()

    def _on_install_finished(self, success: bool, message: str):
        self.progress_bar.setVisible(False)
        self.btn_install_apk.setEnabled(True)
        if success:
            QtWidgets.QMessageBox.information(self, "Cài đặt thành công", message)
            self.refresh_apps()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi cài đặt APK", f"Không thể cài đặt:\n{message}")
