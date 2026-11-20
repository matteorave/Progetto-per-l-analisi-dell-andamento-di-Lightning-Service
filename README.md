# Lightning Service

Lightning Service è la startup fittizia utilizzata come caso di studio per il mio Project Work L-31.

Il progetto simula un piccolo sistema di analisi dei dati relativo a una startup di servizi on-demand. I dati riguardano clienti, fornitori, operatori e richieste di servizio e vengono elaborati attraverso un processo ETL, caricati in un Data Warehouse SQLite e successivamente analizzati tramite query SQL e una dashboard realizzata con Streamlit.

I dati utilizzati sono sintetici e hanno esclusivamente lo scopo di simulare il funzionamento del sistema.

## Avvio della dashboard

I comandi devono essere eseguiti dalla cartella principale del progetto tramite PowerShell.

Se l’ambiente virtuale `.venv` non è ancora presente, può essere creato tramite:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pandas streamlit
```

Se invece il database `datawarehouse.db` è già presente e contiene i dati, è possibile avviare direttamente la dashboard:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/dash.py
```

Streamlit dovrebbe aprire automaticamente la dashboard nel browser.

## Creazione e caricamento del database

Per ricreare il database partendo dai dati iniziali devono essere presenti nella cartella `data` i quattro file:

- `clienti.csv`
- `fornitori.csv`
- `operatori.csv`
- `richieste.csv`

La creazione e il caricamento possono essere eseguiti tramite:

```powershell
.\.venv\Scripts\python.exe scripts/create_db.py
.\.venv\Scripts\python.exe scripts/ETL.py
.\.venv\Scripts\python.exe scripts/queries.py
```

Il primo script crea la struttura del database sulla base del file `sql/schema.sql`.

Il secondo esegue il processo ETL, leggendo i file CSV, controllando e trasformando i dati e caricandoli nel Data Warehouse.

Il terzo permette di effettuare alcune verifiche sui dati caricati e mostra il numero di record presenti nelle tabelle.

Le query utilizzate per il calcolo dei principali KPI sono contenute nel file `sql/kpi.sql`.

È consigliato evitare di eseguire più volte l’ETL sugli stessi dati senza prima controllare il database, perché un nuovo caricamento degli stessi record può generare errori dovuti alla presenza di chiavi primarie duplicate.

## Struttura del Data Warehouse

Il Data Warehouse è organizzato secondo uno schema a stella.

La tabella centrale è:

`fact_richieste`

collegata alle quattro dimensioni:

- dim_cliente
- dim_fornitore
- dim_operatore
- dim_tempo

La dimensione `dim_tempo` viene creata durante il processo ETL partendo dal campo `data_ora` presente nel file delle richieste.

## Verifica dell’integrità referenziale

Durante lo sviluppo ho aggiunto alcuni controlli per verificare che le relazioni tra le tabelle fossero corrette.

SQLite richiede l’attivazione delle chiavi esterne per ogni connessione tramite:

```sql
PRAGMA foreign_keys = ON;
```

Per controllare le relazioni della tabella `fact_richieste` vengono inoltre utilizzati:

```sql
PRAGMA foreign_key_list(fact_richieste);
PRAGMA foreign_key_check;
```

Il primo comando permette di controllare che siano presenti le quattro chiavi esterne relative a cliente, fornitore, operatore e tempo.

Il secondo permette invece di verificare se nel database sono presenti riferimenti non validi.

Per effettuare una verifica completa direttamente da PowerShell è possibile utilizzare:

```powershell
@'
import sqlite3
from contextlib import closing

with closing(sqlite3.connect('file:datawarehouse.db?mode=ro', uri=True)) as conn:
    conn.execute('PRAGMA foreign_keys = ON')

    enabled = conn.execute('PRAGMA foreign_keys').fetchone()[0]
    relations = conn.execute(
        'PRAGMA foreign_key_list(fact_richieste)'
    ).fetchall()
    violations = conn.execute(
        'PRAGMA foreign_key_check'
    ).fetchall()

    print('foreign_keys:', enabled)
    print('Chiavi esterne fact_richieste:', len(relations))
    print('Violazioni:', violations)
'@ | .\.venv\Scripts\python.exe -
```

Il risultato corretto prevede:

- `foreign_keys` uguale a `1`;
- quattro chiavi esterne nella tabella `fact_richieste`;
- nessuna violazione restituita da `foreign_key_check`.

Durante lo sviluppo questo controllo mi ha permesso anche di individuare un problema nella struttura iniziale del database, che non conteneva correttamente tutti i vincoli definiti nel file `schema.sql`.

## Verifica dei filtri

La dashboard utilizza filtri per:

- periodo;
- zona;
- categoria di servizio.

I filtri modificano dinamicamente le query SQL e aggiornano sia i KPI sia i grafici.

Per effettuare un controllo dei filtri può essere utilizzato:

```powershell
.\.venv\Scripts\python.exe scripts/queries.py --verifica-filtri
```

Questo controllo serve per confrontare i risultati ottenuti attraverso i filtri della dashboard con quelli presenti direttamente nel database SQLite.

## Ripristino dello schema

Durante lo sviluppo è stato necessario aggiungere anche una procedura per ricostruire correttamente le tabelle nel caso in cui il database non contenga i vincoli definiti nel file `schema.sql`.

Il comando utilizzato è:

```powershell
.\.venv\Scripts\python.exe scripts/create_db.py --ripristina-schema
```

Prima della ricostruzione viene mantenuta una copia del database precedente.

Durante il ripristino vengono caricate prima le tabelle dimensionali e successivamente `fact_richieste`, così da rispettare le relazioni tra le diverse tabelle.

È consigliato eseguire questa operazione con la dashboard e il processo ETL chiusi.

## KPI presenti nella dashboard

La dashboard permette di visualizzare:

- numero totale delle richieste;
- incasso totale;
- tempo medio di erogazione;
- clienti attivi;
- richieste per zona;
- top 5 fornitori per incasso;
- andamento delle richieste nel tempo;
- distribuzione delle richieste per categoria di servizio.

## Flusso generale del progetto

Il percorso principale seguito dai dati è:

CSV  
→ Python e Pandas  
→ processo ETL  
→ Data Warehouse SQLite  
→ query SQL  
→ dashboard Streamlit

Il progetto è stato realizzato con finalità didattiche e rappresenta una versione semplificata di un possibile sistema di analisi dei dati per una startup di servizi on-demand.
