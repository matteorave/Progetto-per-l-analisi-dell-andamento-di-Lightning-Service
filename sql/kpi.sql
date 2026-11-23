-- 1. Richieste Totali
SELECT COUNT(*) AS richieste_totali FROM fact_richieste;

-- 2. Incasso totale
SELECT SUM(importo) AS incasso_totale
FROM fact_richieste
WHERE stato_richiesta = 'Completata';


-- 3. Tempo medio di erogazione
SELECT AVG(tempo_erogazione) AS tempo_medio
FROM fact_richieste
WHERE stato_richiesta = 'Completata';


-- 4. Numero clienti attivi
SELECT COUNT(DISTINCT id_cliente) AS clienti_attivi
FROM fact_richieste;

-- 5. Top 5 fornitori per incasso
SELECT
    f.nome,
    SUM(r.importo) AS incasso_totale
FROM fact_richieste r
JOIN dim_fornitore f
    ON r.id_fornitore = f.id_fornitore
WHERE r.stato_richiesta = 'Completata'
GROUP BY f.id_fornitore, f.nome
ORDER BY incasso_totale DESC
LIMIT 5;
