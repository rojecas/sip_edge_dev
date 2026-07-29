#!/bin/bash
# sync.sh — EdgeBox: sincroniza sip_edge_dev -> sip_edge y reinicia servicio
set -e

DEV_DIR="/home/sipdev/sip_edge_dev"
PROD_DIR="/home/sipedge/sip_edge"

if [ ! -d "$PROD_DIR" ]; then
    echo "[FAIL] No se encontro sip_edge/ en $PROD_DIR"
    exit 1
fi

echo "[sync] sip_edge_dev -> sip_edge ..."
rsync -av --delete \
    --exclude='harness/' --exclude='.opencode/' --exclude='.git/' \
    --exclude='__pycache__/' --exclude='node_modules/' --exclude='.venv/' --exclude='venv/' \
    --exclude='sync.sh' --exclude='sync.ps1' \
    --exclude='.env' --exclude='config.yaml' --exclude='dump_weighings.sql' --exclude='init.ps1' \
    --exclude='.session' \
    "$DEV_DIR/" "$PROD_DIR/"

echo "[sync] Reiniciando servicio sip-edge..."
sudo systemctl restart sip-edge

echo "[sync] Completado."
