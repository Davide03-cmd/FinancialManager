import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from utils.plotting import plot_product_distribution, plot_maturity_timeline, plot_capital_over_time
from utils.financial import calculate_total_values, calculate_current_values, calculate_future_values, project_values_over_time
import datetime as dt  # Importiamo esplicitamente il modulo datetime per l'uso diretto

def render_dashboard(df):
    """
    Renders the main dashboard with financial overview and charts
    
    Parameters:
    - df: DataFrame containing financial products data
    """
    
    if df.empty:
        st.info("Nessun prodotto finanziario registrato. Utilizza la tab 'Aggiungi Prodotto' per iniziare.")
        return
    
    st.header("📊 Dashboard Finanziaria")
    
    # Assicura che le colonne esistano
    if 'capitale_investito' not in df.columns or 'capitale_finale' not in df.columns:
        st.error("Dati mancanti o in formato non corretto.")
        return
    
    # Assicura che la colonna vincolo esista
    if 'vincolo' not in df.columns:
        df['vincolo'] = 'Liquidità'
    
    # Calcola i valori attuali
    current_values = calculate_current_values(df)
    
    # Primo indicatore: VALUE NOW
    st.subheader("VALUE NOW - Valore Attuale")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<h5>Capitale Totale</h5>", unsafe_allow_html=True)
        st.markdown(f"<h2>{current_values['total_value']:,.2f} €</h2>", unsafe_allow_html=True)
    
    with col2:
        liquid_percent = f"{current_values['liquid_value']/current_values['total_value']*100:.1f}%" if current_values['total_value'] > 0 else "0.0%"
        st.markdown(f"<h5>Liquidità <span style='color:#1E90FF;'>{liquid_percent}</span></h5>", unsafe_allow_html=True)
        st.markdown(f"<h2>{current_values['liquid_value']:,.2f} €</h2>", unsafe_allow_html=True)
    
    with col3:
        bound_percent = f"{current_values['bound_value']/current_values['total_value']*100:.1f}%" if current_values['total_value'] > 0 else "0.0%"
        st.markdown(f"<h5>Vincolato <span style='color:#1E90FF;'>{bound_percent}</span></h5>", unsafe_allow_html=True)
        st.markdown(f"<h2>{current_values['bound_value']:,.2f} €</h2>", unsafe_allow_html=True)
    
    # Secondo indicatore: VALUE FUTURE
    st.subheader("VALUE FUTURE - Valore Prospettico")
    
    # Prepariamo la data di oggi
    today = pd.Timestamp.now()
    
    # Default a 1 anno nel futuro
    default_future_date = today + pd.DateOffset(years=1)
    default_future_date = default_future_date.replace(day=1)  # Primo giorno del mese
    
    # Implementiamo un selettore di data personalizzato senza limiti di anno
    st.write("Data di riferimento")
    
    # Prepariamo i valori di default
    default_year = default_future_date.year
    default_month = default_future_date.month
    default_day = default_future_date.day
    
    # Creiamo tre colonne per anno, mese e giorno
    col_y, col_m, col_d = st.columns(3)
    
    with col_y:
        # Selezione anno con un range molto ampio
        year = st.number_input(
            "Anno",
            min_value=today.year,
            max_value=2100,  # Andiamo ben oltre il 2036
            value=default_year,
            step=1,
            key="future_year"
        )
    
    with col_m:
        # Selezione mese
        month = st.number_input(
            "Mese",
            min_value=1,
            max_value=12,
            value=default_month,
            step=1,
            key="future_month"
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
            value=min(default_day, max_days),  # Assicuriamoci che il valore sia valido
            step=1,
            key="future_day"
        )
    
    # Creiamo l'oggetto datetime a partire dai valori selezionati
    try:
        selected_date = datetime.datetime(year, month, day)
        future_date = pd.Timestamp(selected_date)
    except ValueError:
        # In caso di combinazione non valida, usiamo l'ultimo giorno valido del mese
        if month == 2 and day > 28:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                future_date = pd.Timestamp(datetime.datetime(year, month, 29))
            else:
                future_date = pd.Timestamp(datetime.datetime(year, month, 28))
        else:
            # Usa l'ultimo giorno del mese
            if month in [4, 6, 9, 11] and day > 30:
                future_date = pd.Timestamp(datetime.datetime(year, month, 30))
            else:
                # Questo non dovrebbe mai accadere con i controlli sopra
                future_date = pd.Timestamp(datetime.datetime(year, month, 1))
    
    # Verifico che la data sia nel futuro
    if future_date <= today:
        st.warning("La data selezionata deve essere nel futuro. Usiamo la data di domani come riferimento.")
        future_date = today + pd.DateOffset(days=1)
    
    # Mostra il messaggio informativo sotto il selettore di data
    st.info(f"Mostra la situazione al {future_date.strftime('%d/%m/%Y')}")
    
    # Calcola valori futuri
    future_values = calculate_future_values(df, future_date)
    
    # Mostra valori futuri
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"<h5>Valore Totale al {future_date.strftime('%d/%m/%Y')}</h5>", unsafe_allow_html=True)
        st.markdown(f"<h2>{future_values['total_value']:,.2f} €</h2>", unsafe_allow_html=True)
    
    with col2:
        liquid_percent = f"{future_values['liquid_value']/future_values['total_value']*100:.1f}%" if future_values['total_value'] > 0 else "0.0%"
        st.markdown(f"<h5>Liquidità <span style='color:#1E90FF;'>{liquid_percent}</span></h5>", unsafe_allow_html=True)
        st.markdown(f"<h2>{future_values['liquid_value']:,.2f} €</h2>", unsafe_allow_html=True)
    
    with col3:
        bound_percent = f"{future_values['bound_value']/future_values['total_value']*100:.1f}%" if future_values['total_value'] > 0 else "0.0%"
        st.markdown(f"<h5>Vincolato <span style='color:#1E90FF;'>{bound_percent}</span></h5>", unsafe_allow_html=True)
        st.markdown(f"<h2>{future_values['bound_value']:,.2f} €</h2>", unsafe_allow_html=True)
    
    # Distribuzione per tipologia
    st.subheader("Distribuzione per Tipologia")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution by invested capital
        fig_distribution_invested = plot_product_distribution(
            df, 
            value_column='capitale_investito', 
            title='Capitale per Tipologia'
        )
        st.plotly_chart(fig_distribution_invested, use_container_width=True)
    
    with col2:
        # Distribution by vincolo
        if 'vincolo' in df.columns:
            fig_vincolo = plot_product_distribution(
                df, 
                group_column='vincolo',
                value_column='capitale_finale', 
                title='Distribuzione per Vincolo'
            )
            st.plotly_chart(fig_vincolo, use_container_width=True)
    
    # Proiezione nel tempo
    st.subheader("Proiezione nel Tempo")
    
    # Time horizon selector
    col1, col2 = st.columns([1, 3])
    with col1:
        # Usiamo valori in anni per semplificare la selezione di periodi lunghi
        years_horizon = st.slider(
            "Orizzonte temporale (anni)", 
            min_value=0, 
            max_value=75,  # Fino al 2100 circa
            value=5, 
            step=1
        )
        
        # Convertiamo gli anni in mesi per il calcolo della proiezione
        months_horizon = years_horizon * 12
    
    # Generate projection
    projection_df = project_values_over_time(df, months_horizon)
    
    # Plot projection con il nuovo grafico che mostra capitale liquido, vincolato e totale
    fig_projection = plot_capital_over_time(projection_df)
    st.plotly_chart(fig_projection, use_container_width=True)
    
    # Aggiungiamo una descrizione per spiegare il nuovo grafico
    st.info(f"Il grafico mostra l'evoluzione nel tempo su un orizzonte di {years_horizon} anni ({months_horizon} mesi). Sono visualizzati il capitale liquido (verde chiaro), il capitale vincolato (arancione) e il capitale totale (verde scuro), mantenendo sempre visibile la linea del capitale iniziale (blu) come riferimento.")
    
    # Show maturity timeline for products with expiry date
    has_expiry_products = not df[~pd.isna(df['data_scadenza'])].empty if 'data_scadenza' in df.columns else False
    if has_expiry_products:
        st.subheader("Timeline delle Scadenze")
        fig_timeline = plot_maturity_timeline(df)
        st.plotly_chart(fig_timeline, use_container_width=True)