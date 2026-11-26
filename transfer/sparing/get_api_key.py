import requests

payloads = {
}
headers = {
}
r = requests.get("https://sparing.kemenlh.go.id/api/secret-sensor", json=payloads, headers=headers)
print(r.text)
print(r.status_code)
