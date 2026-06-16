"""
schema_dump.py — Generates docs/database.md from the actual database.

Usage:
    python database/schema_dump.py [--config database/.schema_dump.json]

Supports SQLite (stdlib) and MySQL (requires mysql-connector-python).
Generates docs/database.md that init.ps1 checks for freshness.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def dump_sqlite(db_path: str) -> str:
    """Extract schema from a SQLite database file."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    lines = [
        f"# Database Schema — {Path(db_path).stem}",
        f"",
        f"> Auto-generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"> Source: {db_path}",
        f"> DO NOT EDIT BY HAND.",
        f"",
    ]

    for table_name in tables:
        lines.append(f"## {table_name}")
        lines.append("")
        lines.append("| Column | Type | Nullable | Default | PK |")
        lines.append("|--------|------|----------|---------|----|")

        cursor.execute(f"PRAGMA table_info('{table_name}')")
        for col in cursor.fetchall():
            cid, name, typ, notnull, dflt, pk = col
            null_str = "NO" if notnull else "YES"
            dflt_str = str(dflt) if dflt is not None else "NULL" if notnull else "NULL"
            pk_str = "YES" if pk else ""
            lines.append(f"| {name} | {typ.upper()} | {null_str} | {dflt_str} | {pk_str} |")

        lines.append("")

        # Foreign keys
        cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
        fks = cursor.fetchall()
        if fks:
            lines.append("**Foreign Keys:**")
            for fk in fks:
                id_seq, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                lines.append(f"- `{from_col}` → `{ref_table}.{to_col}` ON DELETE {on_delete}")
            lines.append("")

        # Indexes
        cursor.execute(f"PRAGMA index_list('{table_name}')")
        indexes = cursor.fetchall()
        if indexes:
            lines.append("**Indexes:**")
            for idx in indexes:
                seq, name, unique_flag = idx
                if name.startswith("sqlite_autoindex"):
                    continue
                cursor.execute(f"PRAGMA index_info('{name}')")
                cols = [c[2] for c in cursor.fetchall()]
                unique = "UNIQUE " if unique_flag else ""
                lines.append(f"- {unique}`{name}` ({', '.join(cols)})")
            lines.append("")

    conn.close()
    return "\n".join(lines)


def dump_mysql(config: dict) -> str:
    """Extract schema from a MySQL database."""
    try:
        import mysql.connector
    except ImportError:
        sys.exit("mysql-connector-python not installed. Run: pip install mysql-connector-python")

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    db_name = config.get("database", "unknown")

    cursor.execute("""
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """, (db_name,))
    tables = [row[0] for row in cursor.fetchall()]

    lines = [
        f"# Database Schema — {db_name}",
        f"",
        f"> Auto-generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"> Engine: MySQL @ {config.get('host', 'localhost')}:{config.get('port', 3306)}",
        f"> DO NOT EDIT BY HAND.",
        f"",
    ]

    for table_name in tables:
        lines.append(f"## {table_name}")
        lines.append("")
        lines.append("| Column | Type | Nullable | Default | Extra |")
        lines.append("|--------|------|----------|---------|-------|")

        cursor.execute(f"DESCRIBE `{table_name}`")
        for col in cursor.fetchall():
            field, typ, null, key, dflt, extra = col
            null_str = "NO" if null == "NO" else "YES"
            dflt_str = str(dflt) if dflt is not None else "NULL"
            extra_str = extra if extra else ""
            lines.append(f"| {field} | {typ} | {null_str} | {dflt_str} | {extra_str} |")

        lines.append("")

        # Foreign keys
        cursor.execute(f"""
            SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (db_name, table_name))
        fks = cursor.fetchall()
        if fks:
            lines.append("**Foreign Keys:**")
            for col, ref_table, ref_col in fks:
                lines.append(f"- `{col}` → `{ref_table}.{ref_col}`")
            lines.append("")

        # Indexes
        cursor.execute(f"""
            SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME != 'PRIMARY'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """, (db_name, table_name))
        idx_rows = cursor.fetchall()
        if idx_rows:
            idx_groups = {}
            for name, col, non_unique in idx_rows:
                idx_groups.setdefault(name, []).append((col, non_unique))
            lines.append("**Indexes:**")
            for name, cols in idx_groups.items():
                col_names = [c[0] for c in cols]
                unique = "UNIQUE " if cols[0][1] == 0 else ""
                lines.append(f"- {unique}`{name}` ({', '.join(col_names)})")
            lines.append("")

    conn.close()
    return "\n".join(lines)


def main():
    base = Path(__file__).resolve().parents[2]  # project root
    config_path = base / "database" / ".schema_dump.json"

    engine = "sqlite"
    config = {}

    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
        engine = cfg.get("engine", "sqlite")
        config = cfg.get("connection", {})

    output_path = base / "docs" / "database.md"

    if engine == "sqlite":
        db_path = config.get("path", str(base / "database" / "database.sqlite"))
        md = dump_sqlite(db_path)
    elif engine == "mysql":
        md = dump_mysql(config)
    else:
        sys.exit(f"Unknown engine: {engine}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    print(f"[schema_dump] OK -> {output_path}")


if __name__ == "__main__":
    main()
