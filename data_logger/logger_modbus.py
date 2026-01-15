import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from dataclasses import dataclass
import time
from datetime import datetime
from uuid import UUID
from bbthings_grpc import Auth, Resource
from pymodbus.client import ModbusSerialClient
import config


@dataclass
class DeviceMap:
    slave_id: int
    id: UUID
    model: UUID
    type: str

# Get default gateway ID or ID from input argument and then get corresponding configurations from config file
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

# create client object
client = ModbusSerialClient(GATEWAY['serial_port'], baudrate=9600)
# connect to device
client.connect()

# user login
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

# read devices associated with configured gateway
device_map: list[DeviceMap] = []
devices = resource.list_device_by_gateway(UUID(gateway_id))
for device in devices:
    if device.id != device.gateway_id: # filter out gateway
        slave_id = None
        for conf in device.configs:
            if conf.name == "slave_id":
                slave_id = conf.value
        for model_id in device.model_ids:
            model = resource.read_model(model_id)
            if model.category == "RAW" and slave_id != None:
                device_map.append(DeviceMap(slave_id, device.id, model_id, device.type_name))
for device in device_map:
    print(device)

while True:

    if int(time.time()) % GATEWAY["period_time"] != 0:
        continue
    now = datetime.now().replace(microsecond=0)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Get received data from node
    for device in device_map:
        client.connect()

        try:
            # Request data to the modbus device based on its type
            data = []
            if device.type == "soil inclinometer" or device.type == "inclinometer array":
                rr = client.read_input_registers(device_id=device.slave_id, address=0x00, count=3)
                data = rr.registers
            elif device.type == "SCL3300 inclinometer array":
                rr = client.read_input_registers(device_id=device.slave_id, address=0x04, count=4)
                data = rr.registers
            elif device.type == "HPT604 piezometer":
                rr = client.read_input_registers(device_id=device.slave_id, address=0x10, count=6)
                data = [rr.registers[0], rr.registers[1], rr.registers[3], rr.registers[4]]
            elif device.type == "Hondetec rain gauge":
                rr = client.read_holding_registers(device_id=device.slave_id, address=0x00, count=10)
                data = [rr.registers[2], rr.registers[0], rr.registers[5], rr.registers[4]]
            elif device.type == "environment sensor":
                rr = client.read_input_registers(device_id=device.slave_id, address=0x00, count=3)
                data = rr.registers
            else:
                continue
            print("{0}    {1}  {2:3d}    {3}".format(now_str, device.id, device.slave_id, data))

            # Create buffer with data from request data
            resource.create_buffer(device.id, device.model, now, data, config.STATUS['logger_modbus_end'])

        except Exception as error:
            print(error)

        finally:
            client.close()

    while int(time.time()) % GATEWAY["period_time"] == 0:
        pass
