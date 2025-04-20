import streamlit as st
import pandas as pd
import os
import base64
import io
from PIL import Image
from components.dashboard import render_dashboard
from components.product_form import render_product_form
from components.product_list import render_product_list
from components.login import render_login_page
from components.user_management import render_user_management
from utils.data_manager import load_data
from utils.auth import is_logged_in, is_admin, logout

# Importazione del logo incorporato
from app_logo import LOGO_BASE64

# Set page configuration
st.set_page_config(
    page_title="My $av€ DC",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"  # Cambiato a expanded per mostrare la sidebar del login
)

# Funzione per caricare il logo
def get_logo():
    """
    Restituisce il logo come immagine PIL, usando la versione base64 incorporata
    """
    try:
        # Prima prova a caricare il file dal percorso
        return Image.open('assets/MySaveDCLogo.png')
    except Exception:
        try:
            # Se non funziona, usa la versione base64
            binary_data = base64.b64decode(LOGO_BASE64)
            return Image.open(io.BytesIO(binary_data))
        except Exception:
            # Se anche questo fallisce, restituisci None
            return None

# Ottimizza layout con spazi adeguati - approccio più semplice
st.markdown("""
<style>
    /* Rimuovi gli spazi in alto nel contenitore principale */
    .block-container {
        padding-top: 1rem;
    }
    
    /* Stili per i bottoni */
    div.stButton > button {
        margin-top: 0;
    }
    
    /* Riduci altezza header e footer */
    header {
        visibility: hidden;
        height: 0;
        margin: 0;
        padding: 0;
    }
    
    footer {
        visibility: hidden;
        height: 0;
        margin: 0;
        padding: 0;
    }
    
    /* Nascondi la toolbar */
    div[data-testid="stToolbar"] {
        visibility: hidden;
        height: 0;
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione dello stato della sessione
if 'edit_product' not in st.session_state:
    st.session_state.edit_product = None

if 'duplicate_product' not in st.session_state:
    st.session_state.duplicate_product = None

if 'reload_data' not in st.session_state:
    st.session_state.reload_data = True
    
# Stato per gestire quale tab è attiva - default: "dashboard"
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "dashboard"
    
if 'show_success_message' not in st.session_state:
    st.session_state.show_success_message = False
    st.session_state.success_message = ""
    
# Importiamo datetime per essere usato nel codice
from datetime import datetime, timedelta

# Funzioni per cambiare tab
def set_tab(tab_name):
    st.session_state.active_tab = tab_name

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Rendering della pagina di login nella sidebar
user_logged_in = render_login_page()

# Prosegui solo se l'utente è loggato
if user_logged_in:
    # Load data - always reload from database on page load
    df = load_data()
    
    # Layout con logo sopra e pulsanti di navigazione in linea
    st.markdown("<div style='margin-top: 0;'></div>", unsafe_allow_html=True)
    
    # Crea due righe, una per logo/info e una per i pulsanti
    row1_cols = st.columns([1, 3])  # Logo e info utente
    
    # Logo nella prima colonna
    with row1_cols[0]:
        logo = get_logo()
        if logo:
            st.image(logo, use_container_width=True)
        else:
            st.title("My $av€ DC")
    
    # Informazioni utente nella seconda colonna
    with row1_cols[1]:
        # Disponiamo gli elementi in colonne per mantenere la larghezza originale
        # ma organizziamo verticalmente gli elementi che ci interessano
        info_cols = st.columns([2, 6])
        
        # Colonna sinistra per gli elementi da impilare verticalmente
        with info_cols[0]:
            # Primo elemento: Benvenuto
            st.success(f"Benvenuto, {st.session_state.user['username']}!")
            
            # Secondo elemento: Account Amministratore (se applicabile)
            if st.session_state.user.get('is_admin', False):
                st.info("👑 Account Amministratore")
            
            # Terzo elemento: Logout (per ultimo come richiesto)
            st.button("Logout", key="logout_btn", help="Esci dall'applicazione", on_click=logout)
        
        # Colonna destra per i messaggi di successo (manteniamo questa funzionalità)
        with info_cols[1]:
            if st.session_state.show_success_message:
                st.success(st.session_state.success_message)
                # Reset dopo averlo mostrato
                st.session_state.show_success_message = False
    
    # Crea la riga dei pulsanti con tutti allineati in orizzontale
    nav_cols = st.columns(4 if is_admin() else 3)  # 4 colonne se admin, altrimenti 3
    
    with nav_cols[0]:
        btn_dashboard = st.button("📊 Dashboard", use_container_width=True, 
                               type="primary" if st.session_state.active_tab == "dashboard" else "secondary")
        if btn_dashboard:
            st.session_state.active_tab = "dashboard"
            st.rerun()
            
    with nav_cols[1]:
        btn_add = st.button("➕ Aggiungi Patrimonio", use_container_width=True,
                        type="primary" if st.session_state.active_tab == "add" else "secondary")
        if btn_add:
            st.session_state.active_tab = "add"
            st.rerun()
            
    with nav_cols[2]:
        btn_list = st.button("📋 Listato Patrimonio", use_container_width=True,
                         type="primary" if st.session_state.active_tab == "list" else "secondary")
        if btn_list:
            st.session_state.active_tab = "list"
            st.rerun()
    
    # Mostra il tab di gestione utenti solo per gli admin
    if is_admin():
        with nav_cols[3]:
            btn_users = st.button("👥 Gestione Utenti", use_container_width=True,
                             type="primary" if st.session_state.active_tab == "users" else "secondary")
            if btn_users:
                st.session_state.active_tab = "users"
                st.rerun()
    
    # Aggiungi una separazione visiva
    st.divider()
    
    # Mostra il contenuto in base alla tab selezionata
    if st.session_state.active_tab == "dashboard":
        render_dashboard(df)
        
    elif st.session_state.active_tab == "add":
        # Verifica se c'è un prodotto da modificare
        edit_id = st.session_state.edit_product
        
        # Verifica se c'è un prodotto da duplicare (ha precedenza sull'edit)
        duplicate_id = st.session_state.duplicate_product
        
        if duplicate_id is not None:
            # Siamo in modalità duplicazione
            st.info("Stai creando un nuovo prodotto basato su uno esistente. Modifica i campi come necessario e salva.")
            
            # Passa sia l'ID del prodotto da duplicare che un flag di duplicazione
            result = render_product_form(df, duplicate_id, is_duplicate=True)
        else:
            # Modalità normale edit/create                
            result = render_product_form(df, edit_id, is_duplicate=False)
        
        # Verifica se il risultato è una tupla (nuovo formato) o un booleano (vecchio formato)
        if isinstance(result, tuple):
            form_submitted, success_msg = result
        else:
            form_submitted = result
            success_msg = ""
        
        if form_submitted:
            # Reset edit_product dopo la modifica
            st.session_state.edit_product = None
            # Reset duplicate_product dopo il salvataggio
            st.session_state.duplicate_product = None
            
            st.session_state.reload_data = True
            st.session_state.active_tab = "list"  # Passa alla tab Lista Prodotti
            
            if success_msg:
                st.session_state.show_success_message = True
                st.session_state.success_message = success_msg
                
            # Force page refresh to show the updated data
            st.rerun()
            
    elif st.session_state.active_tab == "list":
        render_product_list(df)
        
    elif st.session_state.active_tab == "users" and is_admin():
        render_user_management()
    
    # Footer
    st.divider()
    st.caption("© 2025 My $av€ DC")
else:
    # Se l'utente non è loggato, mostra il logo e un messaggio di benvenuto con il login form
    # Aggiungiamo spazio extra in alto solo per la pagina di login
    st.markdown("<div style='margin-top: 70px;'></div>", unsafe_allow_html=True)
    
    # Mostra il logo
    logo = get_logo()
    if logo:
        st.image(logo, width=300)
    else:
        st.title("My $av€ DC")
    
    st.header("👋 Benvenuto nella tua app personale di gestione finanziaria!")
    
    # Form di login integrato nella pagina principale - versione compatta
    st.markdown("<h4 style='margin-bottom: 0.5rem;'>Accedi al tuo account</h4>", unsafe_allow_html=True)
    
    # Ottieni l'ultimo username usato, se disponibile
    last_username = ""
    if "last_username" in st.session_state:
        last_username = st.session_state.last_username
        
    # CSS personalizzato per campi di input più compatti
    st.markdown("""
    <style>
    /* Stile per input ridotti in larghezza */
    input.st-bs {
        max-width: 200px !important;
    }
    div[data-testid="column"] {
        width: auto !important;
        flex: 0 1 auto !important;
        min-width: auto !important;
    }
    button[kind="primary"] {
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Layout più compatto con colonne di larghezza automatica
    cols = st.columns([1, 1, 1, 3])  # L'ultima colonna è solo uno spaziatore
    with cols[0]:
        username = st.text_input("Username", value=last_username, key="login_username", 
                               label_visibility="collapsed", placeholder="Username")
    with cols[1]:
        password = st.text_input("Password", type="password", key="login_password", 
                               label_visibility="collapsed", placeholder="Password")
    with cols[2]:
        login_button = st.button("Accedi", use_container_width=True)
    
    if login_button:
        if not username or not password:
            st.error("Inserisci username e password")
        else:
            from utils.auth import login
            success, user_data, message = login(username, password)
            if success:
                # Salva i dati utente nella session state
                st.session_state.user = user_data
                st.rerun()
            else:
                st.error(message)