from PyQt6 import QtWidgets, QtCore, QtGui
from typing import Dict, Any

from ..core.config_manager import ConfigManager, RESOLUTION_PRESETS
from ..core.kwin_rules import KWinRulesManager
from ..core.waydroid_service import WaydroidService


class WindowTab(QtWidgets.QWidget):
    """Tab tùy biến cửa sổ Waydroid, kích thước, độ phân giải và KWin Window Rules trong KDE."""

    def __init__(self, config_mgr: ConfigManager, kwin_mgr: KWinRulesManager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.kwin_mgr = kwin_mgr
        self._init_ui()
        self.load_from_config()

    def _init_ui(self):
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setSpacing(18)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Chế độ hiển thị cửa sổ (Window Mode)
        mode_box = QtWidgets.QGroupBox("1. Chế độ hiển thị Waydroid")
        mode_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        mode_layout = QtWidgets.QVBoxLayout(mode_box)

        self.rb_multi = QtWidgets.QRadioButton("🖥️ Multi-Window Mode (Khuyên dùng trên KDE Desktop)")
        self.rb_multi.setToolTip("Mỗi ứng dụng Android chạy thành một cửa sổ độc lập trên màn hình KDE Plasma.")
        self.rb_multi.toggled.connect(self._on_mode_toggled)
        mode_layout.addWidget(self.rb_multi)

        lbl_multi_desc = QtWidgets.QLabel(
            "<span style='color:gray; font-size:12px;'>"
            "• Từng app Android có thanh tiêu đề KDE riêng, có thể chia màn hình (tiling), phóng to thu nhỏ độc lập."
            "</span>"
        )
        lbl_multi_desc.setContentsMargins(24, 0, 0, 4)
        mode_layout.addWidget(lbl_multi_desc)

        self.rb_full = QtWidgets.QRadioButton("📱 Single Full UI Mode (Giao diện nguyên khối Android)")
        self.rb_full.setToolTip("Toàn bộ Android hiển thị trong 1 cửa sổ duy nhất như một chiếc máy tính bảng hoặc điện thoại.")
        mode_layout.addWidget(self.rb_full)

        lbl_full_desc = QtWidgets.QLabel(
            "<span style='color:gray; font-size:12px;'>"
            "• Thích hợp để giả lập nguyên vẹn chiếc điện thoại / tablet Android kèm thanh thông báo và điều hướng."
            "</span>"
        )
        lbl_full_desc.setContentsMargins(24, 0, 0, 4)
        mode_layout.addWidget(lbl_full_desc)

        layout.addWidget(mode_box)

        # 2. Kích thước & Độ phân giải (Resolution & Presets)
        res_box = QtWidgets.QGroupBox("2. Kích thước & Độ phân giải (Resolution & Presets)")
        res_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        res_layout = QtWidgets.QVBoxLayout(res_box)

        # Hàng chọn Presets
        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(QtWidgets.QLabel("Cấu hình sẵn (Presets):"))
        self.cbo_presets = QtWidgets.QComboBox()
        for k, v in RESOLUTION_PRESETS.items():
            self.cbo_presets.addItem(v["name"], k)
        self.cbo_presets.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.cbo_presets, stretch=1)
        res_layout.addLayout(preset_row)

        self.lbl_preset_desc = QtWidgets.QLabel("")
        self.lbl_preset_desc.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 6px;")
        res_layout.addWidget(self.lbl_preset_desc)

        # Hàng chi tiết: Width, Height, DPI
        dims_grid = QtWidgets.QGridLayout()
        dims_grid.setHorizontalSpacing(16)
        dims_grid.setVerticalSpacing(8)

        dims_grid.addWidget(QtWidgets.QLabel("Chiều rộng (Width px):"), 0, 0)
        self.spn_width = QtWidgets.QSpinBox()
        self.spn_width.setRange(0, 7680)
        self.spn_width.setSingleStep(20)
        self.spn_width.valueChanged.connect(self._on_custom_dim_changed)
        dims_grid.addWidget(self.spn_width, 0, 1)

        dims_grid.addWidget(QtWidgets.QLabel("Chiều cao (Height px):"), 0, 2)
        self.spn_height = QtWidgets.QSpinBox()
        self.spn_height.setRange(0, 4320)
        self.spn_height.setSingleStep(20)
        self.spn_height.valueChanged.connect(self._on_custom_dim_changed)
        dims_grid.addWidget(self.spn_height, 0, 3)

        dims_grid.addWidget(QtWidgets.QLabel("Mật độ điểm ảnh (DPI):"), 1, 0)
        self.spn_dpi = QtWidgets.QSpinBox()
        self.spn_dpi.setRange(0, 640)
        self.spn_dpi.setSingleStep(10)
        self.spn_dpi.setToolTip("Giá trị 0 = để hệ thống tự động tính. Giá trị phổ biến: 160, 240, 280, 320, 400.")
        self.spn_dpi.valueChanged.connect(self._on_custom_dim_changed)
        dims_grid.addWidget(self.spn_dpi, 1, 1)

        # Nút Đảo chiều
        self.btn_rotate = QtWidgets.QPushButton("🔄 Đảo chiều (Dọc ↔ Ngang)")
        self.btn_rotate.setToolTip("Hoán đổi chiều rộng và chiều cao (Portrait ↔ Landscape)")
        self.btn_rotate.clicked.connect(self._rotate_dimensions)
        dims_grid.addWidget(self.btn_rotate, 1, 2, 1, 2)

        res_layout.addLayout(dims_grid)
        layout.addWidget(res_box)

        # 3. Tùy biến KWin Rules trong KDE Plasma (KWin Integration)
        kwin_box = QtWidgets.QGroupBox("3. Tùy biến Cửa sổ KDE KWin (Plasma Rules)")
        kwin_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        kwin_layout = QtWidgets.QVBoxLayout(kwin_box)

        kwin_intro = QtWidgets.QLabel(
            "Tự động áp dụng quy tắc quản lý cửa sổ KWin của KDE Plasma cho Waydroid "
            "(không cần chỉnh tay trong System Settings):"
        )
        kwin_intro.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        kwin_layout.addWidget(kwin_intro)

        # Checkboxes KWin Rules
        kwin_grid = QtWidgets.QGridLayout()
        kwin_grid.setVerticalSpacing(8)

        self.chk_above = QtWidgets.QCheckBox("📌 Luôn nổi trên cùng (Keep Above / Always on Top)")
        self.chk_above.setToolTip("Cửa sổ Waydroid sẽ luôn hiển thị phía trên các ứng dụng desktop khác.")
        kwin_grid.addWidget(self.chk_above, 0, 0)

        self.chk_noborder = QtWidgets.QCheckBox("🔲 Bỏ khung viền & thanh tiêu đề (Borderless / No Titlebar)")
        self.chk_noborder.setToolTip("Loại bỏ thanh tiêu đề và đường viền cửa sổ để giao diện trông giống smartphone thực thụ.")
        kwin_grid.addWidget(self.chk_noborder, 0, 1)

        self.chk_fixed_size = QtWidgets.QCheckBox("📏 Cố định kích thước cửa sổ (Fixed Size theo Width x Height)")
        self.chk_fixed_size.setToolTip("Khóa không cho KWin co giãn méo mó cửa sổ, luôn giữ đúng tỉ lệ.")
        kwin_grid.addWidget(self.chk_fixed_size, 1, 0)

        self.chk_remember_pos = QtWidgets.QCheckBox("🧠 Ghi nhớ vị trí khi di chuyển (Remember Position)")
        self.chk_remember_pos.setToolTip("KWin sẽ tự động nhớ vị trí người dùng đã kéo cửa sổ tới.")
        kwin_grid.addWidget(self.chk_remember_pos, 1, 1)

        self.chk_pin_desktops = QtWidgets.QCheckBox("🌐 Ghim trên mọi Desktop ảo (Pin to all Virtual Desktops)")
        self.chk_pin_desktops.setToolTip("Cửa sổ sẽ xuất hiện trên tất cả các màn hình ảo của KDE.")
        kwin_grid.addWidget(self.chk_pin_desktops, 2, 0)

        kwin_layout.addLayout(kwin_grid)

        # Phạm vi áp dụng (Target)
        target_layout = QtWidgets.QHBoxLayout()
        target_layout.addWidget(QtWidgets.QLabel("Phạm vi áp dụng Rule:"))
        self.cbo_kwin_target = QtWidgets.QComboBox()
        self.cbo_kwin_target.addItem("Tất cả ứng dụng Waydroid (Cả Multi-window & Full UI)", "all")
        self.cbo_kwin_target.addItem("Chỉ cửa sổ Full UI Waydroid", "full_ui")
        target_layout.addWidget(self.cbo_kwin_target, stretch=1)
        kwin_layout.addLayout(target_layout)

        # Độ trong suốt (Opacity)
        op_grid = QtWidgets.QGridLayout()
        op_grid.addWidget(QtWidgets.QLabel("Độ mờ khi Active:"), 0, 0)
        self.sld_opacity_act = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.sld_opacity_act.setRange(50, 100)
        self.sld_opacity_act.setValue(100)
        self.lbl_opacity_act_val = QtWidgets.QLabel("100%")
        self.sld_opacity_act.valueChanged.connect(lambda v: self.lbl_opacity_act_val.setText(f"{v}%"))
        op_grid.addWidget(self.sld_opacity_act, 0, 1)
        op_grid.addWidget(self.lbl_opacity_act_val, 0, 2)

        op_grid.addWidget(QtWidgets.QLabel("Độ mờ khi Inactive:"), 1, 0)
        self.sld_opacity_inact = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.sld_opacity_inact.setRange(30, 100)
        self.sld_opacity_inact.setValue(100)
        self.lbl_opacity_inact_val = QtWidgets.QLabel("100%")
        self.sld_opacity_inact.valueChanged.connect(lambda v: self.lbl_opacity_inact_val.setText(f"{v}%"))
        op_grid.addWidget(self.sld_opacity_inact, 1, 1)
        op_grid.addWidget(self.lbl_opacity_inact_val, 1, 2)

        kwin_layout.addLayout(op_grid)

        # Nút áp dụng và xóa KWin Rules
        kwin_btn_bar = QtWidgets.QHBoxLayout()
        self.btn_apply_kwin = QtWidgets.QPushButton("⚡ Áp dụng KWin Rules ngay")
        self.btn_apply_kwin.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #3498db; }
        """)
        self.btn_apply_kwin.clicked.connect(self._apply_kwin_rules_now)
        kwin_btn_bar.addWidget(self.btn_apply_kwin)

        self.btn_remove_kwin = QtWidgets.QPushButton("🗑️ Xóa KWin Rules (Khôi phục mặc định)")
        self.btn_remove_kwin.clicked.connect(self._remove_kwin_rules)
        kwin_btn_bar.addWidget(self.btn_remove_kwin)
        kwin_btn_bar.addStretch()

        kwin_layout.addLayout(kwin_btn_bar)
        layout.addWidget(kwin_box)

        # 4. Tùy biến tối ưu Waydroid (Tweaks)
        tweaks_box = QtWidgets.QGroupBox("4. Tùy biến tối ưu Waydroid (Tweaks)")
        tweaks_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        tweaks_grid = QtWidgets.QGridLayout(tweaks_box)

        self.chk_suspend = QtWidgets.QCheckBox("Chống tự ngủ (Disable Suspend - Tránh đơ app ngầm)")
        tweaks_grid.addWidget(self.chk_suspend, 0, 0)

        self.chk_cursor = QtWidgets.QCheckBox("Sửa trỏ chuột giật (Cursor on Subsurface)")
        tweaks_grid.addWidget(self.chk_cursor, 0, 1)

        self.chk_fake_touch = QtWidgets.QCheckBox("Giả lập cảm ứng chuột (Fake Touch - Cho game/app)")
        tweaks_grid.addWidget(self.chk_fake_touch, 1, 0)

        self.chk_invert_colors = QtWidgets.QCheckBox("Đảo ngược màu hiển thị (Khắc phục lỗi màu một số GPU)")
        tweaks_grid.addWidget(self.chk_invert_colors, 1, 1)

        layout.addWidget(tweaks_box)

        # 5. Thanh nút Lưu tổng thể ở cuối
        bottom_bar = QtWidgets.QHBoxLayout()
        self.btn_save_all = QtWidgets.QPushButton("💾 Lưu tất cả Cấu hình")
        self.btn_save_all.setMinimumHeight(38)
        self.btn_save_all.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 18px;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        self.btn_save_all.clicked.connect(self.save_and_apply)
        bottom_bar.addWidget(self.btn_save_all)
        bottom_bar.addStretch()
        layout.addLayout(bottom_bar)

        scroll.setWidget(container)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def load_from_config(self):
        """Nạp dữ liệu từ ConfigManager vào các trường giao diện."""
        # Chế độ
        mode = self.config_mgr.get("display.mode", "multi_windows")
        if mode == "multi_windows":
            self.rb_multi.setChecked(True)
        else:
            self.rb_full.setChecked(True)

        # Presets
        preset = self.config_mgr.get("display.preset", "phone_hd")
        idx = self.cbo_presets.findData(preset)
        if idx >= 0:
            self.cbo_presets.setCurrentIndex(idx)

        self.spn_width.setValue(self.config_mgr.get("display.width", 720))
        self.spn_height.setValue(self.config_mgr.get("display.height", 1280))
        self.spn_dpi.setValue(self.config_mgr.get("display.dpi", 260))

        # KWin Rules
        self.chk_above.setChecked(self.config_mgr.get("kwin_rules.above", False))
        self.chk_noborder.setChecked(self.config_mgr.get("kwin_rules.noborder", False))
        self.chk_fixed_size.setChecked(self.config_mgr.get("kwin_rules.fixed_size", False))
        self.chk_remember_pos.setChecked(self.config_mgr.get("kwin_rules.remember_position", True))
        self.chk_pin_desktops.setChecked(self.config_mgr.get("kwin_rules.pin_all_desktops", False))

        target = self.config_mgr.get("kwin_rules.target", "all")
        t_idx = self.cbo_kwin_target.findData(target)
        if t_idx >= 0:
            self.cbo_kwin_target.setCurrentIndex(t_idx)

        op_act = self.config_mgr.get("kwin_rules.opacity_active", 100)
        self.sld_opacity_act.setValue(op_act)
        self.lbl_opacity_act_val.setText(f"{op_act}%")

        op_inact = self.config_mgr.get("kwin_rules.opacity_inactive", 100)
        self.sld_opacity_inact.setValue(op_inact)
        self.lbl_opacity_inact_val.setText(f"{op_inact}%")

        # Tweaks
        self.chk_suspend.setChecked(self.config_mgr.get("tweaks.disable_suspend", True))
        self.chk_cursor.setChecked(self.config_mgr.get("tweaks.cursor_subsurface", True))
        self.chk_fake_touch.setChecked(self.config_mgr.get("tweaks.fake_touch", False))
        self.chk_invert_colors.setChecked(self.config_mgr.get("tweaks.invert_colors", False))

    def _on_mode_toggled(self):
        mode = "multi_windows" if self.rb_multi.isChecked() else "full_ui"
        self.config_mgr.set("display.mode", mode)

    def _on_preset_changed(self):
        preset_key = self.cbo_presets.currentData()
        if preset_key in RESOLUTION_PRESETS:
            p = RESOLUTION_PRESETS[preset_key]
            self.lbl_preset_desc.setText(p.get("description", ""))
            if preset_key != "custom":
                self.spn_width.blockSignals(True)
                self.spn_height.blockSignals(True)
                self.spn_dpi.blockSignals(True)
                self.spn_width.setValue(p["width"])
                self.spn_height.setValue(p["height"])
                self.spn_dpi.setValue(p["dpi"])
                self.spn_width.blockSignals(False)
                self.spn_height.blockSignals(False)
                self.spn_dpi.blockSignals(False)

    def _on_custom_dim_changed(self):
        # Chuyển preset sang 'custom' nếu người dùng tự sửa kích thước
        curr_key = self.cbo_presets.currentData()
        if curr_key in RESOLUTION_PRESETS and curr_key != "custom":
            p = RESOLUTION_PRESETS[curr_key]
            if (
                self.spn_width.value() != p["width"] or
                self.spn_height.value() != p["height"] or
                self.spn_dpi.value() != p["dpi"]
            ):
                idx = self.cbo_presets.findData("custom")
                if idx >= 0:
                    self.cbo_presets.blockSignals(True)
                    self.cbo_presets.setCurrentIndex(idx)
                    self.cbo_presets.blockSignals(False)

    def _rotate_dimensions(self):
        w = self.spn_width.value()
        h = self.spn_height.value()
        self.spn_width.setValue(h)
        self.spn_height.setValue(w)

    def _apply_kwin_rules_now(self):
        self._collect_and_save_data()
        rule_opts = self.config_mgr.get("kwin_rules", {})
        w = self.spn_width.value()
        h = self.spn_height.value()

        ok = self.kwin_mgr.apply_rules(rule_opts, width=w, height=h)
        if ok:
            QtWidgets.QMessageBox.information(
                self,
                "Thành công",
                "Đã áp dụng KWin Rules vào hệ thống KDE Plasma!\nKWin đã tự động nạp lại cấu hình."
            )
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể ghi tệp kwinrulesrc.")

    def _remove_kwin_rules(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn xóa bỏ các quy tắc cửa sổ KWin của Waydroid?\n"
            "Cửa sổ sẽ trở về hành vi mặc định của KDE.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.kwin_mgr.remove_rules()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã gỡ bỏ KWin Rules của Waydroid.")

    def _collect_and_save_data(self):
        mode = "multi_windows" if self.rb_multi.isChecked() else "full_ui"
        self.config_mgr.set("display.mode", mode)
        self.config_mgr.set("display.preset", self.cbo_presets.currentData())
        self.config_mgr.set("display.width", self.spn_width.value())
        self.config_mgr.set("display.height", self.spn_height.value())
        self.config_mgr.set("display.dpi", self.spn_dpi.value())

        self.config_mgr.set("kwin_rules.above", self.chk_above.isChecked())
        self.config_mgr.set("kwin_rules.noborder", self.chk_noborder.isChecked())
        self.config_mgr.set("kwin_rules.fixed_size", self.chk_fixed_size.isChecked())
        self.config_mgr.set("kwin_rules.remember_position", self.chk_remember_pos.isChecked())
        self.config_mgr.set("kwin_rules.pin_all_desktops", self.chk_pin_desktops.isChecked())
        self.config_mgr.set("kwin_rules.target", self.cbo_kwin_target.currentData())
        self.config_mgr.set("kwin_rules.opacity_active", self.sld_opacity_act.value())
        self.config_mgr.set("kwin_rules.opacity_inactive", self.sld_opacity_inact.value())

        self.config_mgr.set("tweaks.disable_suspend", self.chk_suspend.isChecked())
        self.config_mgr.set("tweaks.cursor_subsurface", self.chk_cursor.isChecked())
        self.config_mgr.set("tweaks.fake_touch", self.chk_fake_touch.isChecked())
        self.config_mgr.set("tweaks.invert_colors", self.chk_invert_colors.isChecked())

        self.config_mgr.save()

    def save_and_apply(self):
        """Lưu toàn bộ cấu hình, áp dụng KWin Rules và đồng bộ props nếu Waydroid đang chạy."""
        self._collect_and_save_data()

        # Áp dụng KWin rules
        rule_opts = self.config_mgr.get("kwin_rules", {})
        w = self.spn_width.value()
        h = self.spn_height.value()
        self.kwin_mgr.apply_rules(rule_opts, width=w, height=h)

        # Nếu Waydroid đang chạy, áp dụng ngay các props và tweaks
        status = WaydroidService.get_status()
        applied_msgs = []
        if status["session_status"] == "RUNNING":
            mw_val = "true" if self.rb_multi.isChecked() else "false"
            WaydroidService.set_prop("persist.waydroid.multi_windows", mw_val)
            if w > 0 and h > 0:
                WaydroidService.set_prop("persist.waydroid.width", str(w))
                WaydroidService.set_prop("persist.waydroid.height", str(h))
            if self.spn_dpi.value() > 0:
                WaydroidService.set_prop("persist.waydroid.dpi", str(self.spn_dpi.value()))

            tweaks = self.config_mgr.get("tweaks", {})
            applied_msgs = WaydroidService.apply_tweaks(tweaks)

        msg = "Đã lưu cấu hình và nạp KWin Rules thành công!"
        if status["session_status"] == "RUNNING":
            msg += "\n\nĐã đồng bộ các thuộc tính vào phiên Waydroid đang chạy."
            if applied_msgs:
                msg += "\n" + "\n".join(applied_msgs)
            msg += "\n(Lưu ý: Một số thay đổi kích thước/chế độ có thể cần Khởi động lại phiên để hiển thị đầy đủ)."
        else:
            msg += "\n\nCấu hình sẽ tự động áp dụng khi bạn khởi động phiên Waydroid lần tới."

        QtWidgets.QMessageBox.information(self, "Lưu cấu hình", msg)
