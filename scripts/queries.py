import argparse
import contextlib
from datetime import date
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
PERIODI = [
    (date(2026, 1, 1),),
    (date(2026, 1, 1), date(2026, 1, 1)),
    (date(2026, 1, 1), date(2026, 1, 7)),
    (date(2026, 3, 10), date(2026, 3, 24)),
    (date(2026, 6, 1), date(2026, 8, 31)),
    (date(2026, 9, 29), date(2026, 9, 30)),
    (date(2026, 1, 1), date(2026, 9, 30)),
]


def verifica_filtri():
    from streamlit.testing.v1 import AppTest

    with contextlib.closing(sqlite3.connect(ROOT / "datawarehouse.db")) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        categorie = [r[0] for r in conn.execute(
            "SELECT DISTINCT categoria_servizio FROM dim_fornitore ORDER BY 1"
        )]
        zone = [r[0] for r in conn.execute(
            "SELECT DISTINCT zona FROM dim_cliente ORDER BY 1"
        )]
        app = AppTest.from_file(str(ROOT / "dashboard/dash.py"), default_timeout=60).run()
        assert not app.exception, list(app.exception)
        casi = [(p, categoria, "Tutte") for p in PERIODI for categoria in categorie]
        casi += [(PERIODI[2], categoria, zona) for categoria in categorie for zona in zone]
        vuoti = 0
        senza_media = 0
        for periodo, categoria, zona in casi:
            app.sidebar.date_input[0].set_value(periodo)
            app.sidebar.selectbox[1].select(categoria)
            app.sidebar.selectbox[0].select(zona)
            app.run()
            caso = (periodo, categoria, zona)
            assert not app.exception, (caso, list(app.exception))
            sql = """
                SELECT COUNT(*),
                    SUM(CASE WHEN r.stato_richiesta = 'Completata' THEN r.importo END),
                    AVG(CASE WHEN r.stato_richiesta = 'Completata' THEN r.tempo_erogazione END),
                    COUNT(DISTINCT r.id_cliente)
                FROM fact_richieste r
                JOIN dim_cliente c ON r.id_cliente = c.id_cliente
                JOIN dim_fornitore f ON r.id_fornitore = f.id_fornitore
                JOIN dim_tempo t ON r.id_tempo = t.id_tempo
                WHERE t.data BETWEEN ? AND ? AND f.categoria_servizio = ?
            """
            params = [str(periodo[0]), str(periodo[-1]), categoria]
            if zona != "Tutte":
                sql += " AND c.zona = ?"
                params.append(zona)
            totale, incasso, media, clienti = conn.execute(sql, params).fetchone()
            attesi = [str(totale), f"€ {incasso or 0:,.2f}",
                      "N/D" if media is None else f"{media:.1f} min", str(clienti)]
            effettivi = [m.value for m in app.metric]
            assert effettivi == attesi, (caso, effettivi, attesi)
            vuoti += totale == 0
            senza_media += media is None
        print(f"OK: {len(casi)} combinazioni; {len(categorie)} categorie; "
              f"{len(PERIODI)} intervalli di piu giorni; {len(zone)} zone.")
        print(f"Verificati {vuoti} casi senza richieste e {senza_media} senza media.")
        print("Nessuna eccezione; tutti e quattro i KPI coincidono con SQLite.")


def esecuzione_standard():
    conn = sqlite3.connect("datawarehouse.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    tabelle = [
        "dim_cliente",
        "dim_fornitore",
        "dim_operatore",
        "dim_tempo",
        "fact_richieste"
    ]

    for tabella in tabelle:
        cursor.execute(f"SELECT COUNT(*) FROM {tabella}")
        totale = cursor.fetchone()[0]
        print(f"{tabella}: {totale} record")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifica-filtri", action="store_true")
    args = parser.parse_args()
    if args.verifica_filtri:
        verifica_filtri()
    else:
        esecuzione_standard()
