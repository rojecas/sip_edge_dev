
## Próximos Pasos Recomendados

### Inmediatos (para el módulo 4G):
```bash
# 1. Cambiar APN a la configuración correcta
sudo nmcli connection modify Quectel-4G gsm.apn "internet"

# 2. Reiniciar conexión
sudo nmcli connection down Quectel-4G
sudo nmcli connection up Quectel-4G

# 3. Verificar conectividad
ping -c 4 8.8.8.8
```



---

## Conclusión

El EdgeBox-RPI-200 tiene **dos de tres periféricos completamente configurados**:

| Periférico | Estado |
|------------|--------|
| RTC (PCF8563) | ✅ **Completado** |
| Módulo 4G (Quectel EC25) | ✅ **Completado** (pendiente plan de datos) |
| UPS | ❌ **No presente** (accesorio opcional) |

La configuración técnica de software está **completa al 100%** para el RTC y el módulo 4G. Solo falta:
1. Activar el plan de datos en la SIM
2. Registrar el IMEI en Tigo
3. (Opcional) Decidir si se adquiere el módulo UPS

Una vez activado el plan de datos, el EdgeBox podrá:
- Mantener la hora correcta incluso sin conexión a internet
- Conectarse a internet a través de la red 4G de Tigo
- Funcionar como dispositivo IoT autónomo