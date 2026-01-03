import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import numpy as np

# --- Configuration & Scheme Parameters ---
# !!! IMPORTANT: Ensure this file path is correct for your system !!!
FILE_PATH = r'C:\Users\Rabiya\Desktop\BDA\household_power_consumption.txt'

# --- 1. Load, Clean, and Process Data ---
def load_and_process_data():
    """Loads, cleans, resamples to hourly, and engineers features."""
    try:
        # Load the raw data (it uses semicolon delimiter)
        data = pd.read_csv(FILE_PATH, sep=';', low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file '{FILE_PATH}' not found. Please download the Kaggle dataset and place it in your BDA folder.")
        raise

    # 1. Combine Date and Time into a single DateTime column
    data['DateTime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    # 2. Convert relevant columns to numeric (coercing '?' or non-numeric strings to NaN)
    cols_to_convert = ['Global_active_power', 'Global_reactive_power', 'Voltage', 'Global_intensity', 
                       'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']
    for col in cols_to_convert:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    # 3. Handle Missing Values (Drop rows with any NaN values for simplicity)
    data = data.dropna(subset=cols_to_convert + ['DateTime'])
    
    # Drop original string columns
    data = data.drop(columns=['Date', 'Time'])
    
    # 4. Resample to HOURLY Data (Crucial for performance and hourly trends)
    data = data.set_index('DateTime')
    
    # Use numeric_only=True to prevent issues with non-numeric columns
    hourly_data = data.resample('H').mean(numeric_only=True).reset_index()
    
    # --- Feature Engineering ---
    hourly_data['Energy_Consumption_kWh'] = hourly_data['Global_active_power'] * 1 
    hourly_data['Time_of_Day'] = hourly_data['DateTime'].dt.hour
    hourly_data['Month'] = hourly_data['DateTime'].dt.month
    
    # Has_AC_Numeric (Proxy for cooling/heating demand)
    hourly_data['Has_AC_Numeric'] = (hourly_data['Sub_metering_3'] > 0).astype(int)

    # Peak/Off-Peak Category
    hourly_data['Time_Category'] = hourly_data['Time_of_Day'].apply(
        lambda h: 'Peak Evening (17-21h)' if 17 <= h <= 21 else 
                  'Off-Peak Night (22-8h)' if h >= 22 or h <= 8 else 
                  'Mid-Day (9-16h)'
    )
    
    return hourly_data

# NOTE: The calculate_gruha_jyothi_eligibility function is removed as per your request.


# --- 2. Run Machine Learning Model ---
def train_prediction_model(data):
    """Trains the Linear Regression model using the hourly data."""
    
    # FIX: Drop all rows with any remaining NaNs, as required by LinearRegression
    data_clean = data.dropna()
    if data_clean.empty:
        print("🚨 ERROR: DataFrame is empty after cleaning. Cannot train model.")
        return None, 0.0, 0.0 
    
    # Features for the ML model
    X = data_clean[['Global_reactive_power', 'Voltage', 'Global_intensity', 'Sub_metering_3', 'Time_of_Day', 'Month']]
    y = data_clean['Energy_Consumption_kWh']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    return model, r2, mae

# data_analysis.py (REPLACE THE FINAL SECTION WITH THIS)

# --- Execute Analysis ---
data_df = load_and_process_data()
# The Gruha Jyothi eligibility function is commented out based on past context
# data_df = calculate_gruha_jyothi_eligibility(data_df)
prediction_model, model_r2, model_mae = train_prediction_model(data_df)

# IMPORTANT FIX: Ensure the DateTime column is the index for resample operations in the dashboard file.
data_df = data_df.set_index('DateTime') 


# --- Key Metrics for Frontend (UPDATED with Consumption Breakdown) ---

# 1. Total Consumption Metrics for Frontend Breakdown
# Calculate total usage for each Sub-meter (kWh)
total_sub1_kwh = (data_df['Sub_metering_1'].sum() / 1000).round(2)
total_sub2_kwh = (data_df['Sub_metering_2'].sum() / 1000).round(2)
total_sub3_kwh = (data_df['Sub_metering_3'].sum() / 1000).round(2)
total_all_subs = (total_sub1_kwh + total_sub2_kwh + total_sub3_kwh).round(2)

# Calculate Residual 
total_global_active_kwh = data_df['Energy_Consumption_kWh'].sum().round(2)
total_residual_kwh = (total_global_active_kwh - total_all_subs).round(2)

# Dictionary for the Pie Chart breakdown (This is the full data)
consumption_breakdown = {
    'Kitchen Appliances (Sub-meter 1)': total_sub1_kwh,
    'Refrigerator & Laundry (Sub-meter 2)': total_sub2_kwh,
    'Water Heater / AC (Sub-meter 3)': total_sub3_kwh,
    'General Use (Lights, Plugs, TV)': total_residual_kwh
}

# 2. Normalized Breakdown (EXCLUDING THE DOMINANT CATEGORY for visual clarity)
# This is the variable the dashboard_layout file is trying to import.
normalized_breakdown = {
    k: v 
    for k, v in consumption_breakdown.items() 
    if 'Kitchen Appliances' not in k 
}


# 3. Standard Metrics for Frontend
avg_hourly_usage = data_df['Energy_Consumption_kWh'].mean().round(3)
peak_hour = data_df.groupby('Time_of_Day')['Energy_Consumption_kWh'].mean(numeric_only=True).idxmax()
avg_sub_metering_usage = (data_df['Sub_metering_1'] + data_df['Sub_metering_2'] + data_df['Sub_metering_3']).mean().round(3)