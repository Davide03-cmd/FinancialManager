import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_capital_over_time(df):
    """
    Creates a line chart showing invested, liquid, bound and total capital over time
    
    Parameters:
    - df: DataFrame with time series data
    
    Returns:
    - Plotly figure object
    """
    if df.empty:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="Nessun dato disponibile",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Verifica che ci siano tutte le colonne necessarie
    required_columns = ['date', 'invested_capital', 'liquid_value', 'bound_value', 'total_value']
    if not all(col in df.columns for col in required_columns):
        # Se mancano colonne, aggiungiamo messaggio di errore
        fig = go.Figure()
        fig.add_annotation(
            text="Mancano dati per alcuni valori richiesti",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Create step-based graph showing capital evolution
    fig = go.Figure()
    
    # Add invested capital as a horizontal line (riferimento)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['invested_capital'],
        mode='lines',
        name='Capitale di Partenza',
        line=dict(color='royalblue', width=2)
    ))
    
    # Add liquid value with light green color - use steps
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['liquid_value'],
        mode='lines',
        name='Capitale Liquido',
        line=dict(color='lightgreen', width=2, shape='hv')  # 'hv' creates a step graph (horizontal-vertical)
    ))
    
    # Add bound value with orange color - use steps
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['bound_value'],
        mode='lines',
        name='Capitale Vincolato',
        line=dict(color='orange', width=2, shape='hv')
    ))
    
    # Add total value with dark green color - use steps
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['total_value'],
        mode='lines',
        name='Capitale Totale',
        line=dict(color='green', width=3, shape='hv')
    ))
    
    # Determiniamo il valore massimo nei dati per impostare l'asse Y correttamente
    max_value = max(
        df['invested_capital'].max(),
        df['liquid_value'].max(),
        df['bound_value'].max(),
        df['total_value'].max()
    )
    
    # Arrotondiamo il valore massimo al prossimo multiplo di 5000 o 10000 per un aspetto migliore
    # Questo garantisce che ci sia sempre spazio sopra il valore massimo
    if max_value < 50000:
        # Per valori più piccoli, arrotondiamo al prossimo 5000
        y_max = 5000 * (int(max_value / 5000) + 1)
    else:
        # Per valori più grandi, arrotondiamo al prossimo 10000
        y_max = 10000 * (int(max_value / 10000) + 1)
    
    # Update layout
    fig.update_layout(
        title="Andamento del Capitale nel Tempo",
        xaxis_title="Data",
        yaxis_title="Valore (€)",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # Impostiamo un range fisso per l'asse Y con un margine superiore
        yaxis=dict(
            range=[0, y_max],  # Da 0 al valore massimo arrotondato
            tickformat=",.0f",  # Formato con separatore di migliaia
            tickmode="auto",
            nticks=8  # Numero approssimativo di divisioni sull'asse Y
        )
    )
    
    # Formato asse X e configurazione per date future
    fig.update_xaxes(
        type="date",
        tickformat="%d/%m/%Y",
        tickangle=-45,
        # Disattiva il range slider per evitare problemi con date future
        rangeslider=dict(visible=False),
        # Assicuriamoci che l'asse X possa mostrare date fino al 2100
        range=[df['date'].min(), df['date'].max()],
        # Impostiamo un formato di tick più adatto a intervalli temporali lunghi
        tickmode="array",
        tickvals=pd.date_range(start=df['date'].min(), end=df['date'].max(), periods=10),
        # Aggiorniamo le proprietà dell'asse per garantire una visualizzazione corretta
        calendar="gregorian",
        dtick="M6"  # Tick ogni 6 mesi
    )
    
    return fig

def plot_product_distribution(df, value_column='capitale_investito', group_column='tipologia', title='Distribuzione per Tipologia'):
    """
    Creates a pie chart showing distribution of capital by product type or other grouping
    
    Parameters:
    - df: DataFrame containing financial products data
    - value_column: Column to use for values (capitale_investito or capitale_finale)
    - group_column: Column to use for grouping (tipologia, vincolo, etc.)
    - title: Chart title
    
    Returns:
    - Plotly figure object
    """
    if df.empty or group_column not in df.columns or value_column not in df.columns:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="Dati insufficienti per il grafico",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Group by the specified column and sum the values
    grouped_data = df.groupby(group_column)[value_column].sum().reset_index()
    
    # Create pie chart
    fig = px.pie(
        grouped_data, 
        values=value_column, 
        names=group_column, 
        title=title,
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    
    # Update layout
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        showlegend=False
    )
    
    return fig

