# DC-Financial (My $av€ DC)

Un'applicazione per la gestione finanziaria personale sviluppata con Streamlit, che consente di monitorare e gestire il proprio patrimonio.

## Caratteristiche

- Gestione completa del patrimonio finanziario
- Dashboard interattiva con grafici e analisi
- Sistema di autenticazione sicuro con password hashate (bcrypt)
- Gestione utenti amministrativa (solo admin)
- Interfaccia responsive accessibile da tutti i dispositivi
- Supporto per prodotti liquidi e vincolati con proiezioni future

## Requisiti tecnici

Le dipendenze sono elencate nel file `requirements.txt`:

- streamlit
- pandas
- plotly
- pillow
- bcrypt
- psycopg2-binary
- numpy

## Installazione e configurazione

### Locale
1. Clona il repository
2. Installa le dipendenze: `pip install -r requirements.txt`
3. Crea un file `.streamlit/secrets.toml` basato su `.streamlit/secrets.toml.example`
4. Esegui l'applicazione: `streamlit run app.py`

### Database
L'applicazione utilizza PostgreSQL. Per CockroachDB (consigliato per il deploy):

1. Crea un account gratuito su [CockroachDB](https://www.cockroachlabs.com/get-started-cockroachdb/)
2. Crea un cluster e un database
3. Crea le tabelle utilizzando le query incluse nella sezione "Inizializzazione database"
4. Configura le credenziali nel file dei segreti di Streamlit

## Deploy su Streamlit Community Cloud (Hosting Gratuito)

Per deployare l'applicazione gratuitamente su Streamlit Community Cloud con il tuo database CockroachDB, segui questi passaggi dettagliati:

### 1. Preparazione del repository GitHub

1. Crea un nuovo repository **pubblico** su GitHub
   - Vai su https://github.com/new
   - Inserisci un nome per il repository (es. "my-save-dc")
   - Assicurati che sia impostato come "Public"
   - Clicca su "Create repository"

2. Carica tutti i file del progetto sul repository
   - Puoi scaricare i file da questo progetto e poi caricarli sul tuo repository GitHub
   - Assicurati di includere i file: `.streamlit/config.toml`, `app.py`, e tutti i file nelle cartelle `components/` e `utils/`
   - Rinomina `requirements_for_deploy.txt` in `requirements.txt` prima di caricare

### 2. Registrazione e configurazione su Streamlit Cloud

1. Registrati su Streamlit Community Cloud
   - Vai su https://share.streamlit.io/
   - Clicca su "Sign up" e segui le istruzioni (puoi usare il tuo account GitHub)

2. Connetti un nuovo deployment
   - Dopo aver effettuato l'accesso, clicca su "New app"
   - Seleziona il tuo repository GitHub
   - Per "Main file path" inserisci: `app.py`
   - Clicca su "Deploy!"

3. Configura i segreti dell'app
   - Mentre l'app si sta deployando, clicca su "Advanced settings"
   - Seleziona la tab "Secrets"
   - Clicca su "Paste from dictionary"
   - Incolla i seguenti segreti, sostituendo i valori con quelli del tuo database CockroachDB:

```toml
[postgres]
host = "tu-cluster-id.tu-regione.cockroachlabs.cloud"
port = 26257
user = "tuo_username"
password = "tua_password"
database = "nome_database"
sslmode = "verify-full"
```

Per ottenere queste informazioni da CockroachDB:

1. Accedi al tuo account CockroachDB
2. Seleziona il tuo cluster
3. Vai nella sezione "Connect"
4. Seleziona "Connection parameters" per vedere tutti i dettagli di connessione

## Inizializzazione e migrazione del database

### Creazione delle tabelle su CockroachDB

Accedi alla console SQL del tuo cluster CockroachDB ed esegui queste query per inizializzare il database:

```sql
-- Tabella prodotti finanziari
CREATE TABLE IF NOT EXISTS prodotti_finanziari (
    id VARCHAR(36) PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    fornitore VARCHAR(255) NOT NULL,
    tipologia VARCHAR(100) NOT NULL,
    vincolo VARCHAR(50) NOT NULL,
    capitale_investito DECIMAL(15, 2) NOT NULL,
    capitale_finale DECIMAL(15, 2) NOT NULL,
    data_scadenza DATE,
    note TEXT,
    data_inserimento DATE NOT NULL,
    data_aggiornamento DATE NOT NULL
);

-- Tabella utenti
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- Inserisci l'utente admin iniziale
INSERT INTO users (id, username, password, is_admin)
VALUES (1, 'davide.chirillo', '$2b$12$ijiiVWxT8cG4rDXYzpZ2S.zaavbKTmZYIoy9H4Y6kXsllCpcCbpZK', TRUE)
ON CONFLICT (id) DO UPDATE SET username = 'davide.chirillo', is_admin = TRUE
WHERE users.id = 1;
```

### Migrazione dei dati esistenti (se necessario)

Se hai già un database con dati che vuoi migrare al nuovo database CockroachDB, segui questi passaggi:

1. **Esporta i dati dal database esistente**:
   
   Puoi esportare i dati in formato CSV usando SQL o strumenti come pgAdmin:
   
   ```sql
   COPY prodotti_finanziari TO '/tmp/prodotti.csv' DELIMITER ',' CSV HEADER;
   ```

2. **Importa i dati nel nuovo database CockroachDB**:
   
   Dalla console SQL di CockroachDB:
   
   ```sql
   IMPORT INTO prodotti_finanziari CSV DATA ('https://tu-file-pubblico-url/prodotti.csv') WITH skip='1';
   ```
   
   Oppure usa la console web di CockroachDB che offre un'opzione per importare file CSV.

### Verifica dell'inizializzazione

Per verificare che le tabelle siano state create correttamente e che l'utente admin esista:

```sql
-- Verifica struttura tabelle
SHOW COLUMNS FROM prodotti_finanziari;
SHOW COLUMNS FROM users;

-- Verifica utente admin
SELECT id, username, is_admin FROM users;
```

Assicurati che l'utente `davide.chirillo` abbia `id = 1` e `is_admin = true`.

## Accesso all'applicazione

Credenziali predefinite:
- Username: `davide.chirillo`
- Password: `Ant.REP.DC`

## Funzionalità principali

- **Dashboard**: Panoramica del patrimonio con visualizzazioni
- **Lista prodotti**: Gestione e visualizzazione di tutti i prodotti finanziari
- **Aggiungi prodotto**: Creazione di nuovi prodotti
- **Gestione utenti**: Creazione e gestione degli utenti (solo admin)

## Sicurezza

L'applicazione include:
- Password hashate con bcrypt
- Blocco account dopo 5 tentativi falliti
- Timeout sessione di 60 minuti
- Solo l'admin può gestire gli utenti
