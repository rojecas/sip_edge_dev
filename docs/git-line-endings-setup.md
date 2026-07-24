# Configuración de Line Endings — Entorno Multi-SO

> Evita conflictos de CRLF/LF entre Windows (desarrollo) y Linux (EdgeBox).

## Windows 10 — Máquina de desarrollo

Ejecutar en PowerShell o Git Bash, **una sola vez**:

```bash
git config --global core.autocrlf true
```

**Efecto:** al commitear convierte CRLF → LF (repo limpio). Al hacer checkout convierte LF → CRLF (compatible con editores Windows).

---

## EdgeBox Linux — Producción

Ya aplicado:

```bash
git config core.autocrlf input
```

**Efecto:** al commitear convierte CRLF → LF. Al hacer checkout **no** convierte (Linux ya usa LF).

---

## `.gitattributes` — Archivos compilados del frontend

Agregado al repo:

```
src/static/* -text
```

Los archivos en `src/static/` son generados por `npm run build`. Se tratan como binarios para evitar que git modifique sus line endings en ningún SO.

---

## Verificación

Para confirmar que la configuración es correcta:

```bash
# Windows
git config --global core.autocrlf   # debe decir: true

# Linux
git config core.autocrlf            # debe decir: input
```
