"""
CasualHero BI Platform - Dash Application

Professional BI dashboard with interactive DataTable, conditional formatting,
and Power BI-style data bars.

Architecture:
- Dash for UI (replaces Streamlit)
- Same business logic (kpi_calculator, fiscal_calendar)
- Callback-based interactivity
- Conditional formatting with data bars
"""

import sys
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import polars as pl
import pandas as pd

from src.data.connector import get_db
from src.data.queries import query_all_transactions
from src.core.kpi_calculator import prepare_transaction_data, calculate_weekly_report
from src.core.fiscal_calendar import get_fiscal_year, get_fiscal_week


# ============================================================================
# Data Loading (with caching)
# ============================================================================

# Global cache for data (loaded once at startup)
DATA_CACHE = {}


def load_transactions():
    """
    Load all transaction data (called once at startup).

    For production, implement Redis or similar for distributed caching.
    """
    if 'transactions' in DATA_CACHE:
        return DATA_CACHE['transactions']

    load_start = datetime.now()
    print(f"[{load_start.strftime('%H:%M:%S')}] Loading transaction data...")

    try:
        # Load from database
        query_start = datetime.now()
        print(f"  [Query] Starting database query...")

        db = get_db()
        raw_df = query_all_transactions(db, years=5)

        query_end = datetime.now()
        query_duration = (query_end - query_start).total_seconds()
        print(f"  [Query] Loaded {len(raw_df):,} raw rows in {query_duration:.1f}s")

        # Prepare data (add fiscal calendar columns)
        prep_start = datetime.now()
        print(f"  [Prep] Starting data preparation...")

        prepared_df = prepare_transaction_data(raw_df)

        prep_end = datetime.now()
        prep_duration = (prep_end - prep_start).total_seconds()
        print(f"  [Prep] Prepared {len(prepared_df):,} transactions in {prep_duration:.1f}s")

        # Cache the data
        DATA_CACHE['transactions'] = prepared_df
        DATA_CACHE['last_refresh'] = datetime.now()

        load_end = datetime.now()
        duration = (load_end - load_start).total_seconds()
        print(f"[{load_end.strftime('%H:%M:%S')}] Data loaded in {duration:.1f}s")

        return prepared_df

    except Exception as e:
        print(f"[ERROR] Data load failed: {e}")
        raise


# Load data at startup
print("Initializing CasualHero BI Platform...")
df = load_transactions()
print(f"Ready! Loaded {len(df):,} transactions")


# ============================================================================
# Dash App Initialization
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="CasualHero BI Platform"
)

server = app.server  # For deployment


# ============================================================================
# Layout Components
# ============================================================================

# Navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/", id="nav-home")),
        dbc.NavItem(dbc.NavLink("Weekly Report", href="/weekly", id="nav-weekly")),
        dbc.NavItem(dbc.NavLink("Monthly Report", href="/monthly", id="nav-monthly")),
        dbc.NavItem(dbc.NavLink("Trends", href="/trends", id="nav-trends")),
    ],
    brand="📊 CasualHero BI Platform",
    brand_href="/",
    color="#FF6B9D",  # Snowflake pink
    dark=True,
    className="mb-4"
)

# Sidebar
sidebar = dbc.Col(
    [
        html.H5("Data Summary", className="mt-3"),
        html.Hr(),
        html.P([
            html.Strong("Transactions: "),
            f"{len(df):,}"
        ]),
        html.P([
            html.Strong("Establishments: "),
            f"{df['Establishment'].n_unique()}"
        ]),
        html.P([
            html.Strong("Date Range: "),
            f"{df['Adjusted_Order_Date'].min()} to {df['Adjusted_Order_Date'].max()}"
        ]),
        html.Hr(),
        html.H6("Current Period"),
        html.P([
            f"FY{get_fiscal_year(date.today())} Week {get_fiscal_week(date.today())}"
        ]),
        html.Hr(),
        dbc.Button("🔄 Reload Data", id="reload-btn", color="primary", size="sm", className="mb-2"),
        html.Small("Cache warmer runs at 9:25 AM daily", className="text-muted"),
    ],
    width=2,
    className="bg-light p-3"
)

# Main content area
content = dbc.Col(
    id="page-content",
    width=10,
    className="p-4"
)

# App layout
app.layout = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),
        navbar,
        dbc.Row([sidebar, content]),
    ],
    fluid=True
)


# ============================================================================
# Page Layouts
# ============================================================================

