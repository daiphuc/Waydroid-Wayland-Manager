import os
import re
import glob
import time
import signal
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

LOG_FILE = Path("/var/lib/waydroid/waydroid.log")


class WaydroidService:
    """Quản lý các thao tác bật/tắt, dọn dẹp và kiểm tra trạng thái Waydroid."""

    @staticmethod
    def is_waydroid_installed() -> bool:
        return shutil.which("waydroid") is not None

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """
        Lấy trạng thái toàn diện của Waydroid:
        - session_status: 'RUNNING', 'STOPPED', 'STARTING', 'UNKNOWN'
        - container_active: bool
        - container_status: 'active', 'inactive', 'failed', 'unknown'
        - processes: danh sách PID và thông tin các tiến trình waydroid đang chạy
        - ip_address: IP mạng của waydroid (nếu có)
        - multi_windows: bool
        - width, height, dpi: int
        """
        status: Dict[str, Any] = {
            "session_status": "STOPPED",
            "container_active": False,
            "container_status": "unknown",
            "processes": [],
            "process_count": 0,
            "ip_address": "",
            "multi_windows": True,
            "width": 0,
            "height": 0,
            "dpi": 0,
            "vendor_type": "MAINLINE",
        }

        if not WaydroidService.is_waydroid_installed():
            status["session_status"] = "NOT_INSTALLED"
            return status

        # 1. Kiểm tra session qua 'waydroid status'
        try:
            res = subprocess.run(
                ["waydroid", "status"],
                capture_output=True,
                text=True,
                timeout=4
            )
            out = res.stdout + res.stderr
            for line in out.splitlines():
                if "Session:" in line:
                    val = line.split(":", 1)[1].strip()
                    status["session_status"] = val
                elif "Vendor type:" in line:
                    status["vendor_type"] = line.split(":", 1)[1].strip()
        except Exception:
            pass

        # 2. Kiểm tra container service qua systemctl
        try:
            res = subprocess.run(
                ["systemctl", "is-active", "waydroid-container.service"],
                capture_output=True,
                text=True,
                timeout=2
            )
            c_status = res.stdout.strip()
            status["container_status"] = c_status
            status["container_active"] = (c_status == "active")
        except Exception:
            # Fallback nếu không có systemctl (ví dụ trong container)
            pass

        # Nếu container không active theo systemctl, kiểm tra xem có tiến trình container nào chạy không
        procs = WaydroidService.get_running_processes()
        status["processes"] = procs
        status["process_count"] = len(procs)
        if not status["container_active"]:
            for p in procs:
                if "container" in p["cmd"] or "lxc-start" in p["cmd"]:
                    status["container_active"] = True
                    status["container_status"] = "active (pid)"
                    break

        # Nếu có tiến trình session đang chạy nhưng waydroid status báo STOPPED
        has_session_proc = any("session" in p["cmd"] for p in procs)
        if has_session_proc and status["session_status"] == "STOPPED":
            status["session_status"] = "STARTING / BUSY"

        # 3. Kiểm tra IP của bridge waydroid0
        try:
            res = subprocess.run(
                ["ip", "-4", "addr", "show", "waydroid0"],
                capture_output=True,
                text=True,
                timeout=2
            )
            match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", res.stdout)
            if match:
                status["ip_address"] = match.group(1)
        except Exception:
            pass

        # 4. Đọc props nếu session đang RUNNING
        if status["session_status"] == "RUNNING":
            try:
                mw = WaydroidService.get_prop("persist.waydroid.multi_windows")
                status["multi_windows"] = (mw.lower() == "true")
                w = WaydroidService.get_prop("persist.waydroid.width")
                h = WaydroidService.get_prop("persist.waydroid.height")
                d = WaydroidService.get_prop("persist.waydroid.dpi")
                status["width"] = int(w) if w.isdigit() else 0
                status["height"] = int(h) if h.isdigit() else 0
                status["dpi"] = int(d) if d.isdigit() else 0
            except Exception:
                pass

        return status

    @staticmethod
    def get_running_processes() -> List[Dict[str, Any]]:
        """Lấy danh sách các tiến trình liên quan đến Waydroid."""
        procs = []
        try:
            res = subprocess.run(
                ["ps", "-eo", "pid,user,comm,args", "--sort=-%mem"],
                capture_output=True,
                text=True,
                timeout=3
            )
            for line in res.stdout.splitlines()[1:]:
                parts = line.strip().split(None, 3)
                if len(parts) >= 4:
                    pid, user, comm, cmd = parts[0], parts[1], parts[2], parts[3]
                    if "waydroid" in cmd.lower() or "anbox" in cmd.lower() or ("lxc" in comm and "waydroid" in cmd):
                        # Bỏ qua chính tiến trình hiện tại, ps, grep và waydroid_kde
                        if int(pid) == os.getpid() or "waydroid_kde" in cmd or "ps -eo" in cmd or "grep" in cmd:
                            continue
                        procs.append({
                            "pid": int(pid),
                            "user": user,
                            "comm": comm,
                            "cmd": cmd
                        })
        except Exception:
            pass
        return procs

    @staticmethod
    def get_prop(prop_name: str) -> str:
        """Đọc giá trị prop từ Waydroid."""
        try:
            res = subprocess.run(
                ["waydroid", "prop", "get", prop_name],
                capture_output=True,
                text=True,
                timeout=3
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def set_prop(prop_name: str, value: str) -> Tuple[bool, str]:
        """Ghi giá trị prop vào Waydroid."""
        try:
            res = subprocess.run(
                ["waydroid", "prop", "set", prop_name, str(value)],
                capture_output=True,
                text=True,
                timeout=4
            )
            if res.returncode == 0:
                return True, "Thành công"
            return False, res.stderr.strip() or res.stdout.strip()
        except Exception as e:
            return False, str(e)

    @staticmethod
    def ensure_container_running() -> Tuple[bool, str]:
        """Đảm bảo dịch vụ container waydroid đang chạy."""
        try:
            res = subprocess.run(
                ["systemctl", "is-active", "waydroid-container.service"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if res.stdout.strip() == "active":
                return True, "Container đã chạy"

            # Nếu chưa chạy, dùng pkexec để bật
            cmd = ["pkexec", "systemctl", "start", "waydroid-container.service"]
            start_res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if start_res.returncode == 0:
                time.sleep(1.5)
                return True, "Đã khởi động Container thành công"
            return False, f"Không thể bật container: {start_res.stderr.strip()}"
        except Exception as e:
            return False, f"Lỗi khởi động container: {e}"

    @staticmethod
    def start_session(
        mode: str = "multi_windows",
        width: int = 0,
        height: int = 0,
        dpi: int = 0,
        auto_container: bool = True
    ) -> Tuple[bool, str]:
        """
        Bật Waydroid:
        - mode: 'multi_windows' hoặc 'full_ui'
        - width, height, dpi: cấu hình độ phân giải
        """
        if auto_container:
            ok, msg = WaydroidService.ensure_container_running()
            if not ok:
                return False, f"Lỗi khởi động container: {msg}"

        # Nếu cần chạy Full UI trực tiếp
        if mode == "full_ui":
            try:
                # Thiết lập multi_windows = false
                subprocess.run(["waydroid", "prop", "set", "persist.waydroid.multi_windows", "false"], timeout=3)
                if width > 0 and height > 0:
                    subprocess.run(["waydroid", "prop", "set", "persist.waydroid.width", str(width)], timeout=3)
                    subprocess.run(["waydroid", "prop", "set", "persist.waydroid.height", str(height)], timeout=3)
                if dpi > 0:
                    subprocess.run(["waydroid", "prop", "set", "persist.waydroid.dpi", str(dpi)], timeout=3)

                # Chạy waydroid show-full-ui trong tiến trình nền
                subprocess.Popen(
                    ["waydroid", "show-full-ui"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return True, "Đã khởi chạy Waydroid Full UI"
            except Exception as e:
                return False, f"Lỗi khi chạy Full UI: {e}"
        else:
            # Multi-window mode
            try:
                subprocess.run(["waydroid", "prop", "set", "persist.waydroid.multi_windows", "true"], timeout=3)
                if width > 0 and height > 0:
                    subprocess.run(["waydroid", "prop", "set", "persist.waydroid.width", str(width)], timeout=3)
                    subprocess.run(["waydroid", "prop", "set", "persist.waydroid.height", str(height)], timeout=3)
                if dpi > 0:
                    subprocess.run(["waydroid", "prop", "set", "persist.waydroid.dpi", str(dpi)], timeout=3)

                # Khởi động session ngầm
                subprocess.Popen(
                    ["waydroid", "session", "start"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return True, "Đã khởi động Waydroid Session (Multi-window)"
            except Exception as e:
                return False, f"Lỗi khi khởi động session: {e}"

    @staticmethod
    def stop_session() -> Tuple[bool, str]:
        """Tắt nhẹ nhàng phiên làm việc Waydroid."""
        try:
            res = subprocess.run(["waydroid", "session", "stop"], capture_output=True, text=True, timeout=6)
            if res.returncode == 0:
                return True, "Đã dừng Waydroid Session"
            return False, res.stderr.strip() or res.stdout.strip()
        except Exception as e:
            return False, f"Lỗi dừng session: {e}"

    @staticmethod
    def stop_container() -> Tuple[bool, str]:
        """Dừng hoàn toàn dịch vụ container để giải phóng toàn bộ RAM/CPU."""
        try:
            cmd = ["pkexec", "systemctl", "stop", "waydroid-container.service"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return True, "Đã dừng Container và giải phóng tài nguyên"
            return False, res.stderr.strip()
        except Exception as e:
            return False, str(e)

    @staticmethod
    def cleanup_session(deep: bool = False) -> Dict[str, Any]:
        """
        Dọn dẹp triệt để session Waydroid:
        1. Gọi 'waydroid session stop'
        2. Diệt các tiến trình người dùng treo (waydroid session, show-full-ui, python3.*waydroid)
        3. Dọn sạch socket và lockfile rác trong /run/user/UID và /tmp
        4. (Deep mode): Khởi động lại dịch vụ container cấp root
        """
        report: Dict[str, Any] = {
            "success": True,
            "killed_pids": [],
            "removed_files": [],
            "container_restarted": False,
            "messages": []
        }

        # Bước 1: Thử dừng bình thường trước
        try:
            subprocess.run(["waydroid", "session", "stop"], capture_output=True, timeout=3)
            report["messages"].append("Đã gửi tín hiệu dừng session thông thường.")
        except Exception:
            pass

        time.sleep(0.5)

        # Bước 2: Quét và diệt các tiến trình user waydroid còn sót lại
        curr_uid = os.getuid()
        procs = WaydroidService.get_running_processes()
        for p in procs:
            pid = p["pid"]
            cmd = p["cmd"]
            # Chỉ tự động kill các tiến trình thuộc user hiện tại
            # (các tiến trình container root sẽ xử lý ở deep cleanup)
            if p["user"] == str(curr_uid) or p["user"] == os.getenv("USER", ""):
                if "waydroid" in cmd or "lxc" in cmd:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        report["killed_pids"].append(pid)
                    except Exception:
                        pass

        if report["killed_pids"]:
            time.sleep(0.6)
            # Kiểm tra nếu còn sống thì SIGKILL
            for pid in report["killed_pids"]:
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
            report["messages"].append(f"Đã diệt {len(report['killed_pids'])} tiến trình treo.")

        # Bước 3: Dọn dẹp các socket, binder locks và tệp tạm treo
        uid_str = str(curr_uid)
        potential_locks = [
            f"/run/user/{uid_str}/waydroid*",
            f"/run/user/{uid_str}/waydroid.sock",
            f"/run/user/{uid_str}/waydroid-session*",
            "/tmp/waydroid*",
            f"/run/user/{uid_str}/dbus-waydroid*"
        ]
        for pattern in potential_locks:
            for filepath in glob.glob(pattern):
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.remove(filepath)
                        report["removed_files"].append(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath, ignore_errors=True)
                        report["removed_files"].append(filepath)
                except Exception:
                    pass

        if report["removed_files"]:
            report["messages"].append(f"Đã dọn dẹp {len(report['removed_files'])} file lock/socket tồn đọng.")

        # Bước 4: Dọn dẹp sâu cấp Admin (Deep Cleanup) nếu được yêu cầu
        if deep:
            try:
                # Khởi động lại waydroid-container service
                cmd = ["pkexec", "systemctl", "restart", "waydroid-container.service"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if res.returncode == 0:
                    report["container_restarted"] = True
                    report["messages"].append("Đã khởi động lại dịch vụ container ở mức hệ thống.")
                else:
                    report["messages"].append(f"Cảnh báo: Không thể restart container service: {res.stderr.strip()}")
            except Exception as e:
                report["messages"].append(f"Lỗi deep clean: {e}")

        # Kiểm tra trạng thái cuối cùng
        time.sleep(0.5)
        final_status = WaydroidService.get_status()
        report["final_session_status"] = final_status["session_status"]
        report["messages"].append(f"Trạng thái hiện tại: Session = {final_status['session_status']}")
        return report

    @staticmethod
    def get_log_lines(max_lines: int = 150) -> str:
        """Đọc các dòng log cuối cùng từ waydroid.log."""
        if not LOG_FILE.exists():
            return "Chưa tìm thấy tệp log tại " + str(LOG_FILE)
        try:
            res = subprocess.run(
                ["tail", "-n", str(max_lines), str(LOG_FILE)],
                capture_output=True,
                text=True,
                timeout=3
            )
            return res.stdout
        except Exception as e:
            return f"Không thể đọc log: {e}"

    @staticmethod
    def apply_tweaks(tweaks: Dict[str, Any]) -> List[str]:
        """Áp dụng các tùy biến tối ưu Waydroid."""
        msgs = []
        # Chống suspend
        if tweaks.get("disable_suspend"):
            ok, msg = WaydroidService.set_prop("persist.waydroid.suspend", "false")
            msgs.append(f"Chống ngủ (Disable Suspend): {'Bật' if ok else 'Lỗi: ' + msg}")

        # Cursor trên subsurface
        if tweaks.get("cursor_subsurface"):
            ok, msg = WaydroidService.set_prop("persist.waydroid.cursor_on_subsurface", "true")
            msgs.append(f"Sửa giật trỏ chuột (Cursor on Subsurface): {'Bật' if ok else 'Lỗi: ' + msg}")

        # Fake touch
        if "fake_touch" in tweaks:
            val = "true" if tweaks["fake_touch"] else "false"
            ok, msg = WaydroidService.set_prop("persist.waydroid.fake_touch", val)
            msgs.append(f"Giả lập cảm ứng chuột: {val}")

        # Invert colors
        if "invert_colors" in tweaks:
            val = "true" if tweaks["invert_colors"] else "false"
            ok, msg = WaydroidService.set_prop("persist.waydroid.invert_colors", val)
            msgs.append(f"Đảo màu hiển thị: {val}")

        return msgs
