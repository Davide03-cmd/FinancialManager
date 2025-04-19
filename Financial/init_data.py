import psycopg2
import os
import datetime
from psycopg2 import sql
import random
import string
from config import get_db_config

def generate_id():
    """
    Generates a unique ID for a new product
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

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
                    return None
    except Exception as e:
        print(f"Errore generale di connessione al database: {e}")
        return None

def init_database():
    """
    Initialize the database schema if tables don't exist
    """
    conn = get_db_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    try:
        # Crea la tabella dei prodotti finanziari
        cursor.execute("""
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
        """)
        
        # Crea la tabella degli utenti
        cursor.execute("""
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
        """)
        
        # Inserisci l'utente admin se non esiste
        cursor.execute("""
            INSERT INTO users (id, username, password, is_admin)
            VALUES (1, 'davide.chirillo', '$2b$12$ijiiVWxT8cG4rDXYzpZ2S.zaavbKTmZYIoy9H4Y6kXsllCpcCbpZK', TRUE)
            ON CONFLICT (id) DO UPDATE SET 
                username = 'davide.chirillo', 
                is_admin = TRUE
            WHERE users.id = 1;
        """)
        
        # Insert sample data
        sample_products = [
            {
                'id': generate_id(),
                'nome': 'Conto Corrente',
                'fornitore': 'Banca A',
                'tipologia': 'Conto Corrente',
                'vincolo': 'Liquidità',
                'capitale_investito': 36000.0,
                'capitale_finale': 36000.0,
                'data_scadenza': None,
                'note': 'Conto principale',
                'data_inserimento': datetime.date.today().strftime('%Y-%m-%d'),
                'data_aggiornamento': datetime.date.today().strftime('%Y-%m-%d')
            },
            {
                'id': generate_id(),
                'nome': 'Risparmio Vincolato',
                'fornitore': 'Banca B',
                'tipologia': 'Conto Deposito',
                'vincolo': 'Risparmio Vincolato',
                'capitale_investito': 1000.0,
                'capitale_finale': 1100.0,
                'data_scadenza': '2025-06-30',
                'note': 'Vincolo di 6 mesi',
                'data_inserimento': datetime.date.today().strftime('%Y-%m-%d'),
                'data_aggiornamento': datetime.date.today().strftime('%Y-%m-%d')
            }
        ]
        
        # Insert the products
        for product in sample_products:
            cursor.execute("""
                INSERT INTO prodotti_finanziari (
                    id, nome, fornitore, tipologia, vincolo,
                    capitale_investito, capitale_finale, data_scadenza,
                    note, data_inserimento, data_aggiornamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                product['id'],
                product['nome'],
                product['fornitore'],
                product['tipologia'],
                product['vincolo'],
                product['capitale_investito'],
                product['capitale_finale'],
                product['data_scadenza'],
                product['note'],
                product['data_inserimento'],
                product['data_aggiornamento']
            ))
        
        conn.commit()
        print("Database inizializzato con successo con 2 prodotti di esempio")
        return True
    except Exception as e:
        print(f"Errore durante l'inizializzazione del database: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_database()