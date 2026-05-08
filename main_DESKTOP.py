import sys
import os
import subprocess
import json
import threading
import time
import psutil

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QTabWidget, QHBoxLayout, QLineEdit, QLabel
)
from PySide6.QtCore import QTimer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

STATUS = {
    "ONLINE": "🟢",
    "OFFLINE": "🔴",
    "STARTING": "🟡"
}


# =========================
# SERVER TAB
# =========================
class ServerTab(QWidget):
    def __init__(self, name, config):
        super().__init__()

        self.name = name
        self.config = config

        self.process = None
        self.state = "OFFLINE"
        self._starting = False

        layout = QVBoxLayout()

        self.stats = QLabel("CPU: 0.0% | RAM: 0 MB")

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter command...")
        self.input.returnPressed.connect(self.send_command)

        btns = QHBoxLayout()

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.restart_btn = QPushButton("Restart")

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.restart_btn.clicked.connect(self.restart)

        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.restart_btn)

        layout.addLayout(btns)
        layout.addWidget(self.stats)
        layout.addWidget(self.console)
        layout.addWidget(self.input)

        self.setLayout(layout)

    # =========================
    # START (LOCKED)
    # =========================
    def start(self):
        if self._starting or self.is_alive():
            return

        self._starting = True
        self.state = "STARTING"

        threading.Thread(target=self._start_process, daemon=True).start()

    def _start_process(self):
        try:
            folder = self.config["folder"]
            jar = self.config["jar"]

            cwd = BASE_DIR if folder == "ROOT" else os.path.join(BASE_DIR, folder)

            self.process = subprocess.Popen(
                ["java", "-Xmx2G", "-Xms1G", "-jar", jar, "nogui"],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self.state = "ONLINE"

            threading.Thread(target=self._read_console, daemon=True).start()

        except Exception as e:
            print(f"[ERROR] {self.name}: {e}")
            self.state = "OFFLINE"

        self._starting = False

    # =========================
    # STOP
    # =========================
    def stop(self):
        if not self.process:
            self.state = "OFFLINE"
            return

        try:
            self.send_raw("stop")
            time.sleep(1)
            self.process.terminate()
        except:
            pass

        self.process = None
        self.state = "OFFLINE"

    # =========================
    # RESTART
    # =========================
    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()

    # =========================
    # COMMANDS
    # =========================
    def send_command(self):
        cmd = self.input.text().strip()
        if not cmd:
            return

        self.input.clear()
        self.send_raw(cmd)

    def send_raw(self, cmd):
        try:
            if self.process and self.process.stdin:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
        except:
            pass

    # =========================
    # ALIVE CHECK
    # =========================
    def is_alive(self):
        return self.process and self.process.poll() is None

    # =========================
    # CONSOLE
    # =========================
    def _read_console(self):
        try:
            for line in self.process.stdout:
                if line:
                    self.console.append(line.strip())
        except:
            pass

    # =========================
    # FIXED STATS (CPU + RAM)
    # =========================
    def update_stats(self):
        if not self.is_alive():
            self.stats.setText("CPU: 0.0% | RAM: 0 MB")
            return

        try:
            p = psutil.Process(self.process.pid)

            cpu_raw = p.cpu_percent(interval=None)
            cores = psutil.cpu_count(logical=True) or 1

            cpu = (cpu_raw / cores) * 100
            cpu = max(0.0, min(cpu, 100.0))

            mem = p.memory_info().rss / 1024 / 1024

            self.stats.setText(f"CPU: {cpu:.1f}% | RAM: {mem:.1f} MB")

        except:
            self.stats.setText("CPU: 0.0% | RAM: 0 MB")


# =========================
# MAIN PANEL
# =========================
class MainPanel(QWidget):
    def __init__(self):
        super().__init__()

        with open(os.path.join(BASE_DIR, "config.json")) as f:
            self.config = json.load(f)

        self.setWindowTitle(self.config["panel_name"])
        self.setGeometry(200, 200, 1000, 700)

        self.tabs = QTabWidget()
        self.servers = {}

        layout = QVBoxLayout()

        self.start_all = QPushButton("Start All")
        self.stop_all = QPushButton("Stop All")

        self.start_all.clicked.connect(self.start_all_servers)
        self.stop_all.clicked.connect(self.stop_all_servers)

        layout.addWidget(self.start_all)
        layout.addWidget(self.stop_all)
        layout.addWidget(self.tabs)

        self.setLayout(layout)

        # servers
        for name, cfg in sorted(self.config["servers"].items()):
            self.add_server(name, cfg)

        self.add_server("Proxy", {"folder": "ROOT", "jar": "velocity.jar"}, index=0)

        # refresh loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(300)

        self._start_lock = False

    # =========================
    # ADD SERVER
    # =========================
    def add_server(self, name, cfg, index=None):
        s = ServerTab(name, cfg)
        self.servers[name] = s

        if index is None:
            self.tabs.addTab(s, f"🔴 {name}")
        else:
            self.tabs.insertTab(index, s, f"🔴 {name}")

    # =========================
    # START ALL (SAFE QUEUE)
    # =========================
    def start_all_servers(self):
        if self._start_lock:
            return

        self._start_lock = True
        servers = list(self.servers.values())

        def start_next(i=0):
            if i >= len(servers):
                self._start_lock = False
                return

            s = servers[i]

            if not s.is_alive():
                s.start()

            QTimer.singleShot(2500, lambda: start_next(i + 1))

        start_next()

    # =========================
    # STOP ALL
    # =========================
    def stop_all_servers(self):
        for s in self.servers.values():
            s.stop()

    # =========================
    # REFRESH UI
    # =========================
    def refresh(self):
        for name, s in self.servers.items():
            idx = self.tabs.indexOf(s)
            if idx != -1:
                self.tabs.setTabText(idx, f"{STATUS[s.state]} {name}")

            s.update_stats()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainPanel()
    w.show()
    sys.exit(app.exec())
