import pandas as pd
import numpy as np
import datetime

def calculate_total_values(df):
    """
    Calculates the total invested capital and current value
    
    Parameters:
    - df: DataFrame containing financial products data
    
    Returns:
    - dict: containing total invested capital and current value
    """
    # Ensure columns exist
    if df.empty or 'capitale_investito' not in df.columns or 'capitale_finale' not in df.columns:
        return {
            'total_invested': 0,
            'total_current': 0
        }
    
    # Convert numeric columns to float for calculations
    df['capitale_investito'] = df['capitale_investito'].astype(float)
    df['capitale_finale'] = df['capitale_finale'].astype(float)
    
    total_invested = df['capitale_investito'].sum()
    total_current = df['capitale_finale'].sum()
    
    return {
        'total_invested': total_invested,
        'total_current': total_current
    }

def calculate_current_values(df):
    """
    Calculates current values by separating liquid and bound products
    
    Parameters:
    - df: DataFrame containing financial products data
    
    Returns:
    - dict: containing liquid_value, bound_value, and total_value
    """
    # Default values
    liquid_value = 0
    bound_value = 0
    total_value = 0
    
    # If DataFrame is empty, return default values
    if df.empty:
        return {
            'liquid_value': liquid_value,
            'bound_value': bound_value,
            'total_value': total_value
        }
    
    # Ensure required columns exist
    required_columns = ['capitale_investito', 'capitale_finale', 'vincolo', 'data_scadenza']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None if col == 'data_scadenza' else 'Liquidità' if col == 'vincolo' else 0.0
    
    # Convert numeric columns to float
    df['capitale_investito'] = df['capitale_investito'].astype(float)
    df['capitale_finale'] = df['capitale_finale'].astype(float)
    
    # Convert dates to datetime for comparison
    df['data_scadenza'] = pd.to_datetime(df['data_scadenza'], errors='coerce')
    today = pd.Timestamp.now().floor('D')
    
    # Separate liquid and bound products
    liquid_products = df[(df['vincolo'] == 'Liquido') | 
                         (pd.isna(df['data_scadenza'])) | 
                         (df['data_scadenza'] <= today)]
    
    bound_products = df[(df['vincolo'] == 'Vincolato') & 
                        (~pd.isna(df['data_scadenza'])) & 
                        (df['data_scadenza'] > today)]
    
    # Calculate values - for liquid products use capitale_finale
    liquid_value = liquid_products['capitale_finale'].sum()
    
    # Per i prodotti vincolati, usa il capitale_investito (non il capitale a scadenza)
    bound_value = bound_products['capitale_investito'].sum()
    
    total_value = liquid_value + bound_value
    
    return {
        'liquid_value': liquid_value,
        'bound_value': bound_value,
        'total_value': total_value
    }

def calculate_future_values(df, future_date):
    """
    Calculates values at a future date by adjusting which products are liquid
    
    Parameters:
    - df: DataFrame containing financial products data
    - future_date: Date to project values to
    
    Returns:
    - dict: containing liquid_value, bound_value, and total_value
    """
    # Default values
    liquid_value = 0
    bound_value = 0
    total_value = 0
    
    # If DataFrame is empty, return default values
    if df.empty:
        return {
            'liquid_value': liquid_value,
            'bound_value': bound_value,
            'total_value': total_value
        }
    
    # Ensure required columns exist
    required_columns = ['capitale_investito', 'capitale_finale', 'vincolo', 'data_scadenza']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None if col == 'data_scadenza' else 'Liquidità' if col == 'vincolo' else 0.0
    
    # Convert numeric columns to float
    df['capitale_investito'] = df['capitale_investito'].astype(float)
    df['capitale_finale'] = df['capitale_finale'].astype(float)
    
    # Convert dates to datetime for comparison
    df['data_scadenza'] = pd.to_datetime(df['data_scadenza'], errors='coerce')
    future_ts = pd.Timestamp(future_date)
    
    # Create a copy of dataframe for calculations
    future_df = df.copy()
    
    # At the future date:
    # 1. Products that mature before that date become liquid
    # 2. For bound products that haven't matured yet, use capitale_investito not capitale_finale
    
    # Prodotti già liquidi o che saranno liquidi alla data futura
    liquid_products = future_df[(future_df['vincolo'] == 'Liquido') | 
                               (pd.isna(future_df['data_scadenza'])) | 
                               (future_df['data_scadenza'] <= future_ts)]
    
    # Prodotti che rimarranno vincolati alla data futura
    bound_products = future_df[(future_df['vincolo'] == 'Vincolato') & 
                              (~pd.isna(future_df['data_scadenza'])) & 
                              (future_df['data_scadenza'] > future_ts)]
    
    # Calcola il valore liquido (capitale finale per prodotti maturati)
    liquid_value = liquid_products['capitale_finale'].sum()
    
    # Calcola il valore vincolato (capitale INVESTITO per prodotti non ancora maturati)
    bound_value = bound_products['capitale_investito'].sum()
    
    total_value = liquid_value + bound_value
    
    return {
        'liquid_value': liquid_value,
        'bound_value': bound_value,
        'total_value': total_value
    }

