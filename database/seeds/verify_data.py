import urllib.request, json, urllib.parse

# Login
d = json.dumps({"username": "admin", "password": "admin"}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/api/auth/login", data=d, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["access_token"]
print("Login OK")

# Users (returns list)
req = urllib.request.Request("http://127.0.0.1:8000/api/users", headers={"Authorization": "Bearer " + token})
users = json.loads(urllib.request.urlopen(req).read())
print("Users: " + str(len(users)))
for u in users[:3]:
    print("  - " + u["username"] + " (" + u["role"] + ")")

# Haciendas (paginated)
qs = urllib.parse.urlencode({"page": 1, "page_size": 5})
req = urllib.request.Request("http://127.0.0.1:8000/api/haciendas?" + qs, headers={"Authorization": "Bearer " + token})
h = json.loads(urllib.request.urlopen(req).read())
print("Haciendas: " + str(h["total"]) + " total")
for hh in h["items"][:3]:
    print("  - [" + hh["codigo"] + "] " + hh["nombre"])

# Suertes
qs2 = urllib.parse.urlencode({"hacienda_id": h["items"][0]["id"]})
req = urllib.request.Request("http://127.0.0.1:8000/api/suertes?" + qs2, headers={"Authorization": "Bearer " + token})
s = json.loads(urllib.request.urlopen(req).read())
slist = s if isinstance(s, list) else s.get("items", [])
print("Suertes: " + str(len(slist)))
for ss in slist[:3]:
    print("  - " + ss["codigo_suerte"])
print("Verification complete!")
