from dash import dcc, html
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go # <-- Ensure this is imported
from data_analysis import data_df, model_r2, avg_hourly_usage, peak_hour, avg_sub_metering_usage, consumption_breakdown, normalized_breakdown 
# Ensure normalized_breakdown is imported

# --- 1. Create Plotly Figures ---

# Dynamic: Consumption Over Time 
ts_data_daily = data_df.resample('D')['Energy_Consumption_kWh'].mean(numeric_only=True).reset_index()
fig_time = px.line(
    ts_data_daily, x='DateTime', y='Energy_Consumption_kWh',
    title='1. Energy Consumption Trend Over Time (Daily Mean) - Filtered',
    labels={'Energy_Consumption_kWh': 'Energy (kW)'},
    template='plotly_dark'
)

# Dynamic: Voltage vs. Energy 
fig_voltage = px.scatter(
    data_df.sample(n=min(len(data_df), 1000), random_state=42).reset_index(), x='Voltage', y='Energy_Consumption_kWh', 
    color='Sub_metering_3', 
    title='Voltage vs. Energy Consumption',
    template='plotly_dark',
    color_discrete_map={0: '#90EE90', 1: '#FFA07A'} 
)

# Hourly Consumption Trend (Emphasizing Peak/Off-Peak)
hourly_mean_data = data_df.groupby(data_df.index.hour)['Energy_Consumption_kWh'].mean(numeric_only=True).reset_index().rename(columns={'DateTime': 'Time_of_Day'})
fig_hourly = px.bar(
    hourly_mean_data, 
    x='Time_of_Day', y='Energy_Consumption_kWh',
    title='2. Average Consumption by Hour (Highlighting Peak & Trough Times)',
    template='plotly_dark',
    color='Energy_Consumption_kWh',
    color_continuous_scale=px.colors.sequential.Inferno,
    labels={'Time_of_Day': 'Hour of Day (0-23)', 'Energy_Consumption_kWh': 'Avg. Energy (kW)'}
)


# Sub-System Stacked Bar Chart 
sub_metering_data = data_df[['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']].resample('D').sum(numeric_only=True).reset_index()
sub_metering_data = sub_metering_data.melt(id_vars=['DateTime'], var_name='Sub_Meter', value_name='Consumption_Wh')

fig_submeters = px.bar(
    sub_metering_data.sample(n=min(len(sub_metering_data), 1000), random_state=42), 
    x='DateTime', 
    y='Consumption_Wh', 
    color='Sub_Meter',
    title='3. Daily Consumption Breakdown by Metering Sub-System - Filtered',
    template='plotly_dark',
    labels={'Consumption_Wh': 'Consumption (Wh)', 'Sub_Meter': 'Sub-Meter'},
    color_discrete_map={'Sub_metering_1': '#00FFFF', 'Sub_metering_2': '#FFA07A', 'Sub_metering_3': '#90EE90'}
)

# dashboard_layout.py (Around line 52 - REPLACED fig_breakdown)
import plotly.graph_objects as go # <-- ADD THIS IMPORT AT THE TOP OF THE FILE




# dashboard_layout.py (Around line 60 - FINAL UPDATED fig_breakdown)

# Use the normalized data to create a visually useful chart (excluding the 99.8% category)
breakdown_df_normalized = pd.DataFrame(normalized_breakdown.items(), columns=['Appliance Category', 'Total kWh'])

# Define a consistent, high-contrast color palette
device_colors = {
    'Refrigerator & Laundry (Sub-meter 2)': '#FFA07A',  # Orange/Salmon
    'Water Heater / AC (Sub-meter 3)': '#00FFFF',       # Cyan/Blue
    'General Use (Lights, Plugs, TV)': '#90EE90'        # Green
}
# Only include colors for the categories we are plotting
colors_ordered = [device_colors[c] for c in breakdown_df_normalized['Appliance Category']]

