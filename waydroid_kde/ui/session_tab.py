import html
from PyQt6 import QtWidgets, QtCore, QtGui
from typing import Dict, Any, Optional

from ..core.waydroid_service import WaydroidService
from ..core.config_manager import ConfigManager
from ..core.kwin_rules import KWinRulesManager


class WorkerThread(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(bool, str, object)

    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            if isinstance(result, tuple) and len(result) == 2:
                ok, msg = result
                self.finished_signal.emit(ok, msg, None)
            elif isinstance(result, dict):
                ok = result.get("success", True)
                msg = "\n".join(result.get("messages", []))
                self.finished_signal.emit(ok, msg, result)
            else:
                self.finished_signal.emit(True, str(result), result)
        except Exception as e:
            self.finished_signal.emit(False, str(e), None)


class SessionTab(QtWidgets.QWidget):
    """Tab quản lý phiên, tắt mở và dọn dẹp Waydroid."""

    status_changed = QtCore.pyqtSignal(dict)
    status_message = QtCore.pyqtSignal(str, int)

    def __init__(self, config_mgr: ConfigManager, kwin_mgr: KWinRulesManager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.kwin_mgr = kwin_mgr
        self.worker: Optional[WorkerThread] = None
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Thẻ trạng thái tổng quan (Status Card)
        self.status_card = QtWidgets.QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setStyleSheet("""
            QFrame#statusCard {
                background: palette(window);
                border: 1px solid palette(mid);
                border-radius: 10px;
                padding: 14px;
            }
        """)
        card_layout = QtWidgets.QHBoxLayout(self.status_card)

        # Cột trái thẻ trạng thái
        left_info = QtWidgets.QVBoxLayout()
        self.lbl_status_badge = QtWidgets.QLabel("STOPPED")
        self.lbl_status_badge.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                background-color: #7f8c8d;
                color: white;
            }
        """)
        self.lbl_status_badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        left_info.addWidget(self.lbl_status_badge)
        left_info.addStretch()
        card_layout.addLayout(left_info, stretch=1)

        # Cột phải thẻ trạng thái
        right_info = QtWidgets.QGridLayout()
        right_info.setHorizontalSpacing(14)
        right_info.setVerticalSpacing(8)

        right_info.addWidget(QtWidgets.QLabel("<b>Dịch vụ Container:</b>"), 0, 0)
        self.lbl_container = QtWidgets.QLabel("Đang kiểm tra...")
        right_info.addWidget(self.lbl_container, 0, 1)

        right_info.addWidget(QtWidgets.QLabel("<b>Địa chỉ IP Waydroid:</b>"), 1, 0)
        self.lbl_ip = QtWidgets.QLabel("Chưa kết nối")
        right_info.addWidget(self.lbl_ip, 1, 1)

        right_info.addWidget(QtWidgets.QLabel("<b>Chế độ cửa sổ:</b>"), 2, 0)
        self.lbl_mode = QtWidgets.QLabel("Multi-window")
        right_info.addWidget(self.lbl_mode, 2, 1)

        right_info.addWidget(QtWidgets.QLabel("<b>Tiến trình nền:</b>"), 3, 0)
        self.lbl_procs = QtWidgets.QLabel("0 tiến trình")
        right_info.addWidget(self.lbl_procs, 3, 1)

        card_layout.addLayout(right_info, stretch=3)
        layout.addWidget(self.status_card)

        # 2. Cụm nút thao tác chính (Main Actions)
        actions_box = QtWidgets.QGroupBox("Thao tác Phiên & Điều khiển")
        actions_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        actions_grid = QtWidgets.QGridLayout(actions_box)
        actions_grid.setSpacing(12)

        # Nút Khởi động
        self.btn_start_multi = QtWidgets.QPushButton("🚀 Khởi động Multi-Window")
        self.btn_start_multi.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_start_multi.setMinimumHeight(40)
        self.btn_start_multi.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.btn_start_multi.clicked.connect(lambda: self._start_session("multi_windows"))
        actions_grid.addWidget(self.btn_start_multi, 0, 0)

        # Nút Mở Full UI
        self.btn_start_full = QtWidgets.QPushButton("📱 Mở Cửa sổ Full UI")
        self.btn_start_full.setMinimumHeight(40)
        self.btn_start_full.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #3498db; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.btn_start_full.clicked.connect(lambda: self._start_session("full_ui"))
        actions_grid.addWidget(self.btn_start_full, 0, 1)

        # Nút Dừng phiên
        self.btn_stop = QtWidgets.QPushButton("⏹️ Tắt Waydroid Session")
        self.btn_stop.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #e74c3c; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.btn_stop.clicked.connect(self._stop_session)
        actions_grid.addWidget(self.btn_stop, 0, 2)

        # Nút Khởi động lại
        self.btn_restart = QtWidgets.QPushButton("🔄 Khởi động lại (Restart)")
        self.btn_restart.setMinimumHeight(38)
        self.btn_restart.clicked.connect(self._restart_session)
        actions_grid.addWidget(self.btn_restart, 1, 0)

        # Nút Dọn dẹp session thông thường
        self.btn_clean = QtWidgets.QPushButton("🧹 Dọn dẹp Session (Clean)")
        self.btn_clean.setToolTip("Tắt session, dọn sạch tiến trình zombie, giải phóng socket và lockfile treo")
        self.btn_clean.setMinimumHeight(38)
        self.btn_clean.setStyleSheet("""
            QPushButton {
                background-color: #d35400;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.btn_clean.clicked.connect(lambda: self._cleanup_session(deep=False))
        actions_grid.addWidget(self.btn_clean, 1, 1)

        # Nút Dọn dẹp sâu cấp Root
        self.btn_deep_clean = QtWidgets.QPushButton("🛡️ Dọn dẹp triệt để (Deep Clean)")
        self.btn_deep_clean.setToolTip("Yêu cầu mật khẩu sudo: Khởi động lại service container và dọn mount bị kẹt")
        self.btn_deep_clean.setMinimumHeight(38)
        self.btn_deep_clean.clicked.connect(lambda: self._cleanup_session(deep=True))
        actions_grid.addWidget(self.btn_deep_clean, 1, 2)

        # Nút Dừng Container giải phóng RAM
        self.btn_stop_container = QtWidgets.QPushButton("🛑 Dừng hoàn toàn Container (Giải phóng RAM)")
        self.btn_stop_container.setToolTip("Tắt dịch vụ waydroid-container cấp root để giải phóng toàn bộ bộ nhớ RAM")
        self.btn_stop_container.clicked.connect(self._stop_container)
        actions_grid.addWidget(self.btn_stop_container, 2, 0, 1, 3)

        layout.addWidget(actions_box)

        # 3. Tùy chọn khởi chạy nhanh
        opts_layout = QtWidgets.QHBoxLayout()
        self.chk_auto_container = QtWidgets.QCheckBox("Tự động bật dịch vụ Container nếu chưa chạy")
        self.chk_auto_container.setChecked(self.config_mgr.get("system.auto_start_container", True))
        self.chk_auto_container.stateChanged.connect(
            lambda s: self.config_mgr.set("system.auto_start_container", bool(s)) or self.config_mgr.save()
        )
        opts_layout.addWidget(self.chk_auto_container)

        self.chk_auto_rules = QtWidgets.QCheckBox("Tự động áp dụng KWin Rules khi mở Waydroid")
        self.chk_auto_rules.setChecked(self.config_mgr.get("system.auto_apply_kwin_rules", True))
        self.chk_auto_rules.stateChanged.connect(
            lambda s: self.config_mgr.set("system.auto_apply_kwin_rules", bool(s)) or self.config_mgr.save()
        )
        opts_layout.addWidget(self.chk_auto_rules)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        # 4. Danh sách tiến trình đang chạy (Process Table)
        proc_box = QtWidgets.QGroupBox("Tiến trình Waydroid trong hệ thống")
        proc_layout = QtWidgets.QVBoxLayout(proc_box)

        self.proc_table = QtWidgets.QTableWidget(0, 4)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Người dùng", "Lệnh", "Chi tiết dòng lệnh"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.proc_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        proc_layout.addWidget(self.proc_table)

        proc_btn_bar = QtWidgets.QHBoxLayout()
        self.btn_kill_selected = QtWidgets.QPushButton("Diệt tiến trình đã chọn")
        self.btn_kill_selected.clicked.connect(self._kill_selected_process)
        proc_btn_bar.addWidget(self.btn_kill_selected)

        self.btn_refresh_procs = QtWidgets.QPushButton("🔄 Làm mới danh sách")
        self.btn_refresh_procs.clicked.connect(self.update_status_ui)
        proc_btn_bar.addWidget(self.btn_refresh_procs)
        proc_btn_bar.addStretch()
        proc_layout.addLayout(proc_btn_bar)

        layout.addWidget(proc_box)

        # Tiến trình loading
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def update_status_ui(self):
        """Cập nhật giao diện theo trạng thái hệ thống thực tế."""
        status = WaydroidService.get_status()
        self.status_changed.emit(status)

        s_state = status["session_status"]
        if s_state == "RUNNING":
            self.lbl_status_badge.setText("● ĐANG CHẠY")
            self.lbl_status_badge.setStyleSheet("""
                font-size: 16px; font-weight: bold; padding: 6px 14px;
                border-radius: 6px; background-color: #27ae60; color: white;
            """)
            self.btn_start_multi.setEnabled(False)
            self.btn_stop.setEnabled(True)
        elif "STARTING" in s_state or "BUSY" in s_state:
            self.lbl_status_badge.setText("⏳ ĐANG KHỞI ĐỘNG")
            self.lbl_status_badge.setStyleSheet("""
                font-size: 16px; font-weight: bold; padding: 6px 14px;
                border-radius: 6px; background-color: #f39c12; color: white;
            """)
            self.btn_start_multi.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.lbl_status_badge.setText("○ ĐÃ TẮT")
            self.lbl_status_badge.setStyleSheet("""
                font-size: 16px; font-weight: bold; padding: 6px 14px;
                border-radius: 6px; background-color: #7f8c8d; color: white;
            """)
            self.btn_start_multi.setEnabled(True)
            self.btn_stop.setEnabled(False)

        # Container
        if status["container_active"]:
            self.lbl_container.setText("<span style='color:#27ae60;'><b>Đang hoạt động</b></span>")
        else:
            self.lbl_container.setText("<span style='color:#e74c3c;'>Đã dừng</span>")

        # IP
        ip = status["ip_address"]
        self.lbl_ip.setText(f"<code>{ip}</code>" if ip else "<i>Chưa kết nối</i>")

        # Chế độ
        cfg_mode = self.config_mgr.get("display.mode", "multi_windows")
        mode_text = "Multi-Window (Cửa sổ riêng)" if cfg_mode == "multi_windows" else "Single Full UI (Toàn bộ Android)"
        self.lbl_mode.setText(mode_text)

        # Tiến trình
        procs = status["processes"]
        self.lbl_procs.setText(f"{len(procs)} tiến trình liên quan")

        # Cập nhật bảng
        self.proc_table.setRowCount(len(procs))
        for row, p in enumerate(procs):
            self.proc_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(p["pid"])))
            self.proc_table.setItem(row, 1, QtWidgets.QTableWidgetItem(p["user"]))
            self.proc_table.setItem(row, 2, QtWidgets.QTableWidgetItem(p["comm"]))
            self.proc_table.setItem(row, 3, QtWidgets.QTableWidgetItem(p["cmd"]))

    def _set_busy(self, busy: bool, message: str = ""):
        self.progress_bar.setVisible(busy)
        self.btn_start_multi.setEnabled(not busy)
        self.btn_start_full.setEnabled(not busy)
        self.btn_stop.setEnabled(not busy)
        self.btn_clean.setEnabled(not busy)
        self.btn_deep_clean.setEnabled(not busy)
        self.btn_restart.setEnabled(not busy)

    def _start_session(self, mode: str):
        self._set_busy(True)
        # Tự động nạp kwin rules nếu cấu hình bật
        if self.config_mgr.get("system.auto_apply_kwin_rules", True):
            w = self.config_mgr.get("display.width", 0)
            h = self.config_mgr.get("display.height", 0)
            rules_opts = self.config_mgr.get("kwin_rules", {})
            self.kwin_mgr.apply_rules(rules_opts, width=w, height=h)

        w = self.config_mgr.get("display.width", 0)
        h = self.config_mgr.get("display.height", 0)
        dpi = self.config_mgr.get("display.dpi", 0)
        auto_c = self.config_mgr.get("system.auto_start_container", True)

        self.worker = WorkerThread(WaydroidService.start_session, mode, w, h, dpi, auto_c)
        self.worker.finished_signal.connect(self._on_action_finished)
        self.worker.start()

    def _stop_session(self):
        self._set_busy(True)
        self.worker = WorkerThread(WaydroidService.stop_session)
        self.worker.finished_signal.connect(self._on_action_finished)
        self.worker.start()

    def _restart_session(self):
        self._set_busy(True)
        mode = self.config_mgr.get("display.mode", "multi_windows")
        w = self.config_mgr.get("display.width", 0)
        h = self.config_mgr.get("display.height", 0)
        dpi = self.config_mgr.get("display.dpi", 0)

        def do_restart():
            WaydroidService.stop_session()
            WaydroidService.cleanup_session(deep=False)
            return WaydroidService.start_session(mode, w, h, dpi)

        self.worker = WorkerThread(do_restart)
        self.worker.finished_signal.connect(self._on_action_finished)
        self.worker.start()

    def _cleanup_session(self, deep: bool = False):
        self._set_busy(True)
        self.worker = WorkerThread(WaydroidService.cleanup_session, deep)
        self.worker.finished_signal.connect(self._on_action_finished)
        self.worker.start()

    def _stop_container(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Xác nhận dừng Container",
            "Dừng dịch vụ Container sẽ tắt hoàn toàn Waydroid và giải phóng bộ nhớ RAM.\nBạn có muốn tiếp tục?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self._set_busy(True)
            self.worker = WorkerThread(WaydroidService.stop_container)
            self.worker.finished_signal.connect(self._on_action_finished)
            self.worker.start()

    def _kill_selected_process(self):
        selected = self.proc_table.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.information(self, "Thông báo", "Vui lòng chọn một tiến trình trong danh sách!")
            return
        row = selected[0].row()
        pid_item = self.proc_table.item(row, 0)
        if not pid_item:
            return
        pid = int(pid_item.text())
        try:
            import os, signal
            os.kill(pid, signal.SIGKILL)
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã gửi SIGKILL đến PID {pid}")
            self.update_status_ui()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Lỗi", f"Không thể diệt tiến trình: {e}")

    def _on_action_finished(self, success: bool, message: str, extra: Any):
        self._set_busy(False)
        self.update_status_ui()
        if not success:
            QtWidgets.QMessageBox.warning(self, "Thông báo lỗi", message or "Thao tác không thành công.")
        else:
            if message and len(message) < 200:
                self.status_message.emit(message, 5000)
            elif message:
                QtWidgets.QMessageBox.information(self, "Kết quả thao tác", message)
