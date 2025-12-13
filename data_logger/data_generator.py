import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from dataclasses import dataclass
import time
from datetime import datetime
from uuid import UUID
import grpc
from bbthings_grpc import Auth, Resource, DeviceSchema
import config
import random


@dataclass
class Generator:
    upper_limit: int | float
    lower_limit: int | float
    precission: int | None

@dataclass
class DeviceMap:
    id: UUID
    model: UUID
    type: str
    generators: list[Generator]

# Get default gateway ID or ID from input argument and then get corresponding configurations from config file
invalid = True
if len(config.GATEWAY_GENERATOR) > 0:
    gateway_id = next(iter(config.GATEWAY_GENERATOR))
    if len(sys.argv) > 1:
        gateway_id = sys.argv[1] if sys.argv[1] in config.GATEWAY_GENERATOR else gateway_id
    GATEWAY = config.GATEWAY_GENERATOR[gateway_id]
    if all(k in GATEWAY for k in ("period_time",)):
        invalid = False
if invalid:
    raise Exception("Gateway ID input is missing, invalid format, or invalid gateway configuration")

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
    upper_limits = {}
    lower_limits = {}
    precissions = {}
    if device.id != device.gateway_id: # filter out gateway
        for conf in device.configs:
            if "upper_limit" in conf.name:
                upper_limits[conf.name] = conf.value
            elif "lower_limit" in conf.name:
                lower_limits[conf.name] = conf.value
            elif "precission" in conf.name:
                precissions[conf.name] = conf.value
        for model_id in device.type.model_ids:
            model = resource.read_model(model_id)
            if model.category == "GENERATOR":
                upper_limits = list(dict(sorted(upper_limits.items())).values())
                lower_limits = list(dict(sorted(lower_limits.items())).values())
                precissions = list(dict(sorted(precissions.items())).values())
                length = max(len(upper_limits), len(lower_limits), len(precissions))
                generators = []
                for i in range(length):
                    upper_limit = 1
                    if len(upper_limits) > i: upper_limit = upper_limits[i]
                    lower_limit = -1
                    if len(lower_limits) > i: lower_limit = lower_limits[i]
                    precission = None
                    if len(precissions) > i: precission = precissions[i]
                    generators.append(Generator(upper_limit, lower_limit, precission))
                device_map.append(DeviceMap(device.id, model_id, device.type.name, generators))

for device in device_map:
    print(device)

while True:

    if int(time.time()) % GATEWAY["period_time"] != 0:
        continue
    now = datetime.now().replace(microsecond=0)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Generate data for devices
    for device in device_map:

        data = []
        for generator in device.generators:

            # Generate random integer number
            if generator.precission == None:
                number = random.randint(generator.lower_limit, generator.upper_limit)
                data.append(number)
            # Generate random float number
            else:
                number = random.uniform(generator.lower_limit, generator.upper_limit)
                if generator.precission >= 0:
                    number = round(number, generator.precission)
                data.append(number)

        try:
            print("{0}    {1}    {2}".format(now_str, device.id, data))
            # Create buffer with data from request data
            resource.create_buffer(device.id, device.model, now, data, config.STATUS['logger_generator_end'])

        except Exception as error:
            print(error)

    while int(time.time()) % GATEWAY["period_time"] == 0:
        pass
