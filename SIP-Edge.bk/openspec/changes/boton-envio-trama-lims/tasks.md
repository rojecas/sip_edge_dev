## 1. Driver Serial RS-232 para LIMS

- [ ] 1.1 Implementar driver serial RS-232 para salida unidireccional a LIMS
- [ ] 1.2 Implementar función de construcción de trama CSV con el formato definido
- [ ] 1.3 Implementar generación de Id autoincremental (desde BD o archivo)

## 2. Configuración de Puerto LIMS

- [ ] 2.1 Agregar sección `lims` en config.yaml (port, baudrate, parity)
- [ ] 2.2 Agregar interfaz Admin para configuración de puerto LIMS
- [ ] 2.3 Agregar función "Test" de conectividad para puerto LIMS

## 3. UI - Botón en Kiosko

- [ ] 3.1 Agregar botón "Enviar a LIMS" en formulario de pesaje
- [ ] 3.2 Implementar validación de completitud de campos obligatorios
- [ ] 3.3 Implementar habilitación/deshabilitación dinámica del botón según validación
- [ ] 3.4 Implementar endpoint backend para construir y enviar trama
- [ ] 3.5 Implementar feedback visual de envío exitoso/fallido

## 4. Trazabilidad y Logs

- [ ] 4.1 Registrar en log cada envío de trama con timestamp, Id y resultado
- [ ] 4.2 Almacenar trama enviada en BD para trazabilidad (opcional, según decisión)
