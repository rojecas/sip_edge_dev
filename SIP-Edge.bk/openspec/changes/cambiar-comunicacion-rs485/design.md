## Context

La báscula industrial del laboratorio utiliza bus RS-485, no RS-232 como se especificaba originalmente. RS-485 es un estándar serial diferencial que soporta múltiples dispositivos en un mismo bus (multi-drop) y mayores distancias (hasta 1200m), pero opera en half-duplex, requiriendo control explícito de dirección de transmisión/recepción.

Hardware requerido: adaptador USB-RS485 (ej: FTDI USB-RS485 o similar con control RTS). El EdgeBox RPi-200 no tiene puerto RS-485 nativo, por lo que la comunicación será vía USB.

## Goals / Non-Goals

**Goals:**
- Implementar driver serial para RS-485 half-duplex con control de dirección vía RTS
- Agregar configuración de dirección de dispositivo y terminación en interfaz Admin
- Mantener compatibilidad con el protocolo comando-respuesta existente

**Non-Goals:**
- Implementar protocolo Modbus RTU (a menos que la báscula lo requiera, confirmar con fabricante)
- Soportar múltiples dispositivos RS-485 simultáneos en v1.0

## Decisions

1. **Control de dirección vía RTS en lugar de GPIO**: La mayoría de adaptadores USB-RS485 manejan automáticamente RTS para alternar TX/RX. Usar RTS es más portable que asignar un GPIO específico. Alternativa considerada: control por GPIO software — descartada por depender del pinout específico del EdgeBox.

2. **Abstracción del driver serial existente en lugar de reemplazo**: El cambio de RS-232 a RS-485 afecta solo la capa de control de flujo, no el protocolo de comando-respuesta. Se implementa como una variante del driver existente seleccionable por configuración.

3. **Detección de colisiones con backoff exponencial**: Dado que RS-485 es half-duplex, existe riesgo de colisión si otro dispositivo transmite simultáneamente. Backoff aleatorio simple evita esquemas complejos manteniendo el determinismo del sistema.

## Risks / Trade-offs

- [Compatibilidad de adaptadores] No todos los adaptadores USB-RS485 manejan RTS de la misma forma → Mitigación: Probar con el adaptador especificado por el fabricante y documentar modelos compatibles.
- [Distancia de bus] RS-485 permite hasta 1200m, pero la calidad del cableado existente es desconocida → Mitigación: incluir rutina de diagnóstico de integridad de señal en la función "Test" de configuración.
- [Terminación] La terminación incorrecta del bus causa reflexiones de señal y datos corruptos → Mitigación: documentar claramente en la UI de configuración que la terminación física debe coincidir con la configuración lógica.
- [Migración] Los adaptadores USB-RS232 existentes quedarán obsoletos → Mitigación: el driver es configurable, permitiendo usar RS-232 o RS-485 según el hardware conectado.

## Migration Plan

1. Reemplazar adaptador USB-RS232 por USB-RS485 en el EdgeBox
2. Configurar dirección de dispositivo RS-485 en interfaz Admin
3. Verificar terminación del bus según especificación del fabricante
4. Ejecutar prueba de conectividad (función "Test")
5. Verificar lectura de peso en producción

Rollback: Mantener el adaptador USB-RS232 y la configuración RS-232 como respaldo; el cambio en el driver es conmutativo por configuración.

## Open Questions

- ¿La báscula utiliza protocolo ASCII estándar sobre RS-485 o necesita un protocolo específico (ej: Modbus RTU)? Confirmar con fabricante.
- ¿Hay otros dispositivos en el mismo bus RS-485 o solo la báscula?
- ¿Cuál es la velocidad en baudios soportada por el adaptador USB-RS485 y la báscula?
