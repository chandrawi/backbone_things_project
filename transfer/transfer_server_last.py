import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from dataclasses import dataclass
import time
from datetime import datetime
from uuid import UUID
import grpc
from bbthings_grpc import Auth, Resource, DeviceSchema, Tag
import config


# Get default gateway ID or ID from input argument and then get corresponding configurations from config file
buffer_number = 100
buffer_offset = 0
if len(sys.argv) > 2:
    buffer_number = int(sys.argv[1])
    buffer_offset = int(sys.argv[2])

# user login on local server
address_auth = config.SERVER_LOCAL['address_auth']
address_resource = config.SERVER_LOCAL['address_resource']
resource = Resource(address_resource)
resource.login(address_auth, config.SERVER_LOCAL["admin_name"], config.SERVER_LOCAL["admin_password"])

# user login on main server
address_auth = config.SERVER_MAIN['address_auth']
address_resource = config.SERVER_MAIN['address_resource']
resource_main = Resource(address_resource)
resource_main.login(address_auth, config.SERVER_MAIN["admin_name"], config.SERVER_MAIN["admin_password"])

print("LOCAL LOGIN:")
print("api_id        = {}".format(resource._api_id))
print("user_id       = {}".format(resource.user_id))
print("auth_token    = {}".format(resource.auth_token))
print("access_token  = {}".format(resource.access_token))
print("refresh_token = {}".format(resource.refresh_token))
print("MAIN LOGIN:")
print("user_id       = {}".format(resource_main.user_id))
print("auth_token    = {}".format(resource_main.auth_token))
print("access_token  = {}".format(resource_main.access_token))
print("refresh_token = {}".format(resource_main.refresh_token))

# read devices on the gateways
devices: list[DeviceSchema] = []
for gateway_id in config.GATEWAYS:
    device_list = resource.list_device_by_gateway(UUID(gateway_id))
    devices = devices + device_list

print("DEVICES:")
device_map = {}
for device in devices:
    print("{}: {}".format(device.id, device.name))
    device_map[device.id] = device.name
print()

while True:

    buffers = []
    try:
        buffers = resource.list_buffer_group_last_offset(buffer_number, buffer_offset, device_map.keys(), None, Tag.TRANSFER_SERVER)
    except grpc.RpcError as error:
        if error.code() == grpc.StatusCode.UNAUTHENTICATED:
            resource_main.login(address_auth, config.SERVER_LOCAL['admin_name'], config.SERVER_LOCAL['admin_password'])
            print("RELOGIN LOCAL")
        continue

    # Only transfer if number buffers is greater or equal than buffer_number and wait some moment
    if len(buffers) < buffer_number:
        time.sleep(config.TIMING['transfer_sleep'])
        continue

    for buffer in buffers:
        time_str = buffer.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print("{}    {}    {}".format(time_str, buffer.device_id, device_map[buffer.device_id]))

        # try to create buffer on main server database
        main_exist = True
        try:
            resource_main.create_buffer(buffer.device_id, buffer.model_id, buffer.timestamp, buffer.data, Tag.TRANSFER_LOCAL)
        except grpc.RpcError as error:
            if error.code() == grpc.StatusCode.UNAUTHENTICATED:
                resource_main.login(address_auth, address_auth, config.SERVER_MAIN['admin_name'], config.SERVER_MAIN['admin_password'])
                print("RELOGIN MAIN")
                break
            elif error.code() == grpc.StatusCode.UNAVAILABLE:
                print("UNAVAILABLE")
                break
            # check if buffer already exist
            elif error.code() == grpc.StatusCode.ALREADY_EXISTS:
                print(error)
            else:
                print(error)
                main_exist = False

        # delete or update status based on configuration only if buffer on main exists
        if main_exist:
            try:
                if config.STATUS['transfer_server_end'] == Tag.DELETE:
                    resource.delete_buffer(buffer.id)
                else:
                    resource.update_buffer(buffer.id, None, config.STATUS['transfer_server_end'])
            except grpc.RpcError as error:
                print(error)
