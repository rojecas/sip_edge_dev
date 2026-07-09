# Pruebas Manuales — Feature 13 (frontend_login_kiosk)
# Fecha: 2026-07-09
# Setup: COM1 (115200-8N1) -> conversor RS232/RS485 -> EdgeBox /dev/ttyACM0

================================================================================
CONFIGURACION DEL TERMINAL (Putty)
================================================================================
  Puerto:    COM1
  Baudrate:  115200 (ajusta segun config del SIP-Edge)
  Data bits: 8
  Paridad:   None
  Stop bits: 1
  Flow:      None

================================================================================
PROTOCOLO DINI ARGEO DFWLI-2 — REFERENCIA RAPIDA
================================================================================

COMANDOS que envia el EdgeBox (los ves en Putty):
  Leer -> 00REXT
  Tara -> 00TARE

RESPUESTAS que debes escribir (copia/pega en Putty + Enter):

  [A] Lectura estable, 25.500 kg:
      01ST,1,25.500,PT 0.0,0,kg

  [B] Lectura inestable, 10.350 kg:
      01US,1,10.350,PT 0.0,0,kg

  [C] Lectura con tara de 5.0 kg:
      01ST,1,20.500,PT 5.0,0,kg

  [D] Peso cero:
      01ST,1,0.000,PT 0.0,0,kg

  [E] OK (confirmacion de Tara/ZERO/CLEAR):
      OK

  [F] PRINT simulado (escribir SIN que EdgeBox haya enviado comando):
      01ST,1,32.150,PT 0.0,0,kg

================================================================================
SECCION 1 — BOTONES LEER Y TARA (R15, R16, R43) [NUEVO]
================================================================================

M1 — Leer con respuesta exitosa
  1. En /kiosco, clic en "Leer" junto a "Peso Muestra"
  2. Ver "00REXT" en Putty
  3. Responder: 01ST,1,25.500,PT 0.0,0,kg
  => Campo "Peso Muestra" muestra 25.500 kg. Indicador verde "Estable".

M2 — Leer con bascula inestable
  1. Clic en "Leer" junto a "Peso Mineral"
  2. Responder: 01US,1,10.350,PT 0.0,0,kg
  => Campo muestra 10.350. Indicador amarillo "Inestable".

M3 — Leer los 3 campos independientemente
  1. Repetir M1 para Muestra, Mineral, Vegetal (3 clics)
  => Cada campo conserva su propio peso. No se sobreescriben entre si.

M4 — Tara exitoso
  1. Con un campo con peso >0, clic en "Tara"
  2. Ver "00TARE" en Putty
  3. Responder: OK
  => Campo se pone en 0.000

M5 — Tara sin respuesta (bascula desconectada / timeout)
  1. Desconectar conversor RS485, clic en "Tara"
  2. Esperar ~4 segundos
  => Error en consola/notificacion. Boton se re-habilita.
     (OPORTUNIDAD: esto podria usarse para detectar "balanza desconectada")

M6 — Leer sin respuesta (timeout)
  1. Sin el conversor conectado, clic en "Leer"
  2. Esperar ~4s
  => Error. Boton se re-habilita.

================================================================================
SECCION 2 — AUTO-CAPTURE PRINT (R44) [NUEVO]
================================================================================

M7 — PRINT con campo en foco (captura automatica)
  1. Hacer clic DENTRO del campo "Peso Muestra" (cursor visible)
  2. SIN tocar el kiosco, escribir en Putty: 01ST,1,32.150,PT 0.0,0,kg
  => El peso 32.150 aparece AUTOMATICAMENTE en "Peso Muestra"

M8 — PRINT con otro campo en foco
  1. Clic dentro de "Peso Mineral"
  2. Escribir en Putty: 01ST,1,18.750,PT 0.0,0,kg
  => Peso 18.750 aparece en "Peso Mineral"

M9 — PRINT sin ningun campo con foco
  1. Clic fuera del formulario (en cualquier area vacia)
  2. Escribir en Putty: 01ST,1,45.200,PT 0.0,0,kg
  => Notificacion temporal: "Peso recibido: 45.200 kg" (desaparece en ~3s)

M10 — La notificacion no interfiere
  1. Escribir PRINT (M9) y mientras la notificacion esta visible,
     escribir en campos de texto (tractomula, vagon)
  => Formulario sigue funcionando normalmente

================================================================================
SECCION 3 — REGRESION: MODO EMERGENCIA (R24, R25) [CORREGIDO]
================================================================================

M11 — Sin modo manual: campos NO editables
  1. Verificar que NO hay modo manual activo (sin banner rojo)
  2. Intentar escribir en "Peso Muestra"
  => Campo DESHABILITADO (gris, no acepta entrada)

M12 — Activar modo manual (admin envia SMS "manual on")
  1. Esperar ~15s (polling cada 5s)
  => Aparece banner rojo "MODO MANUAL ACTIVO" con tiempo restante

M13 — Modo manual activo: campos SI editables
  1. Con banner de emergencia visible, escribir "15.750" en "Peso Muestra"
  => El valor se acepta. Campo editable.

