import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import serial
import time
import config
from datetime import datetime

# Get gateway ID from input argument and corresponding configurations from config file
invalid = True
if len(config.GATEWAY_MODBUS) > 0:
    gateway_id = next(iter(config.GATEWAY_MODBUS))
    if len(sys.argv) > 1:
        gateway_id = sys.argv[1] if sys.argv[1] in config.GATEWAY_MODBUS else gateway_id
    GATEWAY = config.GATEWAY_MODBUS[gateway_id]
    if all(k in GATEWAY for k in ("serial_port", "period_time")):
        invalid = False
if invalid:
    raise Exception("Gateway ID input is missing, invalid format, or invalid gateway configuration")

ser = serial.Serial(GATEWAY['serial_port'], 9600, timeout=1)

while True:

    if int(time.time()) % GATEWAY["period_time"] != 0:
        continue
    now = datetime.now().replace(microsecond=0)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # SCL3300 inclinometer X, Y, Z inclination with 0x01 and 0x02 addresses
    # print("SCL3300 inclinometer")
    commands = [
        # b"\x01\x04\x00\x04\x00\x04\xB0\x08",
        # b"\x02\x04\x00\x04\x00\x04\xB0\x3B",
        # b"\x03\x04\x00\x04\x00\x04\xB1\xEA",
        # b"\x04\x04\x00\x04\x00\x04\xB0\x5D",
        # b"\x05\x04\x00\x04\x00\x04\xB1\x8C",
        # b"\x06\x04\x00\x04\x00\x04\xB1\xBF",
        # b"\x07\x04\x00\x04\x00\x04\xB0\x6E",
        # b"\x08\x04\x00\x04\x00\x04\xB0\x91",
        # b"\x09\x04\x00\x04\x00\x04\xB1\x40",
        # b"\x0A\x04\x00\x04\x00\x04\xB1\x73",
        # b"\x0B\x04\x00\x04\x00\x04\xB0\xA2",
        # b"\x0C\x04\x00\x04\x00\x04\xB1\x15",
        # b"\x0D\x04\x00\x04\x00\x04\xB0\xC4",
        # b"\x0E\x04\x00\x04\x00\x04\xB0\xF7",
        b"\x01\x04\x00\x00\x00\x03\xB0\x0B",
    ]
    for i, command in enumerate(commands):
        ser.write(command)
        s = ser.read(13)
        id = s[0]
        angle_x = s[3] * 2**8 + s[4]
        angle_y = s[5] * 2**8 + s[6]
        angle_z = s[7] * 2**8 + s[8]
        if angle_x >= 2**15 : angle_x = angle_x - 2**16
        if angle_y >= 2**15 : angle_y = angle_y - 2**16
        if angle_z >= 2**15 : angle_z = angle_z - 2**16
        print(f"{datetime.now()}, {angle_x}, {angle_y}, {angle_z}")
