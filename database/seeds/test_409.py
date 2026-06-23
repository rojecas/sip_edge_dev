import urllib.request, json

d = json.dumps({"username": "admin", "password": "admin"}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/api/auth/login", data=d, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["access_token"]

d2 = json.dumps({"codigo": "B82", "nombre": "Test409"}).encode()
req2 = urllib.request.Request("http://127.0.0.1:8000/api/haciendas", data=d2, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req2)
    print("Unexpected success:", resp.status)
except urllib.error.HTTPError as e:
    body = json.loads(e.read().decode())
    print("Status:", e.code)
    print("Message:", body.get("detail", "N/A"))
