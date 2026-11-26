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
    distance_offset: int
    distance_coefficient: float

# model and device type
MODEL_RAW_ID = UUID("55a76001-b766-4e18-8d3e-871004bb29f1")
MODEL_DATA_ID = UUID("32e562cf-9487-4bbf-983d-f5c6f3f8fad2")
MODEL_BATTERY_ID = UUID("0a9cff00-58cd-42e9-90bf-9172acd53a03")
TYPE_ID = UUID("3b010faa-57e0-4303-8b36-42afb39fd367")

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

# get models of distance sensor
model_raw = resource.read_model(MODEL_RAW_ID)
model_data = resource.read_model(MODEL_DATA_ID)
model_battery = resource.read_model(MODEL_BATTERY_ID)

# get distance sensor devices
device_map: Dict[UUID, Device] = {}
devices = resource.list_device_by_type(TYPE_ID)
for device in devices:
    bc = next((conf.value for conf in device.configs if conf.name == "battery_coefficient"), None)
    do = next((conf.value for conf in device.configs if conf.name == "distance_offset"), None)
    dc = next((conf.value for conf in device.configs if conf.name == "distance_coefficient"), None)
    # check for all necessary device config
    if bc != None and do != None and dc != None:
        device_map[device.id] = Device(device.serial_number, bc, do, dc)
device_ids = list(device_map.keys())

print("DISTANCE MODEL")
print("{}: {}".format(model_raw.id, model_raw.name))
print("{}: {}".format(model_data.id, model_data.name))
print("DEVICES")
for device in devices:
    print("{}: {}".format(device.id, device.serial_number))

def get_u32(value0: int, value1: int, value2: int, value3: int) -> int:
    return value0 * 16777216 + value1 * 65536 + value2 * 256 + value3


while True:

    # read buffer based on raw model
    buffers = resource.list_buffer_group_first(10, device_ids, [model_raw.id], Tag.ANALYSIS_1)
    # wait some moment when buffer is unavailable
    if len(buffers) == 0:
        time.sleep(config.TIMING['analysis_sleep'])
        continue

    for buffer in buffers:
        device = device_map[buffer.device_id]

        # convert distance data bytes from LoRa to actual value
        battery = ((buffer.data[0] * 2) + 512) * 3.3 / (1023 * device.battery_coefficient)
        value = get_u32(buffer.data[1], buffer.data[2], buffer.data[3], buffer.data[4])
        distance = (value - device.distance_offset) * device.distance_coefficient

        # create data buffer for rain gauge and update raw buffer
        data = [distance]
        time_str = buffer.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        try:
            print("{}    {}    {}".format(time_str, buffer.device_id, data))
            resource.create_buffer(buffer.device_id, model_data.id, buffer.timestamp, data, Tag.TRANSFER_LOCAL)
            resource.create_buffer(buffer.device_id, model_battery.id, buffer.timestamp, [battery], Tag.TRANSFER_LOCAL)
            resource.update_buffer(buffer.id, None, Tag.TRANSFER_LOCAL)
        except Exception as error:
            print(error)
