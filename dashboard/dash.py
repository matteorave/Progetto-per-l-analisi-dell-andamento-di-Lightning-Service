import streamlit as st
import sqlite3
import pandas as pd
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "datawarehouse.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

st.set_page_config(
    page_title="Lightning Service Analytics",
    page_icon="📊",
    layout="wide"
)

st.html("""
<style>
/* Nasconde solo la registrazione, mantenendo le altre voci del menu. */
[data-testid="stMainMenuItem-recordScreencast"] {
    display: none !important;
}
</style>
""")

st.title("📊 Lightning Service Analytics")
st.caption("Dashboard di analisi del Data Warehouse")
st.divider()



# DATI PER I FILTRI


query_zone_filtro = """
SELECT DISTINCT zona
FROM dim_cliente
ORDER BY zona;
"""

df_zone_filtro = pd.read_sql_query(query_zone_filtro, conn)

zone = ["Tutte"] + df_zone_filtro["zona"].tolist()


query_categoria = """
SELECT DISTINCT categoria_servizio
FROM dim_fornitore
ORDER BY categoria_servizio;
"""

df_categoria = pd.read_sql_query(query_categoria, conn)

categorie = ["Tutte"] + df_categoria["categoria_servizio"].tolist()


query_date = """
SELECT MIN(data) AS data_min,
       MAX(data) AS data_max
FROM dim_tempo;
"""

df_date = pd.read_sql_query(query_date, conn)

data_min = pd.to_datetime(df_date.iloc[0]["data_min"]).date()
data_max = pd.to_datetime(df_date.iloc[0]["data_max"]).date()


# FILTRI INTERATTIVI


st.sidebar.title("Filtri")

st.sidebar.markdown(
    "Seleziona i parametri per aggiornare la dashboard."
)

zona_selezionata = st.sidebar.selectbox(
    "Zona",
    zone,
    key="filtro_zona"
)

categoria_selezionata = st.sidebar.selectbox(
    "Categoria di servizio",
    categorie,
    key="filtro_categoria"
)

periodo = st.sidebar.date_input(
    "Periodo",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max,
    key="filtro_periodo"
)



# COSTRUZIONE FILTRI SQL


filtri = []
parametri = []

if zona_selezionata != "Tutte":
    filtri.append("c.zona = ?")
    parametri.append(zona_selezionata)

if categoria_selezionata != "Tutte":
    filtri.append("f.categoria_servizio = ?")
    parametri.append(categoria_selezionata)

if periodo:
    filtri.append("t.data BETWEEN ? AND ?")
    parametri.append(str(periodo[0]))
    parametri.append(str(periodo[-1]))

where_clause = ""

if filtri:
    where_clause = "WHERE " + " AND ".join(filtri)



# KPI 1 - RICHIESTE TOTALI


query_richieste = f"""
SELECT COUNT(*) AS richieste_totali
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause};
"""

df_richieste = pd.read_sql_query(
    query_richieste,
    conn,
    params=parametri
)

totale_richieste = df_richieste.iloc[0]["richieste_totali"]


# KPI 2 - INCASSO TOTALE


query_incasso = f"""
SELECT SUM(r.importo) AS incasso_totale
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause}
{"AND" if where_clause else "WHERE"} r.stato_richiesta = 'Completata';
"""

df_incasso = pd.read_sql_query(
    query_incasso,
    conn,
    params=parametri
)

incasso_totale = df_incasso.iloc[0]["incasso_totale"]

if pd.isna(incasso_totale):
    incasso_totale = 0



# KPI 3 - TEMPO MEDIO


query_tempo = f"""
SELECT AVG(r.tempo_erogazione) AS tempo_medio
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause}
{"AND" if where_clause else "WHERE"} r.stato_richiesta = 'Completata';
"""

df_tempo = pd.read_sql_query(
    query_tempo,
    conn,
    params=parametri
)

tempo_medio = df_tempo.iloc[0]["tempo_medio"]



# KPI 4 - CLIENTI ATTIVI


query_clienti = f"""
SELECT COUNT(DISTINCT r.id_cliente) AS clienti_attivi
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause};
"""

df_clienti = pd.read_sql_query(
    query_clienti,
    conn,
    params=parametri
)

clienti_attivi = df_clienti.iloc[0]["clienti_attivi"]



# VISUALIZZAZIONE KPI


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Richieste totali",
        totale_richieste
    )

with col2:
    st.metric(
        "Incasso totale",
        f"€ {incasso_totale:,.2f}"
    )

with col3:
    st.metric(
        "Tempo medio",
        "N/D" if pd.isna(tempo_medio) else f"{tempo_medio:.1f} min"
    )

with col4:
    st.metric(
        "Clienti attivi",
        clienti_attivi
    )

st.divider()



# RICHIESTE PER ZONA


query_zone = f"""
SELECT
    c.zona,
    COUNT(*) AS numero_richieste
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause}
GROUP BY c.zona
ORDER BY numero_richieste DESC;
"""

df_zone = pd.read_sql_query(
    query_zone,
    conn,
    params=parametri
)



# TOP 5 FORNITORI PER INCASSO


query_fornitori = f"""
SELECT
    f.nome,
    SUM(r.importo) AS incasso_totale
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause}
{"AND" if where_clause else "WHERE"} r.stato_richiesta = 'Completata'
GROUP BY f.id_fornitore, f.nome
ORDER BY incasso_totale DESC
LIMIT 5;
"""

df_fornitori = pd.read_sql_query(
    query_fornitori,
    conn,
    params=parametri
)



# VISUALIZZAZIONE PRIMI DUE GRAFICI


col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Richieste per zona")
    st.bar_chart(
        df_zone.set_index("zona"),
        use_container_width=True
    )

with col_grafico2:
    st.subheader("Top 5 fornitori per incasso")
    st.bar_chart(
        df_fornitori.set_index("nome"),
        use_container_width=True
    )

st.divider()



# ANDAMENTO DELLE RICHIESTE NEL TEMPO


query_andamento = f"""
SELECT
    t.data,
    COUNT(*) AS numero_richieste
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause}
GROUP BY t.data
ORDER BY t.data;
"""

df_andamento = pd.read_sql_query(
    query_andamento,
    conn,
    params=parametri
)

st.subheader("Andamento delle richieste nel tempo")

st.line_chart(
    df_andamento.set_index("data"),
    use_container_width=True
)

st.divider()



# DISTRIBUZIONE PER CATEGORIA DI SERVIZIO


query_categorie = f"""
SELECT
    f.categoria_servizio,
    COUNT(*) AS numero_richieste
FROM fact_richieste r
JOIN dim_cliente c
    ON r.id_cliente = c.id_cliente
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
JOIN dim_tempo t
    ON r.id_tempo = t.id_tempo
{where_clause}
GROUP BY f.categoria_servizio
ORDER BY numero_richieste DESC;
"""

df_categorie = pd.read_sql_query(
    query_categorie,
    conn,
    params=parametri
)

st.subheader("Distribuzione delle richieste per categoria di servizio")

st.bar_chart(
    df_categorie.set_index("categoria_servizio"),
    use_container_width=True
)



# CHIUSURA CONNESSIONE


conn.close()