fig_breakdown = go.Figure(data=[go.Pie(
    labels=breakdown_df_normalized['Appliance Category'],
    values=breakdown_df_normalized['Total kWh'],
    # Key settings for look and feel:
    name="", # Remove secondary chart name
    hole=0.4,
    marker_colors=colors_ordered,
    textinfo='percent+label', # Display both percentage and label inside the slice
    insidetextorientation='radial', # Place text radially inside the slice (like your example)
    textfont_size=16, # Increase text size for clarity
)])

fig_breakdown.update_layout(
    title_text='5. Consumption Breakdown (Excluding Dominant Kitchen Use)',
    template='plotly_dark',
    height=400,
    # Center the chart and adjust margins
    margin=dict(l=20, r=20, t=50, b=20),
    # Move legend outside and below the chart
    legend=dict(
        orientation="h",
        y=-0.2,
        x=0.5,
        xanchor="center"
    )
)
# Ensure plotly.graph_objects is imported at the top of dashboard_layout.py


# --- 2. Define Enhanced Components (UI Styles) ---

SIDEBAR_WIDTH = '25%'
CONTENT_MARGIN = '30%'

HEADER_STYLE = {'textAlign': 'center', 'color': 'white', 'backgroundColor': '#1E2130', 'padding': '25px 0'} 
SIDEBAR_STYLE = {
    'position': 'fixed', 
    'top': 0, 
    'left': 0, 
    'bottom': 0, 
    'width': SIDEBAR_WIDTH, 
    'padding': '30px', 
    'backgroundColor': '#1E2130', 
    'color': 'white', 
    'boxShadow': '4px 0 10px rgba(0,0,0,0.6)', 
    'zIndex': 10 
}
CONTENT_STYLE = {
    'marginLeft': CONTENT_MARGIN, 
    'marginRight': '5%', 
    'padding': '30px 10px', 
    'minHeight': '100vh',
    'backgroundColor': '#252934' 
}


