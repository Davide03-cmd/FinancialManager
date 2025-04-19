import os
import streamlit as st

# Configurazione del database
# Su Streamlit Cloud, imposta queste variabili nei segreti
# https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management

def get_db_config():
    """
    Restituisce la configurazione del database, con priorità ai segreti di Streamlit
    """
    # Controlla se siamo in un ambiente Streamlit Cloud con segreti configurati
    if hasattr(st, "secrets") and "postgres" in st.secrets:
        # Se è presente una stringa di connessione completa, usala direttamente
        if "url" in st.secrets["postgres"]:
            return {"url": st.secrets["postgres"]["url"]}
        # Altrimenti usa i parametri individuali
        else:
            return {
                "host": st.secrets["postgres"]["host"],
                "port": st.secrets["postgres"]["port"],
                "user": st.secrets["postgres"]["user"],
                "password": st.secrets["postgres"]["password"],
                "database": st.secrets["postgres"]["database"],
                # Parametri aggiuntivi per la sicurezza
                "sslmode": st.secrets["postgres"].get("sslmode", "require"),
                "options": st.secrets["postgres"].get("options", "")
            }
    
    # Altrimenti usa le variabili d'ambiente (Replit)
    elif "DATABASE_URL" in os.environ:
        db_url = os.environ["DATABASE_URL"]
        return {"url": db_url}
    
    # Default per sviluppo locale
    else:
        return {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "postgres",
            "database": "finance_app"
        }