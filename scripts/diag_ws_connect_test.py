import urllib.request, json, asyncio, websockets, sys

data = json.dumps({"username": "admin", "password": "admin"}).encode()
req = urllib.request.Request("http://localhost:8000/api/auth/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
body = json.loads(resp.read())
TOKEN = body.get("access_token", "")
print(f"Token: {len(TOKEN)} chars")

async def test():
    uri = f"ws://localhost:8000/ws/scale?token={TOKEN}"
    print(f"Conectando a WS...")
    try:
        async with websockets.connect(uri) as ws:
            print(f"Conectado! protocol={ws.protocol.state}")
            await asyncio.sleep(2)
            print("Aun activo tras 2s")
            return True
    except Exception as e:
        print(f"ERROR WS: {e}")
        return False

success = asyncio.run(test())
print(f"Resultado: {success}")
sys.exit(0 if success else 1)