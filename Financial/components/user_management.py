import streamlit as st
import pandas as pd
import time
from utils.auth import get_all_users, create_user, delete_user, change_password, is_admin

def render_user_management():
    """
    Renders the user management page (admin only)
    """
    if not is_admin():
        st.error("Accesso negato. Solo gli amministratori possono gestire gli utenti.")
        return
    
    st.header("👥 Gestione Utenti")
    
    # Sezione per creare un nuovo utente
    st.subheader("Crea un nuovo utente")
    
    col1, col2 = st.columns(2)
    with col1:
        new_username = st.text_input("Username", key="new_username")
    with col2:
        new_password = st.text_input("Password", type="password", key="new_password")
    
    is_new_admin = st.checkbox("Amministratore", key="is_new_admin")
    
    if st.button("Crea Utente", key="create_user_btn"):
        if not new_username or not new_password:
            st.error("Username e password sono obbligatori")
        else:
            success, message = create_user(new_username, new_password, is_new_admin)
            if success:
                st.success(message)
                # Rerun senza tentare di reimpostare i campi
                # (i campi verranno reimpostati automaticamente al ricaricamento della pagina)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)
    
    st.divider()
    
    # Lista degli utenti esistenti
    st.subheader("Utenti esistenti")
    
    users = get_all_users()
    
    if not users:
        st.info("Nessun utente trovato")
    else:
        # Convertire i dati in un DataFrame per visualizzarli
        users_df = pd.DataFrame(users)
        users_df = users_df.rename(columns={
            'id': 'ID',
            'username': 'Username',
            'is_admin': 'Amministratore',
            'created_at': 'Data Creazione'
        })
        
        # Formattare i valori boolean
        users_df['Amministratore'] = users_df['Amministratore'].apply(lambda x: "✅" if x else "❌")
        
        # Formattare la data di creazione
        users_df['Data Creazione'] = pd.to_datetime(users_df['Data Creazione']).dt.strftime('%d/%m/%Y %H:%M')
        
        # Visualizzare la tabella
        st.dataframe(users_df, hide_index=True)
        
        # Gestione utenti (modificare password, eliminare)
        st.subheader("Gestione utente esistente")
        
        # Dropdown per selezionare l'utente
        user_options = [f"{user['id']} - {user['username']}" for user in users]
        selected_user = st.selectbox("Seleziona utente", user_options, key="user_select")
        
        if selected_user:
            selected_user_id = int(selected_user.split(" - ")[0])
            selected_username = selected_user.split(" - ")[1]
            
            # Evitare operazioni su sé stessi per non bloccarsi l'accesso
            if selected_user_id == st.session_state.user.get('id'):
                st.warning("Stai modificando il tuo account. Fai attenzione a non bloccarti l'accesso.")
            
            tab1, tab2 = st.tabs(["Cambia Password", "Elimina Utente"])
            
            with tab1:
                new_password = st.text_input("Nuova Password", type="password", key="change_password")
                if st.button("Aggiorna Password", key="update_password_btn"):
                    if not new_password:
                        st.error("La password non può essere vuota")
                    else:
                        success, message = change_password(selected_user_id, new_password)
                        if success:
                            st.success(message)
                            # Non serve reset campo - verrà fatto al rerun
                        else:
                            st.error(message)
            
            with tab2:
                st.warning(f"Stai per eliminare l'utente: {selected_username}")
                confirm_delete = st.checkbox("Confermo l'eliminazione", key="confirm_delete")
                if st.button("Elimina Utente", key="delete_user_btn", disabled=not confirm_delete):
                    success, message = delete_user(selected_user_id)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)