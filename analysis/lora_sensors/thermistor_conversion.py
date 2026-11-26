import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from dataclasses import dataclass
from typing import Dict
import time
import math
from uuid import UUID
from bbthings_grpc import Resource, Tag
import config


@dataclass
class Device:
    serial_number: str
    battery_coefficient: float
    resistor_nominal: float
    resistor_reference: float
    temperature_nominal: float
    betha_coefficient: float

# model and device type
MODEL_RAW_ID = UUID("55a76001-b766-4e18-8d3e-871004bb29f1")
MODEL_DATA_ID = UUID("692d4e16-422c-48d9-becf-79eb92fe48e1")
MODEL_BATTERY_ID = UUID("0a9cff00-58cd-42e9-90bf-9172acd53a03")
TYPE_ID = UUID("614d7305-e589-4b0b-a623-d9545b833329")

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

# get models of thermistor
model_raw = resource.read_model(MODEL_RAW_ID)
model_data = resource.read_model(MODEL_DATA_ID)
model_battery = resource.read_model(MODEL_BATTERY_ID)

# get thermistor devices
device_map: Dict[UUID, Device] = {}
devices = resource.list_device_by_type(TYPE_ID)
for device in devices:
    bc = next((conf.value for conf in device.configs if conf.name == "battery_coefficient"), None)
    rn = next((conf.value for conf in device.configs if conf.name == "resistor_nominal"), None)
    rr = next((conf.value for conf in device.configs if conf.name == "resistor_reference"), None)
    tn = next((conf.value for conf in device.configs if conf.name == "temperature_nominal"), None)
    ec = next((conf.value for conf in device.configs if conf.name == "betha_coefficient"), None)
    # check for all necessary device config
    if bc != None and rn != None and rr != None and tn != None and ec != None:
        device_map[device.id] = Device(device.serial_number, bc, rn, rr, tn, ec)
device_ids = list(device_map.keys())

print("THERMISTOR MODEL")
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

        # convert thermistor data bytes from LoRa to actual value
        battery = ((buffer.data[0] * 2) + 512) * 3.3 / (1023 * device.battery_coefficient)
        value = get_u32(buffer.data[1], buffer.data[2], buffer.data[3], buffer.data[4])
        resistance = device.resistor_reference * value / (8388608 - value)
        temperature = 1 / ((1 / device.temperature_nominal) + math.log(resistance / device.resistor_nominal) / device.betha_coefficient) - 273.15

        # create data buffer for rain gauge and update raw buffer
        data = [temperature]
        time_str = buffer.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        try:
            print("{}    {}    {}".format(time_str, buffer.device_id, data))
            resource.create_buffer(buffer.device_id, model_data.id, buffer.timestamp, data, Tag.TRANSFER_LOCAL)
            resource.create_buffer(buffer.device_id, model_battery.id, buffer.timestamp, [battery], Tag.TRANSFER_LOCAL)
            resource.update_buffer(buffer.id, None, Tag.TRANSFER_LOCAL)
        except Exception as error:
            print(error)
