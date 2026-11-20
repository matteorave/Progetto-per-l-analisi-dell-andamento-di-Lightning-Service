import pandas as pd
import sqlite3

# Lettura CSV
clienti = pd.read_csv("data/clienti.csv")
fornitori = pd.read_csv("data/fornitori.csv")
operatori = pd.read_csv("data/operatori.csv")
richieste = pd.read_csv("data/richieste.csv")

# Controllo iniziale
print("Clienti:")
print(clienti.head())

print("\nFornitori:")
print(fornitori.head())

print("\nOperatori:")
print(operatori.head())

print("\nRichieste:")
print(richieste.head())




print("\nValori nulli clienti:")
print(clienti.isnull().sum())

print("\nValori nulli fornitori:")
print(fornitori.isnull().sum())

print("\nValori nulli operatori:")
print(operatori.isnull().sum())

print("\nValori nulli richieste:")
print(richieste.isnull().sum())


print(clienti.duplicated().sum())
print(fornitori.duplicated().sum())
print(operatori.duplicated().sum())
print(richieste.duplicated().sum())


richieste["data_ora"] = pd.to_datetime(richieste["data_ora"])


richieste["data"] = richieste["data_ora"].dt.date
richieste["giorno"] = richieste["data_ora"].dt.day
richieste["mese"] = richieste["data_ora"].dt.month
richieste["anno"] = richieste["data_ora"].dt.year
richieste["ora"] = richieste["data_ora"].dt.hour
richieste["giorno_settimana"] = richieste["data_ora"].dt.day_name()


def fascia_oraria(ora):
    if 6 <= ora < 12:
        return "Mattina"
    elif 12 <= ora < 18:
        return "Pomeriggio"
    elif 18 <= ora < 23:
        return "Sera"
    else:
        return "Notte"

richieste["fascia_oraria"] = richieste["ora"].apply(fascia_oraria)





dim_tempo = richieste[
    [
        "data",
        "giorno",
        "mese",
        "anno",
        "giorno_settimana",
        "ora",
        "fascia_oraria"
    ]
].drop_duplicates().reset_index(drop=True)


dim_tempo["id_tempo"] = range(1, len(dim_tempo) + 1)


richieste = richieste.merge(
    dim_tempo,
    on=[
        "data",
        "giorno",
        "mese",
        "anno",
        "giorno_settimana",
        "ora",
        "fascia_oraria"
    ],
    how="left"
)



fact_richieste = richieste[
    [
        "id_richiesta",
        "id_cliente",
        "id_fornitore",
        "id_operatore",
        "id_tempo",
        "importo",
        "tempo_erogazione",
        "stato_richiesta"
    ]
]

print(fact_richieste.head())


conn = sqlite3.connect("datawarehouse.db")
conn.execute("PRAGMA foreign_keys = ON")

clienti.to_sql(
    "dim_cliente",
    conn,
    if_exists="append",
    index=False
)

fornitori.to_sql(
    "dim_fornitore",
    conn,
    if_exists="append",
    index=False
)

operatori.to_sql(
    "dim_operatore",
    conn,
    if_exists="append",
    index=False
)

dim_tempo.to_sql(
    "dim_tempo",
    conn,
    if_exists="append",
    index=False
)

fact_richieste.to_sql(
    "fact_richieste",
    conn,
    if_exists="append",
    index=False
)

conn.close()

print("ETL completato correttamente.")
