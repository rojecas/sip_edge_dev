import urllib.request, json, asyncio, websockets, sys

# Login
data = json.dumps({"username": "admin", "password": "admin"}).encode()
req = urllib.request.Request("http://localhost:8000/api/auth/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
body = json.loads(resp.read())
TOKEN = body.get("access_token") or body.get("token") or ""
print("TOKEN obtenido: " + str(len(TOKEN)) + " chars")

async def test():
    uri = "ws://localhost:8000/ws/scale?token=" + TOKEN
    print("Conectando a WebSocket...")
    try:
        async with websockets.connect(uri) as ws:
            print("Conectado! Esperando datos de escala (timeout 30s)...")
            print("ENVIA LAS CADENAS DESDE TU PC AHORA")
            msg = await asyncio.wait_for(ws.recv(), timeout=30)
            data = json.loads(msg)
            print("RECIBIDO: " + json.dumps(data, indent=2))
            # Keep trying to get more
            try:
                while True:
                    msg2 = await asyncio.wait_for(ws.recv(), timeout=5)
                    data2 = json.loads(msg2)
                    print("RECIBIDO: " + json.dumps(data2, indent=2))
            except asyncio.TimeoutError:
                print("(no more data for 5s)")
            return True
    except asyncio.TimeoutError:
        print("TIMEOUT: No se recibieron datos en 30s")
        return False
    except Exception as e:
        print("ERROR: " + str(e))
        return False

success = asyncio.run(test())
sys.exit(0 if success else 1)