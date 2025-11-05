#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
from contextlib import redirect_stdout
from flask import Flask, render_template, request, jsonify
from communication import Communication

app = Flask(__name__)
com = Communication()

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

@app.route("/")
def index():
    return render_template("index.html", commands=COMMANDS.keys())

@app.route("/connect", methods=["POST"])
def connect():
    ip = request.form["ip"].strip()
    port = int(request.form["port"].strip())
    ok = com.connect_tcp(ip, port)
    return jsonify({"success": ok})

@app.route("/disconnect", methods=["POST"])
def disconnect():
    com.disconnect()
    return jsonify({"success": True})

@app.route("/send", methods=["POST"])
def send():
    cmd_label = request.form["command"]
    data_hex = COMMANDS[cmd_label]
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            value = com.readParameter(data_hex)
        except Exception as e:
            print(f"[Error] {e}")
            value = None
    log_output = buf.getvalue()
    return jsonify({"log": log_output, "value": value})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
