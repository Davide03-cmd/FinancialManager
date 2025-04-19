import streamlit as st
import psycopg2
import bcrypt
import os
from datetime import datetime, timedelta
from config import get_db_config

def get_db_connection():
    """
    Creates a connection to the PostgreSQL database
    
    Returns:
    - connection: psycopg2 connection object
    """
    try:
        db_config = get_db_config()
        
        # Se abbiamo un URL diretto, usalo
        if "url" in db_config:
            try:
                # Prima prova con verify-full
                conn = psycopg2.connect(db_config["url"])
                return conn
            except Exception as ssl_error:
                print(f"Errore con SSL verify-full: {ssl_error}")
                # Modifica l'URL per usare sslmode=require
                modified_url = db_config["url"].replace("sslmode=verify-full", "sslmode=require")
                if modified_url == db_config["url"]:  # Se non c'era verify-full nell'URL
                    if "?" in modified_url:
                        modified_url += "&sslmode=require"
                    else:
                        modified_url += "?sslmode=require"
                try:
                    conn = psycopg2.connect(modified_url)
                    print("Connessione riuscita con sslmode=require")
                    return conn
                except Exception as second_error:
                    print(f"Errore anche con sslmode=require: {second_error}")
                    # Ultimo tentativo senza SSL
                    try:
                        no_ssl_url = modified_url.replace("sslmode=require", "sslmode=disable")
                        conn = psycopg2.connect(no_ssl_url)
                        print("Connessione riuscita con sslmode=disable")
                        return conn
                    except Exception as final_error:
                        print(f"Tutti i tentativi di connessione falliti: {final_error}")
                        st.error("Impossibile connettersi al database. Controlla le credenziali.")
                        return None
        # Altrimenti, usa i parametri individuali
        else:
            connect_params = {
                "host": db_config["host"],
                "port": db_config["port"],
                "user": db_config["user"],
                "password": db_config["password"],
                "database": db_config["database"],
                "sslmode": "require"  # Impostiamo sempre require come default
            }
            
            # Aggiungi parametri opzionali se presenti nel config
            if "sslmode" in db_config:
                connect_params["sslmode"] = db_config["sslmode"]
            if "options" in db_config:
                connect_params["options"] = db_config["options"]
                
            try:
                conn = psycopg2.connect(**connect_params)
                return conn
            except Exception as params_error:
                print(f"Errore con parametri individuali: {params_error}")
                # Prova con sslmode=disable come ultima risorsa
                connect_params["sslmode"] = "disable"
                try:
                    conn = psycopg2.connect(**connect_params)
                    print("Connessione riuscita con sslmode=disable")
                    return conn
                except Exception as final_params_error:
                    print(f"Fallimento finale della connessione: {final_params_error}")
                    st.error("Impossibile connettersi al database. Controlla le credenziali.")
                    return None
    except Exception as e:
        print(f"Errore generale di connessione al database: {e}")
        st.error(f"Errore di connessione al database: {e}")
        return None

def hash_password(password):
    """
    Create a secure hash of the password using bcrypt
    """
    # Genera un salt casuale e esegue l'hashing della password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')  # Convertiamo in stringa per salvare nel database

