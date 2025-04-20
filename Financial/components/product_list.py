import streamlit as st
import pandas as pd
from utils.data_manager import delete_product, duplicate_product, load_data
from components.inline_edit_form import render_inline_edit_form
from components.update_liquid_form import render_update_liquid_form
from utils.formatting import format_currency, format_number, format_percentage

def render_product_list(df):
    """
    Renders a list of all financial products with options to edit or delete
    
    Parameters:
    - df: DataFrame containing financial products data
    """
    # Verifica se è attiva la modalità modifica in linea
    if 'inline_edit_mode' not in st.session_state:
        st.session_state.inline_edit_mode = False
        st.session_state.inline_edit_product_id = None
    st.header("📋 Listato Patrimonio")
    
    if df.empty or len(df) == 0:
        st.info("Nessun elemento di patrimonio trovato. Aggiungi un elemento dalla tab 'Aggiungi Patrimonio'.")
        return
    
    # Preparing the data for display
    # Make a copy of the dataframe to avoid modifying the original
    display_df = df.copy()
    
    # Rimuovi la colonna ID se presente
    if 'id' in display_df.columns:
        display_df = display_df.drop(columns=['id'])
    
    # Format numeric columns using Italian format
    if 'capitale_investito' in display_df.columns:
        display_df['capitale_investito'] = display_df['capitale_investito'].apply(format_currency)
    
    if 'capitale_finale' in display_df.columns:
        display_df['capitale_finale'] = display_df['capitale_finale'].apply(format_currency)
    
    # Format dates
    if 'data_scadenza' in display_df.columns:
        display_df['data_scadenza'] = pd.to_datetime(display_df['data_scadenza'], errors='coerce')
        display_df['data_scadenza'] = display_df['data_scadenza'].dt.strftime('%d/%m/%Y').replace('NaT', '-')
    
    if 'data_inserimento' in display_df.columns:
        display_df['data_inserimento'] = pd.to_datetime(display_df['data_inserimento'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    if 'data_aggiornamento' in display_df.columns:
        display_df['data_aggiornamento'] = pd.to_datetime(display_df['data_aggiornamento'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    # Rename columns for display
    display_df = display_df.rename(columns={
        'nome': 'Nome',
        'fornitore': 'Fornitore',
        'tipologia': 'Tipologia',
        'vincolo': 'Vincolo',
        'capitale_investito': 'Capitale Investito',
        'capitale_finale': 'Capitale Finale',
        'data_scadenza': 'Data Scadenza',
        'data_inserimento': 'Data Inserimento',
        'data_aggiornamento': 'Data Aggiornamento',
        'note': 'Note'
    })
    
    # Select and reorder columns for display
    display_columns = [
        'Nome', 'Fornitore', 'Tipologia', 'Vincolo', 
        'Capitale Investito', 'Capitale Finale', 'Data Scadenza',
        'Data Inserimento', 'Data Aggiornamento'
    ]
    
    # Keep only columns that actually exist in the dataframe
    display_columns = [col for col in display_columns if col in display_df.columns]
    
    # Search feature
    search_term = st.text_input(
        "🔍 Cerca per nome, fornitore o tipologia", 
        placeholder="Inizia a digitare per filtrare i prodotti..."
    )
    
    # Filter based on search term
    if search_term:
        search_mask = (
            display_df['Nome'].str.contains(search_term, case=False, na=False) |
            display_df['Fornitore'].str.contains(search_term, case=False, na=False) |
            display_df['Tipologia'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = display_df[search_mask]
    else:
        filtered_df = display_df
    
    if len(filtered_df) == 0:
        st.warning(f"Nessun prodotto trovato con la ricerca: '{search_term}'")
        return
    
    # Add action buttons with unique keys for each row
    # Store original index/id for actions
    id_mapping = {}
    for i, row in filtered_df.iterrows():
        if 'id' in df.columns:
            id_mapping[i] = df.loc[i, 'id'] if i in df.index else None
    
    # Creare una copia del DataFrame filtrando esplicitamente le colonne da visualizzare
    # e rimuovendo qualsiasi colonna ID che potrebbe essere visualizzata
    df_to_display = filtered_df[display_columns].copy()
    
    # Reimposta l'indice con numeri progressivi per non mostrare gli ID come indice
    df_to_display = df_to_display.reset_index(drop=True)
    
    # Rimuovi esplicitamente la colonna ID se presente
    if 'id' in df_to_display.columns:
        df_to_display = df_to_display.drop(columns=['id'])
    
    # Display the products in a table
    st.dataframe(
        df_to_display,
        use_container_width=True,
        column_config={
            'Nome': st.column_config.TextColumn("Nome", width="auto"),
            'Fornitore': st.column_config.TextColumn("Fornitore", width="auto"),
            'Tipologia': st.column_config.TextColumn("Tipologia", width="auto"),
            'Vincolo': st.column_config.TextColumn("Vincolo", width="auto"),
            'Capitale Investito': st.column_config.TextColumn("Capitale Investito", width="auto"),
            'Capitale Finale': st.column_config.TextColumn("Capitale Finale", width="auto"),
            'Data Scadenza': st.column_config.TextColumn("Data Scadenza", width="auto"),
            'Data Inserimento': st.column_config.TextColumn("Data Inserimento", width="auto"),
            'Data Aggiornamento': st.column_config.TextColumn("Data Aggiornamento", width="auto"),
        },
        height=400,
        hide_index=True,  # Nascondi completamente la colonna dell'indice
    )
    
    # Buttons for actions below the table
    st.subheader("Modifica Patrimonio")
    
    # Inizializza gli stati per le varie modalità se non esistono
    if 'update_liquid_mode' not in st.session_state:
        st.session_state.update_liquid_mode = False
        st.session_state.update_liquid_product_id = None
    
    # Se siamo in modalità aggiornamento prodotto liquido
    if st.session_state.update_liquid_mode and st.session_state.update_liquid_product_id is not None:
        st.divider()
        
        # Funzione per annullare l'aggiornamento
        def cancel_update_liquid():
            st.session_state.update_liquid_mode = False
            st.session_state.update_liquid_product_id = None
            st.rerun()
        
        # Mostra il form di aggiornamento e verifica se l'aggiornamento è avvenuto
        if render_update_liquid_form(df, st.session_state.update_liquid_product_id):
            # Ricarica i dati aggiornati
            updated_df = load_data()
            st.session_state.update_liquid_mode = False
            st.session_state.update_liquid_product_id = None
            st.session_state.show_success_message = True
            st.session_state.success_message = "✅ Valore aggiornato con successo!"
            st.session_state.active_tab = "list"  # Assicurati di restare nella tab "Lista Prodotti"
            st.rerun()
        
        # Pulsante per annullare
        if st.button("❌ Annulla e torna alla lista", key="cancel_update_liquid"):
            cancel_update_liquid()
            
        # Non mostrare le altre opzioni se siamo in modalità aggiornamento
        return
        
    # Se siamo in modalità modifica in linea, mostra il form di modifica
    if st.session_state.inline_edit_mode and st.session_state.inline_edit_product_id is not None:
        st.divider()
        # Cancellazione della modalità modifica in caso di successo o annullamento
        def cancel_edit():
            st.session_state.inline_edit_mode = False
            st.session_state.inline_edit_product_id = None
            st.rerun()
        
        # Aggiorna il DataFrame se necessario
        if render_inline_edit_form(df, st.session_state.inline_edit_product_id, cancel_edit):
            # Ricarica i dati aggiornati
            updated_df = load_data()
            st.session_state.inline_edit_mode = False
            st.session_state.inline_edit_product_id = None
            st.session_state.show_success_message = True
            st.session_state.success_message = "✅ Prodotto aggiornato con successo!"
            st.session_state.active_tab = "list"  # Assicurati di restare nella tab "Lista Prodotti"
            st.rerun()
        
        # Non mostrare le altre opzioni se siamo in modalità modifica
        return
    
    # Interfaccia semplificata con un unico selectbox e tre pulsanti
    # Selezione prodotto unica
    selected_product_idx = st.selectbox(
        "Seleziona un prodotto:",
        options=filtered_df.index,
        format_func=lambda x: filtered_df.loc[x, 'Nome'] + " - " + filtered_df.loc[x, 'Fornitore']
    )
    
    # Ottieni l'ID del prodotto selezionato
    product_id = None
    product_name = None
    if selected_product_idx is not None and selected_product_idx in id_mapping:
        product_id = id_mapping[selected_product_idx]
        product_name = filtered_df.loc[selected_product_idx, 'Nome']
    
    # Determina se il prodotto selezionato è liquido
    is_liquid_product = False
    if selected_product_idx is not None:
        vincolo = filtered_df.loc[selected_product_idx, 'Vincolo'] if 'Vincolo' in filtered_df.columns else ""
        is_liquid_product = (vincolo == 'Liquido')
    
    # Crea un layout con 2 o 3 colonne, a seconda se il prodotto è liquido
    if is_liquid_product:
        # Per prodotti liquidi, mostra 4 pulsanti
        col1, col2, col3, col4 = st.columns(4)
    else:
        # Per altri prodotti, mostra 3 pulsanti
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
    with col1:
        edit_button = st.button(
            "✏️ Modifica Patrimonio", 
            type="primary",
            use_container_width=True,
            key="edit_button"
        )
        
        if edit_button and product_id is not None:
            # Attiva la modalità modifica in linea
            st.session_state.inline_edit_mode = True
            st.session_state.inline_edit_product_id = product_id
            st.session_state.active_tab = "list"  # Assicurati di rimanere nella tab lista prodotti
            st.rerun()
    
    # Per prodotti liquidi, mostra il pulsante di aggiornamento valore
    if is_liquid_product:
        with col2:
            update_liquid_button = st.button(
                "💰 Aggiorna Valore", 
                type="primary",
                use_container_width=True,
                key="update_liquid_button"
            )
            
            if update_liquid_button and product_id is not None:
                # Attiva la modalità aggiornamento prodotto liquido
                st.session_state.update_liquid_mode = True
                st.session_state.update_liquid_product_id = product_id
                st.session_state.active_tab = "list"  # Assicurati di rimanere nella tab lista prodotti
                st.rerun()
        
        # Sposta gli altri pulsanti
        with col3:
            # Inizializza lo stato per il dialog di conferma se non esiste
            if 'show_delete_dialog' not in st.session_state:
                st.session_state.show_delete_dialog = False
                st.session_state.delete_product_id = None
                st.session_state.delete_product_name = None
            
            delete_button = st.button(
                "🗑️ Elimina", 
                type="secondary", 
                use_container_width=True,
                key="delete_button"
            )
            
            # Quando il pulsante viene premuto, mostra il dialog di conferma
            if delete_button and product_id is not None:
                st.session_state.show_delete_dialog = True
                st.session_state.delete_product_id = product_id
                st.session_state.delete_product_name = product_name
                st.rerun()  # Ricarica la pagina per mostrare il dialog
        
        with col4:
            duplicate_button = st.button(
                "🔄 Duplica", 
                type="secondary", 
                use_container_width=True,
                key="duplicate_button"
            )
            
            if duplicate_button and product_id is not None:
                # Anziché duplicare direttamente, imposta il prodotto da duplicare 
                # e passa alla schermata di inserimento/modifica
                st.session_state.duplicate_product = product_id
                st.session_state.active_tab = "add"  # Passa alla tab di inserimento prodotto
                st.rerun()
    else:
        # Per prodotti non liquidi, uso il layout standard a 3 colonne
        with col2:
            # Inizializza lo stato per il dialog di conferma se non esiste
            if 'show_delete_dialog' not in st.session_state:
                st.session_state.show_delete_dialog = False
                st.session_state.delete_product_id = None
                st.session_state.delete_product_name = None
            
            delete_button = st.button(
                "🗑️ Elimina Patrimonio", 
                type="secondary", 
                use_container_width=True,
                key="delete_button"
            )
            
            # Quando il pulsante viene premuto, mostra il dialog di conferma
            if delete_button and product_id is not None:
                st.session_state.show_delete_dialog = True
                st.session_state.delete_product_id = product_id
                st.session_state.delete_product_name = product_name
                st.rerun()  # Ricarica la pagina per mostrare il dialog
        
        with col3:
            duplicate_button = st.button(
                "🔄 Duplica Patrimonio", 
                type="secondary", 
                use_container_width=True,
                key="duplicate_button"
            )
            
            if duplicate_button and product_id is not None:
                # Anziché duplicare direttamente, imposta il prodotto da duplicare 
                # e passa alla schermata di inserimento/modifica
                st.session_state.duplicate_product = product_id
                st.session_state.active_tab = "add"  # Passa alla tab di inserimento prodotto
                st.rerun()
    
    # Se il dialog di conferma eliminazione è attivo, mostralo
    if st.session_state.show_delete_dialog:
        # Crea un container per il messaggio di conferma
        confirm_container = st.container()
        with confirm_container:
            st.warning(f"Sei sicuro di voler eliminare l'elemento di patrimonio '{st.session_state.delete_product_name}'?")
            
            # Pulsanti Sì e No affiancati
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Sì, elimina", key="confirm_delete_yes", use_container_width=True):
                    # Esegui l'eliminazione
                    if delete_product(st.session_state.delete_product_id):
                        st.session_state.show_success_message = True
                        st.session_state.success_message = f"✅ Patrimonio '{st.session_state.delete_product_name}' eliminato con successo!"
                        # Resetta il dialog
                        st.session_state.show_delete_dialog = False
                        st.session_state.delete_product_id = None
                        st.session_state.delete_product_name = None
                        st.session_state.active_tab = "list"
                        st.rerun()
                    else:
                        st.error(f"Errore durante l'eliminazione del prodotto")
            
            with col_no:
                if st.button("No, annulla", key="confirm_delete_no", use_container_width=True):
                    # Annulla e chiudi il dialog
                    st.session_state.show_delete_dialog = False
                    st.session_state.delete_product_id = None
                    st.session_state.delete_product_name = None
                    st.rerun()
    
    # Separatore
    st.divider()
    
    # Pulsante per aggiungere un nuovo elemento di patrimonio
    st.button(
        "➕ Aggiungi Nuovo Patrimonio", 
        on_click=lambda: setattr(st.session_state, 'active_tab', "add"),
        use_container_width=True
    )