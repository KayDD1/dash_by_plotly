import dash
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html
import plotly.express as px
import pandas as pd

# Loading Data
def load_data():
    data = pd.read_csv('assets/healthcare.csv')
    data["Billing Amount"] = pd.to_numeric(data["Billing Amount"], errors='coerce')
    data["Date of Admission"] = pd.to_datetime(data["Date of Admission"])
    data["YearMonth"] = data["Date of Admission"].dt.to_period("M")
    return data

data = load_data()

# Displaying the first few rows of the data
print(data.head())

num_of_records = len(data)
avg_billing_amount = data["Billing Amount"].mean()
total_billing_amount = data["Billing Amount"].sum()

# Creating a Web App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout and Design
app.layout = dbc.Container([
    dbc.Row([
       dbc.Col([html.H1("Healthcare Billing Dashboard", className="text-center")], width=12) 
    ]),

    # Hospital Statistics
    dbc.Row([
        dbc.Col([html.Div(f'Total Patient Records: {num_of_records}', className="text-center my-5")], width=4),
        dbc.Col([html.Div(f'Average Billing Amount: ${avg_billing_amount:.2f}', className="text-center my-5 top-text")], width=4),
        dbc.Col([html.Div(f'Total Billing Amount: ${total_billing_amount:.2f}', className="text-center my-5 top-text")], width=4)
    ], className="mb-4"),

    # Patient Demographics
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Patient Demographics", className="card-title"),
                    dcc.Dropdown(
                        id='gender-filter',
                        options=[{'label': gender, 'value': gender} for gender in data["Gender"].unique()],
                        value=None,
                        placeholder="Select a Gender"
                    ),
                    dcc.Graph(id='age-distribution')
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Medical Condition Distribution", className="card-title"),
                    dcc.Graph(id='medical-condition-distribution')
                ])
            ])
        ])
    ]),
    # Insurance Provider Data
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Insurance Provider Comparison", className="card-title"),
                    dcc.Graph(id='insurance-comparison')

                ])
            ])
        ], width=12)
    ]),

    # Billing Distribution
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Billing Amount Distribution", className="card-title"),
                    dcc.Slider(
                        id="billing-slider",
                        min=data["Billing Amount"].min(),
                        max=data["Billing Amount"].max(),
                        value=data["Billing Amount"].median(),
                        marks={int(value): f"${int(value)}" for value in data["Billing Amount"].quantile([0, 0.25, 0.5, 0.75, 1]).values},
                        step=100
                    ),
                    dcc.Graph(id='billing-distribution')
                ])
            ])
        ], width=12)
    ]),
    # Patient Admission Trends
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Trends in Admissions", className="card-title"),
                    dcc.RadioItems(
                        id='chart-type',
                        options=[
                            {'label': 'Line Chart', 'value': 'line'},
                            {'label': 'Bar Chart', 'value': 'bar'}
                        ],
                        value='line',
                        inline=True,
                        className="mb-4"
                    ),
                    dcc.Dropdown(
                        id='condition-filter',
                        options=[{'label': condition, 'value': condition} for condition in data["Medical Condition"].unique()],
                        value=None,
                        placeholder="Select a Medical Condition",
                    ),
                    dcc.Graph(id='admission-trends')
                ])
            ])
        ], width=12)
    ]),
    # Footer
    dbc.Row([
        dbc.Col([
            html.Div("© 2025 Healthcare Dashboard", className="text-center my-5")
        ], width=12)
    ])
], fluid=True)


# Create our Callbacks
@app.callback(
    Output('age-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_age_distribution(selected_gender):
    if selected_gender:
        filtered_data = data[data["Gender"] == selected_gender]
    else:
        filtered_data = data
    if filtered_data.empty:
        return {}
    fig = px.histogram(filtered_data, 
                       x="Age", 
                       title="Age Distribution by Gender", 
                       nbins=10, 
                       color="Gender",
                       color_discrete_sequence=["#636EFA", "#EF553B"]
                       )
    return fig

# Callback for Medical Condition Distribution
@app.callback(
    Output('medical-condition-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_medical_condition_distribution(selected_gender):
    filtered_data = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.pie(filtered_data, names='Medical Condition',
                   title="Medical Condition Distribution",
                   color_discrete_sequence=px.colors.sequential.RdBu)
    return fig

# Callback for Insurance Provider Comparison
@app.callback(
    Output('insurance-comparison', 'figure'),
    Input('gender-filter', 'value')
)
def update_insurance_comparison(selected_gender):
    filtered_data = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.bar(filtered_data, 
                  x="Insurance Provider", 
                  y="Billing Amount", 
                  title="Insurance Provider Price Comparison",
                  color="Medical Condition",
                  barmode="group",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    return fig

# Callback for Billing Amount Distribution
@app.callback(
    Output('billing-distribution', 'figure'),
    [Input('gender-filter', 'value'),
    Input('billing-slider', 'value')]
)
def update_billing_distribution(selected_gender, slider_value):
    filtered_data = data[data["Gender"] == selected_gender] if selected_gender else data
    filtered_data = filtered_data[filtered_data["Billing Amount"] <= slider_value]  
    fig = px.histogram(filtered_data,
                       x="Billing Amount", 
                       title="Billing Amount Distribution",
                       nbins=10)
    return fig

# Callback for Admission Trends
@app.callback(
    Output('admission-trends', 'figure'),
    [Input('chart-type', 'value'),
     Input('condition-filter', 'value')]
)
def update_admission_trends(chart_type, selected_condition):
    filtered_data = data[data["Medical Condition"] == selected_condition] if selected_condition else data
    trend_data = filtered_data.groupby('YearMonth').size().reset_index(name='Counts')
    trend_data['YearMonth'] = trend_data['YearMonth'].astype(str)

    if chart_type == 'line':
        fig = px.line(trend_data, 
                      x='YearMonth', 
                      y='Counts', 
                      title="Trends in Admissions",
                      markers=True)
    else:
        fig = px.bar(trend_data, 
                     x='YearMonth', 
                     y='Counts', 
                     title="Trends in Admissions",
                     color_discrete_sequence=px.colors.qualitative.Set2)
    return fig


if __name__ == '__main__':
    app.run(debug=True)