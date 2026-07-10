#!/bin/bash
cd /home/sipedge/sip_edge
source venv/bin/activate

for creds in "analyst1:analyst1" "operator:operator" "admin:admin"; do
    user="${creds%%:*}"
    pass="${creds##*:}"
    TOKEN=$(curl -s -X POST http://localhost:8000/login \
      -H "Content-Type: application/json" \
      -d '{"username":"'"$user"'","password":"'"$pass"'"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except: pass
")
    if [ -n "$TOKEN" ]; then
        echo "Login OK: $user"
        break
    fi
done

if [ -z "$TOKEN" ]; then
    echo "ERROR: No se pudo obtener token"
    exit 1
fi

echo "TOKEN chars: ${#TOKEN}"
echo ""
echo "=========================================="
echo "  ESCUCHANDO WEBSOCKET /ws/scale"
echo "  Envia las cadenas desde tu PC ahora"
echo "=========================================="
echo ""

TOKEN=$TOKEN python /tmp/ws_test.py