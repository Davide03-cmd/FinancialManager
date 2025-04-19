# Guida alla Migrazione dei Dati

Questa guida ti aiuterà a migrare i dati esistenti dall'attuale database al nuovo database CockroachDB per il deployment su Streamlit Community Cloud.

## Migrazione dei Dati dei Prodotti Finanziari

### 1. Esportazione dei Dati dal Database Originale

Per esportare i dati dalla tabella `prodotti_finanziari`:

```sql
-- Esegui nella console SQL del database originale
COPY prodotti_finanziari TO '/tmp/prodotti_finanziari.csv' WITH CSV HEADER;
```

Se non hai accesso diretto al server, puoi ottenere un CSV tramite psql:

```bash
# Sostituisci DB_URL con l'URL del tuo database originale
psql "DB_URL" -c "COPY (SELECT * FROM prodotti_finanziari) TO STDOUT WITH CSV HEADER" > prodotti_finanziari.csv
```

### 2. Importazione dei Dati nel Database CockroachDB

#### Metodo 1: Tramite SQL Console di CockroachDB

1. Vai alla console SQL di CockroachDB
2. Seleziona il tuo database
3. Nella sezione "Import" carica il file CSV
4. Seleziona la tabella di destinazione `prodotti_finanziari`
5. Mappa le colonne se necessario
6. Clicca su "Import"

#### Metodo 2: Tramite Query SQL (se hai accesso a URL pubblico del CSV)

```sql
-- Esegui nella console SQL di CockroachDB
IMPORT INTO prodotti_finanziari CSV DATA ('https://url-pubblico/prodotti_finanziari.csv') WITH 
  skip = '1',
  nullif = '';
```

#### Metodo 3: Inserimento Manuale

Se hai pochi prodotti, puoi inserirli manualmente tramite SQL:

```sql
INSERT INTO prodotti_finanziari (
    id, nome, fornitore, tipologia, vincolo,
    capitale_investito, capitale_finale, data_scadenza,
    note, data_inserimento, data_aggiornamento
) VALUES 
('ID1', 'Nome Prodotto 1', 'Fornitore 1', 'Tipologia 1', 'Vincolo 1', 1000.00, 1100.00, '2025-12-31', 'Note 1', '2025-04-19', '2025-04-19'),
('ID2', 'Nome Prodotto 2', 'Fornitore 2', 'Tipologia 2', 'Vincolo 2', 2000.00, 2200.00, '2026-06-30', 'Note 2', '2025-04-19', '2025-04-19');
```

### Verifica della Migrazione

Dopo aver importato i dati, verifica che tutto sia stato migrato correttamente:

```sql
-- Conteggio dei prodotti
SELECT COUNT(*) FROM prodotti_finanziari;

-- Visualizza tutti i prodotti
SELECT * FROM prodotti_finanziari;

-- Verifica i totali
SELECT SUM(capitale_investito) AS totale_investito, SUM(capitale_finale) AS totale_finale 
FROM prodotti_finanziari;
```

## Note Importanti

1. **Backup**: Prima di procedere con la migrazione, assicurati di avere un backup completo del database originale.

2. **ID Utente**: L'utente admin (`davide.chirillo`) deve avere ID=1 nel nuovo database. Questo è già configurato nei script di inizializzazione.

3. **Timezone**: Verifica che le date siano migrate correttamente, considerando che CockroachDB potrebbe usare UTC come timezone predefinita.

4. **Caratteri Speciali**: Se i tuoi dati contengono caratteri speciali, assicurati che l'encoding sia corretto durante l'importazione (UTF-8 consigliato).

5. **Indici e Vincoli**: Dopo la migrazione, verifica che tutti gli indici e i vincoli funzionino correttamente.

## Risoluzione Problemi Comuni

- **Errore di formato CSV**: Assicurati che il CSV abbia l'intestazione corretta e che i campi siano delimitati da virgole.

- **Errore di tipo di dati**: Controlla che i tipi di dati nel CSV corrispondano a quelli della tabella di destinazione.

- **Errore di vincoli**: Se ci sono violazioni di vincoli (es. ID duplicati), risolvi i conflitti prima di riprovare l'importazione.