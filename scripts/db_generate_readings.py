"""Generador de datasets CSV para la balanza virtual DINI ARGEO DFWLI-2.

Genera 5 datasets (A–E) de 50 medidas cada uno con distribuciones
estadísticas específicas usando random de la stdlib. Cada dataset
tiene 7 columnas: status_muestra, peso_muestra, status_mineral,
peso_mineral, status_vegetal, peso_vegetal, unit.
"""

import argparse
import csv
import os
import random
import sys


HEADER = [
    "status_muestra",
    "peso_muestra",
    "status_mineral",
    "peso_mineral",
    "status_vegetal",
    "peso_vegetal",
    "unit",
]

ROWS = 50


def _random_status(prob_us: float = 0.2) -> str:
    """Devuelve 'ST' o 'US' con la probabilidad de US indicada."""
    return "US" if random.random() < prob_us else "ST"


def _fmt(weight: float) -> str:
    """Formatea un peso a string con un decimal."""
    return f"{weight:.1f}"


def generate_dataset_a() -> list[list[str]]:
    """Dataset A: contaminación baja (muestra 200-350, mineral 10-50, vegetal 2-15)."""
    rows = []
    for _ in range(ROWS):
        muestra = random.uniform(200, 350)
        mineral = random.uniform(10, 50)
        vegetal = random.uniform(2, 15)
        rows.append([
            _random_status(0.1),
            _fmt(muestra),
            _random_status(0.15),
            _fmt(mineral),
            _random_status(0.15),
            _fmt(vegetal),
            "kg",
        ])
    return rows


def generate_dataset_b() -> list[list[str]]:
    """Dataset B: contaminación media (mineral 30-120, vegetal 10-50), ~40% US."""
    rows = []
    for _ in range(ROWS):
        muestra = random.uniform(200, 350)
        mineral = random.uniform(30, 120)
        vegetal = random.uniform(10, 50)
        rows.append([
            _random_status(0.4),
            _fmt(muestra),
            _random_status(0.4),
            _fmt(mineral),
            _random_status(0.4),
            _fmt(vegetal),
            "kg",
        ])
    return rows


def generate_dataset_c() -> list[list[str]]:
    """Dataset C: contaminación alta con tendencia creciente."""
    rows = []
    for i in range(ROWS):
        t = i / (ROWS - 1)  # 0 → 1
        muestra = random.uniform(200 + 200 * t, 300 + 100 * t)
        mineral = random.uniform(50 + 150 * t, 100 + 100 * t)
        vegetal = random.uniform(15 + 65 * t, 40 + 40 * t)
        rows.append([
            _random_status(0.5),
            _fmt(muestra),
            _random_status(0.5),
            _fmt(mineral),
            _random_status(0.5),
            _fmt(vegetal),
            "kg",
        ])
    return rows


def generate_dataset_d() -> list[list[str]]:
    """Dataset D: outliers ocasionales en mineral y vegetal."""
    rows = []
    for _ in range(ROWS):
        muestra = random.uniform(180, 350)

        # Outlier mineral en ~10% de las filas
        if random.random() < 0.1:
            mineral = random.uniform(200, 300)
        else:
            mineral = random.uniform(8, 120)

        # Outlier vegetal en ~10% de las filas
        if random.random() < 0.1:
            vegetal = random.uniform(40, 80)
        else:
            vegetal = random.uniform(1, 30)

        rows.append([
            _random_status(0.25),
            _fmt(muestra),
            _random_status(0.25),
            _fmt(mineral),
            _random_status(0.25),
            _fmt(vegetal),
            "kg",
        ])
    return rows


def generate_dataset_e() -> list[list[str]]:
    """Dataset E: aleatoria uniforme dentro de rangos típicos."""
    rows = []
    for _ in range(ROWS):
        muestra = random.uniform(150, 400)
        mineral = random.uniform(5, 300)
        vegetal = random.uniform(1, 100)
        rows.append([
            _random_status(0.3),
            _fmt(muestra),
            _random_status(0.3),
            _fmt(mineral),
            _random_status(0.3),
            _fmt(vegetal),
            "kg",
        ])
    return rows


DATASETS = {
    "A": generate_dataset_a,
    "B": generate_dataset_b,
    "C": generate_dataset_c,
    "D": generate_dataset_d,
    "E": generate_dataset_e,
}


def write_dataset(output_dir: str, letter: str, rows: list[list[str]]) -> str:
    """Escribe un dataset CSV y retorna la ruta del archivo."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"dataset_{letter}.csv")
    with open(filepath, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        writer.writerows(rows)
    return filepath


def main() -> None:
    """Punto de entrada: genera los 5 datasets CSV."""
    parser = argparse.ArgumentParser(
        description="Generar datasets CSV de prueba para la balanza virtual DINI ARGEO DFWLI-2."
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("src", "tools", "readings"),
        help="Directorio donde guardar los CSVs (default: src/tools/readings/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semilla para el generador aleatorio (opcional, para reproducibilidad)",
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    print(f"Generando datasets en: {args.output_dir}")
    for letter in sorted(DATASETS):
        rows = DATASETS[letter]()
        filepath = write_dataset(args.output_dir, letter, rows)
        print(f"  dataset_{letter}.csv -- {len(rows)} medidas -> {filepath}")

    print("Listo. 5 datasets generados (250 medidas totales).")


if __name__ == "__main__":
    main()
