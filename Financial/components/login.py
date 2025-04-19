import streamlit as st
from utils.auth import login, is_logged_in, logout

def render_login_page():
    """
    Renders the login page or user info if already logged in
    
    Returns:
    - Boolean: True if user is logged in, False otherwise
    """
    # Stile per mantenere le informazioni utente A DESTRA del logo ma VERTICALMENTE
    st.markdown("""
    <style>
    /* Rimuovi il padding delle colonne nel contenitore principale */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Rendere più compatti i messaggi di informazione */
    div.stAlert {
        padding: 3px !important;
        margin-bottom: 3px !important;
        min-height: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Limita l'altezza del bottone logout */
    div.stButton > button {
        height: 32px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        margin-bottom: 3px !important;
        line-height: 1.2 !important;
    }
    
    /* Fai in modo che le informazioni prendano meno spazio */
    div.stAlert > div {
        min-height: 0 !important;
        padding: 2px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Se l'utente è già loggato, ritorna True
    if is_logged_in():
        # Le info utente sono ora gestite direttamente in app.py
        return True
    
    # Login inserito direttamente nella pagina principale anziché nella sidebar
    # (questa parte viene gestita direttamente in app.py)
    return False