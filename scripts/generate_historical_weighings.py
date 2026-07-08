"""Generador de datos historicos de pesaje.

Genera N dias continuos de pesajes (60-70 por dia en 3 turnos),
referenciando haciendas y suertes reales de la BD local.
Salida: archivo SQL listo para importar.
"""

import argparse
import random
import subprocess
import sys
from datetime import date, timedelta


# === CONSTANTES ===

TIPO_COSECHA = [
    "Manual - Incendio",
    "Manual - Quemado",
    "Manual - Verde",
    "Mecanico - Incendio",
    "Mecanico - Verde",
    "No convencional - Verde",
]

PESO_MUESTRA_RANGE = (200.0, 350.0)
PESO_MINERAL_RANGE = (10.0, 50.0)
PESO_VEGETAL_RANGE = (2.0, 15.0)

OPERATOR_IDS = [2, 5, 6, 7, 8, 9, 10, 11, 12]

BATCH_SIZE = 500


def random_tractomula() -> str:
    letras = random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3)
    nums = random.randint(100, 999)
    return f"{''.join(letras)}-{nums:03d}"


def random_vagon() -> str:
    return f"{random.randint(1000, 9999):04d}"


def random_guia() -> str:
    return f"{random.randint(1000000, 9999999):07d}"


def random_peso(rng: tuple[float, float]) -> float:
    return round(random.uniform(*rng), 3)


def fetch_suerte_hacienda_pairs(mysql_cmd: list[str]) -> list[tuple[int, int]]:
    sql = "SELECT id, hacienda_id FROM suertes ORDER BY id"
    result = subprocess.run(
        mysql_cmd + ["-e", sql, "-N", "-B"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"ERROR fetching suertes: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    pairs = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.strip().split("\t")
        if len(parts) >= 2:
            pairs.append((int(parts[0]), int(parts[1])))
    return pairs


def generate_inserts(
    pairs: list[tuple[int, int]],
    operator_ids: list[int],
    start: date,
    days: int,
    batch_size: int = BATCH_SIZE,
) -> list[str]:
    total_weighings = 0
    batches = []
    current_values: list[str] = []

    def flush():
        nonlocal current_values, batches
        if current_values:
            sql = (
                "INSERT INTO weighings "
                "(fecha, hora, tractomula, vagon, numero_guia, hacienda_id, suerte_id, "
                "peso_muestra, peso_mineral, peso_vegetal_extrano, usuario_id, "
                "enviado_pc, manual_entry, tipo_cosecha) VALUES\n"
                + ",\n".join(current_values)
                + ";\n"
            )
            batches.append(sql)
            current_values = []

    def add_row(fecha: date, hora: str, h_id: int, s_id: int, usuario: int):
        nonlocal total_weighings
        muestra = random_peso(PESO_MUESTRA_RANGE)
        mineral = random_peso(PESO_MINERAL_RANGE)
        vegetal = random_peso(PESO_VEGETAL_RANGE)
        tracto = random_tractomula()
        vagon = random_vagon()
        guia = random_guia()
        cosecha = random.choice(TIPO_COSECHA)
        enviado = 1 if random.random() < 0.85 else 0
        manual = 0

        vals = (
            f"('{fecha.isoformat()}', '{hora}', '{tracto}', '{vagon}', '{guia}', "
            f"{h_id}, {s_id}, {muestra}, {mineral}, {vegetal}, {usuario}, "
            f"{enviado}, {manual}, '{cosecha}')"
        )
        current_values.append(vals)
        total_weighings += 1

        if len(current_values) >= batch_size:
            flush()

    print(f"Generando {days} dias continuos desde {start}...", file=sys.stderr)

    for day_idx in range(days):
        current = start + timedelta(days=day_idx)
        if day_idx > 0 and day_idx % 15 == 0:
            print(f"  Dia {day_idx}/{days}...", file=sys.stderr)

        n_weighings = random.randint(60, 70)

        n1 = max(20, int(n_weighings * 0.4))
        n2 = max(20, int(n_weighings * 0.4))
        n3 = n_weighings - n1 - n2

        for _ in range(n1):
            h = random.randint(6, 13)
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            hora = f"{h:02d}:{m:02d}:{s:02d}"
            s_id, h_id = random.choice(pairs)
            uid = random.choice(operator_ids)
            add_row(current, hora, h_id, s_id, uid)

        for _ in range(n2):
            h = random.randint(14, 21)
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            hora = f"{h:02d}:{m:02d}:{s:02d}"
            s_id, h_id = random.choice(pairs)
            uid = random.choice(operator_ids)
            add_row(current, hora, h_id, s_id, uid)

        for _ in range(n3):
            h = random.randint(22, 23)
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            hora = f"{h:02d}:{m:02d}:{s:02d}"
            s_id, h_id = random.choice(pairs)
            uid = random.choice(operator_ids)
            add_row(current, hora, h_id, s_id, uid)

    flush()
    print(f"Total: {total_weighings} pesajes en {len(batches)} batches", file=sys.stderr)
    return batches, total_weighings


def main():
    parser = argparse.ArgumentParser(description="Generar datos historicos de pesaje")
    parser.add_argument("--output", "-o", default="dump_weighings.sql",
                        help="Archivo SQL de salida")
    parser.add_argument("--seed", type=int, default=42,
                        help="Semilla aleatoria")
    parser.add_argument("--start", default="2026-05-03",
                        help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=65,
                        help="Numero de dias consecutivos")
    parser.add_argument("--mysql", default="mysql",
                        help="Comando mysql")
    parser.add_argument("--db-args", default="-usip_user -psip_pass sip_edge",
                        help="Argumentos conexion BD")
    args = parser.parse_args()

    random.seed(args.seed)
    start_date = date.fromisoformat(args.start)

    mysql_cmd = args.mysql.split() + args.db_args.split()
    print(f"Conectando a BD local...", file=sys.stderr)
    pairs = fetch_suerte_hacienda_pairs(mysql_cmd)
    print(f"Obtenidos {len(pairs)} pares (suerte_id, hacienda_id)", file=sys.stderr)

    batches, total = generate_inserts(pairs, OPERATOR_IDS, start_date, args.days)

    end_date = start_date + timedelta(days=args.days - 1)
    print(f"Escribiendo {args.output} ({total} registros)...", file=sys.stderr)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("-- Generated historical weighings data\n")
        f.write(f"-- From: {start_date} To: {end_date} ({args.days} days)\n")
        f.write(f"-- Seed: {args.seed}  Total: {total} records\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write("TRUNCATE TABLE weighings;\n\n")
        for batch in batches:
            f.write(batch)
        f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")

    print(f"Listo. Archivo: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
