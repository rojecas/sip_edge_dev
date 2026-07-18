#!/usr/bin/env bash
# init.sh - Verifica el entorno sip_edge antes de trabajar.
# Usa venv + .env si estan disponibles. Modo nativo o Docker.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

exit_code=0
RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail() { echo -e "${RED}[FAIL]${NC}  $*"; exit_code=1; }

# === 1. Python ==============================================================
echo -e "-- 1. Verificando entorno ----------------------------------"

PYTHON_BIN=""
if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    fail "python3 no esta instalado o no esta en PATH"
    exit 1
fi

py_ver=$("$PYTHON_BIN" --version 2>&1)
ok "python -> $py_ver (via $PYTHON_BIN)"

"$PYTHON_BIN" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null
if [ $? -eq 0 ]; then
    ok "Version de Python compatible"
else
    fail "Se requiere Python >= 3.9"
    exit 1
fi

# Load .env if present; fallback to compose defaults
if [ -f ".env" ]; then
    set -a; source .env; set +a
    ok ".env cargado (DB_HOST=${DB_HOST:-not set})"
elif [ -f "compose.yml" ]; then
    export DB_HOST="${DB_HOST:-mariadb}"
    export DB_PORT="${DB_PORT:-3306}"
    export DB_NAME="${DB_NAME:-sip_edge}"
    export DB_USER="${DB_USER:-sip_user}"
    export DB_PASSWORD="${DB_PASSWORD:-sip_pass}"
    export JWT_SECRET_KEY="${JWT_SECRET_KEY:-sip_edge_jwt_secret_key_dev}"
    export ADMIN_DEFAULT_PASSWORD="${ADMIN_DEFAULT_PASSWORD:-admin}"
    export DEV_MODE="${DEV_MODE:-true}"
    warn ".env no encontrado, usando defaults de compose.yml"
else
    warn "Sin .env ni compose.yml. Algunas pruebas pueden fallar."
fi

echo ""
echo -e "-- 1.5. Estado de sesion anterior --------------------------"

if [ -f "harness/.session" ]; then
    session_status=$(tr -d '[:space:]' < "harness/.session")
    if [ "$session_status" = "open" ]; then
        warn "Sesion anterior no cerrada (harness/.session = open)"
        echo "  Revisa harness/progress/current.md y git status."
        echo "  Ejecuta harness/scripts/close.sh para cerrar formalmente."
    elif [ "$session_status" = "closed" ]; then
        ok "Sesion anterior cerrada correctamente"
    else
        warn "harness/.session = '$session_status' (desconocido)"
    fi
else
    warn "harness/.session no existe. El agente debe crearlo."
fi

# === 2. Archivos base =======================================================
echo ""
echo -e "-- 2. Archivos base del harness ----------------------------"

base_files=(
    "harness/AGENTS.md"       "harness/VERSION"
    "harness/feature_list.json" "harness/progress/current.md"
    "harness/docs/architecture.md" "harness/docs/conventions.md"
    "harness/docs/verification.md" "harness/docs/specs.md"
    "harness/docs/environment.md"  "harness/docs/sessions.md"
    "harness/CHECKPOINTS.md"
)
for f in "${base_files[@]}"; do
    if [ -f "$f" ]; then ok "Existe $f"; else fail "Falta archivo base: $f"; fi
done

# === 3. Entorno =============================================================
echo ""
echo -e "-- 3. Entorno de ejecucion ---------------------------------"

is_in_container=false; has_compose=false; has_docker=false
[ -f /.dockerenv ] || [ -f /.containerenv ] && is_in_container=true
[ -f compose.yml ] || [ -f docker-compose.yml ] || [ -f docker-compose.yaml ] && has_compose=true
command -v docker &>/dev/null && has_docker=true

if $is_in_container; then
    ok "Ejecutando dentro de contenedor Docker"
elif $has_compose; then
    if $has_docker; then
        ok "compose.yml + Docker -- entorno de desarrollo"
    else
        warn "compose.yml detectado, Docker NO disponible. Modo nativo."
    fi
else
    ok "Entorno nativo (sin Docker)"
fi

# === 4. Schema BD ===========================================================
echo ""
echo -e "-- 4. Schema de base de datos ------------------------------"

