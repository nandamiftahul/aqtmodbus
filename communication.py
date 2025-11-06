#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from crccheck.crc import Crc16Modbus
from time import sleep
from datetime import datetime


class Communication:
    """
    Communication class supporting only TCP Client
    (default host 192.168.0.7 port 9001)
    """

    def __init__(self, host="198.168.0.7", port=9001, timeout=1.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.mode = "tcp"

    # =========================
    # TCP CONNECTION
    # =========================
    def connect_tcp(self, host=None, port=None):
        """Buka koneksi TCP Client"""
        self.host = host or self.host
        self.port = port or self.port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            print(f"[TCP] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[TCP] Connection failed: {e}")
            self.sock = None
            return False

    def disconnect(self):
        """Tutup koneksi TCP"""
        if self.sock:
            try:
                self.sock.close()
                print(f"[TCP] Disconnected from {self.host}:{self.port}")
            except Exception as e:
                print(f"[TCP] Close error: {e}")
            self.sock = None

    def isOpen(self):
        """Cek koneksi aktif"""
        return self.sock is not None

    # =========================
    # UTILITIES
    # =========================
    def swab_hex(self, obj_str):
        """Tukar endian 16-bit (AB -> BA)"""
        return obj_str[2:], obj_str[:2]

    def checksum_chr(self, obj_str):
        """Hitung CRC16(Modbus)"""
        msg = obj_str.encode("utf-8")
        crc = Crc16Modbus().process(msg).finalhex()
        crc_swab = self.swab_hex(crc)
        chr1 = chr(int(crc_swab[0], 16))
        chr2 = chr(int(crc_swab[1], 16))
        hex1 = format(ord(chr1), "x").zfill(2)
        hex2 = format(ord(chr2), "x").zfill(2)
        return [chr1, chr2, hex1, hex2]

    def _recv_exact(self, n: int) -> bytes:
        """Baca tepat n byte dari socket TCP."""
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise RuntimeError("Socket closed while receiving")
            buf.extend(chunk)
        return bytes(buf)

    

    # =========================
    # READ PARAMETER
    # =========================
    def readParameter(self, data_hex):
        """
        Kirim frame Modbus (data_hex tanpa CRC)
        Return:
            - 16-bit: int
            - 32-bit: int
            - 8-char: str
            - lainnya: bytes (raw)
        """
        import time
        from crccheck.crc import Crc16Modbus
    
        if not self.sock:
            print("[Error] Tidak ada koneksi TCP aktif.")
            return None
    
        # --- Hitung CRC16 dari data_hex langsung (tanpa decode/encode) ---
        data_bytes = bytes.fromhex(data_hex)
        crc_val = Crc16Modbus.calc(data_bytes)
        crc_lo = crc_val & 0xFF
        crc_hi = (crc_val >> 8) & 0xFF
    
        # --- Gabungkan full frame ---
        data_full = f"{data_hex}{crc_lo:02x}{crc_hi:02x}"
        data_send = bytes.fromhex(data_full)
    
        try:
            # --- Kirim frame ---
            self.sock.settimeout(3.0)
            self.sock.sendall(data_send)
            time.sleep(0.05)  # beri jeda singkat biar gateway sempat balas
            stream = self.sock.recv(256)
        except Exception as e:
            print("[TCP] Error saat kirim/baca:", e)
            return None
    
        # --- Log RX lengkap ---
        rx_hex = " ".join(f"{b:02X}" for b in stream)
        now = datetime.now()
        print(now.strftime("Waktu Sampling : %d-%m-%y %H:%M:%S"))
        print("========== AQT560 (TCP) ==========")
        print(f"WRITE > {data_full.upper()}")
        print(f"RX RAW> {rx_hex}")
    
        # --- Validasi panjang minimal ---
        if len(stream) < 5:
            print("[Error] Data tidak lengkap:", list(stream))
            return None
    
        try:
            addr        = stream[0]
            func        = stream[1]
            byte_count  = stream[2]
            data_bytes  = stream[3:3 + byte_count]
            recv_crc_lo = stream[-2]
            recv_crc_hi = stream[-1]
    
            # --- CRC Check ---
            calc = Crc16Modbus.calc(stream[:-2])
            calc_lo = calc & 0xFF
            calc_hi = (calc >> 8) & 0xFF
            crc_ok = (recv_crc_lo == calc_lo) and (recv_crc_hi == calc_hi)
            print(f"CRC: {'OK' if crc_ok else 'BAD'} (recv={recv_crc_hi:02X}{recv_crc_lo:02X}, calc={calc_hi:02X}{calc_lo:02X})")
    
            # --- Parsing sesuai panjang data ---
            if byte_count == 2:
                val = (data_bytes[0] << 8) | data_bytes[1]
                print(f"Parsed 16-bit: {val}")
                return val
    
            elif byte_count == 4:
                val = (data_bytes[0] << 24) | (data_bytes[1] << 16) | (data_bytes[2] << 8) | data_bytes[3]
                print(f"Parsed 32-bit: {val}")
                return val
    
            elif byte_count == 8:
                text = bytes(data_bytes).decode("ascii", "ignore").strip("\x00 \r\n ")
                print(f"Parsed ASCII: '{text}'")
                return text
    
            else:
                print(f"[Warning] ByteCount={byte_count}, data={list(data_bytes)}")
                return bytes(data_bytes)
    
        except Exception as e:
            print("[Parse Error]", e)
            return None
    