def home_layout():
    """Home page layout"""
    today = date.today()
    current_fy = get_fiscal_year(today)
    current_week = get_fiscal_week(today)

    return html.Div([
        html.H2("🏠 Welcome to CasualHero BI Platform"),
        html.Hr(),
        dbc.Alert(f"Current Period: FY{current_fy} Week {current_week}", color="info"),
        html.H4("Available Reports:"),
        dbc.ListGroup([
            dbc.ListGroupItem("Weekly Report - YoY comparison, 4W avg, order volumes, ATV"),
            dbc.ListGroupItem("Monthly Report - Monthly aggregations and trends (Coming soon)"),
            dbc.ListGroupItem("Trends - 5-year historical analysis (Coming soon)"),
        ]),
        html.Hr(),
        html.H4("Quick Stats:"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H5("Total Orders", className="card-title"),
                    html.H3(f"{df['Order_Number'].n_unique():,}", className="text-primary")
                ])
            ])),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H5("Total Sales", className="card-title"),
                    html.H3(f"£{df['Order_Net_Sales'].sum():,.2f}", className="text-success")
                ])
            ])),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H5("Establishments", className="card-title"),
                    html.H3(f"{df['Establishment'].n_unique()}", className="text-info")
                ])
            ])),
        ])
    ])


def weekly_report_layout():
    """Weekly Report page layout"""
    # Get available fiscal years and weeks
    available_years = sorted(df['Fiscal_Year'].unique().to_list(), reverse=True)
    current_fy = available_years[0] if available_years else 2026

    available_weeks = sorted(
        df.filter(pl.col('Fiscal_Year') == current_fy)['Fiscal_Week'].unique().to_list()
    )
    current_week = available_weeks[-1] if available_weeks else 1

    return html.Div([
        html.H2("📅 Weekly Report"),
        html.Hr(),

        # Week selector
        dbc.Row([
            dbc.Col([
                html.Label("Fiscal Year:"),
                dcc.Dropdown(
                    id='fiscal-year-dropdown',
                    options=[{'label': f'FY{year}', 'value': year} for year in available_years],
                    value=current_fy,
                    clearable=False
                )
            ], width=3),
            dbc.Col([
                html.Label("Week:"),
                dcc.Dropdown(
                    id='fiscal-week-dropdown',
                    options=[{'label': f'Week {week}', 'value': week} for week in available_weeks],
                    value=current_week,
                    clearable=False
                )
            ], width=3),
        ], className="mb-4"),

        # Loading indicator
        dcc.Loading(
            id="loading-weekly-report",
            type="default",
            children=html.Div(id='weekly-report-table')
        )
    ])


