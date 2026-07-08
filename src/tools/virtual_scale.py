"""Balanza Virtual DINI ARGEO DFWLI-2 para desarrollo y pruebas.

Simula el protocolo DINI ARGEO DFWLI-2 via puerto serial, respondiendo
a los comandos REXT, TARE, TMAN, ZERO y CLEAR con datos desde archivos
CSV pre-generados. Incluye un REPL interactivo (Windows-only, usa msvcrt)
para navegar por las medidas y simular eventos de la balanza real.

Uso:
    python src/tools/virtual_scale.py --port COM3 --dataset B
"""

import argparse
import csv
import os
import random
import select
import sys
import time

try:
    import msvcrt  # Windows-only: lectura de teclado sin Enter
except ImportError:
    msvcrt = None  # type: ignore[assignment]

try:
    import serial
except ImportError:
    serial = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# constantes del protocolo
# ---------------------------------------------------------------------------

CMD_REXT = "00REXT"
CMD_TARE = "00TARE"
CMD_ZERO = "00ZERO"
CMD_CLEAR = "00CLEAR"
CMD_TMAN_PREFIX = "00TMAN"

# Columnas esperadas en el CSV
EXPECTED_COLUMNS = [
    "status_muestra",
    "peso_muestra",
    "status_mineral",
    "peso_mineral",
    "status_vegetal",
    "peso_vegetal",
    "unit",
]

SUB_STEP_NAMES = ["muestra", "mineral", "vegetal"]


# ---------------------------------------------------------------------------
# T5 â€” carga de dataset
# ---------------------------------------------------------------------------


