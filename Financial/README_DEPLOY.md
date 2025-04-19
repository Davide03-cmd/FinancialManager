# Guida al Deployment di My $av€ DC su Streamlit Community Cloud

Questa guida ti guiderà passo per passo nel processo di deployment dell'applicazione My $av€ DC su Streamlit Community Cloud, utilizzando un database CockroachDB gratuito.

## Indice
1. [Prerequisiti](#prerequisiti)
2. [Preparazione del Repository GitHub](#preparazione-del-repository-github)
3. [Configurazione del Database CockroachDB](#configurazione-del-database-cockroachdb)
4. [Deployment su Streamlit Community Cloud](#deployment-su-streamlit-community-cloud)
5. [Verifica dell'Installazione](#verifica-dellinstallazione)
6. [Risoluzione dei Problemi](#risoluzione-dei-problemi)

## Prerequisiti

Prima di iniziare, assicurati di avere:
- Un account GitHub (gratuitamente su [github.com](https://github.com/))
- Un account CockroachDB Cloud (gratuitamente su [cockroachlabs.cloud](https://cockroachlabs.cloud))
- Un account Streamlit Community Cloud (gratuitamente su [streamlit.io](https://streamlit.io/cloud))

## Preparazione del Repository GitHub

1. **Crea un nuovo repository pubblico su GitHub**
   - Vai su https://github.com/new
   - Inserisci un nome per il repository (es. "my-save-dc")
   - Descrizione (opzionale): "Gestione finanziaria personale"
   - Seleziona "Public" (importante: deve essere pubblico per Streamlit Cloud gratuito)
   - Seleziona "Add a README file"
   - Clicca su "Create repository"

2. **Clona il repository sul tuo computer**
   ```bash
   git clone https://github.com/TUOUSERNAME/my-save-dc.git
   cd my-save-dc
   ```

3. **Copia tutti i file dell'applicazione**
   - Scarica tutti i file da questa applicazione
   - Copia i file nel repository clonato
   - Rinomina `requirements_for_deploy.txt` in `requirements.txt`

4. **Carica i file su GitHub**
   ```bash
   git add .
   git commit -m "Caricamento iniziale dell'applicazione"
   git push origin main
   ```

## Configurazione del Database CockroachDB

1. **Crea un account CockroachDB Cloud**
   - Vai su [cockroachlabs.cloud](https://cockroachlabs.cloud) e registrati
   - Scegli "Create a FREE cluster"

2. **Configura il tuo cluster**
   - Scegli un nome per il cluster (es. "my-save-dc")
   - Seleziona il provider cloud (es. AWS, GCP, Azure)
   - Seleziona una regione vicina alla tua posizione geografica
   - Clicca su "Create Cluster"

3. **Crea il database**
   - Una volta creato il cluster, vai alla sezione "SQL Users"
   - Crea un nuovo utente SQL (annota username e password)
   - Vai alla sezione "Connect" e seleziona "Connection parameters"
   - Annota i parametri di connessione (host, porta, etc.)

4. **Crea le tabelle nel database**
   - Vai alla sezione "SQL Console" del tuo cluster
   - Copia e incolla le seguenti query e clicca su "Run":

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
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login TIMESTAMP
);

-- Inserisci l'utente admin iniziale
INSERT INTO users (id, username, password, is_admin)
VALUES (1, 'davide.chirillo', '$2b$12$ijiiVWxT8cG4rDXYzpZ2S.zaavbKTmZYIoy9H4Y6kXsllCpcCbpZK', TRUE)
ON CONFLICT (id) DO UPDATE SET 
    username = 'davide.chirillo', 
    is_admin = TRUE
WHERE users.id = 1;
```

## Deployment su Streamlit Community Cloud

1. **Registrati su Streamlit Community Cloud**
   - Vai su [streamlit.io/cloud](https://streamlit.io/cloud)
   - Clicca su "Sign up" (puoi usare il tuo account GitHub)

2. **Connetti un nuovo deployment**
   - Dopo aver effettuato l'accesso, clicca su "New app"
   - Seleziona il tuo repository GitHub (se non lo vedi, potrebbe essere necessario concedere l'accesso a Streamlit)
   - Per "Main file path" inserisci: `app.py`
   - Clicca su "Advanced settings..."
   - Nella tab "Secrets", clicca su "Paste from a dictionary" e incolla:

```toml
[postgres]
host = "tu-cluster-id.tu-regione.cockroachlabs.cloud"
port = 26257
user = "tuo_username"
password = "tua_password"
database = "defaultdb"  # o il nome del tuo database
sslmode = "verify-full"
```

Sostituisci i valori con quelli ottenuti dalla console CockroachDB.

3. **Completa il deployment**
   - Clicca su "Save" per salvare i segreti
   - Clicca su "Deploy!" per avviare il deployment

## Verifica dell'Installazione

1. **Attendi il completamento del deployment**
   - Streamlit Cloud mostrerà lo stato del deployment
   - Una volta completato, clicca sul link dell'app per aprirla

2. **Verifica l'accesso**
   - Accedi all'applicazione con le seguenti credenziali:
     - Username: `davide.chirillo`
     - Password: `Ant.REP.DC`
   - Verifica che tutte le funzionalità siano operative

## Risoluzione dei Problemi

### Problema: Errore di connessione al database
- **Soluzione**: Verifica che i segreti contengano i dati di connessione corretti
- **Procedura**: Vai nelle impostazioni dell'app su Streamlit Cloud, tab "Secrets" e controlla i parametri

### Problema: Errore nelle tabelle del database
- **Soluzione**: Controlla che le tabelle siano state create correttamente
- **Procedura**: Usa la SQL Console di CockroachDB per verificare con `SHOW TABLES;`

### Problema: Nessun utente admin disponibile
- **Soluzione**: Verifica che l'utente admin sia stato creato
- **Procedura**: Esegui `SELECT * FROM users;` nella SQL Console di CockroachDB