def check_password(password, hashed):
    """
    Verifica se la password corrisponde all'hash memorizzato
    """
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def login(username, password):
    """
    Verify user credentials and log them in
    
    Parameters:
    - username: Username
    - password: Password
    
    Returns:
    - Boolean: True if login successful, False otherwise
    - Dict: User data if login successful, None otherwise
    - String: Error message, if any
    """
    try:
        # Memorizza l'username per autocompletarlo la prossima volta
        st.session_state.last_username = username
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Prima verifichiamo se l'account è bloccato
        cur.execute(
            "SELECT id, username, password, is_admin, login_attempts, locked_until FROM users WHERE username = %s",
            (username,)
        )
        user = cur.fetchone()
        
        # Se l'utente non esiste
        if not user:
            # Non aggiorniamo login_attempts perché l'utente non esiste
            cur.close()
            conn.close()
            return False, None, "Username o password non validi"
        
        user_id, db_username, db_password, is_admin, login_attempts, locked_until = user
        
        # Verifica se l'account è bloccato
        if locked_until and locked_until > datetime.now():
            remaining_time = locked_until - datetime.now()
            minutes = int(remaining_time.total_seconds() / 60)
            cur.close()
            conn.close()
            return False, None, f"Account bloccato. Riprova tra {minutes} minuti."
        
        # Verifica della password
        password_correct = False
        
        # Controllo se la password è in formato bcrypt o MD5 (per retrocompatibilità)
        if db_password.startswith('$2b$') or db_password.startswith('$2a$'):
            # Password in formato bcrypt
            password_correct = check_password(password, db_password)
        else:
            # Password in vecchio formato MD5, la verifichiamo e aggiorniamo
            import hashlib
            old_hash = hashlib.md5(password.encode()).hexdigest()
            password_correct = (old_hash == db_password)
            
            # Se la password è corretta, aggiorniamo al nuovo formato bcrypt
            if password_correct:
                new_hash = hash_password(password)
                cur.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (new_hash, user_id)
                )
                conn.commit()
        
        if password_correct:
            # Login successful - Reset login attempts e aggiorna last_login
            current_time = datetime.now()
            cur.execute(
                "UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = %s WHERE id = %s",
                (current_time, user_id)
            )
            conn.commit()
            
            # Salva info di sessione
            user_data = {
                'id': user_id,
                'username': db_username,
                'is_admin': is_admin,
                'logged_in': True,
                'login_time': current_time,
                'session_expires': current_time + timedelta(minutes=60)  # Scadenza 60 minuti
            }
            
            cur.close()
            conn.close()
            return True, user_data, "Login effettuato con successo"
        else:
            # Login failed - Incrementa login_attempts
            new_attempts = login_attempts + 1
            
            # Se raggiunge 5 tentativi, blocca l'account per 30 minuti
            if new_attempts >= 5:
                lock_time = datetime.now() + timedelta(minutes=30)
                cur.execute(
                    "UPDATE users SET login_attempts = %s, locked_until = %s WHERE id = %s",
                    (new_attempts, lock_time, user_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                return False, None, "Troppi tentativi falliti. Account bloccato per 30 minuti."
            else:
                cur.execute(
                    "UPDATE users SET login_attempts = %s WHERE id = %s",
                    (new_attempts, user_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                remaining_attempts = 5 - new_attempts
                return False, None, f"Username o password non validi. Tentativi rimasti: {remaining_attempts}"
            
    except Exception as e:
        st.error(f"Errore durante il login: {e}")
        return False, None, f"Errore durante il login: {e}"

def is_logged_in():
    """
    Check if user is logged in
    
    Returns:
    - Boolean: True if user is logged in, False otherwise
    """
    if 'user' not in st.session_state or not st.session_state.user.get('logged_in', False):
        return False
    
    # Verifica scadenza sessione (60 minuti)
    if 'session_expires' in st.session_state.user:
        if datetime.now() > st.session_state.user['session_expires']:
            # Sessione scaduta
            logout()
            st.warning("La sessione è scaduta. Effettua nuovamente il login.")
            return False
        else:
            # Aggiorniamo la scadenza della sessione ad ogni interazione
            st.session_state.user['session_expires'] = datetime.now() + timedelta(minutes=60)
    
    return True

def is_admin():
    """
    Check if logged in user is an admin
    
    Returns:
    - Boolean: True if user is admin, False otherwise
    """
    return is_logged_in() and st.session_state.user.get('is_admin', False)

def logout():
    """
    Log out the current user
    """
    # Salviamo l'username prima di rimuovere la sessione
    if 'user' in st.session_state and 'username' in st.session_state.user:
        # Memorizziamo l'ultimo username usato
        st.session_state.last_username = st.session_state.user['username']
    
    # Rimuoviamo l'utente dalla sessione
    if 'user' in st.session_state:
        del st.session_state.user

def get_all_users():
    """
    Get all users from the database (admin only)
    
    Returns:
    - List: List of user dictionaries
    """
    if not is_admin():
        return []
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id")
        users_data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        users = []
        for user in users_data:
            users.append({
                'id': user[0],
                'username': user[1],
                'is_admin': user[2],
                'created_at': user[3]
            })
            
        return users
    except Exception as e:
        st.error(f"Errore durante il recupero degli utenti: {e}")
        return []

def create_user(username, password, is_admin_user=False):
    """
    Create a new user (admin only)
    
    Parameters:
    - username: Username
    - password: Password
    - is_admin_user: Boolean indicating if user is admin
    
    Returns:
    - Boolean: True if user creation successful, False otherwise
    - String: Message indicating result
    """
    # Verifica che chi sta creando l'utente sia un amministratore
    if not is_admin():
        return False, "Solo gli amministratori possono creare nuovi utenti"
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if username already exists
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, f"Lo username '{username}' è già in uso"
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Insert the new user
        cur.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
            (username, hashed_password, is_admin_user)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Utente '{username}' creato con successo"
    except Exception as e:
        return False, f"Errore durante la creazione dell'utente: {e}"

def delete_user(user_id):
    """
    Delete a user (admin only)
    
    Parameters:
    - user_id: ID of the user to delete
    
    Returns:
    - Boolean: True if deletion successful, False otherwise
    - String: Message indicating result
    """
    if not is_admin():
        return False, "Solo gli amministratori possono eliminare utenti"
        
    try:
        # Prevent deleting the master admin
        if user_id == st.session_state.user.get('id'):
            return False, "Non puoi eliminare il tuo account"
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Delete the user
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return False, "Utente non trovato"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, "Utente eliminato con successo"
    except Exception as e:
        return False, f"Errore durante l'eliminazione dell'utente: {e}"

def change_password(user_id, new_password):
    """
    Change a user's password (admin only)
    
    Parameters:
    - user_id: ID of the user
    - new_password: New password
    
    Returns:
    - Boolean: True if change successful, False otherwise
    - String: Message indicating result
    """
    if not is_admin():
        return False, "Solo gli amministratori possono modificare le password"
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Update the password
        cur.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed_password, user_id)
        )
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return False, "Utente non trovato"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, "Password aggiornata con successo"
    except Exception as e:
        return False, f"Errore durante l'aggiornamento della password: {e}"