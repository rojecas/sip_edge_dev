# F43 — Corporate Branding (Identidad Corporativa Mayaguez)

## Paleta de Colores Corporativos

### R1
CUANDO se carga `app.css`, el sistema DEBE declarar las siguientes variables CSS
corporativas en `:root`:

| Variable            | Valor      | Referencia                  |
|---------------------|------------|-----------------------------|
| `--color-primary`   | `#FDB814`  | Amarillo corporativo        |
| `--color-primary-hover` | `#e5a612` | Hover del amarillo        |
| `--color-accent`    | `#32373c`  | Fondo oscuro (sidebar/header) |
| `--color-accent-hover` | `#3a3a3a` | Hover del fondo oscuro    |
| `--color-gray`      | `#f4f4f4`  | Texto claro                 |
| `--color-gray-dark` | `#878787`  | Texto secundario            |
| `--color-gray-darker` | `#646464` | Texto terciario             |

### R2
MIENTRAS el frontend está cargado, las variables funcionales existentes
(`--accent`, `--bg-primary`, `--bg-secondary`, `--bg-input`, `--text-primary`,
`--text-secondary`, `--border`) DEBEN reasignarse para reflejar la paleta
corporativa:

| Variable funcional   | Nuevo valor          |
|----------------------|----------------------|
| `--accent`           | `--color-primary`    |
| `--accent-hover`     | `--color-primary-hover` |
| `--bg-primary`       | `--color-accent`     |
| `--bg-secondary`     | `#3a3a3a`           |
| `--bg-input`         | `#2d2d2d`           |
| `--text-primary`     | `#f4f4f4`           |
| `--text-secondary`   | `#b0b0b0`           |
| `--border`           | `#4a4a4a`           |

### R3
Las variables semánticas `--success`, `--error` y `--warning` NO DEBEN
modificarse. Los valores actuales se preservan: verde éxito (`#51cf66`),
rojo error (`#ff6b6b`), amarillo procesando (`#ffd43b`).

## Tipografía Montserrat

### R4
CUANDO se carga `index.html`, el sistema DEBE incluir la hoja de estilos de
Google Fonts para la familia Montserrat con los pesos 300, 400, 600 y 700.

### R5
CUANDO el frontend se renderiza en el navegador, la propiedad `font-family` del
`body` DEBE declarar `"Montserrat", system-ui, -apple-system, sans-serif` como
primera opción, aplicando Montserrat a todos los elementos de texto en todas las
vistas (login, kiosko/\*, admin/\*).

## Logo Mayaguez

### R6
CUANDO el usuario ve el modal de login (`AuthModal.svelte`), el sistema DEBE
mostrar el logo corporativo (`/static/logo-mayaguez.png`) centrado arriba del
título "SIP-Edge", con altura máxima de 64px y manteniendo la relación de
aspecto.

### R7
MIENTRAS el usuario ve el layout de kiosko (`KioskLayout.svelte`,
rutas `/kiosco/*`), el sistema DEBE mostrar el logo corporativo en el
header, reemplazando o junto al texto "Sip-Edge" del elemento `.app-name`.

### R8
MIENTRAS el usuario ve el layout admin (`AdminLayout.svelte`, rutas
`/admin/*`), el sistema DEBE mostrar el logo corporativo en el
`sidebar-header`, sobre el título "SIP-Edge Admin".

## Modal About

### R9
DONDE el modal About (`AboutModal.svelte`) está visible, el sistema DEBE
mostrar: razón social "Ingenio Mayagüez S.A.", versión del sistema
("SIP-Edge v1.0"), copyright "(c) 2026 Ingenio Mayagüez S.A. Todos los
derechos reservados.", y disclaimer legal. (YA IMPLEMENTADO)

### R10
DONDE el modal About (`AboutModal.svelte`) está visible, el sistema DEBE usar
el logo corporativo (`/static/logo-mayaguez.png`) como imagen principal en lugar
del placeholder actual (`/static/favicon.png`), con dimensiones de 64x64
píxeles y borde redondeado.

## Favicon

### R11
CUANDO el navegador carga la aplicación, el favicon en
`frontend/public/favicon.png` DEBE ser el isotipo de Mayaguez (versión a color
del logo). (YA IMPLEMENTADO)

## Sidebar de Administración

### R12
MIENTRAS el sidebar de admin está visible (`AdminLayout.svelte`), DEBE tener
fondo `var(--color-accent)` (#32373c) con texto en gris claro (#f4f4f4). La
sección activa (`.sidebar-link.active`) DEBE resaltarse con
`var(--color-primary)` (#FDB814) como color de fondo.

### R13
MIENTRAS el sidebar de admin está visible, el `sidebar-header` DEBE mostrar
el logo de Mayaguez (64x64px) centrado y debajo el título "SIP-Edge Admin"
en color `var(--color-primary)`.

## Componentes de Formulario

### R14
CUANDO un botón primario (`.btn-primary` o elementos equivalentes con
background `var(--accent)`) se renderiza, DEBE usar
`background: var(--color-primary)` como color principal.

### R15
MIENTRAS un campo de entrada (input, select, textarea) tiene foco, el borde
DEBE usar `border-color: var(--color-primary)` en lugar de
`var(--accent)`.

### R16
CUANDO un enlace se renderiza en cualquier vista, DEBE usar
`color: var(--color-primary)` como color de texto.

## Corrección ⓘ en AdminLayout

### R17
SI el layout admin se renderiza, ENTONCES el botón ⓘ con clase
`.sidebar-about` (About) DEBE ser visible sin quedar oculto total o
parcialmente por el `LogoutButton` de posición fija. El botón DEBE estar
íntegramente dentro del flujo del `header-right` y responder al click
abriendo el `AboutModal`.
