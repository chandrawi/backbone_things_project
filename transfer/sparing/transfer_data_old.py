import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import time
from datetime import datetime
from uuid import UUID
from bbthings_grpc import Resource, Tag
import config
import requests
import jwt


# Get external API configuration
UID = config.EXTERNAL_API["uid"]
KEY = config.EXTERNAL_API["key"]
PERIOD = int(config.EXTERNAL_API["period"])
SET_ID = UUID(config.EXTERNAL_API["set_id"])
URL = config.EXTERNAL_API["url"]
headers = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}
jwtHeaders = {
    "typ" : "JWT",
    "alg" : "HS256"
}
jwtPayload = {
    "uid" : "90b9077d18e204c3325a917c",
    "data" : []
}
OFFSET = 30


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

# Get devices and models in the set
set_ = resource.read_set(SET_ID)
device_ids: list[UUID] = []
model_ids: list[UUID] = []
print("Device_ID                               Model_ID")
for member in set_.members:
    device_ids.append(member.device_id)
    model_ids.append(member.model_id)
    print("{}    {}".format(member.device_id, member.model_id))


while True:

    # Check for unsent old data
    datetimes = resource.list_buffer_group_timestamp_first(1, device_ids, model_ids, Tag.EXTERNAL_OUTPUT)

    # wait some moment when buffer is unavailable
    if len(datetimes) == 0:
        time.sleep(config.TIMING['transfer_sleep'])
        continue

    # Check if buffer time is before current period minus some offset
    # Offset time is used to let periodic transfer run first
    time_buffer = int(datetimes[0].timestamp())
    if time_buffer >= (int(time.time()) // PERIOD * PERIOD - OFFSET):
        time.sleep(config.TIMING['transfer_sleep'])
        continue

    # Read all data buffer set on the period
    begin = datetime.fromtimestamp(time_buffer)
    end = datetime.fromtimestamp(time_buffer - (time_buffer % PERIOD) + PERIOD - 1)
    datasets = resource.list_buffer_set_by_range(SET_ID, begin, end, Tag.EXTERNAL_OUTPUT)

    # Skip if no buffer found
    if len(datasets) == 0:
        continue

    # Make payload data from buffer set
    payload_data = []
    buffer_ids: list[int] = []
    for dataset in datasets:
        print("{0}    {1}    {2}".format(dataset.timestamp, dataset.set_id, dataset.data))
        payload_data.append({
            "datetime": int(dataset.timestamp.timestamp()),
            "debit": dataset.data[0],
            "tss": dataset.data[1],
            "pH": dataset.data[2],
            "cod": dataset.data[3],
            "nh3n": dataset.data[4],
        })
        buffer_ids.extend(dataset.ids)
    jwtPayload["data"] = payload_data

    # Send data to external sparing API
    try:
        enc = jwt.encode(jwtPayload,KEY,algorithm='HS256',headers=jwtHeaders)
        r = requests.post(URL, json={ "token": enc }, headers=headers)
        print(r.json())
        print(r.status_code)
        # Delete all buffers in the dataset
        for buffer_id in set(buffer_ids):
            resource.delete_buffer(buffer_id)

    except Exception as error:
        print(error)
