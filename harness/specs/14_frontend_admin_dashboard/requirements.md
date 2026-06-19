# Requirements — Frontend Admin: Dashboard y Navegación

> Feature 14 (14a) — Fundación del módulo administrativo. EARS notation.
> Corresponde a la subdivisión 14a de la feature 14 original (R1-R6, R34, R35, R38, R41).

---

## R1
CUANDO un usuario autenticado con rol "admin" navega a `/admin`, el sistema
DEBE mostrar un dashboard con cards de acceso rapido a cada seccion
administrativa: Configuracion, Usuarios, Haciendas, Suertes, y Backup. Cada
card DEBE contener un titulo, un icono, y un enlace que navega a la ruta
correspondiente. Cubre: RF-F14-01a.

## R2
CUANDO el admin hace clic en la card "Configuracion" del dashboard, el sistema
DEBE navegar a `/admin/config`. Cubre: RF-F14-01a.

## R3
CUANDO el admin hace clic en la card "Usuarios" del dashboard, el sistema
DEBE navegar a `/admin/usuarios`. Cubre: RF-F14-01a.

## R4
CUANDO el admin hace clic en la card "Haciendas" del dashboard, el sistema
DEBE navegar a `/admin/haciendas`. Cubre: RF-F14-01a.

## R5
CUANDO el admin hace clic en la card "Suertes" del dashboard, el sistema
DEBE navegar a `/admin/suertes`. Cubre: RF-F14-01a.

## R6
CUANDO el admin hace clic en la card "Backup" del dashboard, el sistema
DEBE navegar a `/admin/backup`. Cubre: RF-F14-01a.

## R7
MIENTRAS el admin esta en cualquier vista de administracion
(`/admin`, `/admin/config`, `/admin/usuarios`, `/admin/haciendas`,
`/admin/suertes`, `/admin/backup`), el sistema DEBE mostrar un sidebar o
barra de navegacion lateral con enlaces a todas las secciones administrativas,
permitiendo la navegacion rapida entre secciones. El sidebar DEBE resaltar
visualmente la seccion activa. Cubre: RF-F14-01b, RF-F14-01c.

## R8
El sistema DEBE validar que solo los usuarios con rol "admin" puedan acceder
a cualquier ruta bajo `/admin/`. SI un usuario con rol "operator" intenta
navegar a `/admin/*`, el sistema DEBE redirigirlo a `/kiosco`. Cubre: RF-F14-01d.

## R9
CUANDO el admin navega a cualquier sub-ruta de administracion
(`/admin/config`, `/admin/usuarios`, `/admin/haciendas`, `/admin/suertes`,
`/admin/backup`) directamente por URL (sin pasar por el dashboard), el
sistema DEBE cargar la seccion correspondiente correctamente. Cubre: RF-F14-01e.

## R10
CUANDO el admin esta en cualquier vista de administracion y la sesion expira
(HTTP 401 del backend), el sistema DEBE redirigir al modal de login con el
mensaje "Sesion expirada o no autorizada". Esto DEBE ser manejado por el
interceptor 401 del `api.js` existente. Cubre: RF-F14-01f.