def project_values_over_time(df, months_horizon):
    """
    Projects the values of financial products over time, properly handling
    restricted products becoming liquid upon maturity
    
    Parameters:
    - df: DataFrame containing financial products data
    - months_horizon: Number of months to project
    
    Returns:
    - DataFrame: containing dates and projected values (invested_capital, liquid_value, bound_value, total_value)
    """
    if df.empty:
        # Return empty dataframe with expected columns
        return pd.DataFrame(columns=['date', 'invested_capital', 'liquid_value', 'bound_value', 'total_value'])
    
    # Se l'orizzonte è 0, restituiamo solo la data attuale
    if months_horizon == 0:
        start_date = pd.Timestamp.now()
        # Calculate start values
        total_values = calculate_total_values(df)
        initial_invested = total_values['total_invested']
        
        # Calcola valori attuali
        current_values = calculate_current_values(df)
        
        return pd.DataFrame([{
            'date': start_date,
            'invested_capital': initial_invested,
            'liquid_value': current_values['liquid_value'],
            'bound_value': current_values['bound_value'],
            'total_value': current_values['total_value']
        }])
    
    # Calculate start values
    total_values = calculate_total_values(df)
    initial_invested = total_values['total_invested']
    
    # Create date range for projection
    start_date = pd.Timestamp.now()
    
    # Per orizzonte temporale molto lungo (>10 anni), aumentiamo l'intervallo di campionamento
    # in modo da non avere troppe date e rendere il grafico troppo pesante
    if months_horizon > 120:  # Più di 10 anni
        # Per periodi lunghi, campiona ogni 3 mesi fino a 10 anni, poi ogni 6 mesi
        sampling_dates1 = [start_date + pd.DateOffset(months=m) for m in range(0, min(121, months_horizon + 1), 3)]
        sampling_dates2 = [start_date + pd.DateOffset(months=m) for m in range(120, months_horizon + 1, 6)]
        primary_dates = sampling_dates1 + [d for d in sampling_dates2 if d > sampling_dates1[-1]]
    else:
        # Per periodi più brevi, campiona mensilmente
        primary_dates = [start_date + pd.DateOffset(months=m) for m in range(months_horizon + 1)]
    
    # Aggiungiamo le date di scadenza come punti chiave per la proiezione
    # per mostrare chiaramente i cambiamenti quando i vincolati diventano liquidi
    extra_dates = []
    
    if 'data_scadenza' in df.columns:
        # Prendi tutte le date di scadenza future
        expiry_dates = df[~pd.isna(df['data_scadenza'])]
        if not expiry_dates.empty:
            expiry_dates['data_scadenza'] = pd.to_datetime(expiry_dates['data_scadenza'], errors='coerce')
            
            # Filtriamo le date non-null e future nel range di tempo considerato
            future_expiry = expiry_dates[
                (expiry_dates['data_scadenza'] > start_date) & 
                (expiry_dates['data_scadenza'] <= start_date + pd.DateOffset(months=months_horizon))
            ]
            
            if not future_expiry.empty:
                # Per ogni data di scadenza, aggiungiamo un punto appena prima e uno appena dopo
                for exp_date in future_expiry['data_scadenza'].unique():
                    # Un giorno prima della scadenza
                    extra_dates.append(exp_date - pd.Timedelta(days=1))
                    # Giorno esatto della scadenza
                    extra_dates.append(exp_date)
                    # Un giorno dopo la scadenza
                    extra_dates.append(exp_date + pd.Timedelta(days=1))
    
    # Combiniamo le date primarie con quelle delle scadenze
    all_dates = sorted(list(set(primary_dates + extra_dates)))
    
    # Ensure we have all necessary columns
    required_columns = ['capitale_investito', 'capitale_finale', 'vincolo', 'data_scadenza']
    for col in required_columns:
        if col not in df.columns:
            if col == 'data_scadenza':
                df[col] = None
            elif col == 'vincolo':
                df[col] = 'Liquidità'
            else:
                df[col] = 0.0
    
    # Create a deep copy to avoid modifying the original dataframe
    projection_df = df.copy()
    
    # Convert dates to datetime for comparison
    projection_df['data_scadenza'] = pd.to_datetime(projection_df['data_scadenza'], errors='coerce')
    
    # Make sure numeric columns are float
    projection_df['capitale_investito'] = projection_df['capitale_investito'].astype(float)
    projection_df['capitale_finale'] = projection_df['capitale_finale'].astype(float)
    
    # Create projection dataframe
    projection_data = []
    
    for date in all_dates:
        # For each future date, calculate the actual value by considering
        # which products have matured by that date
        
        # Invested capital stays constant
        invested_capital = initial_invested
        
        # Calculate value at this date by determining which products have matured
        future_values = calculate_future_values(projection_df, date)
        liquid_value = future_values['liquid_value']
        bound_value = future_values['bound_value']
        total_value = future_values['total_value']
        
        # Add a row for this date
        projection_data.append({
            'date': date,
            'invested_capital': invested_capital,
            'liquid_value': liquid_value,
            'bound_value': bound_value,
            'total_value': total_value
        })
    
    # Sort by date to ensure proper order
    result_df = pd.DataFrame(projection_data)
    result_df = result_df.sort_values('date').reset_index(drop=True)
    
    return result_df