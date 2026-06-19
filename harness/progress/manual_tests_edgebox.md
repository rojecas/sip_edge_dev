# Test Manuales — EdgeBox (http://192.168.1.42:8000)

## Ya pasan (API, no requieren navegador)
- [PASS] Health check: curl devuelve {"status":"healthy"}
- [PASS] Login admin/admin: token JWT recibido
- [PASS] Login op_test/op_test: token JWT recibido
- [PASS] BD: 1 hacienda, 1 suerte, 25 pesajes (fechas 11-20 jun)
- [PASS] Filtro fecha (11-15): 5 registros
- [PASS] Emergency status endpoint responde
- [PASS] Backup status endpoint responde
- [PASS] Fix: pageSize como string (select muestra seleccion)
- [PASS] Fix: acentos Vag�n, Gu�a
- [PASS] Fix: layout pesos 160px, 32px, 3 en fila
- [PASS] Fix: boton Solicitar Modo Manual al fondo
- [PASS] Fix: ancho card 960 -> 1280px

## Test en navegador

### 1. Login admin
[ ] Abrir http://192.168.1.42:8000
[ ] Login con admin / admin
[ ] Ver dashboard con 5 cards (Config, Usuarios, Haciendas, Suertes, Backup)
[ ] Ver sidebar con 6 enlaces

### 2. Sidebar navigation
[ ] Click "Configuraci�n" -> /admin/config carga sin error
[ ] Click "Usuarios" -> /admin/usuarios carga sin error
[ ] Click "Haciendas" -> /admin/haciendas carga sin error
[ ] Click "Suertes" -> /admin/suertes carga sin error
[ ] Click "Backup" -> /admin/backup carga sin error
[ ] Secci�n activa resaltada en sidebar

### 3. Logout
[ ] Click "Cerrar sesi�n"
[ ] Modal de confirmaci�n aparece
[ ] Confirmar -> vuelve a login

### 4. Login operator + formulario kiosco
[ ] Login con op_test / op_test
[ ] Redirige a /kiosco
[ ] Campos visibles: Tractomula, Vag�n, Gu�a
[ ] Dropdown Hacienda: seleccionar "T01"
[ ] Dropdown Suerte se carga con "S01"
[ ] 3 campos de peso (160px, fuente 32px)
[ ] NO editables manualmente
[ ] Botones Tara y Leer en cada campo

### 5. Boton Solicitar Modo Manual
[ ] Bot�n rojo "Solicitar Modo Manual" al fondo del formulario
[ ] Click -> modal con dropdown de supervisores
[ ] Campo "Motivo" presente
[ ] Bot�n "Enviar solicitud" presente

### 6. Historial
[ ] Ir a /kiosco/historial
[ ] Tabla con 25 pesajes visibles
[ ] Columnas: Fecha, Hora, Tractomula, Vag�n, Gu�a, Hacienda, Suerte, Pesos
[ ] Acentos correctos en "Vag�n" y "Gu�a"

### 7. Paginaci�n
[ ] Select page size muestra "20 por p�gina" seleccionado
[ ] Cambiar a "10 por p�gina" -> 10 registros, select en "10"
[ ] Click Siguiente -> p�gina 2
[ ] Click Anterior -> p�gina 1
[ ] Cambiar a "50 por p�gina" -> 25 registros, select en "50"

### 8. Filtro de fechas
[ ] Seleccionar Desde=2026-06-11, Hasta=2026-06-15
[ ] Click Filtrar -> 5 registros
[ ] Click Limpiar -> 25 registros

### 9. URL directa sin JWT
[ ] Cerrar sesi�n
[ ] Navegar a http://192.168.1.42:8000/kiosco
[ ] Redirige al login (no muestra el kiosco)
