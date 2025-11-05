#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, io
from contextlib import redirect_stdout
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit, QVBoxLayout, QStatusBar
)

# 🔗 import class kamu
from communication import Communication

# ================== daftar command ==================
COMMANDS = {
    "NO2 (ppb, LC)": "010300000001",
    "SO2 (ppb, LC)": "010300010001",
    "CO (ppb, LC)": "010300020001",
    "H2S (ppb, LC)": "010300040001",
    "O3 (ppb, LC)": "010300050001",
    "NO (ppb, LC)": "010300060001",
    "PM2.5 (0.1 µg/m3, LC)": "010300080001",
    "PM10 (0.1 µg/m3, LC)": "010300090001",
    "Temperature (0.1 °C/°F)": "0103000A0001",
    "Humidity (0.1 %RH)": "0103000B0001",
    "Pressure (0.1 hPa)": "0103000C0001",
    "Device health (%)": "0103001F0001",
    "AQI": "010300290001",
    "AQI criteria": "0103002A0001",
    "PM1 (0.1 µg/m3, LC)": "010300370001",
    "Stabilization flag": "010300330001",
    "Temp invalid flag": "010300340001",
    "Humidity compensation": "010300360001",
    "LPC data state": "010300760001",
    "LPC fog present": "0103007B0001",
    "Fog flag PM1": "0103007C0001",
    "Fog flag PM2.5": "0103007D0001",
    "Fog flag PM10": "0103007E0001",
    "LPC interval (min)": "0103007F0001",
    "Uptime (s, 32-bit)": "010300980002",
    "AQT serial (8-char)": "010300B40004",
    "HMP110 serial (8-char)": "010300B80004",
    "LPC serial (8-char)": "010300BC0004",
}

# ================== GUI ==================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AQT560 TCP Modbus Checker")
        self.setMinimumSize(700, 500)
        self.com = Communication()
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        # --- koneksi group
        g_conn = QGroupBox("Koneksi TCP")
        grid = QGridLayout(g_conn)
        self.ed_ip = QLineEdit("192.168.0.7")
        self.ed_port = QLineEdit("9001")
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setEnabled(False)
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_disconnect.clicked.connect(self.on_disconnect)

        grid.addWidget(QLabel("IP:"), 0, 0)
        grid.addWidget(self.ed_ip, 0, 1)
        grid.addWidget(QLabel("Port:"), 0, 2)
        grid.addWidget(self.ed_port, 0, 3)
        grid.addWidget(self.btn_connect, 1, 0, 1, 2)
        grid.addWidget(self.btn_disconnect, 1, 2, 1, 2)
        layout.addWidget(g_conn)

        # --- perintah
        g_cmd = QGroupBox("Perintah")
        vcmd = QVBoxLayout(g_cmd)
        self.cb_cmd = QComboBox()
        for label in COMMANDS.keys():
            self.cb_cmd.addItem(label)
        self.btn_send = QPushButton("Send Command")
        self.btn_send.clicked.connect(self.on_send)
        self.btn_send.setEnabled(False)
        vcmd.addWidget(self.cb_cmd)
        vcmd.addWidget(self.btn_send)
        layout.addWidget(g_cmd)

        # --- hasil
        g_out = QGroupBox("Output")
        vout = QVBoxLayout(g_out)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.lbl_value = QLabel("Value: -")
        self.lbl_value.setStyleSheet("font-size:16px;font-weight:600;color:#00e676;")
        vout.addWidget(self.txt_log)
        vout.addWidget(self.lbl_value)
        layout.addWidget(g_out)

        # status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    # ------------------- actions -------------------
    def on_connect(self):
        ip = self.ed_ip.text().strip()
        port = int(self.ed_port.text().strip())
        ok = self.com.connect_tcp(ip, port)
        if ok:
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.btn_send.setEnabled(True)
            self.status.showMessage(f"Connected to {ip}:{port}")
        else:
            self.status.showMessage("Failed to connect")

    def on_disconnect(self):
        self.com.disconnect()
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_send.setEnabled(False)
        self.status.showMessage("Disconnected")

    def on_send(self):
        if not self.com.isOpen():
            self.status.showMessage("Not connected")
            return

        cmd_label = self.cb_cmd.currentText()
        data_hex = COMMANDS[cmd_label]

        # tangkap print output dari readParameter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                value = self.com.readParameter(data_hex)
            except Exception as e:
                print(f"[Error] {e}")
                value = None
        log_output = buf.getvalue()

        # tampilkan log RX/TX dari stdout
        self.txt_log.setPlainText(log_output)
        if value is not None:
            self.lbl_value.setText(f"Value: {value}")
        else:
            self.lbl_value.setText("Value: -")

        self.status.showMessage(f"Command sent: {cmd_label}")

    def closeEvent(self, e):
        self.com.disconnect()
        e.accept()


# ================== run ==================
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
