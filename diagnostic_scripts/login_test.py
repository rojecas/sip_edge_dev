import urllib.request, json

for user, pwd in [("admin", "admin"), ("admin", "admin1234"), ("operator", "operator"), ("analyst1", "analyst1")]:
    data = json.dumps({"username": user, "password": pwd}).encode()
    req = urllib.request.Request("http://localhost:8000/api/auth/login", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        body = json.loads(resp.read())
        token = body.get("access_token") or body.get("token") or ""
        if token:
            print(f"LOGIN OK: {user}/{pwd} -> token len={len(token)}")
            with open("/tmp/token.txt", "w") as f:
                f.write(token)
            break
        else:
            print(f"LOGIN NO TOKEN: {user}/{pwd}")
    except Exception as e:
        print(f"LOGIN FAIL: {user}/{pwd} -> {e}")
else:
    print("NO LOGIN WORKED")