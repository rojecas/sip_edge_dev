#!/bin/bash
cd /home/sipedge/sip_edge
source venv/bin/activate

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst1","password":"analyst1"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except: pass
")

if [ -z "$TOKEN" ]; then
  echo "Fallback login with operator..."
  TOKEN=$(curl -s -X POST http://localhost:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"operator","password":"operator"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except: pass
")
fi

export TOKEN
echo "TOKEN obtenido: ${#TOKEN} chars"
echo "Iniciando listener WebSocket..."
echo "ENVIA LAS CADENAS DESDE TU PC AHORA"
TOKEN=$TOKEN python /tmp/ws_test.py