def load_dataset(data_dir: str, dataset_id: str) -> list[dict]:
    """Carga el CSV del dataset y devuelve una lista de dicts.

    Valida: existencia del archivo, header de 7 columnas exactas,
    y parseo numÃ©rico de los pesos.  Lanza SystemExit en caso de error.
    """
    filepath = os.path.join(data_dir, f"dataset_{dataset_id.upper()}.csv")
    if not os.path.isfile(filepath):
        print(f"ERROR: Dataset no encontrado: {filepath}", file=sys.stderr)
        sys.exit(1)

    rows: list[dict] = []
    with open(filepath, "r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)

        if header is None:
            print(f"ERROR: El archivo {filepath} esta vacio.", file=sys.stderr)
            sys.exit(1)

        if header != EXPECTED_COLUMNS:
            print(
                f"ERROR: Header del CSV no coincide con el formato esperado. "
                f"Se esperaba: {EXPECTED_COLUMNS}, se obtuvo: {header}",
                file=sys.stderr,
            )
            sys.exit(1)

        for line_num, cols in enumerate(reader):
            try:
                peso_muestra = float(cols[1])
                peso_mineral = float(cols[3])
                peso_vegetal = float(cols[5])
            except (ValueError, IndexError) as exc:
                print(
                    f"ERROR: Fila {line_num + 1} del CSV contiene datos no "
                    f"numÃ©ricos donde se esperaban pesos: {exc}",
                    file=sys.stderr,
                )
                sys.exit(1)

            rows.append({
                "status_muestra": cols[0].strip(),
                "peso_muestra": peso_muestra,
                "status_mineral": cols[2].strip(),
                "peso_mineral": peso_mineral,
                "status_vegetal": cols[4].strip(),
                "peso_vegetal": peso_vegetal,
                "unit": cols[6].strip(),
            })

    return rows


# ---------------------------------------------------------------------------
# T6 â€” lectura actual
# ---------------------------------------------------------------------------


def _current_reading(
    pointer: tuple[int, int],
    dataset: list[dict],
    override: float | None,
) -> dict:
    """Devuelve un dict con status, peso y unit del sub-paso activo.

    Si override estÃ¡ activo, usa ese peso en lugar del valor del CSV.
    """
    row, sub = pointer
    cols = ["status_muestra", "status_mineral", "status_vegetal"]
    weights = ["peso_muestra", "peso_mineral", "peso_vegetal"]

    status = dataset[row][cols[sub]]
    peso = override if override is not None else dataset[row][weights[sub]]
    unit = dataset[row]["unit"]

    return {"status": status, "peso": peso, "unit": unit}


# ---------------------------------------------------------------------------
# T7 â€” construir respuesta extendida (REXT)
# ---------------------------------------------------------------------------


def _build_extended_response(reading: dict) -> str:
    """Construye la cadena de respuesta extendida: 01ST,1,<peso>,PT 0.0,0,kg\\r\\n.

    La respuesta siempre lleva ST (la balanza virtual solo transmite
    cuando estÃ¡ estable).
    """
    peso = reading["peso"]
    unit = reading["unit"]
    return f"01ST,1,{peso},PT 0.0,0,{unit}\r\n"


# ---------------------------------------------------------------------------
# T8 â€” construir respuesta OK
# ---------------------------------------------------------------------------


def _build_ok_response() -> str:
    """Devuelve 'OK\\r\\n'."""
    return "OK\r\n"


# ---------------------------------------------------------------------------
# T9 â€” simulaciÃ³n de estabilidad
# ---------------------------------------------------------------------------


def _simulate_stability(status: str) -> None:
    """Si status es 'US', duerme entre 200ms y 3s. Si 'ST', no duerme.

    Valores desconocidos se tratan como ST y emiten warning a stderr.
    """
    upper = status.strip().upper()
    if upper == "ST":
        return
    if upper == "US":
        delay = random.uniform(0.2, 3.0)
        time.sleep(delay)
        return
    # valor desconocido â†’ tratar como ST + warning
    print(
        f"WARNING: Status desconocido '{status}' tratado como ST.",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# T10 â€” parseo de comandos seriales
# ---------------------------------------------------------------------------


def _parse_serial_command(line: str) -> tuple[str, str | None]:
    """Parsea una lÃ­nea recibida por el puerto serial.

    Retorna (comando, argumento) donde comando es uno de:
    'REXT', 'TARE', 'TMAN', 'ZERO', 'CLEAR', o 'UNKNOWN'.
    El argumento es None excepto para TMAN, donde contiene el valor.
    """
    stripped = line.strip()
    if not stripped:
        return ("EMPTY", None)

    if stripped == CMD_REXT:
        return ("REXT", None)
    if stripped == CMD_TARE:
        return ("TARE", None)
    if stripped == CMD_ZERO:
        return ("ZERO", None)
    if stripped == CMD_CLEAR:
        return ("CLEAR", None)
    if stripped.startswith(CMD_TMAN_PREFIX):
        valor = stripped[len(CMD_TMAN_PREFIX):]
        return ("TMAN", valor if valor else None)

    return ("UNKNOWN", None)


# ---------------------------------------------------------------------------
# T15 â€” mostrar estado
# ---------------------------------------------------------------------------


def _show_status(
    dataset_id: str,
    pointer: tuple[int, int],
    dataset: list[dict],
    override: float | None,
    port: str,
    baudrate: int,
    serial_connected: bool,
) -> None:
    """Imprime el estado actual del simulador."""
    row, sub = pointer
    reading = _current_reading(pointer, dataset, override)
    total = len(dataset)
    sub_name = SUB_STEP_NAMES[sub]
    override_str = f"{reading['peso']}" if override is not None else "NO"

    print()
    print(f"Dataset: {dataset_id} | Medida: {row + 1}/{total}")
    print(f"Sub-paso: {sub_name} ({sub + 1}/3)")
    print(
        f"Peso actual: {reading['peso']:.3f} {reading['unit']}"
        f" | Status CSV: {reading['status']} | Override: {override_str}"
    )
    print(
        f"Puerto: {port} @ {baudrate} baud"
        f" | Conectado: {'SI' if serial_connected else 'NO'}"
    )


# ---------------------------------------------------------------------------
# T14 â€” manejar tecla w (override)
# ---------------------------------------------------------------------------


def _handle_override(
    pointer: tuple[int, int],
    dataset: list[dict],
) -> float | None:
    """Solicita un valor numÃ©rico por consola y retorna el peso override."""
    try:
        raw = input("Ingrese peso override (valor numerico): ")
        return float(raw)
    except (ValueError, EOFError):
        print("Valor invalido. Override cancelado.")
        return None


# ---------------------------------------------------------------------------
# T14 â€” manejar tecla g (goto)
# ---------------------------------------------------------------------------


def _handle_goto(dataset: list[dict]) -> tuple[int, int] | None:
    """Solicita un Ã­ndice de fila y retorna el nuevo pointer."""
    total = len(dataset)
    try:
        raw = input(f"Ingrese indice de medida (0-{total - 1}): ")
        idx = int(raw)
        if 0 <= idx < total:
            return (idx, 0)
        print(f"Indice fuera de rango. Debe ser 0-{total - 1}.")
    except (ValueError, EOFError):
        print("Indice invalido.")
    return None


# ---------------------------------------------------------------------------
# T17 â€” cierre limpio
# ---------------------------------------------------------------------------


def _shutdown(
    ser: "serial.Serial | None",
    serial_connected: bool,
) -> None:
    """Cierra el puerto serial y muestra mensaje de despedida."""
    if serial_connected and ser is not None:
        try:
            ser.close()
        except Exception:
            pass
    print("\nBalanza virtual detenida. Puerto serial cerrado.")


# ---------------------------------------------------------------------------
# T11â€“T16 â€” bucle principal
# ---------------------------------------------------------------------------


def main() -> None:
    """Punto de entrada del script: parsea args, carga dataset, abre serial, REPL."""

    # ------------------------------------------------------------------
    # T16 â€” argparse
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Balanza Virtual DINI ARGEO DFWLI-2 â€” Simulador serial para desarrollo.",
    )
    parser.add_argument(
        "--port",
        default="COM1",
        help="Ruta del puerto serial (default: COM1). Ej: COM3, /dev/ttyUSB0",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="Velocidad en baudios (default: 9600)",
    )
    parser.add_argument(
        "--dataset",
        default="A",
        help="Letra del dataset A-E (default: A)",
    )
    parser.add_argument(
        "--data-dir",
        default=os.path.join("data", "readings"),
        help="Ruta a la carpeta que contiene los archivos CSV (default: data/readings/)",
    )
    args = parser.parse_args()

    # Validar dataset
    dataset_id = args.dataset.upper()
    if dataset_id not in ("A", "B", "C", "D", "E"):
        print(
            f"ERROR: Dataset '{args.dataset}' no valido. Use A, B, C, D o E.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # T5 â€” cargar dataset
    # ------------------------------------------------------------------
    dataset = load_dataset(args.data_dir, dataset_id)
    total_rows = len(dataset)

    # ------------------------------------------------------------------
    # Inicializar puntero y estado
    # ------------------------------------------------------------------
    pointer: tuple[int, int] = (0, 0)  # (row, sub_step)
    override: float | None = None

    # ------------------------------------------------------------------
    # T16 â€” abrir puerto serial
    # ------------------------------------------------------------------
    if serial is None:
        print(
            "ERROR: pyserial no esta instalado. Ejecute: pip install pyserial",
            file=sys.stderr,
        )
        sys.exit(1)

    ser = None
    serial_connected = False
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,  # non-blocking poll
        )
        serial_connected = True
    except serial.SerialException as exc:
        print(
            f"ERROR: No se pudo abrir el puerto serial {args.port}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Mensaje de bienvenida
    # ------------------------------------------------------------------
    print("=" * 60)
    print("  BALANZA VIRTUAL DINI ARGEO DFWLI-2")
    print("=" * 60)
    print()
    print(f"  Puerto serial : {args.port} @ {args.baudrate} baud")
    print(f"  Dataset       : {dataset_id} ({total_rows} medidas)")
    print(f"  Data dir      : {args.data_dir}")
    print()
    print("  Comandos aceptados: 00REXT, 00TARE, 00TMAN<v>, 00ZERO, 00CLEAR")
    print()
    print("  REPL:")
    print("    n        = siguiente sub-paso/medida")
    print("    p        = anterior sub-paso/medida")
    print("    w        = override de peso")
    print("    g        = saltar a medida N")
    print("    s        = mostrar estado")
    print("    q        = salir")
    print("    Espacio/d = simular PRINT (enviar sin delay ni avance)")
    print()

    # ------------------------------------------------------------------
    # Buffer para datos seriales (acumular hasta \n)
    # ------------------------------------------------------------------
    serial_buffer = ""

    # ------------------------------------------------------------------
    # T11 â€” bucle principal
    # ------------------------------------------------------------------
    try:
        while True:
            # -------------------------------------------------------------
            # Leer datos del puerto serial (non-blocking)
            # -------------------------------------------------------------
            try:
                if serial_connected and ser is not None:
                    while ser.in_waiting > 0:
                        chunk = ser.read(ser.in_waiting)
                        serial_buffer += chunk.decode("ascii", errors="replace")
            except serial.SerialException as exc:
                print(
                    f"WARNING: Error de lectura serial: {exc}",
                    file=sys.stderr,
                )
                serial_connected = False

            # Procesar lÃ­neas completas del buffer serial
            while "\n" in serial_buffer:
                line, serial_buffer = serial_buffer.split("\n", 1)
                line = line.rstrip("\r")

                cmd, arg = _parse_serial_command(line)

                if cmd == "EMPTY":
                    continue

                if cmd == "UNKNOWN":
                    print(
                        f"[SERIAL] Comando no reconocido: {line!r}",
                        file=sys.stderr,
                    )
                    continue

                # ---------------------------------------------------------
                # T10 â€” enrutar comando
                # ---------------------------------------------------------
                if cmd == "REXT":
                    # T6 â€” leer el valor actual
                    reading = _current_reading(pointer, dataset, override)

                    # T9 â€” simular estabilidad (delay si US)
                    _simulate_stability(reading["status"])

                    # T7 â€” construir y enviar respuesta
                    response = _build_extended_response(reading)
                    try:
                        ser.write(response.encode("ascii"))  # type: ignore[union-attr]
                    except serial.SerialException as exc:
                        print(
                            f"WARNING: Error de escritura serial: {exc}",
                            file=sys.stderr,
                        )
                        serial_connected = False

                    # Log a consola
                    row, sub = pointer
                    print(
                        f"[REXT] row={row} sub={sub}"
                        f" ({SUB_STEP_NAMES[sub]}) status={reading['status']}"
                        f" peso={reading['peso']} -> {response.strip()}"
                    )

                elif cmd == "TARE":
                    try:
                        ser.write(_build_ok_response().encode("ascii"))  # type: ignore[union-attr]
                    except serial.SerialException as exc:
                        print(
                            f"WARNING: Error de escritura serial: {exc}",
                            file=sys.stderr,
                        )
                        serial_connected = False
                    print("[TARE] -> OK")

                elif cmd == "TMAN":
                    try:
                        ser.write(_build_ok_response().encode("ascii"))  # type: ignore[union-attr]
                    except serial.SerialException as exc:
                        print(
                            f"WARNING: Error de escritura serial: {exc}",
                            file=sys.stderr,
                        )
                        serial_connected = False
                    print(f"[TMAN] valor={arg or ''} -> OK")

                elif cmd == "ZERO":
                    try:
                        ser.write(_build_ok_response().encode("ascii"))  # type: ignore[union-attr]
                    except serial.SerialException as exc:
                        print(
                            f"WARNING: Error de escritura serial: {exc}",
                            file=sys.stderr,
                        )
                        serial_connected = False
                    print("[ZERO] -> OK")

                elif cmd == "CLEAR":
                    try:
                        ser.write(_build_ok_response().encode("ascii"))  # type: ignore[union-attr]
                    except serial.SerialException as exc:
                        print(
                            f"WARNING: Error de escritura serial: {exc}",
                            file=sys.stderr,
                        )
                        serial_connected = False
                    print("[CLEAR] -> OK")

            # -------------------------------------------------------------
            # Leer tecla del teclado (non-blocking via msvcrt o stdin)
            # -------------------------------------------------------------
            key = None
            if msvcrt is not None:
                # Windows: usar msvcrt para lectura non-blocking de teclado
                if msvcrt.kbhit():
                    raw = msvcrt.getch()
                    try:
                        key = raw.decode("ascii", errors="replace").lower()
                    except Exception:
                        key = None
            else:
                # Fallback Unix: usar select para ver si hay stdin disponible
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    raw = sys.stdin.read(1)
                    if raw:
                        key = raw.lower()

            if key is None:
                time.sleep(0.01)  # breve pausa para no saturar CPU
                continue

            # -------------------------------------------------------------
            # Procesar tecla
            # -------------------------------------------------------------
            row, sub = pointer

            if key == "n":
                # T12 â€” next
                if sub < 2:
                    pointer = (row, sub + 1)
                elif row < total_rows - 1:
                    pointer = (row + 1, 0)
                override = None  # descartar override al avanzar
                row2, sub2 = pointer
                print(
                    f"[n] -> row={row2} sub={sub2}"
                    f" ({SUB_STEP_NAMES[sub2]})"
                )

            elif key == "p":
                # T13 â€” previous
                if sub > 0:
                    pointer = (row, sub - 1)
                elif row > 0:
                    pointer = (row - 1, 2)
                # si row==0 y sub==0, no retrocede
                override = None  # descartar override al retroceder
                row2, sub2 = pointer
                print(
                    f"[p] -> row={row2} sub={sub2}"
                    f" ({SUB_STEP_NAMES[sub2]})"
                )

            elif key == "w":
                # T14 â€” override
                new_override = _handle_override(pointer, dataset)
                if new_override is not None:
                    override = new_override
                    print(
                        f"[w] Override activo: {override} para "
                        f"sub-paso {SUB_STEP_NAMES[sub]}"
                    )

            elif key == "g":
                # T14 â€” goto
                result = _handle_goto(dataset)
                if result is not None:
                    pointer = result
                    override = None
                    print(f"[g] -> row={result[0]} sub=0 (muestra)")

            elif key == "s":
                # T15 â€” status
                _show_status(
                    dataset_id, pointer, dataset, override,
                    args.port, args.baudrate, serial_connected,
                )

            elif key == "q":
                # T17 â€” quit
                _shutdown(ser, serial_connected)
                break

            elif key in (" ", "d"):
                # T14 / R9 â€” PRINT: enviar sin delay ni avance
                reading = _current_reading(pointer, dataset, override)
                # Forzar status ST (sin delay) para PRINT
                # Enviamos directamente sin llamar _simulate_stability
                response = _build_extended_response(reading)
                try:
                    ser.write(response.encode("ascii"))  # type: ignore[union-attr]
                    print(
                        f"[PRINT] row={row} sub={sub}"
                        f" ({SUB_STEP_NAMES[sub]}) peso={reading['peso']}"
                        f" -> {response.strip()}"
                    )
                except serial.SerialException as exc:
                    print(
                        f"WARNING: Error de escritura serial: {exc}",
                        file=sys.stderr,
                    )
                    serial_connected = False

            else:
                # tecla no reconocida
                pass

    except KeyboardInterrupt:
        _shutdown(ser, serial_connected)

    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