# ============================================================================
# Callbacks
# ============================================================================

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route pages based on URL"""
    if pathname == '/weekly':
        return weekly_report_layout()
    elif pathname == '/monthly':
        return html.Div([
            html.H2("📆 Monthly Report"),
            html.Hr(),
            html.P("Coming soon...")
        ])
    elif pathname == '/trends':
        return html.Div([
            html.H2("📈 5-Year Trends"),
            html.Hr(),
            html.P("Coming soon...")
        ])
    else:
        return home_layout()


@app.callback(
    Output('fiscal-week-dropdown', 'options'),
    Output('fiscal-week-dropdown', 'value'),
    Input('fiscal-year-dropdown', 'value')
)
def update_week_options(selected_year):
    """Update available weeks when fiscal year changes"""
    if selected_year is None:
        return [], None

    available_weeks = sorted(
        df.filter(pl.col('Fiscal_Year') == selected_year)['Fiscal_Week'].unique().to_list()
    )

    options = [{'label': f'Week {week}', 'value': week} for week in available_weeks]
    default_value = available_weeks[-1] if available_weeks else None

    return options, default_value


@app.callback(
    Output('weekly-report-table', 'children'),
    Input('fiscal-year-dropdown', 'value'),
    Input('fiscal-week-dropdown', 'value')
)
def update_weekly_report(fiscal_year, fiscal_week):
    """Generate weekly report with conditional formatting"""
    if fiscal_year is None or fiscal_week is None:
        return html.P("Please select a fiscal year and week")

    calc_start = datetime.now()

    # Calculate report using existing business logic
    report = calculate_weekly_report(df, fiscal_year=fiscal_year, fiscal_week=fiscal_week)

    calc_duration = (datetime.now() - calc_start).total_seconds()

    # Format data for display
    formatted_report = report.with_columns([
        # Convert to float for DataTable
        pl.col('Current_Year_Sales').cast(pl.Float64),
        pl.col('Last_Year_Sales').cast(pl.Float64),
        pl.col('Current_Year_4W_Avg').cast(pl.Float64),
        pl.col('Last_Year_4W_Avg').cast(pl.Float64),
        pl.col('Current_Year_Vol').cast(pl.Float64),
        pl.col('Last_Year_Vol').cast(pl.Float64),
        pl.col('Current_Year_ATV').cast(pl.Float64),
        pl.col('Last_Year_ATV').cast(pl.Float64),
        # Variance percentages - convert to percentage
        (pl.col('Weekly_Sales_Var_Pct') * 100).alias('Weekly_Sales_Var_Pct'),
        (pl.col('FourWeek_Avg_Var_Pct') * 100).alias('FourWeek_Avg_Var_Pct'),
        (pl.col('Volume_Var_Pct') * 100).alias('Volume_Var_Pct'),
        (pl.col('ATV_Var_Pct') * 100).alias('ATV_Var_Pct'),
    ])

    # Convert to pandas for DataTable
    df_pandas = formatted_report.to_pandas()

    # Create DataTable with conditional formatting
    table = dash_table.DataTable(
        data=df_pandas.to_dict('records'),
        columns=[
            {'name': 'Company', 'id': 'Company'},
            {'name': 'Establishment', 'id': 'Establishment'},
            {'name': 'Current Year Sales', 'id': 'Current_Year_Sales', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Last Year Sales', 'id': 'Last_Year_Sales', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Sales Var %', 'id': 'Weekly_Sales_Var_Pct', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Current 4W Avg', 'id': 'Current_Year_4W_Avg', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Last 4W Avg', 'id': 'Last_Year_4W_Avg', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': '4W Avg Var %', 'id': 'FourWeek_Avg_Var_Pct', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Current Vol', 'id': 'Current_Year_Vol', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Last Vol', 'id': 'Last_Year_Vol', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
            {'name': 'Vol Var %', 'id': 'Volume_Var_Pct', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Current ATV', 'id': 'Current_Year_ATV', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Last ATV', 'id': 'Last_Year_ATV', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'ATV Var %', 'id': 'ATV_Var_Pct', 'type': 'numeric', 'format': {'specifier': '.2f'}},
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '12px'
        },
        style_header={
            'backgroundColor': '#FF6B9D',  # Snowflake pink
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_data_conditional=(
            # Data bars using diverging color scale (Power BI style)
            # Create gradient bars for positive values (green on right side)
            [
                {
                    'if': {
                        'filter_query': f'{{Weekly_Sales_Var_Pct}} >= {i} && {{Weekly_Sales_Var_Pct}} < {i+5}',
                        'column_id': 'Weekly_Sales_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*50}%, white {50 + (i+2.5)/100*50}%)',
                    'color': '#006400',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            # Negative values (red on left side)
            [
                {
                    'if': {
                        'filter_query': f'{{Weekly_Sales_Var_Pct}} >= {-i-5} && {{Weekly_Sales_Var_Pct}} < {-i}',
                        'column_id': 'Weekly_Sales_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*50}%, #FFB6C1 {50 - (i+2.5)/100*50}%, #FFB6C1 50%, white 50%)',
                    'color': '#8B0000',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            # Repeat for other variance columns
            [
                {
                    'if': {
                        'filter_query': f'{{FourWeek_Avg_Var_Pct}} >= {i} && {{FourWeek_Avg_Var_Pct}} < {i+5}',
                        'column_id': 'FourWeek_Avg_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*50}%, white {50 + (i+2.5)/100*50}%)',
                    'color': '#006400',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            [
                {
                    'if': {
                        'filter_query': f'{{FourWeek_Avg_Var_Pct}} >= {-i-5} && {{FourWeek_Avg_Var_Pct}} < {-i}',
                        'column_id': 'FourWeek_Avg_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*50}%, #FFB6C1 {50 - (i+2.5)/100*50}%, #FFB6C1 50%, white 50%)',
                    'color': '#8B0000',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            [
                {
                    'if': {
                        'filter_query': f'{{Volume_Var_Pct}} >= {i} && {{Volume_Var_Pct}} < {i+5}',
                        'column_id': 'Volume_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*50}%, white {50 + (i+2.5)/100*50}%)',
                    'color': '#006400',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            [
                {
                    'if': {
                        'filter_query': f'{{Volume_Var_Pct}} >= {-i-5} && {{Volume_Var_Pct}} < {-i}',
                        'column_id': 'Volume_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*50}%, #FFB6C1 {50 - (i+2.5)/100*50}%, #FFB6C1 50%, white 50%)',
                    'color': '#8B0000',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            [
                {
                    'if': {
                        'filter_query': f'{{ATV_Var_Pct}} >= {i} && {{ATV_Var_Pct}} < {i+5}',
                        'column_id': 'ATV_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*50}%, white {50 + (i+2.5)/100*50}%)',
                    'color': '#006400',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ] +
            [
                {
                    'if': {
                        'filter_query': f'{{ATV_Var_Pct}} >= {-i-5} && {{ATV_Var_Pct}} < {-i}',
                        'column_id': 'ATV_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*50}%, #FFB6C1 {50 - (i+2.5)/100*50}%, #FFB6C1 50%, white 50%)',
                    'color': '#8B0000',
                    'fontWeight': 'bold'
                }
                for i in range(0, 100, 5)
            ]
        ),
        sort_action='native',  # Enable sorting
        filter_action='native',  # Enable filtering
        page_action='native',  # Enable pagination
        page_size=20,  # Rows per page
        export_format='xlsx',  # Enable Excel export
        export_headers='display',
    )

    return html.Div([
        dbc.Alert(f"Report generated in {calc_duration*1000:.0f}ms (cached data)", color="success"),
        html.H4(f"FY{fiscal_year} Week {fiscal_week} - YoY Comparison"),
        table
    ])


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8050,
        use_reloader=False  # Prevent double-loading data on startup
    )
