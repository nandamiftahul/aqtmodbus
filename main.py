#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from communication import Communication
import time

def main():
    print("=== AQT560 TCP Client Test ===")

    com = Communication("192.168.0.7", 9001)

    print("\n>>> Connecting TCP...")
    if not com.connect_tcp():
        print("❌ Gagal konek ke TCP Server.")
        return

    if not com.isOpen():
        print("❌ TCP tidak aktif.")
        return

    print("✅ TCP Connected.")
    print("-----------------------------")

    frame_hex = "010300980002"
    try:
        print(f"Kirim frame: {frame_hex}")
        value = com.readParameter(frame_hex)
        print(f"Hasil respon register: {value}")
    except Exception as e:
        print("Terjadi error saat kirim/baca:", e)

    time.sleep(0.5)
    com.disconnect()
    print("Selesai.\n")


if __name__ == "__main__":
    main()
