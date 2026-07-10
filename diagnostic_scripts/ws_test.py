import asyncio, websockets, json, sys, os

TOKEN = os.environ.get("TOKEN", "")

async def test():
    uri = "ws://localhost:8000/ws/scale?token=" + TOKEN
    print("Conectando a " + uri + "...")
    try:
        async with websockets.connect(uri) as ws:
            print("Conectado. Esperando datos de escala (timeout 30s)...")
            msg = await asyncio.wait_for(ws.recv(), timeout=30)
            data = json.loads(msg)
            print("RECIBIDO: " + json.dumps(data, indent=2))
            try:
                while True:
                    msg2 = await asyncio.wait_for(ws.recv(), timeout=2)
                    data2 = json.loads(msg2)
                    print("RECIBIDO: " + json.dumps(data2, indent=2))
            except asyncio.TimeoutError:
                pass
            return True
    except asyncio.TimeoutError:
        print("TIMEOUT: No se recibieron datos en 30s")
        return False
    except Exception as e:
        print("ERROR: " + str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)