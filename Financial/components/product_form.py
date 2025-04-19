import streamlit as st
import pandas as pd
import datetime
from utils.data_manager import save_data, load_data, generate_id

def render_product_form(df, edit_id=None, is_duplicate=False, force_save=False):
    """
    Renders a form for adding or editing financial products
    
    Parameters:
    - df: DataFrame containing financial products data
    - edit_id: ID of the product to edit (None for new product)
    - is_duplicate: Boolean indicating if we're duplicating a product
    - force_save: Boolean indicando che bisogna salvare anche con perdita
    
    Returns:
    - Boolean indicating if a product was added/updated
    """
    # Verifica se siamo in modalità di modifica
    is_edit_mode = edit_id is not None
    
    # Usiamo il parametro is_duplicate per determinare se siamo in modalità duplicazione
    is_duplicate_mode = is_duplicate
    
    # Set up form title
    if is_edit_mode:
        if is_duplicate_mode:
            st.header("➕ Duplica Prodotto")
        else:
            st.header("✏️ Modifica Prodotto")
            
        # Find the product with matching ID
        product_to_edit = df[df['id'] == edit_id].iloc[0].to_dict() if not df.empty and 'id' in df.columns and not df[df['id'] == edit_id].empty else None
        
        # If product not found, show error and return
        if product_to_edit is None:
            st.error("Prodotto non trovato. Potrebbe essere stato eliminato.")
            return False
            
        # Se siamo in modalità duplicazione, modifichiamo leggermente il nome per indicare che è una copia
        if is_duplicate_mode and 'nome' in product_to_edit:
            product_to_edit['nome'] = product_to_edit['nome'] + " (Copia)"
            
            # In modalità duplicazione, assicuriamoci che i campi di ID e date vengano trattati come nuovi
            if 'id' in product_to_edit:
                del product_to_edit['id']  # Rimuovi l'ID per generarne uno nuovo
            
    else:
        st.header("➕ Aggiungi Nuovo Patrimonio")
        # Create empty product for new mode
        product_to_edit = {
            'nome': "",
            'fornitore': "",
            'tipologia': "Conto Corrente",
            'capitale_investito': 0.0,
            'capitale_finale': 0.0,
            'vincolo': "Liquidità",
            'data_scadenza': None,
            'note': ""
        }
    
    # Form definition
    with st.form(key="product_form"):
        # Product name and provider
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input(
                "Nome del prodotto", 
                value=product_to_edit.get('nome', ''),
                key="nome_input"
            )
        
        with col2:
            fornitore = st.text_input(
                "Fornitore/Emittente",
                value=product_to_edit.get('fornitore', ''),
                key="fornitore_input"
            )
        
        # Product type
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
            "Tipologia di prodotto",
            options=tipologie,
            index=tipologie.index(product_to_edit.get('tipologia', 'Conto Corrente')) if product_to_edit.get('tipologia', '') in tipologie else 0,
            key="tipologia_input"
        )
        
        # Constraint type
        vincolo_options = ["Liquido", "Vincolato"]
        vincolo = st.selectbox(
            "Vincolo",
            options=vincolo_options,
            index=vincolo_options.index(product_to_edit.get('vincolo', 'Liquido')) if product_to_edit.get('vincolo', '') in vincolo_options else 0,
            key="vincolo_input"
        )
        
        # Mostriamo sempre tutti i campi, ma disabilitiamo quelli non applicabili in base al tipo di vincolo
        st.subheader("Dettagli Investimento")
        
        # Gestiamo il cambiamento del capitale investito tramite session_state
        if "capitale_investito_last" not in st.session_state:
            st.session_state.capitale_investito_last = float(product_to_edit.get('capitale_investito', 0))
        
        # Capitale investito (sempre visibile e attivo)
        col1, col2 = st.columns(2)
        with col1:
            capitale_investito = st.number_input(
                "Capitale investito (€)",
                min_value=0.0,
                value=float(product_to_edit.get('capitale_investito', 0)),
                step=100.0,
                format="%.2f",
                key="capitale_investito_input"
            )
        
        # Capitale a scadenza (sempre visibile, ma attivo solo per prodotti vincolati)
        with col2:
            if vincolo == "Liquido":
                # Per prodotti liquidi, mostriamo il campo ma è disabilitato e uguale al capitale investito
                capitale_finale = st.number_input(
                    "Capitale a scadenza (€)",
                    min_value=0.0,
                    value=capitale_investito,  # Uguale al capitale investito
                    step=100.0,
                    format="%.2f",
                    key="capitale_finale_input",
                    disabled=True  # Disabilitato
                )
                # Impostiamo capitale_finale = capitale_investito
                capitale_finale = capitale_investito
            else:
                # Per prodotti vincolati, il campo è attivo e modificabile
                capitale_finale = st.number_input(
                    "Capitale a scadenza (€)",
                    min_value=0.0,
                    value=float(product_to_edit.get('capitale_finale', 0)),
                    step=100.0,
                    format="%.2f",
                    key="capitale_finale_input"
                )
        
        # Default date (one year from now or from product)
        default_date = datetime.date.today() + datetime.timedelta(days=365)
        if is_edit_mode and 'data_scadenza' in product_to_edit and pd.notna(product_to_edit['data_scadenza']):
            try:
                default_date = pd.to_datetime(product_to_edit['data_scadenza']).date()
            except:
                pass
        
        # Data di scadenza (sempre visibile, ma attiva solo per prodotti vincolati)
        if vincolo == "Liquido":
            # Per prodotti liquidi, mostriamo il campo data ma è disabilitato
            data_scadenza_input = st.date_input(
                "Data di scadenza",
                value=default_date,
                key="data_scadenza_input",
                disabled=True  # Disabilitato
            )
            data_scadenza = None  # Per prodotti liquidi, impostiamo None
            
            # Show info message
            st.info("Per i prodotti di tipo 'Liquido', il capitale finale è uguale al capitale investito e la data di scadenza non è applicabile")
        else:
            # Per prodotti vincolati, implementiamo un selettore di data personalizzato
            # che permette di inserire date molto lontane nel futuro
            st.write("Data di scadenza")
            
            # Determiniamo i valori di default
            default_year = default_date.year
            default_month = default_date.month
            default_day = default_date.day
            
            # Creiamo tre colonne per anno, mese e giorno
            col_y, col_m, col_d = st.columns(3)
            
            with col_y:
                # Selezione anno con un range molto ampio
                year = st.number_input(
                    "Anno",
                    min_value=datetime.date.today().year,
                    max_value=2100,  # Andiamo ben oltre il 2036
                    value=default_year,
                    step=1,
                    key="expiry_year"
                )
            
            with col_m:
                # Selezione mese
                month = st.number_input(
                    "Mese",
                    min_value=1,
                    max_value=12,
                    value=default_month,
                    step=1,
                    key="expiry_month"
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
                    key="expiry_day"
                )
            
            # Creiamo l'oggetto date a partire dai valori selezionati
            try:
                data_scadenza = datetime.date(year, month, day)
            except ValueError:
                # In caso di combinazione non valida, usiamo l'ultimo giorno valido del mese
                if month == 2 and day > 28:
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        data_scadenza = datetime.date(year, month, 29)
                    else:
                        data_scadenza = datetime.date(year, month, 28)
                else:
                    # Usa l'ultimo giorno del mese
                    if month in [4, 6, 9, 11] and day > 30:
                        data_scadenza = datetime.date(year, month, 30)
                    else:
                        # Questo non dovrebbe mai accadere con i controlli sopra
                        data_scadenza = datetime.date(year, month, 1)
        
        # Notes
        note = st.text_area(
            "Note aggiuntive",
            value=product_to_edit.get('note', ''),
            key="note_input"
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if is_duplicate_mode:
                button_text = "Duplica Prodotto"
            elif is_edit_mode:
                button_text = "Salva Modifiche"
            else:
                button_text = "Aggiungi Prodotto"
                
            submit_button = st.form_submit_button(
                button_text,
                type="primary",
                use_container_width=True
            )
        
        with col2:
            cancel_button = st.form_submit_button(
                "Annulla",
                use_container_width=True
            )
            
        # Non usiamo più la checkbox per conferma
    
    # Process form submission
    if submit_button:
        # Validate form data
        if not nome:
            st.error("Il nome del prodotto è obbligatorio.")
            return False
        
        if not fornitore:
            st.error("Il fornitore/emittente è obbligatorio.")
            return False
        
        # Validazione per prodotti vincolati
        if vincolo == "Vincolato":
            if data_scadenza is None:
                st.error("La data di scadenza è obbligatoria per i prodotti vincolati.")
                return False
            
            if capitale_finale <= 0:
                st.error("L'importo a scadenza deve essere maggiore di zero per i prodotti vincolati.")
                return False
            
            # Ensure the date is in the future
            if data_scadenza <= datetime.date.today():
                st.error("La data di scadenza deve essere nel futuro.")
                return False
                
            # Verifica se il capitale finale è minore del capitale investito
            if vincolo == "Vincolato" and capitale_finale < capitale_investito:
                # Mostriamo un avviso e richiediamo conferma con checkbox
                st.write("") # Spazio vuoto
                st.warning(f"⚠️ Attenzione! Stai impostando un capitale a scadenza ({capitale_finale:.2f} €) più basso del capitale investito ({capitale_investito:.2f} €). Questo significa che questo prodotto genererà una perdita.")
                
                # Aggiungiamo una checkbox di conferma subito dopo l'avviso
                # Utilizziamo direttamente una chiave univoca senza gestire manualmente lo stato
                confirm_checkbox = st.checkbox(
                    "Confermo che questo prodotto comporterà una perdita e desidero salvarlo comunque", 
                    key="confirm_loss_checkbox"
                )
                
                # Se la checkbox non è spuntata, impedisci il salvataggio
                if not confirm_checkbox:
                    st.error("Per salvare un prodotto con perdita, devi confermare spuntando la casella sopra.")
                    return False
        
        # Create product data
        # Per i prodotti liquidi, forziamo il capitale finale uguale al capitale investito
        capitale_finale_effettivo = capitale_investito if vincolo == "Liquido" else capitale_finale
        
        new_product = {
            'nome': nome,
            'fornitore': fornitore,
            'tipologia': tipologia,
            'vincolo': vincolo,
            'capitale_investito': capitale_investito,
            'capitale_finale': capitale_finale_effettivo,  # Usiamo il valore aggiornato
            'data_scadenza': data_scadenza,
            'note': note,
            'data_aggiornamento': datetime.datetime.now().strftime("%Y-%m-%d")
        }
        
        if is_edit_mode and not is_duplicate_mode:
            # Solo se siamo in modalità modifica ma NON in modalità duplicazione
            # Update existing product
            new_product['id'] = edit_id
            new_product['data_inserimento'] = product_to_edit.get('data_inserimento', datetime.datetime.now().strftime("%Y-%m-%d"))
            
            # Find and update the row
            df_copy = df.copy()
            df_copy.loc[df_copy['id'] == edit_id] = pd.Series(new_product)
            
            success_message = "✅ Prodotto aggiornato con successo!"
        elif is_duplicate_mode:
            # Se siamo in modalità duplicazione, creiamo un nuovo prodotto
            # Add data_inserimento for duplicated products
            new_product['data_inserimento'] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Aggiungi un ID univoco per il nuovo prodotto
            new_product['id'] = generate_id()
            
            # Add to dataframe
            new_df = pd.DataFrame([new_product])
            df_copy = pd.concat([df, new_df], ignore_index=True) if not df.empty else new_df
            
            success_message = "✅ Prodotto duplicato con successo!"
        else:
            # Add data_inserimento for new products
            new_product['data_inserimento'] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Aggiungi un ID univoco per il nuovo prodotto
            new_product['id'] = generate_id()
            
            # Add to dataframe
            new_df = pd.DataFrame([new_product])
            df_copy = pd.concat([df, new_df], ignore_index=True) if not df.empty else new_df
            
            success_message = "✅ Nuovo prodotto aggiunto con successo!"
        
        # Save to database
        save_data(df_copy)
        
        # Reload the data from database to ensure we have all the products
        reloaded_df = load_data()
        
        # Non abbiamo più bisogno di resettare lo stato
        
        # Return True e il messaggio di successo
        return True, success_message
    
    if cancel_button:
        # Reload the page to refresh the data
        st.rerun()
        return True, ""
    
    return False, ""