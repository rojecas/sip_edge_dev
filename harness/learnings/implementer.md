# Lecciones para el Implementer

## Encoding y escritura de archivos en Windows
- En entornos Windows con PS 5.1, el shell opera en CP-1252 por defecto.
  Al escribir archivos con caracteres Unicode (acentos, enie, emojis) desde
  Python, verifica que el script use encoding='utf-8' explicito en open().
  NUNCA confies en el locale del sistema.
- El pipeline de corrupcion mas comun: UTF-8 valido -> leido por shell como
  CP-1252 -> guardado como UTF-8 (doble codificacion). Produce mojibake como
  "aprobacion" -> "aprobaciA?A3n".
- Si encuentras caracteres corruptos en archivos existentes, diagnostica con
  bytes.hex() antes de asumir que es un error de tu implementacion.
- SOLUCION RAPIDA: $OutputEncoding = [System.Text.Encoding]::UTF8 al inicio
  de scripts PS1. A largo plazo: ACP=65001 en registry (requiere reboot).

## Escritura de JSON
- NUNCA uses regex o -replace en PS para modificar JSON.
- Siempre usa Python: json.load() -> modificar -> json.dump().
- Usa ensure_ascii=False para preservar caracteres Unicode en el JSON.
