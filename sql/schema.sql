CREATE TABLE IF NOT EXISTS dim_cliente (
    id_cliente TEXT PRIMARY KEY,
    zona TEXT NOT NULL,
    data_iscrizione TEXT
);

CREATE TABLE IF NOT EXISTS dim_fornitore (
    id_fornitore TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria_servizio TEXT,
    zona TEXT
);

CREATE TABLE IF NOT EXISTS dim_operatore (
    id_operatore TEXT PRIMARY KEY,
    zona TEXT,
    tipo_attivita TEXT
);

CREATE TABLE IF NOT EXISTS dim_tempo (
    id_tempo INTEGER PRIMARY KEY,
    data TEXT,
    giorno INTEGER,
    mese INTEGER,
    anno INTEGER,
    giorno_settimana TEXT,
    ora INTEGER,
    fascia_oraria TEXT
);

CREATE TABLE IF NOT EXISTS fact_richieste (
    id_richiesta TEXT PRIMARY KEY,

    id_cliente TEXT,
    id_fornitore TEXT,
    id_operatore TEXT,
    id_tempo INTEGER,

    importo REAL,
    tempo_erogazione INTEGER,
    stato_richiesta TEXT,

    FOREIGN KEY (id_cliente)
        REFERENCES dim_cliente(id_cliente),

    FOREIGN KEY (id_fornitore)
        REFERENCES dim_fornitore(id_fornitore),

    FOREIGN KEY (id_operatore)
        REFERENCES dim_operatore(id_operatore),

    FOREIGN KEY (id_tempo)
        REFERENCES dim_tempo(id_tempo)
);