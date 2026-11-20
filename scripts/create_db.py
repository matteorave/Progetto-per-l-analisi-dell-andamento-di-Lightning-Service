import argparse
import contextlib
from datetime import datetime
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]


def ripristina_schema():
    database = ROOT / "datawarehouse.db"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup = ROOT / f"datawarehouse.before_constraints_{stamp}.db"
    rebuilt = ROOT / f"datawarehouse.rebuilt_{stamp}.db"
    tables = ("dim_cliente", "dim_fornitore", "dim_operatore", "dim_tempo", "fact_richieste")
    with contextlib.closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source:
        source.execute("PRAGMA foreign_keys = ON")
        with contextlib.closing(sqlite3.connect(backup)) as saved:
            saved.execute("PRAGMA foreign_keys = ON")
            source.backup(saved)
        with contextlib.closing(sqlite3.connect(rebuilt)) as target:
            target.execute("PRAGMA foreign_keys = ON")
            target.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
            with target:
                for table in tables:
                    columns = [r[1] for r in target.execute(f"PRAGMA table_info({table})")]
                    names = ", ".join(columns)
                    rows = source.execute(f"SELECT {names} FROM {table}").fetchall()
                    placeholders = ", ".join("?" for _ in columns)
                    target.executemany(f"INSERT INTO {table} ({names}) VALUES ({placeholders})", rows)
                    assert target.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == len(rows)
                    print(f"{table}: {len(rows)} record conservati")
                assert not target.execute("PRAGMA foreign_key_check").fetchall()
    rebuilt.replace(database)
    print(f"Schema ripristinato. Copia originale: {backup.name}")


def esecuzione_standard():
    conn = sqlite3.connect("datawarehouse.db")
    conn.execute("PRAGMA foreign_keys = ON")

    with open("sql/schema.sql", "r", encoding="utf-8") as file:
        schema = file.read()

    conn.executescript(schema)

    conn.commit()
    conn.close()

    print("Database creato correttamente.")


    conn = sqlite3.connect("datawarehouse.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name;
    """)

    for tabella in cursor.fetchall():
        print(tabella[0])

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ripristina-schema", action="store_true")
    args = parser.parse_args()
    if args.ripristina_schema:
        ripristina_schema()
    else:
        esecuzione_standard()
