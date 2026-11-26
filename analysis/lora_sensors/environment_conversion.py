import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from dataclasses import dataclass
from typing import Dict
import time
from uuid import UUID
from bbthings_grpc import Resource, Tag
import config


@dataclass
class Device:
    serial_number: str
    battery_coefficient: float

# model and device type
MODEL_RAW_ID = UUID("77aa02f3-c6b1-497e-a633-9ad938a7cc1e")
MODEL_DATA_ID = UUID("165cd0ac-5565-4907-b0df-05661f9156d1")
MODEL_BATTERY_ID = UUID("0a9cff00-58cd-42e9-90bf-9172acd53a03")
TYPE_ID = UUID("100efa43-c2b1-4afb-942a-53cb5944381d")

# user login on local server
address_auth = config.SERVER_LOCAL['address_auth']
address_resource = config.SERVER_LOCAL['address_resource']
resource = Resource(address_resource)
resource.login(address_auth, config.SERVER_LOCAL["admin_name"], config.SERVER_LOCAL["admin_password"])

print("LOGIN:")
print("api_id        = {}".format(resource._api_id))
print("user_id       = {}".format(resource.user_id))
print("auth_token    = {}".format(resource.auth_token))
print("access_token  = {}".format(resource.access_token))
print("refresh_token = {}".format(resource.refresh_token))

# get models of environment sensor
model_raw = resource.read_model(MODEL_RAW_ID)
model_data = resource.read_model(MODEL_DATA_ID)
model_battery = resource.read_model(MODEL_BATTERY_ID)

# get environment sensor devices
device_map: Dict[UUID, Device] = {}
devices = resource.list_device_by_type(TYPE_ID)
for device in devices:
    bc = next((conf.value for conf in device.configs if conf.name == "battery_coefficient"), None)
    # check for all necessary device config
    if bc != None:
        device_map[device.id] = Device(device.serial_number, bc)
device_ids = list(device_map.keys())

print("ENVIRONMENT MODEL")
print("{}: {}".format(model_raw.id, model_raw.name))
print("{}: {}".format(model_data.id, model_data.name))
print("DEVICES")
for device in devices:
    print("{}: {}".format(device.id, device.serial_number))

def get_u16(value0: int, value1: int) -> int:
    return value0 * 256 + value1

def get_i16(value0: int, value1: int) -> int:
    value = value0 * 256 + value1
    if value0 < 128: 
        return value
    return value - 65536


while True:

    # read buffer based on raw model
    buffers = resource.list_buffer_group_first(10, device_ids, [model_raw.id], Tag.ANALYSIS_1)
    # wait some moment when buffer is unavailable
    if len(buffers) == 0:
        time.sleep(config.TIMING['analysis_sleep'])
        continue

    for buffer in buffers:
        device = device_map[buffer.device_id]

        # convert environment data bytes from LoRa to actual value
        battery = ((buffer.data[0] * 2) + 512) * 3.3 / (1023 * device.battery_coefficient)
        temperature = get_i16(buffer.data[1], buffer.data[2]) / 100.0
        humidity = get_i16(buffer.data[3], buffer.data[4]) / 100.0
        pressure = get_i16(buffer.data[5], buffer.data[6]) / 100.0

        # create data buffer for rain gauge and update raw buffer
        data = [temperature, humidity, pressure]
        time_str = buffer.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        try:
            print("{}    {}    {:.2f}    {}".format(time_str, buffer.device_id, battery, data))
            resource.create_buffer(buffer.device_id, model_data.id, buffer.timestamp, data, Tag.TRANSFER_LOCAL)
            resource.create_buffer(buffer.device_id, model_battery.id, buffer.timestamp, [battery], Tag.TRANSFER_LOCAL)
            resource.update_buffer(buffer.id, None, Tag.TRANSFER_LOCAL)
        except Exception as error:
            print(error)
