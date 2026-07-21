"""Generador de datos historicos de pesaje con anomalias y notas.

Genera N dias continuos de pesajes (60-70 por dia en 3 turnos),
referenciando haciendas y suertes reales de la BD local.
Inyecta anomalias en al menos 2 dias por semana y genera notas
contextuales (tractomula de empalme, alta materia extrana, etc.).
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

OPERATOR_IDS = [2, 5, 6, 7, 8, 9, 10, 11, 12]

BATCH_SIZE = 500

# Notas contextuales para diferentes escenarios
NOTAS_EMPALME = [
    "tractomula de empalme",
    "tractomula de empalme — sin carga",
    "tractomula de empalme — solo maniobra",
]

NOTAS_ALTO_MINERAL = [
    "se encontraron muchos cogollos en la muestra",
    "alta presencia de cogollos y hojas secas",
    "muestra con exceso de cogollos — revisar corte",
    "muchos cogollos, posible problema en cosechadora",
]

NOTAS_ALTO_VEGETAL = [
    "alta cantidad de pasto de corte en la muestra",
    "caña con mucho barro adherido",
    "mucha materia extraña vegetal — pasto y hojas",
    "caña sucia, exceso de barro en los tallos",
    "alta presencia de pasto de corte y maleza",
]

NOTAS_CORE_SAMPLER = [
    "problemas con core sampler — muestra incompleta",
    "core sampler atascado, repetir muestreo",
    "core sampler dañado, muestra no representativa",
]

NOTAS_GENERALES = [
    "muestra con leve presencia de hojas secas",
    "muestra limpia, buena calidad de corte",
    "vagón con nivel de caña muy bajo",
    "muestra de verificación — control de calidad",
    "muestra húmeda por lluvia reciente",
    None,  # sin notas
    None,
    None,
    None,
    None,
]


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


def generate_nota(
    muestra: float,
    mineral: float,
    vegetal: float,
    is_empalme: bool = False,
    is_alto_mineral: bool = False,
    is_alto_vegetal: bool = False,
) -> str | None:
    """Genera una nota contextual basada en los valores del pesaje."""
    if is_empalme:
        return random.choice(NOTAS_EMPALME)
    if is_alto_mineral:
        return random.choice(NOTAS_ALTO_MINERAL)
    if is_alto_vegetal:
        return random.choice(NOTAS_ALTO_VEGETAL)
    if random.random() < 0.02:
        return random.choice(NOTAS_CORE_SAMPLER)
    return random.choice(NOTAS_GENERALES)


def escape_sql(s: str | None) -> str:
    """Escapa una string para SQL, o retorna NULL."""
    if s is None:
        return "NULL"
    escaped = s.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def generate_inserts(
    pairs: list[tuple[int, int]],
    operator_ids: list[int],
    start: date,
    days: int,
    rango_muestra: tuple[float, float],
    rango_mineral: tuple[float, float],
    rango_vegetal: tuple[float, float],
    batch_size: int = BATCH_SIZE,
) -> tuple[list[str], int, int]:
    """Genera batches SQL INSERT con anomalias y notas.

    Anomalias: 2-3 dias por semana con datos anomalos.
    Tipos de anomalia:
      - empalme: pesos 0,0,0 para 15-25% de pesajes del dia
      - alto_mineral: mineral > 85% del rango max, para 20-30% de pesajes
      - alto_vegetal: vegetal > 85% del rango max, para 20-30% de pesajes
    """
    total_weighings = 0
    total_anomalies = 0
    batches = []
    current_values: list[str] = []

    def flush():
        nonlocal current_values, batches
        if current_values:
            sql = (
                "INSERT INTO weighings "
                "(fecha, hora, tractomula, vagon, numero_guia, hacienda_id, suerte_id, "
                "peso_muestra, peso_mineral, peso_vegetal_extrano, usuario_id, "
                "enviado_pc, manual_entry, tipo_cosecha, notas) VALUES\n"
                + ",\n".join(current_values)
                + ";\n"
            )
            batches.append(sql)
            current_values = []

    def add_row(
        fecha: date, hora: str, h_id: int, s_id: int, usuario: int,
        muestra: float, mineral: float, vegetal: float, nota: str | None,
    ):
        nonlocal total_weighings
        tracto = random_tractomula()
        vagon = random_vagon()
        guia = random_guia()
        cosecha = random.choice(TIPO_COSECHA)
        enviado = 1 if random.random() < 0.85 else 0
        manual = 0

        vals = (
            f"('{fecha.isoformat()}', '{hora}', '{tracto}', '{vagon}', '{guia}', "
            f"{h_id}, {s_id}, {muestra}, {mineral}, {vegetal}, {usuario}, "
            f"{enviado}, {manual}, '{cosecha}', {escape_sql(nota)})"
        )
        current_values.append(vals)
        total_weighings += 1

        if len(current_values) >= batch_size:
            flush()

    # Pre-calcular dias de anomalia: 2-3 dias por semana
    anomaly_days: set[int] = set()
    week = -1
    for day_idx in range(days):
        current_week = day_idx // 7
        if current_week != week:
            week = current_week
            # 2 o 3 dias anomalos esta semana
            n_anom = random.randint(2, 3)
            candidates = list(range(day_idx, min(day_idx + 7, days)))
            chosen = random.sample(candidates, min(n_anom, len(candidates)))
            anomaly_days.update(chosen)

    print(f"Generando {days} dias continuos desde {start}...", file=sys.stderr)
    print(f"  Dias con anomalias: {len(anomaly_days)} de {days}", file=sys.stderr)

    for day_idx in range(days):
        current = start + timedelta(days=day_idx)
        if day_idx > 0 and day_idx % 15 == 0:
            print(f"  Dia {day_idx}/{days}...", file=sys.stderr)

        n_weighings = random.randint(60, 70)
        is_anomaly_day = day_idx in anomaly_days

        # Elegir tipo de anomalia para este dia
        anom_type = None
        if is_anomaly_day:
            anom_type = random.choice(["empalme", "alto_mineral", "alto_vegetal"])

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

            muestra, mineral, vegetal, nota, is_anom = _generate_reading(
                rango_muestra, rango_mineral, rango_vegetal,
                anom_type, is_anomaly_day,
            )
            if is_anom:
                total_anomalies += 1
            add_row(current, hora, h_id, s_id, uid, muestra, mineral, vegetal, nota)

        for _ in range(n2):
            h = random.randint(14, 21)
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            hora = f"{h:02d}:{m:02d}:{s:02d}"
            s_id, h_id = random.choice(pairs)
            uid = random.choice(operator_ids)

            muestra, mineral, vegetal, nota, is_anom = _generate_reading(
                rango_muestra, rango_mineral, rango_vegetal,
                anom_type, is_anomaly_day,
            )
            if is_anom:
                total_anomalies += 1
            add_row(current, hora, h_id, s_id, uid, muestra, mineral, vegetal, nota)

        for _ in range(n3):
            h = random.randint(22, 23)
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            hora = f"{h:02d}:{m:02d}:{s:02d}"
            s_id, h_id = random.choice(pairs)
            uid = random.choice(operator_ids)

            muestra, mineral, vegetal, nota, is_anom = _generate_reading(
                rango_muestra, rango_mineral, rango_vegetal,
                anom_type, is_anomaly_day,
            )
            if is_anom:
                total_anomalies += 1
            add_row(current, hora, h_id, s_id, uid, muestra, mineral, vegetal, nota)

    flush()
    print(f"Total: {total_weighings} pesajes ({total_anomalies} anomalos) en {len(batches)} batches", file=sys.stderr)
    return batches, total_weighings, total_anomalies


def _generate_reading(
    rango_muestra: tuple[float, float],
    rango_mineral: tuple[float, float],
    rango_vegetal: tuple[float, float],
    anom_type: str | None,
    is_anomaly_day: bool,
) -> tuple[float, float, float, str | None, bool]:
    """Genera una lectura individual, posiblemente anomal a."""
    is_anom = False

    if anom_type == "empalme" and random.random() < 0.20:
        muestra = 0.0
        mineral = 0.0
        vegetal = 0.0
        nota = generate_nota(0, 0, 0, is_empalme=True)
        is_anom = True
    elif anom_type == "alto_mineral" and random.random() < 0.25:
        muestra = random_peso(rango_muestra)
        mineral = round(random.uniform(rango_mineral[1] * 0.85, rango_mineral[1]), 3)
        vegetal = random_peso(rango_vegetal)
        nota = generate_nota(muestra, mineral, vegetal, is_alto_mineral=True)
        is_anom = True
    elif anom_type == "alto_vegetal" and random.random() < 0.25:
        muestra = random_peso(rango_muestra)
        mineral = random_peso(rango_mineral)
        vegetal = round(random.uniform(rango_vegetal[1] * 0.85, rango_vegetal[1]), 3)
        nota = generate_nota(muestra, mineral, vegetal, is_alto_vegetal=True)
        is_anom = True
    else:
        muestra = random_peso(rango_muestra)
        mineral = random_peso(rango_mineral)
        vegetal = random_peso(rango_vegetal)
        nota = generate_nota(muestra, mineral, vegetal)

    return muestra, mineral, vegetal, nota, is_anom


def main():
    parser = argparse.ArgumentParser(description="Generar datos historicos de pesaje con anomalias y notas")
    parser.add_argument("--output", "-o", default="dump_weighings.sql",
                        help="Archivo SQL de salida")
    parser.add_argument("--seed", type=int, default=42,
                        help="Semilla aleatoria")
    parser.add_argument("--start", default="2026-04-01",
                        help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=110,
                        help="Numero de dias consecutivos")
    parser.add_argument("--muestra-min", type=float, default=0.90,
                        help="Peso minimo muestra (kg)")
    parser.add_argument("--muestra-max", type=float, default=1.62,
                        help="Peso maximo muestra (kg)")
    parser.add_argument("--mineral-min", type=float, default=0.0,
                        help="Peso minimo mineral (kg)")
    parser.add_argument("--mineral-max", type=float, default=0.40,
                        help="Peso maximo mineral (kg)")
    parser.add_argument("--vegetal-min", type=float, default=0.10,
                        help="Peso minimo vegetal (kg)")
    parser.add_argument("--vegetal-max", type=float, default=0.50,
                        help="Peso maximo vegetal (kg)")
    parser.add_argument("--mysql", default="mysql",
                        help="Comando mysql")
    parser.add_argument("--db-args", default="-usip_user -psip_pass sip_edge",
                        help="Argumentos conexion BD")
    args = parser.parse_args()

    random.seed(args.seed)
    start_date = date.fromisoformat(args.start)

    rango_muestra = (args.muestra_min, args.muestra_max)
    rango_mineral = (args.mineral_min, args.mineral_max)
    rango_vegetal = (args.vegetal_min, args.vegetal_max)

    mysql_cmd = args.mysql.split() + args.db_args.split()
    print(f"Conectando a BD local...", file=sys.stderr)
    pairs = fetch_suerte_hacienda_pairs(mysql_cmd)
    print(f"Obtenidos {len(pairs)} pares (suerte_id, hacienda_id)", file=sys.stderr)

    batches, total, total_anom = generate_inserts(
        pairs, OPERATOR_IDS, start_date, args.days,
        rango_muestra, rango_mineral, rango_vegetal,
    )

    end_date = start_date + timedelta(days=args.days - 1)
    print(f"Escribiendo {args.output} ({total} registros, {total_anom} anomalos)...", file=sys.stderr)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("-- Generated historical weighings data with anomalies and notes\n")
        f.write(f"-- From: {start_date} To: {end_date} ({args.days} days)\n")
        f.write(f"-- Seed: {args.seed}  Total: {total} records  Anomalies: {total_anom}\n")
        f.write(f"-- Ranges: muestra={rango_muestra}, mineral={rango_mineral}, vegetal={rango_vegetal}\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write("TRUNCATE TABLE weighings;\n\n")
        for batch in batches:
            f.write(batch)
        f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")

    print(f"Listo. Archivo: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()