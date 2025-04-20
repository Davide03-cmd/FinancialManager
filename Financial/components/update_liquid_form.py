import streamlit as st
import pandas as pd
from utils.data_manager import update_liquid_product, get_product_history
import plotly.express as px
from utils.formatting import format_currency, format_number, format_percentage


def render_update_liquid_form(df, product_id):
    """
    Renderizza un form per aggiornare il valore di un prodotto liquido
    
    Parameters:
    - df: DataFrame contenente i dati dei prodotti finanziari
    - product_id: ID del prodotto da aggiornare
    
    Returns:
    - Boolean: indica se un prodotto è stato aggiornato
    """
    if not product_id:
        st.error("Nessun prodotto selezionato.")
        return False

    # Trova il prodotto nel DataFrame
    product_info = None
    for idx, row in df.iterrows():
        if row['id'] == product_id:
            product_info = row
            break

    if product_info is None:
        st.error("Prodotto non trovato.")
        return False

    # Verifica che il prodotto sia di tipo liquido
    if product_info['vincolo'] != 'Liquido':
        st.error(
            "Solo i prodotti liquidi possono essere aggiornati con questo metodo."
        )
        st.info(
            "Per aggiornare prodotti vincolati, usa la funzionalità 'Modifica Patrimonio'."
        )
        return False

    # Titolo e descrizione
    st.subheader(f"Aggiorna valore: {product_info['nome']}")
    st.write(
        "Questa funzionalità permette di aggiornare il valore attuale di un prodotto liquido, mantenendo il capitale investito iniziale invariato e tracciando lo storico delle variazioni."
    )

    # Mostra i dettagli del prodotto
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Tipologia:** {product_info['tipologia']}")
    with col2:
        st.markdown(f"**Fornitore:** {product_info['fornitore']}")
    with col3:
        st.markdown(f"**Vincolo:** {product_info['vincolo']}")

    # Mostra valore attuale e capitale investito
    st.markdown("### Valori attuali")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Capitale Investito",
                  format_currency(product_info['capitale_investito']))
    with col2:
        st.metric("Capitale Attuale",
                  format_currency(product_info['capitale_finale']))

    # Utilizziamo il form per evitare salvataggi automatici non voluti
    st.markdown("### Inserisci nuovo valore")

    # Creazione di un ID unico per questo form
    form_key = f"update_liquid_form_{product_id}"

    # Inizializza il valore nel session state se non esiste
    if f"new_value_{product_id}" not in st.session_state:
        st.session_state[f"new_value_{product_id}"] = float(
            product_info['capitale_finale'])

    # Inizializza i valori di sessione se non esistono
    if 'update_day' not in st.session_state:
        st.session_state.update_day = pd.Timestamp.now().day
    if 'update_month' not in st.session_state:
        st.session_state.update_month = pd.Timestamp.now().month
    if 'update_year' not in st.session_state:
        st.session_state.update_year = pd.Timestamp.now().year

    today = pd.Timestamp.now().date()

    # Data di inserimento del prodotto
    min_date = None
    if 'data_inserimento' in product_info:
        min_date = pd.to_datetime(product_info['data_inserimento']).date()
    else:
        # Se non c'è data di inserimento, imposta un limite molto indietro nel tempo
        min_date = pd.Timestamp(year=2000, month=1, day=1).date()

    # Ottieni gli anni possibili (dal minimo al massimo)
    years = list(range(min_date.year, today.year + 1))

    # Prepara i componenti per la data di aggiornamento fuori dal form
    st.markdown("#### Data di aggiornamento")

    # Fornisci un selettore a 3 campi separati per la data
    col1, col2, col3 = st.columns(3)

    with col1:
        # Selettore per il giorno (1-31)
        day_index = st.session_state.update_day - 1
        day = st.selectbox("Giorno",
                           options=list(range(1, 32)),
                           index=day_index,
                           key=f"day_selector_{product_id}_outside")
        st.session_state.update_day = day

    with col2:
        # Usa i nomi dei mesi per maggiore chiarezza
        month_names = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        month_index = st.session_state.update_month - 1
        month_idx = st.selectbox("Mese",
                                 options=range(len(month_names)),
                                 format_func=lambda x: month_names[x],
                                 index=month_index,
                                 key=f"month_selector_{product_id}_outside")
        month = month_idx + 1  # Converti da indice (0-11) a mese (1-12)
        st.session_state.update_month = month

    with col3:
        # Selettore per l'anno
        year_index = years.index(
            st.session_state.update_year
        ) if st.session_state.update_year in years else 0
        year = st.selectbox("Anno",
                            options=years,
                            index=year_index,
                            key=f"year_selector_{product_id}_outside")
        st.session_state.update_year = year

    # Controllo per data valida e preparazione
    update_date = None
    try:
        selected_date = pd.Timestamp(year=int(year),
                                     month=int(month),
                                     day=int(day)).date()

        # Verifica che la data sia nel range consentito
        if min_date and selected_date < min_date:
            st.warning(
                f"La data selezionata è precedente alla data di inserimento del prodotto ({min_date.strftime('%d/%m/%Y')}). Verrà utilizzata la data di inserimento."
            )
            selected_date = min_date
        elif selected_date > today:
            st.warning(
                f"La data selezionata è nel futuro. Verrà utilizzata la data odierna ({today.strftime('%d/%m/%Y')})."
            )
            selected_date = today

        # Converti la data nel formato corretto per SQL (YYYY-MM-DD)
        update_date = selected_date.strftime("%Y-%m-%d")

        # Informazione sulla data selezionata
        st.info(
            f"L'aggiornamento sarà registrato con data: {selected_date.strftime('%d/%m/%Y')}"
        )

    except ValueError:
        st.error(
            "Data non valida. Controlla che la combinazione di giorno, mese e anno sia corretta."
        )
        # Imposta su None per indicare che la data non è valida
        update_date = None

    # Ora inizia il form per l'inserimento del nuovo valore
    with st.form(key=form_key):
        # In un form, non è possibile usare on_change, quindi dobbiamo usare direttamente il valore dalla session_state
        new_value = st.number_input(
            "Nuovo valore (€)",
            min_value=0.0,
            max_value=1000000000.0,  # 1 miliardo
            value=float(product_info['capitale_finale']),
            step=100.0,
            format="%.2f",
            key=f"new_value_input_{product_id}"  # Chiave unica per questo input
        )

        notes = st.text_area(
            "Note (opzionale)",
            placeholder=
            "Inserisci eventuali note sull'aggiornamento, ad es. 'Aggiornamento mensile' o 'Versamento extra'",
            max_chars=500,
            key=f"notes_{product_id}")

        # Calcola la variazione
        change = new_value - float(product_info['capitale_finale'])
        change_percent = (
            change / float(product_info['capitale_finale'])) * 100 if float(
                product_info['capitale_finale']) > 0 else 0

        # Mostra la variazione con colore appropriato
        if change != 0:
            col1, col2 = st.columns(2)
            with col1:
                if change > 0:
                    st.success(
                        f"Variazione: +{format_currency(change)} (+{format_percentage(change_percent)})"
                    )
                else:
                    st.error(
                        f"Variazione: {format_currency(change)} ({format_percentage(change_percent)})"
                    )

        submit = st.form_submit_button("Aggiorna Valore", type="primary")

        if submit:
            # Aggiorna il prodotto
            success, message = update_liquid_product(product_id, new_value,
                                                     notes, update_date)

            if success:
                st.success(message)
                # Aggiornamento riuscito, restituisci True
                return True
            else:
                st.error(message)

    # Mostra lo storico degli aggiornamenti se esistente
    st.markdown("### Storico aggiornamenti")
    history_df = get_product_history(product_id)

    if history_df.empty:
        st.info("Nessun aggiornamento registrato finora.")
    else:
        # Formatta le colonne numeriche e di data
        history_display = history_df.copy()
        history_display['data_aggiornamento'] = pd.to_datetime(
            history_display['data_aggiornamento']).dt.strftime('%d/%m/%Y')
        history_display['capitale_precedente'] = history_display[
            'capitale_precedente'].apply(format_currency)
        history_display['capitale_nuovo'] = history_display[
            'capitale_nuovo'].apply(format_currency)

        # Rinomina le colonne per la visualizzazione
        history_display = history_display.rename(
            columns={
                'data_aggiornamento': 'Data',
                'capitale_precedente': 'Valore Precedente',
                'capitale_nuovo': 'Nuovo Valore',
                'note': 'Note'
            })

        # Rimuovi la colonna ID
        if 'id' in history_display.columns:
            history_display = history_display.drop(columns=['id'])

        # Mostra la tabella
        st.dataframe(history_display,
                     use_container_width=True,
                     hide_index=True)

        # Crea anche un grafico dello storico valori se ci sono più di un aggiornamento
        if len(history_df) > 0:
            # Prepariamo i dati per il grafico
            # Aggiungiamo il valore iniziale (capitale investito)
            chart_data = []

            # Prima riga: valore iniziale
            chart_data.append({
                'data':
                pd.to_datetime(product_info['data_inserimento']),
                'valore':
                float(product_info['capitale_investito']),
                'tipo':
                'Capitale Investito'
            })

            # Aggiungiamo tutti gli aggiornamenti
            for _, row in history_df.iterrows():
                chart_data.append({
                    'data':
                    pd.to_datetime(row['data_aggiornamento']),
                    'valore':
                    float(row['capitale_nuovo']),
                    'tipo':
                    'Valore Aggiornato'
                })

            # Converti in DataFrame
            chart_df = pd.DataFrame(chart_data)

            # Crea il grafico
            fig = px.line(chart_df,
                          x='data',
                          y='valore',
                          color='tipo',
                          title='Andamento del valore nel tempo',
                          labels={
                              'data': 'Data',
                              'valore': 'Valore (€)'
                          },
                          color_discrete_map={
                              'Capitale Investito': '#2962FF',
                              'Valore Aggiornato': '#00C853'
                          })

            # Aggiunge i punti
            fig.update_traces(mode='lines+markers')

            # Formattazione asse Y con formato italiano (punto per migliaia, virgola per decimali)
            fig.update_layout(
                yaxis=dict(
                    # Formato italiano: punto per separare migliaia, virgola per decimali
                    tickformat=",. ",
                    hoverformat=",. ",
                    title="Valore (€)"),
                xaxis=dict(title="Data", tickformat="%d/%m/%Y"),
                legend=dict(orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1))

            # Mostra il grafico
            st.plotly_chart(fig, use_container_width=True)

    # Se arriviamo qui, nessun aggiornamento è stato effettuato
    return False
