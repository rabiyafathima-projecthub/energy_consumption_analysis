import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Import functions and data from data_analysis.py
from dashboard_layout import create_layout
from data_analysis import data_df, prediction_model, model_r2, avg_hourly_usage, peak_hour

# --- App Initialization ---
# FIX: Updated browser tab title
app = dash.Dash(__name__, title="Energy Consumption Analysis System")
server = app.server

# --- App Layout ---
app.layout = create_layout()

# --- Callbacks ---

# 1. Prediction Callback (For Sidebar)
@app.callback(
    Output('prediction-output', 'children'),
    [Input('voltage-input', 'value')]
)
def update_prediction(voltage):
    if voltage is None or voltage <= 0 or prediction_model is None:
        return "N/A"
    
    # Create a dummy DataFrame with mean values for features, replacing Voltage with user input
    # The columns must match the features used during training: 
    # ['Global_reactive_power', 'Voltage', 'Global_intensity', 'Sub_metering_3', 'Time_of_Day', 'Month']
    
    # Use mean values from the data for all features except Voltage
    dummy_data = data_df[['Global_reactive_power', 'Global_intensity', 'Sub_metering_3', 'Time_of_Day', 'Month']].mean().to_frame().T
    
    # Insert the user's Voltage input
    dummy_data['Voltage'] = voltage
    
    # Reorder columns to match the model's training order
    X_predict = dummy_data[['Global_reactive_power', 'Voltage', 'Global_intensity', 'Sub_metering_3', 'Time_of_Day', 'Month']]
    
    try:
        prediction = prediction_model.predict(X_predict)[0]
        return f"{prediction:.3f} kW"
    except Exception as e:
        return f"Error: {e}"


# 2. Interactive Filtering Callback (For Charts)
@app.callback(
    [Output('time-series-graph', 'figure'),
     Output('sub-meter-breakdown-graph', 'figure'),
     Output('hourly-trend-graph', 'figure')],
    [Input('time-category-dropdown', 'value')]
)
def update_graphs_by_time_category(selected_category):
    filtered_df = data_df.copy()
    
    # Filter the main DataFrame based on the selected Time Category
    if selected_category != 'ALL':
        filtered_df = filtered_df[filtered_df['Time_Category'] == selected_category]
        
    # Recalculate Time Series Graph
    ts_data = filtered_df.resample('D')['Energy_Consumption_kWh'].mean(numeric_only=True).reset_index()
    fig_time = px.line(
        ts_data, x='DateTime', y='Energy_Consumption_kWh',
        title=f'1. Energy Consumption Trend Over Time (Daily Mean) - Category: {selected_category}',
        labels={'Energy_Consumption_kWh': 'Energy (kW)'},
        template='plotly_dark'
    )
    
    # Recalculate Sub-meter Stacked Bar Chart
    sub_metering_data = filtered_df[['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']].resample('D').sum(numeric_only=True).reset_index()
    sub_metering_data = sub_metering_data.melt(id_vars=['DateTime'], var_name='Sub_Meter', value_name='Consumption_Wh')
    
    fig_submeters = px.bar(
        sub_metering_data.sample(n=min(len(sub_metering_data), 1000), random_state=42),
        x='DateTime', 
        y='Consumption_Wh', 
        color='Sub_Meter',
        title=f'3. Daily Consumption Breakdown by Metering Sub-System - Category: {selected_category}',
        template='plotly_dark',
        labels={'Consumption_Wh': 'Consumption (Wh)', 'Sub_Meter': 'Sub-Meter'},
        color_discrete_map={'Sub_metering_1': '#00FFFF', 'Sub_metering_2': '#FFA07A', 'Sub_metering_3': '#90EE90'}
    )
    
    # Recalculate Hourly Trend Graph
    hourly_mean_data = filtered_df.groupby(filtered_df.index.hour)['Energy_Consumption_kWh'].mean(numeric_only=True).reset_index().rename(columns={'DateTime': 'Time_of_Day'})
    fig_hourly = px.bar(
        hourly_mean_data, 
        x='Time_of_Day', y='Energy_Consumption_kWh',
        title=f'2. Average Consumption by Hour - Category: {selected_category}',
        template='plotly_dark',
        color='Energy_Consumption_kWh',
        color_continuous_scale=px.colors.sequential.Inferno,
        labels={'Time_of_Day': 'Hour of Day (0-23)', 'Energy_Consumption_kWh': 'Avg. Energy (kW)'}
    )
    
    return fig_time, fig_submeters, fig_hourly

# app.py (Corrected Run App section)

# --- Run App ---
if __name__ == '__main__':
    # Ensure dash-table is installed: pip install dash-table
    app.run(debug=True) # <-- FIX APPLIED: Changed to app.run