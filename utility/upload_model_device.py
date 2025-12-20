import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from dataclasses import dataclass
import time
from datetime import datetime
import uuid
from uuid import UUID
from bbthings_grpc import Auth, Resource, ModelSchema, TypeSchema
import config


# user login on local server
address_auth = config.SERVER_LOCAL['address_auth']
address_resource = config.SERVER_LOCAL['address_resource']
auth = Auth(address_auth)
login = auth.user_login(config.SERVER_LOCAL['admin_name'], config.SERVER_LOCAL['admin_password'])
resource = Resource(address_resource, login.access_tokens[0].access_token)

# user login on main server
address_auth = config.SERVER_MAIN['address_auth']
address_resource = config.SERVER_MAIN['address_resource']
auth_main = Auth(address_auth)
login_main = auth_main.user_login(config.SERVER_MAIN['admin_name'], config.SERVER_MAIN['admin_password'])
resource_main = Resource(address_resource, login_main.access_tokens[0].access_token)

print("LOCAL LOGIN:")
print("user_id       = {}".format(login.user_id))
print("auth_token    = {}".format(login.auth_token))
for token in login.access_tokens:
    print("api_id        = {}".format(token.api_id))
    print("access_token  = {}".format(token.access_token))
    print("refresh_token = {}".format(token.refresh_token))
print("MAIN LOGIN:")
print("user_id       = {}".format(login_main.user_id))
print("auth_token    = {}".format(login_main.auth_token))
for token in login_main.access_tokens:
    print("api_id        = {}".format(token.api_id))
    print("access_token  = {}".format(token.access_token))
    print("refresh_token = {}".format(token.refresh_token))

# read gateway and devices
gateway_id = UUID(config.GATEWAY_MODBUS['id'])
devices = resource.list_device_by_gateway(gateway_id)
model_ids = []
type_ids = []
types: list[TypeSchema] = []
for device in devices:
    for model_id in device.model_ids:
        if model_id not in model_ids and model_id != UUID(int=0):
            model_ids.append(model_id)
    if device.type_id not in type_ids:
        type_ids.append(device.type_id)
        type_schema = resource.read_type(device.type_id)
        types.append(type_schema)

# read data model, data types and configs
models: list[ModelSchema] = []
for model_id in model_ids:
    model = resource.read_model(model_id)
    models.append(model)

print("MODELS:")
for model in models:
    print("{}: {}".format(model.id, model.name))
print("TYPES:")
for ty in types:
    print("{}: {}".format(ty.id, ty.name))
print("DEVICES:")
for device in devices:
    print("{}: {}".format(device.id, device.name))

# create data model and add data types and configs on main server
for model in models:
    resource_main.create_model(model.id, model.data_type, model.category, model.name, model.description)
    for index, configs in enumerate(model.configs):
        for conf in configs:
            resource_main.create_model_config(model.id, index, conf.name, conf.value, conf.category)

# create type and add type model on main server
for type_ in types:
    resource_main.create_type(type_.id, type_.name, type_.description)
    for model_id in type_.model_ids:
        resource_main.add_type_model(type_.id, model_id)
    for type_config in type_.configs:
        resource_main.create_type_config(type_config.id, type_config.name, type_config.value_type, type_config.category)

# create devices and configs on main server
for device in devices:
    resource_main.create_device(device.id, device.gateway_id, device.type_id, device.serial_number, device.name, device.description)
    for conf in device.configs:
        resource_main.create_device_config(device.id, conf.name, conf.value, conf.category)
