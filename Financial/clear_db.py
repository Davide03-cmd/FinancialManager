import psycopg2
import os
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

def clear_products_table():
    """
    Svuota la tabella dei prodotti finanziari
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Svuota completamente la tabella
        cursor.execute("DELETE FROM prodotti_finanziari")
        
        # Commit dei cambiamenti
        conn.commit()
        print("Tabella 'prodotti_finanziari' svuotata con successo!")
        
    except Exception as e:
        print(f"Errore durante lo svuotamento della tabella: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_products_table()