# --- 3. Full Layout (Raw Data Table Removed) ---
def create_layout():
    """Returns the full HTML layout for the Dash application."""
    return html.Div(style={'backgroundColor': '#252934', 'minHeight': '100vh', 'fontFamily': 'Arial, sans-serif'}, children=[
        
        # --- HEADER (Minimal to avoid overlap) ---
        html.Div(style={'padding': '25px 0', 'backgroundColor': '#1E2130'}),
        
        # --- SIDEBAR: KEY METRICS and PREDICTION TOOL ---
        html.Div(style=SIDEBAR_STYLE, children=[
            html.H3("Key Energy Insights", style={'color': '#00FFFF', 'borderBottom': '2px solid #00FFFF', 'paddingBottom': '15px', 'marginBottom': '30px', 'fontSize': '24px'}),
            
            # Metric 1: Avg. Hourly Usage
            html.Div(style={'backgroundColor': '#333A4A', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '25px'}, children=[
                html.H4("Avg. Total Usage (kW/h)", style={'color': '#A9A9A9', 'fontSize': '16px'}),
                html.P(f"{avg_hourly_usage} kW", style={'fontSize': '32px', 'fontWeight': 'bold', 'color': 'white'}),
            ]),
            
            # Metric 2: Peak Hour
            html.Div(style={'backgroundColor': '#333A4A', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '25px'}, children=[
                html.H4("Overall Peak Usage Time", style={'color': '#A9A9A9', 'fontSize': '16px'}),
                html.P(f"{peak_hour}:00 Hrs", style={'fontSize': '32px', 'fontWeight': 'bold', 'color': '#FFA07A'}),
            ]),

            # Metric 3: Avg Sub-Metering
            html.Div(style={'backgroundColor': '#333A4A', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '25px'}, children=[
                html.H4("Avg. Sub-Metering (Wh/min)", style={'color': '#A9A9A9', 'fontSize': '16px'}),
                html.P(f"{avg_sub_metering_usage} Wh", style={'fontSize': '32px', 'fontWeight': 'bold', 'color': '#90EE90'}),
            ]),

            # Metric 4: Model R2
            html.Div(style={'backgroundColor': '#333A4A', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '40px'}, children=[
                html.H4("Prediction Model R²", style={'color': '#A9A9A9', 'fontSize': '16px'}),
                html.P(f"{model_r2:.2f}", style={'fontSize': '32px', 'fontWeight': 'bold', 'color': '#00FFFF'}),
            ]),

            # Prediction Input Section
            html.Hr(style={'borderColor': '#4A5060'}),
            html.H4("⚡ Hourly Energy Prediction", style={'color': '#00FFFF', 'marginTop': '20px'}),
            html.Label("Input Voltage (V):", style={'display': 'block', 'marginTop': '10px', 'color': '#A9A9A9'}),
            dcc.Input(id='voltage-input', type='number', value=240, style={'width': '90%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #4A5060', 'backgroundColor': '#1E2130', 'color': 'white'}),
            html.P("Predicted Power (kW):", style={'marginTop': '15px', 'color': 'white'}),
            html.Div(id='prediction-output', style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#90EE90'}),
            
        ]),

        # --- MAIN CONTENT ---
        html.Div(id='dashboard-content', style=CONTENT_STYLE, children=[
            
            # Main Title 
            html.H1(" Energy Consumption Analysis System", style={'fontSize': '38px', 'color': '#00FFFF', 'marginBottom': '5px'}),
            html.P("Peak/Trough Analysis, Consumption Breakdown, and Predictive Modeling", style={'color': '#A9A9A9', 'fontSize': '16px', 'marginBottom': '20px'}),
            
            html.H2("Interactive Data Visualization & Component Breakdown", style={'color': 'white', 'marginBottom': '20px', 'fontSize': '28px'}),
            
            # RAW DATA TABLE SECTION HAS BEEN REMOVED HERE
            
            # Dropdown Filter for Time Category
            html.Div(style={'marginBottom': '30px', 'backgroundColor': '#1E2130', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.3)'}, children=[
                html.Label("Filter Charts by Time Category (Peak/Off-Peak):", style={'color': '#00FFFF', 'display': 'block', 'marginBottom': '10px', 'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='time-category-dropdown',
                    options=[
                        {'label': 'All Time Categories', 'value': 'ALL'},
                        {'label': 'Peak Evening (17:00 - 21:00) - High Usage', 'value': 'Peak Evening (17-21h)'},
                        {'label': 'Off-Peak Night (22:00 - 08:00) - Low Usage', 'value': 'Off-Peak Night (22-8h)'},
                        {'label': 'Mid-Day (09:00 - 16:00)', 'value': 'Mid-Day (9-16h)'}
                    ],
                    value='ALL',
                    clearable=False,
                    style={'color': '#252934'}
                ),
            ]),
            
            # Row 1: Time Series and NEW Breakdown Pie Chart
            html.Div(className='row', style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '20px'}, children=[
                html.Div(style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'}, children=[
                    dcc.Graph(id='time-series-graph', figure=fig_time, style={'height': '400px'})
                ]),
                html.Div(style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'}, children=[
                    dcc.Graph(id='appliance-breakdown-pie', figure=fig_breakdown, style={'height': '400px'})
                ]),
            ]),
            
            # Row 2: Hourly Trend and Sub-System Stacked Bar
            html.Div(className='row', style={'display': 'flex', 'flexWrap': 'wrap'}, children=[
                html.Div(style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'}, children=[
                    dcc.Graph(id='hourly-trend-graph', figure=fig_hourly, style={'height': '400px'})
                ]),
                 html.Div(style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'}, children=[
                    dcc.Graph(id='sub-meter-breakdown-graph', figure=fig_submeters, style={'height': '400px'})
                ]),
            ]),
        ])
    ])