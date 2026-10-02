import os
import shutil
import subprocess
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui

from ..core.waydroid_service import WaydroidService


class LogsTab(QtWidgets.QWidget):
    """Tab xem nhật ký hoạt động (Logs) và công cụ chẩn đoán hệ thống."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_log()

        # Timer tự động cập nhật log nếu được bật
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._on_auto_refresh)
        self.timer.start(3000)

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Thanh công cụ trên
        top_bar = QtWidgets.QHBoxLayout()

        self.chk_auto_refresh = QtWidgets.QCheckBox("Tự động cuộn & cập nhật log (3s)")
        self.chk_auto_refresh.setChecked(True)
        top_bar.addWidget(self.chk_auto_refresh)

        top_bar.addStretch()

        self.btn_refresh = QtWidgets.QPushButton("🔄 Tải lại")
        self.btn_refresh.clicked.connect(self.refresh_log)
        top_bar.addWidget(self.btn_refresh)

        self.btn_clear = QtWidgets.QPushButton("🧹 Xóa màn hình log")
        self.btn_clear.clicked.connect(lambda: self.txt_log.clear())
        top_bar.addWidget(self.btn_clear)

        layout.addLayout(top_bar)

        # 2. Khung xem Log
        self.txt_log = QtWidgets.QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("""
            QPlainTextEdit {
                font-family: monospace;
                font-size: 12px;
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid palette(mid);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.txt_log, stretch=3)

        # 3. Hộp công cụ chẩn đoán nhanh (Diagnostic tools)
        diag_box = QtWidgets.QGroupBox("Công cụ Nâng cao & Thiết bị đầu cuối")
        diag_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        diag_layout = QtWidgets.QHBoxLayout(diag_box)

        # Mở Shell
        self.btn_shell = QtWidgets.QPushButton("💻 Mở Android Shell (Konsole)")
        self.btn_shell.setToolTip("Mở cửa sổ dòng lệnh bash bên trong container Android")
        self.btn_shell.clicked.connect(self._open_shell)
        diag_layout.addWidget(self.btn_shell)

        # Mở Logcat
        self.btn_logcat = QtWidgets.QPushButton("📜 Theo dõi Logcat (Konsole)")
        self.btn_logcat.setToolTip("Theo dõi luồng logcat trực tiếp của Android")
        self.btn_logcat.clicked.connect(self._open_logcat)
        diag_layout.addWidget(self.btn_logcat)

        # Mở thư mục dữ liệu
        self.btn_open_data = QtWidgets.QPushButton("📂 Mở thư mục dữ liệu Waydroid (Dolphin)")
        self.btn_open_data.clicked.connect(self._open_data_folder)
        diag_layout.addWidget(self.btn_open_data)

        layout.addWidget(diag_box)

    def refresh_log(self):
        logs = WaydroidService.get_log_lines(200)
        self.txt_log.setPlainText(logs)
        if self.chk_auto_refresh.isChecked():
            self.txt_log.verticalScrollBar().setValue(
                self.txt_log.verticalScrollBar().maximum()
            )

    def _on_auto_refresh(self):
        if self.chk_auto_refresh.isChecked() and self.isVisible():
            self.refresh_log()

    def _launch_in_terminal(self, cmd: str, title: str):
        terminals = [
            ["konsole", "-p", f"tabtitle={title}", "-e", cmd],
            ["x-terminal-emulator", "-e", cmd],
            ["alacritty", "-e", cmd],
            ["kitty", cmd]
        ]
        for term_cmd in terminals:
            if shutil.which(term_cmd[0]):
                try:
                    subprocess.Popen(term_cmd, start_new_session=True)
                    return
                except Exception:
                    pass
        QtWidgets.QMessageBox.warning(self, "Lỗi", "Không tìm thấy trình giả lập Terminal (Konsole)!")

    def _open_shell(self):
        self._launch_in_terminal("waydroid shell", "Waydroid Android Shell")

    def _open_logcat(self):
        self._launch_in_terminal("waydroid logcat", "Waydroid Logcat")

    def _open_data_folder(self):
        data_dir = Path.home() / ".local" / "share" / "waydroid"
        if data_dir.exists():
            subprocess.Popen(["xdg-open", str(data_dir)], start_new_session=True)
        else:
            QtWidgets.QMessageBox.information(self, "Thông báo", f"Thư mục chưa tồn tại:\n{data_dir}")
