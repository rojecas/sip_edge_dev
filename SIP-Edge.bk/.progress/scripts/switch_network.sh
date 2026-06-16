#!/bin/bash
# Cambiar interfaz de red principal
# Uso: switch_network.sh [4g|eth|dual|status]

# Ver estado actual
# sudo /usr/local/bin/switch_network.sh status

# Activar ambas interfaces (Ethernet principal, 4G respaldo)
# sudo /usr/local/bin/switch_network.sh dual

# Verificar que ambas están activas
# ip route show | grep default
# Deberías ver dos líneas: una por eth0 (metric 100) y otra por wwan0 (metric 200)

# Probar envío de SMS (debería funcionar siempre)
# sudo mmcli -m 0 --messaging-create-sms="number='+573006117436',text='Prueba con interfaz dual'"
# Tomar nota del ID y enviar
# sudo mmcli -s <ID> --send

# Volver a solo ethernet si deseas
#sudo /usr/local/bin/switch_network.sh eth

# Volver a solo 4G
# sudo /usr/local/bin/switch_network.sh 4g


# Obtener nombres reales de las conexiones
ETH_CONN=$(nmcli connection show --active 2>/dev/null | grep -E "ethernet|Wired|eth0" | head -1 | awk '{print $1}')
if [ -z "$ETH_CONN" ]; then
    # Buscar conexión ethernet aunque no esté activa
    ETH_CONN=$(nmcli connection show 2>/dev/null | grep -E "ethernet|Wired" | head -1 | awk '{print $1}')
    if [ -z "$ETH_CONN" ]; then
        ETH_CONN="Wired connection 1"
    fi
fi

CONN_4G="Quectel-4G"

case "$1" in
    4g)
        echo "Cambiando a conexión 4G (solo 4G)..."
        # Verificar si el módem está disponible
        if ! mmcli -L 2>/dev/null | grep -q Modem; then
            echo "Error: Módem 4G no detectado"
            exit 1
        fi
        
        # Dar prioridad a 4G
        sudo nmcli connection modify "$CONN_4G" ipv4.route-metric 100 2>/dev/null
        sudo nmcli connection modify "$ETH_CONN" ipv4.route-metric 200 2>/dev/null
        
        # Activar 4G y desactivar ethernet
        sudo nmcli connection up "$CONN_4G" 2>/dev/null
        sudo nmcli connection down "$ETH_CONN" 2>/dev/null
        
        echo "✓ Usando solo 4G (wwan0)"
        ;;
    eth)
        echo "Cambiando a conexión Ethernet (solo Ethernet)..."
        # Dar prioridad a Ethernet
        sudo nmcli connection modify "$ETH_CONN" ipv4.route-metric 100 2>/dev/null
        sudo nmcli connection modify "$CONN_4G" ipv4.route-metric 200 2>/dev/null
        
        # Activar ethernet y desactivar 4G
        sudo nmcli connection up "$ETH_CONN" 2>/dev/null
        sudo nmcli connection down "$CONN_4G" 2>/dev/null
        
        echo "✓ Usando solo Ethernet"
        ;;
    dual)
        echo "Activando ambas interfaces (4G como respaldo)..."
        
        # Verificar si el módem está disponible
        if ! mmcli -L 2>/dev/null | grep -q Modem; then
            echo "Error: Módem 4G no detectado"
            exit 1
        fi
        
        # Activar ambas interfaces
        sudo nmcli connection up "$ETH_CONN" 2>/dev/null
        sudo nmcli connection up "$CONN_4G" 2>/dev/null
        
        # Configurar métricas: Ethernet como principal (métrica más baja)
        sudo nmcli connection modify "$ETH_CONN" ipv4.route-metric 100 2>/dev/null
        sudo nmcli connection modify "$CONN_4G" ipv4.route-metric 200 2>/dev/null
        
        # Reiniciar conexiones para aplicar métricas
        sudo nmcli connection down "$ETH_CONN" 2>/dev/null && sudo nmcli connection up "$ETH_CONN" 2>/dev/null
        sudo nmcli connection down "$CONN_4G" 2>/dev/null && sudo nmcli connection up "$CONN_4G" 2>/dev/null
        
        echo "✓ Ambas interfaces activas"
        echo "  - Ethernet: principal (métrica 100)"
        echo "  - 4G: respaldo (métrica 200)"
        echo "  Si Ethernet falla, el tráfico pasará automáticamente a 4G"
        ;;
    status)
        echo "=== Interfaces activas ==="
        ip route show | grep default
        
        echo -e "\n=== Métricas actuales ==="
        if nmcli connection show "$ETH_CONN" &>/dev/null; then
            METRIC_ETH=$(nmcli connection show "$ETH_CONN" | grep ipv4.route-metric | awk '{print $2}')
            STATUS_ETH=$(nmcli connection show --active | grep -c "$ETH_CONN")
            echo "Ethernet ($ETH_CONN): métrica ${METRIC_ETH:-desconocida} - $([ $STATUS_ETH -gt 0 ] && echo 'activa' || echo 'inactiva')"
        fi
        
        if nmcli connection show "$CONN_4G" &>/dev/null; then
            METRIC_4G=$(nmcli connection show "$CONN_4G" | grep ipv4.route-metric | awk '{print $2}')
            STATUS_4G=$(nmcli connection show --active | grep -c "$CONN_4G")
            echo "4G ($CONN_4G): métrica ${METRIC_4G:-desconocida} - $([ $STATUS_4G -gt 0 ] && echo 'activa' || echo 'inactiva')"
        fi
        
        echo -e "\n=== Conexiones activas ==="
        nmcli connection show --active 2>/dev/null | grep -E "$ETH_CONN|$CONN_4G" || echo "Ninguna conexión activa"
        
        echo -e "\n=== IP pública actual ==="
        IP_PUB=$(curl -s --max-time 5 ifconfig.me 2>/dev/null)
        if [ -n "$IP_PUB" ]; then
            echo "$IP_PUB"
            # Intentar identificar qué interfaz está usando
            if ip route get "$IP_PUB" 2>/dev/null | grep -q "wwan0"; then
                echo "(saliendo por 4G)"
            elif ip route get "$IP_PUB" 2>/dev/null | grep -q "eth0"; then
                echo "(saliendo por Ethernet)"
            fi
        else
            echo "No se pudo determinar (¿sin internet?)"
        fi
        
        echo -e "\n=== SMS: estado del módem 4G ==="
        if mmcli -L 2>/dev/null | grep -q Modem; then
            SIGNAL=$(mmcli -m 0 2>/dev/null | grep "signal quality" | awk '{print $3}')
            echo "Módem 4G: presente - Señal: ${SIGNAL:-desconocida}"
            echo "Envío de SMS: disponible (independiente de la ruta de internet)"
        else
            echo "Módem 4G: no detectado"
        fi
        ;;
    *)
        echo "Uso: $0 [4g|eth|dual|status]"
        echo "  4g     - Usar solo módulo 4G como salida"
        echo "  eth    - Usar solo Ethernet como salida"
        echo "  dual   - Usar ambas interfaces (Ethernet principal, 4G respaldo)"
        echo "  status - Mostrar estado actual"
        ;;
esac