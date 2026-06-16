## 1. Driver Serial RS-485

- [ ] 1.1 Implementar driver serial con soporte half-duplex y control RTS
- [ ] 1.2 Implementar direccionamiento de dispositivo en bus RS-485
- [ ] 1.3 Implementar detección de colisiones con backoff aleatorio y reintentos (hasta 3)
- [ ] 1.4 Refactorizar driver existente para que RS-232 y RS-485 sean seleccionables por configuración

## 2. Configuración

- [ ] 2.1 Agregar campos de dirección de dispositivo y habilitación de terminación RS-485 en config.yaml
- [ ] 2.2 Agregar campos de configuración RS-485 en interfaz Admin
- [ ] 2.3 Actualizar función "Test" de conectividad para incluir diagnóstico de integridad de señal RS-485

## 3. Documentación y Hardware

- [ ] 3.1 Actualizar ERS y specs existentes (weighing-scale) con RS-485
- [ ] 3.2 Documentar adaptadores USB-RS485 compatibles y procedimiento de instalación
- [ ] 3.3 Adquirir e instalar adaptador USB-RS485 en EdgeBox
- [ ] 3.4 Verificar terminación del bus RS-485 según especificación del fabricante

## 4. Pruebas

- [ ] 4.1 Probar comunicación RS-485 con báscula en entorno de desarrollo
- [ ] 4.2 Probar conmutación RS-232/RS-485 por configuración
- [ ] 4.3 Probar detección de colisiones y reintentos
- [ ] 4.4 Probar timeout y escenarios de error
