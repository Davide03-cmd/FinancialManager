import pandas as pd
import psycopg2
import os
import random
import string
import datetime
from psycopg2 import sql
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
        # Check if the products table exists
        cursor.execute("""
            SELECT EXISTS (
               SELECT FROM information_schema.tables 
               WHERE table_name = 'prodotti_finanziari'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create the table
            cursor.execute("""
                CREATE TABLE prodotti_finanziari (
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
            conn.commit()
            print("Tabella prodotti_finanziari creata con successo")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'inizializzazione del database: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_id():
    """
    Generates a unique ID for a new product
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def load_data():
    """
    Loads financial products data from PostgreSQL database
    
    Returns:
    - DataFrame: containing financial products data
    """
    # Initialize the database if needed
    init_database()
    
    conn = get_db_connection()
    if conn is None:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            'id', 'nome', 'fornitore', 'tipologia', 'vincolo',
            'capitale_investito', 'capitale_finale', 'data_scadenza',
            'note', 'data_inserimento', 'data_aggiornamento'
        ])
    
    try:
        # Read data from the database
        query = "SELECT * FROM prodotti_finanziari ORDER BY data_inserimento DESC;"
        df = pd.read_sql_query(query, conn)
        
        # Set id as the index but non visibile come colonna
        if not df.empty and 'id' in df.columns:
            # Salviamo l'ID come indice ma impostando drop=True per non mantenerlo come colonna
            df = df.set_index('id', drop=True)
            # Ricreaiamo una colonna 'id' nascosta per operazioni interne ma non visibile nell'interfaccia
            df['id'] = df.index
        
        return df
    except Exception as e:
        print(f"Errore durante il caricamento dei dati: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            'id', 'nome', 'fornitore', 'tipologia', 'vincolo',
            'capitale_investito', 'capitale_finale', 'data_scadenza',
            'note', 'data_inserimento', 'data_aggiornamento'
        ])
    finally:
        conn.close()

def save_data(df):
    """
    Saves financial products data to PostgreSQL database
    
    Parameters:
    - df: DataFrame containing financial products data
    """
    if df.empty:
        return
    
    # Make a copy of the dataframe to avoid modifying the original
    df_copy = df.copy()
    
    # Ensure all required columns exist
    required_columns = [
        'id', 'nome', 'fornitore', 'tipologia', 'vincolo',
        'capitale_investito', 'capitale_finale', 'data_scadenza',
        'note', 'data_inserimento', 'data_aggiornamento'
    ]
    
    for col in required_columns:
        if col not in df_copy.columns:
            if col == 'id':
                df_copy['id'] = [generate_id() for _ in range(len(df_copy))]
            elif col == 'data_inserimento' or col == 'data_aggiornamento':
                df_copy[col] = datetime.datetime.now().strftime('%Y-%m-%d')
            elif col == 'data_scadenza':
                df_copy[col] = None
            elif col == 'note':
                df_copy[col] = ''
            else:
                df_copy[col] = ''
    
    # Gestire correttamente la colonna data_scadenza per evitare errori di tipo
    # Convertiamo le date a oggetti datetime e gestisci i valori nulli correttamente
    df_copy['data_scadenza'] = pd.to_datetime(df_copy['data_scadenza'], errors='coerce')
    
    # Creiamo una lista per memorizzare le date in formato corretto per SQL
    data_scadenze_sql = []
    
    for d in df_copy['data_scadenza']:
        if pd.isna(d):
            data_scadenze_sql.append(None)  # Usa None per date NULL in SQL
        else:
            data_scadenze_sql.append(d.strftime('%Y-%m-%d'))  # Formatta le date valide
    
    # Sostituisci la colonna con i dati formattati correttamente
    df_copy['data_scadenza'] = data_scadenze_sql
    
    # Connect to the database
    conn = get_db_connection()
    if conn is None:
        print("Impossibile connettersi al database per salvare i dati")
        return
    
    cursor = conn.cursor()
    
    try:
        # For each record, do an "UPSERT" - update if ID exists, insert if it doesn't
        for _, row in df_copy.iterrows():
            # Ensure each product has an ID
            if pd.isna(row['id']) or row['id'] == '':
                row['id'] = generate_id()
            
            # Assicuriamoci che i prodotti liquidi abbiano capitale_finale == capitale_investito
            if row['vincolo'] == 'Liquido':
                row['capitale_finale'] = row['capitale_investito']
            
            # First check if this ID already exists
            cursor.execute("SELECT COUNT(*) FROM prodotti_finanziari WHERE id = %s", (row['id'],))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Update existing record
                update_query = sql.SQL("""
                    UPDATE prodotti_finanziari
                    SET nome = %s, fornitore = %s, tipologia = %s, vincolo = %s,
                        capitale_investito = %s, capitale_finale = %s, data_scadenza = %s,
                        note = %s, data_inserimento = %s, data_aggiornamento = %s
                    WHERE id = %s;
                """)
                
                cursor.execute(update_query, (
                    row['nome'],
                    row['fornitore'],
                    row['tipologia'],
                    row['vincolo'],
                    row['capitale_investito'],
                    row['capitale_finale'],
                    row['data_scadenza'],
                    row['note'],
                    row['data_inserimento'],
                    row['data_aggiornamento'],
                    row['id']
                ))
            else:
                # Insert new record
                insert_query = sql.SQL("""
                    INSERT INTO prodotti_finanziari (
                        id, nome, fornitore, tipologia, vincolo,
                        capitale_investito, capitale_finale, data_scadenza,
                        note, data_inserimento, data_aggiornamento
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """)
                
                # Execute the query with the row values
                cursor.execute(insert_query, (
                    row['id'],
                    row['nome'],
                    row['fornitore'],
                    row['tipologia'],
                    row['vincolo'],
                    row['capitale_investito'],
                    row['capitale_finale'],
                    row['data_scadenza'],
                    row['note'],
                    row['data_inserimento'],
                    row['data_aggiornamento']
                ))
        
        # Commit the changes
        conn.commit()
        print(f"Salvati {len(df_copy)} prodotti nel database")
    except Exception as e:
        print(f"Errore durante il salvataggio dei dati: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def delete_product(product_id):
    """
    Deletes a product from the database
    
    Parameters:
    - product_id: ID of the product to delete
    
    Returns:
    - Boolean: indicating if deletion was successful
    """
    if not product_id:
        return False
    
    conn = get_db_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Delete the product
        cursor.execute("DELETE FROM prodotti_finanziari WHERE id = %s;", (product_id,))
        
        # Check if a row was affected
        rows_deleted = cursor.rowcount
        
        # Commit the changes
        conn.commit()
        
        return rows_deleted > 0
    except Exception as e:
        print(f"Errore durante l'eliminazione del prodotto: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def duplicate_product(product_id):
    """
    Duplicates a product in the database
    
    Parameters:
    - product_id: ID of the product to duplicate
    
    Returns:
    - Boolean: indicating if duplication was successful
    - String: New product ID if successful
    """
    if not product_id:
        return False, None
    
    conn = get_db_connection()
    if conn is None:
        return False, None
    
    cursor = conn.cursor()
    
    try:
        # Get the product data
        cursor.execute("""
            SELECT nome, fornitore, tipologia, vincolo, capitale_investito, 
                   capitale_finale, data_scadenza, note
            FROM prodotti_finanziari 
            WHERE id = %s;
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            return False, None
        
        # Generate new ID
        new_id = generate_id()
        
        # Current date for insertion
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Ottieni i valori dal prodotto
        nome = product[0] + " (Copia)"
        fornitore = product[1]
        tipologia = product[2]
        vincolo = product[3]
        capitale_investito = product[4]
        capitale_finale = product[5]
        data_scadenza = product[6]
        note = product[7]
        
        # Per prodotti liquidi, forza capitale_finale = capitale_investito
        if vincolo == 'Liquido':
            capitale_finale = capitale_investito
        
        # Insert duplicate with new ID and current date
        cursor.execute("""
            INSERT INTO prodotti_finanziari (
                id, nome, fornitore, tipologia, vincolo,
                capitale_investito, capitale_finale, data_scadenza,
                note, data_inserimento, data_aggiornamento
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            new_id,
            nome,
            fornitore,
            tipologia,
            vincolo,
            capitale_investito,
            capitale_finale,
            data_scadenza,
            note,
            current_date,
            current_date
        ))
        
        # Commit the changes
        conn.commit()
        
        return True, new_id
    except Exception as e:
        print(f"Errore durante la duplicazione del prodotto: {e}")
        conn.rollback()
        return False, None
    finally:
        cursor.close()
        conn.close()