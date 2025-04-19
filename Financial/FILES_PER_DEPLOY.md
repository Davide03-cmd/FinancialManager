# File Essenziali per il Deployment

Questo documento elenca tutti i file necessari per effettuare il deployment dell'applicazione My $av€ DC su Streamlit Community Cloud.

## File Principali

- `app.py` - File principale dell'applicazione Streamlit
- `requirements.txt` - Elenco delle dipendenze Python (rinomina `requirements_for_deploy.txt` in `requirements.txt`)
- `.streamlit/config.toml` - Configurazione di Streamlit

## File di Immagine e Asset

- `assets/MySaveDCLogo.png` - Logo dell'applicazione

## Directory e File per Componenti

- `components/`
  - `dashboard.py` - Componente per la dashboard principale
  - `product_list.py` - Componente per la lista dei prodotti finanziari
  - `product_form.py` - Componente per l'aggiunta/modifica di prodotti
  - `inline_edit_form.py` - Componente per la modifica inline
  - `login.py` - Componente per la gestione dell'autenticazione
  - `user_management.py` - Componente per la gestione degli utenti

## Directory e File per Utilities

- `utils/`
  - `auth.py` - Funzioni per l'autenticazione e gestione utenti
  - `data_manager.py` - Funzioni per la gestione dei dati
  - `financial.py` - Calcoli finanziari
  - `plotting.py` - Funzioni per i grafici

## File di Configurazione e Inizializzazione

- `config.py` - Configurazione dell'applicazione
- `init_data.py` - Script per l'inizializzazione del database

## File di Documentazione

- `README.md` - Documentazione generale dell'applicazione
- `README_DEPLOY.md` - Guida al deployment

## File di Supporto

- `.gitignore` - File per escludere file/cartelle da Git
- `.streamlit/secrets.toml.example` - Esempio di configurazione dei segreti (non caricare su GitHub)

## Come Preparare i File per il Deployment

1. Raccogli tutti i file elencati sopra
2. Rinomina `requirements_for_deploy.txt` in `requirements.txt`
3. Crea un repository GitHub pubblico
4. Carica tutti questi file sul repository
5. Segui le istruzioni in `README_DEPLOY.md` per completare il deployment

## Nota su Segreti e Configurazioni

Non includere mai il file `.streamlit/secrets.toml` (se lo hai creato localmente) nel repository GitHub. Questo file contiene informazioni sensibili come le credenziali del database. Invece, configura i segreti direttamente nella console di Streamlit Community Cloud come spiegato nella guida al deployment.