def plot_maturity_timeline(df):
    """
    Creates a timeline showing when products will mature
    
    Parameters:
    - df: DataFrame containing financial products data
    
    Returns:
    - Plotly figure object
    """
    if df.empty or 'data_scadenza' not in df.columns:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="Nessun dato disponibile per la timeline",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Filter products with expiry date
    has_expiry = df[~pd.isna(df['data_scadenza'])].copy()
    
    if has_expiry.empty:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="Nessun prodotto con data di scadenza",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Convert expiry dates to datetime
    has_expiry['data_scadenza'] = pd.to_datetime(has_expiry['data_scadenza'])
    
    # Sort by expiry date
    has_expiry = has_expiry.sort_values('data_scadenza')
    
    # Create figure
    fig = go.Figure()
    
    # Add vertical lines for each product maturity
    for i, row in has_expiry.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['data_scadenza'], row['data_scadenza']],
            y=[0, row['capitale_finale']],
            mode='lines',
            name=row['nome'],
            line=dict(color='rgba(0, 150, 255, 0.5)', width=2),
            showlegend=False
        ))
        
        # Add markers for the product value
        fig.add_trace(go.Scatter(
            x=[row['data_scadenza']],
            y=[row['capitale_finale']],
            mode='markers+text',
            marker=dict(color='rgba(0, 150, 255, 0.8)', size=12),
            text=[row['nome']],
            textposition="top center",
            name=row['nome'],
            hovertemplate="%{y:,.2f}€<br>%{x|%d/%m/%Y}",
            showlegend=False
        ))
    
    # Add today marker
    today = pd.Timestamp.now()
    fig.add_trace(go.Scatter(
        x=[today, today],
        y=[0, has_expiry['capitale_finale'].max() * 1.1],
        mode='lines',
        name='Oggi',
        line=dict(color='red', width=2, dash='dash'),
        showlegend=False
    ))
    
    # Determiniamo il valore massimo per l'asse Y
    max_value = has_expiry['capitale_finale'].max()
    
    # Arrotondiamo il valore massimo al prossimo multiplo di 5000 o 10000 per un aspetto migliore
    if max_value < 50000:
        # Per valori più piccoli, arrotondiamo al prossimo 5000
        y_max = 5000 * (int(max_value / 5000) + 1)
    else:
        # Per valori più grandi, arrotondiamo al prossimo 10000
        y_max = 10000 * (int(max_value / 10000) + 1)
    
    # Update layout
    fig.update_layout(
        title="Timeline delle Scadenze",
        xaxis_title="Data",
        yaxis_title="Valore (€)",
        template="plotly_dark",
        hovermode="closest",
        # Impostiamo un range fisso per l'asse Y con un margine superiore
        yaxis=dict(
            range=[0, y_max],  # Da 0 al valore massimo arrotondato
            tickformat=",.0f",  # Formato con separatore di migliaia
            tickmode="auto",
            nticks=8  # Numero approssimativo di divisioni sull'asse Y
        )
    )
    
    # Format x-axis to show dates properly
    fig.update_xaxes(
        tickformat="%d/%m/%Y",
        tickangle=-45,
        # Disattiva il range slider per evitare problemi con date future
        rangeslider=dict(visible=False),
        # Assicuriamoci che l'asse X possa mostrare date fino al 2100
        range=[has_expiry['data_scadenza'].min(), has_expiry['data_scadenza'].max()],
        # Impostiamo un formato di tick più adatto a intervalli temporali lunghi
        tickmode="array", 
        tickvals=pd.date_range(start=has_expiry['data_scadenza'].min(), 
                              end=has_expiry['data_scadenza'].max(), 
                              periods=min(10, len(has_expiry))),
        # Aggiorniamo le proprietà dell'asse per garantire una visualizzazione corretta
        calendar="gregorian"
    )
    
    return fig