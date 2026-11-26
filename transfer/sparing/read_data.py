import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import time
from datetime import datetime
from uuid import UUID
import grpc
import requests
from bbthings_grpc import Auth, Resource, ModelSchema, DeviceSchema, Tag
import config

set_id = UUID("0944dd19-a398-495a-bfc1-b5899ce4056c")
times = [
    "2026-11-25 17:00:00",
    "2026-11-25 17:02:00",
    "2026-11-25 17:04:00",
    "2026-11-25 17:06:00",
    "2026-11-25 17:08:00",
    "2026-11-25 17:10:00",
    "2026-11-25 17:12:00",
    "2026-11-25 17:14:00",
    "2026-11-25 17:16:00",
    "2026-11-25 17:18:00",
    "2026-11-25 17:20:00",
    "2026-11-25 17:22:00",
    "2026-11-25 17:24:00",
    "2026-11-25 17:26:00",
    "2026-11-25 17:28:00",
    "2026-11-25 17:30:00",
    "2026-11-25 17:32:00",
    "2026-11-25 17:34:00",
    "2026-11-25 17:36:00",
    "2026-11-25 17:38:00",
    "2026-11-25 17:40:00",
    "2026-11-25 17:42:00",
    "2026-11-25 17:44:00",
    "2026-11-25 17:46:00",
    "2026-11-25 17:48:00",
    "2026-11-25 17:50:00",
    "2026-11-25 17:52:00",
    "2026-11-25 17:54:00",
    "2026-11-25 17:56:00",
    "2026-11-25 17:58:00"
]

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

# read set data
datasets = []
for tm in times:
    dt = datetime.strptime(tm, "%Y-%m-%d %H:%M:%S")
    print(dt.timestamp())
    dataset = resource.read_data_set(set_id, timestamp=dt)
    setdata = {
        "datetime": int(dt.timestamp()),
        "debit": dataset.data[0],
        "tss": dataset.data[1],
        "pH": dataset.data[2],
        "cod": dataset.data[3],
        "nh3n": dataset.data[4],
    }
    datasets.append(setdata)

print(datasets)

