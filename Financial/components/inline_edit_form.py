import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_manager import load_data, save_data

def render_inline_edit_form(df, product_id, on_cancel):
    """
    Renders an inline form for editing an existing product directly in the list
    
    Parameters:
    - df: DataFrame containing financial products data
    - product_id: ID of the product to edit
    - on_cancel: Function to call when cancel button is pressed
    
    Returns:
    - Boolean indicating if the product was updated
    """
    # Filtra il DataFrame per ottenere il prodotto da modificare
    product_df = df[df['id'] == product_id]
    
    if product_df.empty:
        st.error(f"Prodotto con ID {product_id} non trovato.")
        return False
    
    # Ottieni i dati del prodotto
    product = product_df.iloc[0]
    
    st.subheader(f"Modifica Prodotto: {product['nome']}")
    
    # Dividi il form in sezioni
    col1, col2 = st.columns(2)
    
    with col1:
        # Informazioni di base del prodotto
        nome = st.text_input("Nome Prodotto", value=product['nome'])
        fornitore = st.text_input("Fornitore", value=product['fornitore'])
        # Utilizziamo lo stesso elenco di tipologie presente nel form di aggiunta prodotto
        tipologie = [
            "Conto Corrente", 
            "Conto Deposito",
            "Polizza Assicurativa", 
            "Buono Fruttifero", 
            "Titolo Azionario", 
            "Obbligazione", 
            "Fondo Comune", 
            "ETF",
            "Polizza di Accumulo",
            "Altro"
        ]
        
        tipologia = st.selectbox(
            "Tipologia",
            options=tipologie,
            index=tipologie.index(product['tipologia']) if product['tipologia'] in tipologie else 9  # Altro come fallback
        )
        
        # Vincolo (con spiegazione)
        vincolo_opzioni = ["Liquido", "Vincolato"]
        vincolo_index = 0 if product['vincolo'] == "Liquido" else 1
        vincolo = st.radio(
            "Vincolo",
            options=vincolo_opzioni,
            index=vincolo_index,
            help="Indica se il prodotto è liquidabile in qualsiasi momento o se è vincolato fino a una certa data"
        )
        
    with col2:
        # Informazioni finanziarie
        capitale_investito = st.number_input(
            "Capitale Investito (€)",
            min_value=0.0,
            value=float(product['capitale_investito']),
            step=100.0,
            format="%.2f"
        )
        
        capitale_finale = st.number_input(
            "Capitale Finale Previsto (€)",
            min_value=0.0,
            value=float(product['capitale_finale']),
            step=100.0,
            format="%.2f"
        )
        
        # Data di scadenza (mostrata solo se il prodotto è vincolato)
        data_scadenza = None
        if vincolo == "Vincolato":
            # Convert to datetime if it's not None
            current_date = pd.to_datetime(product['data_scadenza']) if pd.notna(product['data_scadenza']) else datetime.now()
            
            # Per prodotti vincolati, implementiamo un selettore di data personalizzato
            # che permette di inserire date molto lontane nel futuro
            st.write("Data di Scadenza")
            
            # Determiniamo i valori di default
            default_year = current_date.year
            default_month = current_date.month
            default_day = current_date.day
            
            # Creiamo tre colonne per anno, mese e giorno
            col_y, col_m, col_d = st.columns(3)
            
            with col_y:
                # Selezione anno con un range molto ampio
                year = st.number_input(
                    "Anno",
                    min_value=datetime.now().year,
                    max_value=2100,  # Andiamo ben oltre il 2036
                    value=default_year,
                    step=1,
                    key=f"expiry_year_{product_id}"
                )
            
            with col_m:
                # Selezione mese
                month = st.number_input(
                    "Mese",
                    min_value=1,
                    max_value=12,
                    value=default_month,
                    step=1,
                    key=f"expiry_month_{product_id}"
                )
            
            with col_d:
                # Selezione giorno
                # Determiniamo il numero massimo di giorni nel mese
                if month in [4, 6, 9, 11]:
                    max_days = 30
                elif month == 2:
                    # Verifica anno bisestile
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        max_days = 29
                    else:
                        max_days = 28
                else:
                    max_days = 31
                
                day = st.number_input(
                    "Giorno",
                    min_value=1,
                    max_value=max_days,
                    value=min(default_day, max_days),  # Assicuriamoci che il valore di default sia valido
                    step=1,
                    key=f"expiry_day_{product_id}"
                )
            
            # Creiamo l'oggetto date a partire dai valori selezionati
            try:
                data_scadenza = datetime(year, month, day).date()
            except ValueError:
                # In caso di combinazione non valida, usiamo l'ultimo giorno valido del mese
                if month == 2 and day > 28:
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        data_scadenza = datetime(year, month, 29).date()
                    else:
                        data_scadenza = datetime(year, month, 28).date()
                else:
                    # Usa l'ultimo giorno del mese
                    if month in [4, 6, 9, 11] and day > 30:
                        data_scadenza = datetime(year, month, 30).date()
                    else:
                        # Questo non dovrebbe mai accadere con i controlli sopra
                        data_scadenza = datetime(year, month, 1).date()
    
    # Note e informazioni aggiuntive
    note = st.text_area("Note Aggiuntive", value=product['note'] if pd.notna(product['note']) else "")
    
    # Bottoni di azione
    col1, col2 = st.columns(2)
    with col1:
        save_button = st.button("💾 Salva Modifiche", type="primary", use_container_width=True)
    with col2:
        cancel_button = st.button("❌ Annulla", use_container_width=True)
        
    # Non usiamo più la checkbox
    
    if cancel_button:
        on_cancel()
        return False
    
    # Non utilizziamo lo stato della sessione
    # Utilizziamo un approccio differente basato sui valori correnti
    
    if save_button:
        # Verifica se il capitale finale è minore del capitale investito
        if vincolo == "Vincolato" and capitale_finale < capitale_investito:
            # Mostriamo un avviso e richiediamo conferma con checkbox
            st.write("") # Spazio vuoto
            st.warning(f"⚠️ Attenzione! Stai impostando un capitale a scadenza ({capitale_finale:.2f} €) più basso del capitale investito ({capitale_investito:.2f} €). Questo significa che questo prodotto genererà una perdita.")
            
            # Aggiungiamo una checkbox di conferma subito dopo l'avviso
            # Utilizziamo direttamente una chiave univoca senza gestire manualmente lo stato
            checkbox_key = f"confirm_loss_checkbox_{product_id}"
            confirm_checkbox = st.checkbox(
                "Confermo che questo prodotto comporterà una perdita e desidero salvarlo comunque", 
                key=checkbox_key
            )
            
            # Se la checkbox non è spuntata, impedisci il salvataggio
            if not confirm_checkbox:
                st.error("Per salvare un prodotto con perdita, devi confermare spuntando la casella sopra.")
                return False
        
        # Preparazione dati per il salvataggio
        updated_product = product.copy()
        updated_product['nome'] = nome
        updated_product['fornitore'] = fornitore
        updated_product['tipologia'] = tipologia
        updated_product['vincolo'] = vincolo
        updated_product['capitale_investito'] = capitale_investito
        
        # Se il prodotto è liquido, forziamo il capitale finale uguale al capitale investito
        if vincolo == "Liquido":
            updated_product['capitale_finale'] = capitale_investito
        else:
            updated_product['capitale_finale'] = capitale_finale
            
        updated_product['note'] = note
        updated_product['data_aggiornamento'] = datetime.now()
        
        # Aggiorna la data di scadenza solo se il prodotto è vincolato
        if vincolo == "Vincolato" and data_scadenza is not None:
            updated_product['data_scadenza'] = data_scadenza
        elif vincolo == "Liquido":
            updated_product['data_scadenza'] = None
        
        # Ottieni l'indice della riga da aggiornare
        index_to_update = df.index[df['id'] == product_id].tolist()
        
        if len(index_to_update) > 0:
            # Aggiorna solo le colonne specifiche
            for column in df.columns:
                if column in updated_product:
                    df.loc[index_to_update[0], column] = updated_product[column]
            
            # Salva i dati aggiornati
            save_data(df)
            
            # Non abbiamo più bisogno di resettare lo stato di conferma
        else:
            st.error("Errore: prodotto non trovato nel database.")
        
        # Successo!
        return True
    
    return False