if [ -f "harness/database/.schema_dump.json" ]; then
    ok "database/.schema_dump.json detectado"
    if "$PYTHON_BIN" harness/scripts/schema_dump.py &>/dev/null; then
        ok "docs/database.md regenerado desde la BD"
    else
        warn "schema_dump.py fallo (BD no disponible?)"
    fi
    if [ -d "harness/database/migrations" ]; then
        n=$(find harness/database/migrations -maxdepth 1 -name '*.sql' 2>/dev/null | wc -l)
        [ "$n" -gt 0 ] && ok "database/migrations/ contiene $n archivos SQL"
    fi
else
    [ -f "harness/docs/database.md" ] && ok "docs/database.md presente"
fi

# === 5. Validacion feature_list.json + specs ================================
echo ""
echo -e "-- 5. Validando feature_list.json y specs ------------------"

set +e
validation_output=$("$PYTHON_BIN" harness/scripts/validate_features.py 2>&1)
val_exit=$?
set -e
if [ $val_exit -ne 0 ]; then
    echo "$validation_output"
    fail "feature_list.json tiene errores de validacion"
else
    ok "feature_list.json es valido"
fi

# Verify specs for done/in_progress SDD features
set +e
"$PYTHON_BIN" << 'PYEOF'
import json, os, sys
with open("harness/feature_list.json", "r", encoding="utf-8") as f:
    data = json.load(f)
ok_flag = True
for feat in data["features"]:
    if feat.get("type","feature") == "bug": continue
    if not feat.get("sdd", False): continue
    if feat["status"] not in ("spec_ready", "in_progress", "done"): continue
    fid = feat["id"]; fname = feat["name"]
    spec_dir = f"harness/specs/{fid:02d}_{fname}"
    if not os.path.isdir(spec_dir):
        print(f"[FAIL] Falta carpeta spec: {spec_dir} (feature {fid} - {fname})")
        ok_flag = False; continue
    missing = [s for s in ("requirements.md","design.md","tasks.md")
               if not os.path.isfile(os.path.join(spec_dir, s))]
    if missing:
        for m in missing:
            print(f"[WARN] Falta {m} en {spec_dir} (feature {fid} - {fname})")
        ok_flag = False
    else:
        print(f"[OK] Spec completo para feature {fid} ({fname})")
if not ok_flag: sys.exit(1)
PYEOF
spec_exit=$?
set -e
[ $spec_exit -ne 0 ] && exit_code=1

# === 6. Tests ===============================================================
echo ""
echo -e "-- 6. Ejecutando tests -------------------------------------"

if [ ! -d "tests" ]; then
    warn "Carpeta tests/ no existe todavia"
else
    TIMEOUT_PER_MODULE=180
    passed=0; failed=0; hung=0

    for test_file in tests/test_*.py; do
        [ -f "$test_file" ] || continue
        mod_name=$(echo "$test_file" | sed 's|/|.|g; s|\.py$||')
        printf "  %-45s " "$mod_name"

        set +e
        result=$(timeout $TIMEOUT_PER_MODULE "$PYTHON_BIN" -m unittest "$mod_name" 2>&1)
        rc=$?
        set -e

        if [ $rc -eq 0 ]; then
            n=$(echo "$result" | grep -oP '^Ran \K\d+' || echo "?")
            echo -e "${GREEN}OK${NC} ($n tests)"
            passed=$((passed + 1))
        elif [ $rc -eq 124 ]; then
            echo -e "${YELLOW}HUNG${NC} (timeout ${TIMEOUT_PER_MODULE}s)"
            hung=$((hung + 1))
        else
            nf=$(echo "$result" | grep -cE '^(FAILED|ERROR):' 2>/dev/null || echo "?")
            echo -e "${RED}FAIL${NC} ($nf)"
            failed=$((failed + 1))
            exit_code=1
        fi
    done

    echo ""
    [ $hung -gt 0 ] && warn "$hung modulo(s) excedieron timeout (posiblemente esperando hardware/serial/modem)"
    if [ $failed -eq 0 ] && [ $hung -eq 0 ]; then
        ok "Todos los tests pasan ($passed modulos)"
    elif [ $failed -gt 0 ]; then
        fail "$failed modulo(s) con fallos (ejecuta con mas detalle para ver)"
    fi
fi

# === 7. Resumen =============================================================
echo ""
echo -e "-- 7. Resumen ---------------------------------------------"
if [ $exit_code -eq 0 ]; then
    ok "Entorno listo. Puedes empezar a trabajar."
else
    fail "Entorno NO esta listo. Resuelve los errores antes de avanzar."
fi
exit $exit_code
