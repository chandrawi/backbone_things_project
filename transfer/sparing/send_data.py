import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from uuid import UUID
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


# Make payload data from read data output
jwtPayload["data"] = [{'datetime': 1795600800, 'debit': 0.0014, 'tss': 10.5, 'pH': 6.96, 'cod': 3.7, 'nh3n': 1.5}, {'datetime': 1795600920, 'debit': 0.0013, 'tss': 10.0, 'pH': 7.03, 'cod': 4.2, 'nh3n': 1.6}, {'datetime': 1795601040, 'debit': 0.0012, 'tss': 8.9, 'pH': 7.01, 'cod': 4.7, 'nh3n': 1.5}, {'datetime': 1795601160, 'debit': 0.0012, 'tss': 8.3, 'pH': 6.86, 'cod': 4.1, 'nh3n': 1.3}, {'datetime': 1795601280, 'debit': 0.0012, 'tss': 7.3, 'pH': 6.85, 'cod': 5.4, 'nh3n': 1.5}, {'datetime': 1795601400, 'debit': 0.0014, 'tss': 8.6, 'pH': 6.91, 'cod': 3.8, 'nh3n': 1.8}, {'datetime': 1795601520, 'debit': 0.0013, 'tss': 7.1, 'pH': 7.02, 'cod': 4.6, 'nh3n': 1.4}, {'datetime': 1795601640, 'debit': 0.0013, 'tss': 10.3, 'pH': 7.03, 'cod': 4.7, 'nh3n': 1.7}, {'datetime': 1795601760, 'debit': 0.0014, 'tss': 8.5, 'pH': 6.93, 'cod': 3.5, 'nh3n': 1.2}, {'datetime': 1795601880, 'debit': 0.0014, 'tss': 8.8, 'pH': 6.95, 'cod': 3.7, 'nh3n': 1.2}, {'datetime': 1795602000, 'debit': 0.0014, 'tss': 7.8, 'pH': 6.9, 'cod': 5.0, 'nh3n': 1.5}, {'datetime': 1795602120, 'debit': 0.0015, 'tss': 10.1, 'pH': 6.98, 'cod': 5.0, 'nh3n': 1.6}, {'datetime': 1795602240, 'debit': 0.0014, 'tss': 7.7, 'pH': 6.86, 'cod': 3.2, 'nh3n': 1.6}, {'datetime': 1795602360, 'debit': 0.0014, 'tss': 9.5, 'pH': 7.01, 'cod': 4.0, 'nh3n': 1.5}, {'datetime': 1795602480, 'debit': 0.0013, 'tss': 9.2, 'pH': 6.98, 'cod': 4.1, 'nh3n': 1.4}, {'datetime': 1795602600, 'debit': 0.0012, 'tss': 10.4, 'pH': 6.85, 'cod': 4.0, 'nh3n': 1.6}, {'datetime': 1795602720, 'debit': 0.0014, 'tss': 10.6, 'pH': 7.02, 'cod': 4.6, 'nh3n': 1.4}, {'datetime': 1795602840, 'debit': 0.0014, 'tss': 10.7, 'pH': 7.05, 'cod': 4.5, 'nh3n': 1.3}, {'datetime': 1795602960, 'debit': 0.0012, 'tss': 11.0, 'pH': 6.91, 'cod': 4.0, 'nh3n': 1.7}, {'datetime': 1795603080, 'debit': 0.0013, 'tss': 10.1, 'pH': 7.05, 'cod': 4.9, 'nh3n': 1.2}, {'datetime': 1795603200, 'debit': 0.0013, 'tss': 10.5, 'pH': 6.85, 'cod': 5.2, 'nh3n': 1.7}, {'datetime': 1795603320, 'debit': 0.0013, 'tss': 7.9, 'pH': 6.94, 'cod': 5.5, 'nh3n': 1.5}, {'datetime': 1795603440, 'debit': 0.0013, 'tss': 10.8, 'pH': 6.91, 'cod': 5.5, 'nh3n': 1.4}, {'datetime': 1795603560, 'debit': 0.0013, 'tss': 10.7, 'pH': 7.04, 'cod': 5.4, 'nh3n': 1.6}, {'datetime': 1795603680, 'debit': 0.0015, 'tss': 8.9, 'pH': 6.94, 'cod': 4.3, 'nh3n': 1.4}, {'datetime': 1795603800, 'debit': 0.0014, 'tss': 10.3, 'pH': 6.96, 'cod': 3.6, 'nh3n': 1.4}, {'datetime': 1795603920, 'debit': 0.0013, 'tss': 7.9, 'pH': 6.95, 'cod': 4.5, 'nh3n': 1.5}, {'datetime': 1795604040, 'debit': 0.0012, 'tss': 9.2, 'pH': 6.91, 'cod': 4.6, 'nh3n': 1.5}, {'datetime': 1795604160, 'debit': 0.0014, 'tss': 9.0, 'pH': 7.02, 'cod': 3.7, 'nh3n': 1.7}, {'datetime': 1795604280, 'debit': 0.0012, 'tss': 8.9, 'pH': 7.04, 'cod': 4.6, 'nh3n': 1.7}]

# Send data to external sparing API
try:
    enc = jwt.encode(jwtPayload,KEY,algorithm='HS256',headers=jwtHeaders)
    r = requests.post(URL, json={ "token": enc }, headers=headers)
    print(r.json())
    print(r.status_code)

except Exception as error:
    print(error)