M14 — Pesaje en modo manual
  1. Llenar todos los campos (tractomula, vagon, guia, hacienda, suerte)
  2. Poner pesos manuales en los 3 campos
  3. Clic en Confirmar
  => "Pesaje registrado". Formulario limpio.

M15 — Desactivar modo manual ("manual off")
  1. Esperar polling (~5-15s)
  => Banner desaparece. Campos vuelven a NO editables.

================================================================================
SECCION 4 — WEBSOCKET PESO EN VIVO (R17, R35, R45)
================================================================================

M16 — Indicador de peso en vivo
  1. En /kiosco, ver el indicador de peso en la parte superior
  2. Enviar varios PRINT en Putty con pesos diferentes:
     01ST,1,10.100,PT 0.0,0,kg
     01ST,1,10.200,PT 0.0,0,kg
     01US,1,10.350,PT 0.0,0,kg
     01ST,1,10.300,PT 0.0,0,kg
  => El indicador se actualiza en tiempo real con cada valor

M17 — Indicador estable (verde)
  1. Enviar: 01ST,1,50.000,PT 0.0,0,kg
  => Indicador verde + "Estable"

M18 — Indicador inestable (amarillo)
  1. Enviar: 01US,1,50.000,PT 0.0,0,kg
  => Indicador amarillo + "Inestable"

M19 — ScaleReader no interferido por Leer/Tara
  1. Usar Leer y Tara varias veces
  2. Verificar que el indicador de peso en vivo SIGUE actualizandose
  => El indicador NUNCA se congela

================================================================================
SECCION 5 — SMOKE TEST: FLUJO COMPLETO DE PESAJE
================================================================================

M20 — Formulario completo
  1. Llenar Tractomula: "ABC123", Vagon: "V001", Guia: "G-2026"
  2. Seleccionar Hacienda del dropdown
  3. Verificar que dropdown Suerte se actualiza (muestra "Cargando..." breve)
  4. Seleccionar Suerte
  5. Leer los 3 pesos (M1 x3, responder cada uno)
  6. Clic en Confirmar
  => "Pesaje registrado". Formulario limpio.

M21 — Reset con confirmacion
  1. Llenar algunos campos
  2. Clic en "Reset"
  3. Modal "Esta seguro de limpiar el formulario?" -> Confirmar
  => Todos los campos vacios

M22 — Reset cancelado
  1. Llenar campos. Clic Reset -> Cancelar
  => Campos intactos

M23 — Validacion de campos requeridos
  1. Dejar campos vacios, clic en Confirmar
  => NO se envia. Debe indicar campos faltantes.

================================================================================
SECCION 6 — HISTORIAL (R22, R37-R39)
================================================================================

M24 — Tabla de historial
  1. Navegar a /kiosco/historial
  => Tabla con pesajes del operador, ordenados por fecha (mas reciente primero)

M25 — Paginacion
  1. Si hay >20 registros, verificar botones Anterior/Siguiente
  => Paginacion funcional

M26 — Filtro por fechas
  1. Seleccionar "Fecha desde" y "Fecha hasta"
  => Tabla se recarga con registros en ese rango

================================================================================
SECCION 7 — LOGIN / LOGOUT / SESION
================================================================================

M27 — Login operator
  1. Abrir http://192.168.1.42:8000
  2. Login: operador1 / <password>
  => Redirige a /kiosco. Nombre de usuario visible arriba izquierda

M28 — Logout
  1. Clic en "Cerrar sesion"
  2. Confirmar en modal
  => Vuelve al login. localStorage limpio.

M29 — Enter en campo contraseña
  1. En modal login, escribir usuario + contraseña, presionar Enter
  => Mismo efecto que clic en "Iniciar Sesion"

M30 — Login credenciales incorrectas
  1. Usuario o contraseña erroneos
  => "Usuario o contrasena incorrectos". No redirige.

M31 — Sesion expirada por inactividad
  1. Estar autenticado. Esperar timeout de sesion (15 min por defecto)
  => Cierra sesion automaticamente. "Sesion expirada".

================================================================================
SECCION 8 — EMERGENCIA (R23, R26-R28)
================================================================================

M32 — Polling de emergencia
  1. Abrir DevTools (F12) -> Network. Estar en /kiosco
  => Cada 5s: GET /api/emergency/status

M33 — Solicitar emergencia
  1. Clic en "Solicitar emergencia"
  2. Seleccionar supervisor del dropdown, escribir motivo, Enviar
  => "Solicitud enviada. Espere respuesta del supervisor."

================================================================================
RESUMEN
================================================================================
  [NUEVO]    Seccion 1-2:  Leer/Tara via API, auto-capture PRINT  (10 pruebas)
  [CORREGIDO] Seccion 3:   Modo emergencia reactivo                (5 pruebas)
  [REGRESION] Seccion 4:   WebSocket peso en vivo                  (4 pruebas)
  [SMOKE]     Seccion 5-8: Flujo completo                          (14 pruebas)
  TOTAL: 33 pruebas
