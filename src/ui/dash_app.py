"""
CasualHero BI Platform - Dash Application

Professional BI dashboard for specialty food retailers:
- Clean, minimal, professional design
- Primary color: #2C5F7C (deep blue-grey)
- Accent: #E67E22 (warm orange for CTAs)
- Font: Inter for UI, Roboto for data
- Left sidebar navigation with collapsible sections
- Top header with location selector and search
- Interactive DataTable with conditional formatting

Architecture:
- Dash for UI (replaces Streamlit)
- Same business logic (kpi_calculator, fiscal_calendar)
- Callback-based interactivity
- Smooth transitions (200ms ease)
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
from dash.exceptions import PreventUpdate
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
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME  # For icons
    ],
    suppress_callback_exceptions=True,
    title="CasualHero BI Platform"
)

server = app.server  # For deployment


# ============================================================================
# Custom CSS Styles (CasualHero Theme)
# ============================================================================

# CasualHero Brand Colors
PRIMARY_COLOR = "#2C5F7C"      # Deep blue-grey
ACCENT_COLOR = "#E67E22"       # Warm orange
SIDEBAR_BG = "#FAFAFA"         # Light grey
SELECTED_BG = "#E8F4F8"        # Light blue-grey for selected items
HEADER_BG = "#FFFFFF"          # White
BORDER_COLOR = "#E0E0E0"       # Border grey
BG_COLOR = "#F5F5F5"           # Page background

# Custom CSS for CasualHero layout
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            /* CasualHero Custom Styles */
            body {
                margin: 0;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background-color: #F5F5F5;
            }

            /* Top Header */
            .casualhero-header {
                background-color: white;
                border-bottom: 1px solid #E0E0E0;
                padding: 12px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                height: 60px;
            }

            /* Sidebar */
            .casualhero-sidebar {
                background-color: #FAFAFA;
                border-right: 1px solid #E0E0E0;
                position: fixed;
                left: 0;
                top: 60px;
                bottom: 0;
                width: 220px;
                overflow-y: auto;
                padding: 20px 0;
            }

            .casualhero-sidebar .nav-item {
                padding: 10px 20px;
                cursor: pointer;
                transition: all 200ms ease;
                color: #333;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .casualhero-sidebar .nav-item:hover {
                background-color: #F0F0F0;
            }

            .casualhero-sidebar .nav-item.selected {
                background-color: #E8F4F8;
                color: #2C5F7C;
                border-left: 3px solid #2C5F7C;
            }

            .casualhero-sidebar .nav-section {
                margin-bottom: 20px;
            }

            .casualhero-sidebar .section-title {
                padding: 10px 20px;
                font-size: 11px;
                font-weight: 600;
                color: #999;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .casualhero-sidebar .subsection {
                padding-left: 40px;
                font-size: 14px;
            }

            /* Main Content */
            .casualhero-content {
                margin-left: 220px;
                margin-top: 60px;
                padding: 30px;
                background-color: #F5F5F5;
                min-height: calc(100vh - 60px);
            }

            .content-card {
                background-color: white;
                border-radius: 8px;
                padding: 24px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                transition: all 200ms ease;
            }

            .content-card:hover {
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            }

            /* CTA Button */
            .btn-casualhero {
                background-color: #E67E22 !important;
                border-color: #E67E22 !important;
                color: white !important;
                transition: all 200ms ease;
            }

            .btn-casualhero:hover {
                background-color: #D35400 !important;
                border-color: #D35400 !important;
            }

            /* Filters Section */
            .filters-bar {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            /* Primary color accent for dropdowns */
            .Select-control:focus {
                border-color: #2C5F7C !important;
            }

            /* Data tables use Roboto font */
            .dash-table-container {
                font-family: 'Roboto', sans-serif !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


# ============================================================================
# Layout Components (CasualHero Style)
# ============================================================================

# Top Header
header = html.Div(
    className="casualhero-header",
    children=[
        # Left side: Logo + menu toggle
        html.Div([
            html.Span("☰", style={'fontSize': '24px', 'marginRight': '15px', 'cursor': 'pointer', 'color': '#999', 'transition': 'all 200ms ease'}),
            html.Span("CasualHero", style={'fontSize': '24px', 'fontWeight': '700', 'color': PRIMARY_COLOR, 'letterSpacing': '-0.5px'}),
        ], style={'display': 'flex', 'alignItems': 'center'}),

        # Center: Location selector
        html.Div([
            html.I(className="fas fa-map-marker-alt", style={'color': '#666', 'marginRight': '8px'}),
            dcc.Dropdown(
                id='location-selector',
                options=[
                    {'label': 'All Locations', 'value': 'all'},
                    {'label': 'Meadowhall, Sheffield', 'value': 'meadowhall'},
                    {'label': 'The O2, London', 'value': 'o2'},
                    {'label': 'Westfield, Stratford', 'value': 'westfield'},
                ],
                value='all',
                clearable=False,
                style={'width': '250px', 'display': 'inline-block'}
            )
        ], style={'display': 'flex', 'alignItems': 'center'}),

        # Right side: Search + user menu
        html.Div([
            html.Div([
                html.I(className="fas fa-search", style={'color': '#999', 'marginRight': '8px'}),
                dcc.Input(
                    placeholder="Search reports, data, settings...",
                    type="text",
                    style={
                        'width': '350px',
                        'border': '1px solid #E0E0E0',
                        'borderRadius': '4px',
                        'padding': '8px 12px',
                        'fontSize': '14px',
                        'transition': 'all 200ms ease'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginRight': '20px'}),
            html.Span("Last refresh: 9:30 AM", style={'marginRight': '15px', 'fontSize': '14px', 'color': '#666'}),
            html.I(className="fas fa-shopping-cart", style={'marginRight': '15px', 'fontSize': '18px', 'color': '#666', 'cursor': 'pointer'}),
            html.I(className="fas fa-user-circle", style={'marginRight': '15px', 'fontSize': '18px', 'color': '#666', 'cursor': 'pointer'}),
            html.I(className="fas fa-question-circle", style={'fontSize': '18px', 'color': '#666', 'cursor': 'pointer'}),
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ]
)

# Left Sidebar Navigation (CasualHero Style)
sidebar = html.Div(
    className="casualhero-sidebar",
    children=[
        # Home
        html.Div(
            className="nav-section",
            children=[
                dcc.Link(
                    [html.I(className="fas fa-home"), html.Span("Home")],
                    href="/",
                    className="nav-item",
                    id="nav-home"
                )
            ]
        ),

        # Reports Section
        html.Div(
            className="nav-section",
            children=[
                html.Div("REPORTS", className="section-title"),
                dcc.Link(
                    [html.I(className="far fa-file-alt"), html.Span("Overview")],
                    href="/overview",
                    className="nav-item",
                    id="nav-overview"
                ),

                # Sales subsection
                html.Div([
                    html.Div(
                        [html.I(className="fas fa-dollar-sign"), html.Span("Sales")],
                        className="nav-item",
                        style={'fontWeight': '500'}
                    ),
                    dcc.Link(
                        html.Span("Sales summary"),
                        href="/sales-summary",
                        className="nav-item subsection",
                        id="nav-sales-summary"
                    ),
                    dcc.Link(
                        html.Span("Sales analytics"),
                        href="/sales-analytics",
                        className="nav-item subsection",
                        id="nav-sales-analytics"
                    ),
                    dcc.Link(
                        html.Span("Sales breakdown"),
                        href="/sales-breakdown",
                        className="nav-item subsection",
                        id="nav-sales-breakdown"
                    ),
                ]),

                # Orders subsection
                dcc.Link(
                    [html.I(className="fas fa-receipt"), html.Span("Orders")],
                    href="/orders",
                    className="nav-item",
                    id="nav-orders"
                ),
                dcc.Link(
                    html.Span("Order details"),
                    href="/order-details",
                    className="nav-item subsection"
                ),

                # Employee performance
                dcc.Link(
                    [html.I(className="fas fa-users"), html.Span("Employee performance")],
                    href="/employee-performance",
                    className="nav-item"
                ),
            ]
        ),

        # Other Sections (placeholder)
        html.Div(
            className="nav-section",
            children=[
                html.Div("MANAGEMENT", className="section-title"),
                html.Div(
                    [html.I(className="fas fa-utensils"), html.Span("Menus")],
                    className="nav-item"
                ),
                html.Div(
                    [html.I(className="fas fa-credit-card"), html.Span("Payments")],
                    className="nav-item"
                ),
            ]
        ),
    ]
)

# Main content area
content = html.Div(
    id="page-content",
    className="casualhero-content"
)

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    header,
    sidebar,
    content
])


# ============================================================================
# Page Layouts (CasualHero Style)
# ============================================================================

def home_layout():
    """Home page layout - CasualHero style"""
    today = date.today()
    current_fy = get_fiscal_year(today)
    current_week = get_fiscal_week(today)

    return html.Div([
        # Page title
        html.H2("Overview", style={'marginBottom': '20px', 'color': '#333'}),

        # Current period card
        html.Div(
            className="content-card",
            children=[
                html.Div([
                    html.I(className="fas fa-calendar-alt", style={'color': PRIMARY_COLOR, 'marginRight': '10px', 'fontSize': '20px'}),
                    html.Span(f"Current Period: FY{current_fy} Week {current_week}", style={'fontSize': '16px', 'fontWeight': '500'})
                ], style={'padding': '10px 0'})
            ]
        ),

        # Quick Stats Cards
        html.Div([
            html.H4("Quick Stats", style={'marginBottom': '15px', 'color': '#333'}),
            html.Div([
                # Total Orders
                html.Div(
                    className="content-card",
                    style={'flex': '1', 'marginRight': '15px', 'textAlign': 'center'},
                    children=[
                        html.I(className="fas fa-receipt", style={'fontSize': '32px', 'color': ACCENT_COLOR, 'marginBottom': '10px'}),
                        html.H5("Total Orders", style={'color': '#666', 'fontSize': '14px', 'marginBottom': '5px'}),
                        html.H2(f"{df['Order_Number'].n_unique():,}", style={'color': '#333', 'margin': '0', 'fontFamily': 'Roboto'})
                    ]
                ),
                # Total Sales
                html.Div(
                    className="content-card",
                    style={'flex': '1', 'marginRight': '15px', 'textAlign': 'center'},
                    children=[
                        html.I(className="fas fa-pound-sign", style={'fontSize': '32px', 'color': '#28a745', 'marginBottom': '10px'}),
                        html.H5("Total Sales", style={'color': '#666', 'fontSize': '14px', 'marginBottom': '5px'}),
                        html.H2(f"£{df['Order_Net_Sales'].sum():,.0f}", style={'color': '#333', 'margin': '0', 'fontFamily': 'Roboto'})
                    ]
                ),
                # Establishments
                html.Div(
                    className="content-card",
                    style={'flex': '1', 'textAlign': 'center'},
                    children=[
                        html.I(className="fas fa-store", style={'fontSize': '32px', 'color': PRIMARY_COLOR, 'marginBottom': '10px'}),
                        html.H5("Establishments", style={'color': '#666', 'fontSize': '14px', 'marginBottom': '5px'}),
                        html.H2(f"{df['Establishment'].n_unique()}", style={'color': '#333', 'margin': '0', 'fontFamily': 'Roboto'})
                    ]
                ),
            ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '20px'}),
        ]),

        # Available Reports Card
        html.Div(
            className="content-card",
            children=[
                html.H4("Available Reports", style={'marginBottom': '15px', 'color': '#333'}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-line", style={'color': PRIMARY_COLOR, 'marginRight': '10px'}),
                        html.Span("Sales Summary - YoY comparison, 4W avg, order volumes, ATV", style={'fontSize': '14px'})
                    ], style={'padding': '12px', 'borderBottom': '1px solid #E0E0E0'}),
                    html.Div([
                        html.I(className="fas fa-chart-bar", style={'color': PRIMARY_COLOR, 'marginRight': '10px'}),
                        html.Span("Sales Analytics - Detailed breakdown and trends", style={'fontSize': '14px', 'color': '#999'})
                    ], style={'padding': '12px', 'borderBottom': '1px solid #E0E0E0'}),
                    html.Div([
                        html.I(className="fas fa-chart-area", style={'color': PRIMARY_COLOR, 'marginRight': '10px'}),
                        html.Span("Sales Breakdown - 5-year historical analysis", style={'fontSize': '14px', 'color': '#999'})
                    ], style={'padding': '12px'}),
                ])
            ]
        ),

        # Data info card
        html.Div(
            className="content-card",
            children=[
                html.H5("Data Information", style={'marginBottom': '10px', 'color': '#333'}),
                html.P([
                    html.Strong("Transactions: "), f"{len(df):,}"
                ], style={'marginBottom': '5px', 'fontSize': '14px'}),
                html.P([
                    html.Strong("Date Range: "), f"{df['Adjusted_Order_Date'].min()} to {df['Adjusted_Order_Date'].max()}"
                ], style={'marginBottom': '5px', 'fontSize': '14px'}),
                html.P([
                    html.Strong("Last Refresh: "), f"{DATA_CACHE.get('last_refresh', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}"
                ], style={'marginBottom': '0', 'fontSize': '14px'}),
            ]
        ),
    ])


def weekly_report_layout():
    """Weekly Report page layout - CasualHero style"""
    # Get available fiscal years and weeks
    available_years = sorted(df['Fiscal_Year'].unique().to_list(), reverse=True)
    current_fy = available_years[0] if available_years else 2026

    available_weeks = sorted(
        df.filter(pl.col('Fiscal_Year') == current_fy)['Fiscal_Week'].unique().to_list()
    )
    current_week = available_weeks[-1] if available_weeks else 1

    return html.Div([
        # Page title
        html.H2("Sales summary", style={'marginBottom': '20px', 'color': '#333'}),

        # Filters card (Toast style)
        html.Div(
            className="filters-bar",
            children=[
                html.Div([
                    # Date range picker (mimicking Toast)
                    html.Div([
                        html.I(className="fas fa-calendar", style={'color': '#666', 'marginRight': '8px'}),
                        html.Label("Fiscal Year:", style={'marginRight': '10px', 'fontSize': '14px', 'fontWeight': '500'}),
                        dcc.Dropdown(
                            id='fiscal-year-dropdown',
                            options=[{'label': f'FY{year}', 'value': year} for year in available_years],
                            value=current_fy,
                            clearable=False,
                            style={'width': '150px', 'display': 'inline-block', 'marginRight': '20px'}
                        ),
                    ], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '30px'}),

                    html.Div([
                        html.I(className="fas fa-calendar-week", style={'color': '#666', 'marginRight': '8px'}),
                        html.Label("Week:", style={'marginRight': '10px', 'fontSize': '14px', 'fontWeight': '500'}),
                        dcc.Dropdown(
                            id='fiscal-week-dropdown',
                            options=[{'label': f'Week {week}', 'value': week} for week in available_weeks],
                            value=current_week,
                            clearable=False,
                            style={'width': '150px', 'display': 'inline-block', 'marginRight': '20px'}
                        ),
                    ], style={'display': 'inline-flex', 'alignItems': 'center'}),

                    # More filters button
                    html.Button(
                        [html.I(className="fas fa-filter", style={'marginRight': '8px'}), "More filters"],
                        className="btn btn-casualhero",
                        style={
                            'marginLeft': '20px',
                            'padding': '8px 16px',
                            'fontSize': '14px',
                            'borderRadius': '4px',
                            'border': 'none',
                            'backgroundColor': 'white',
                            'color': ACCENT_COLOR,
                            'border': f'1px solid {ACCENT_COLOR}',
                            'cursor': 'pointer',
                            'transition': 'all 200ms ease'
                        }
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'gap': '15px'}),
            ]
        ),

        # Loading indicator
        dcc.Loading(
            id="loading-weekly-report",
            type="default",
            color=PRIMARY_COLOR,
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
    """Route pages based on URL (CasualHero structure)"""
    # Map CasualHero routes to content
    if pathname == '/sales-summary':
        return weekly_report_layout()
    elif pathname == '/sales-analytics':
        return html.Div([
            html.H2("Sales Analytics", style={'color': '#333'}),
            html.Div(className="content-card", children=[
                html.P("Detailed analytics coming soon...")
            ])
        ])
    elif pathname == '/sales-breakdown':
        return html.Div([
            html.H2("Sales Breakdown", style={'color': '#333'}),
            html.Div(className="content-card", children=[
                html.P("Breakdown by product, category, etc. coming soon...")
            ])
        ])
    elif pathname == '/overview':
        return html.Div([
            html.H2("Reports Overview", style={'color': '#333'}),
            html.Div(className="content-card", children=[
                html.P("Quick overview of all reports coming soon...")
            ])
        ])
    elif pathname == '/orders':
        return html.Div([
            html.H2("Orders", style={'color': '#333'}),
            html.Div(className="content-card", children=[
                html.P("Order details coming soon...")
            ])
        ])
    elif pathname == '/employee-performance':
        return html.Div([
            html.H2("Employee Performance", style={'color': '#333'}),
            html.Div(className="content-card", children=[
                html.P("Employee metrics coming soon...")
            ])
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
            'fontFamily': 'Roboto, sans-serif',
            'fontSize': '12px'
        },
        style_header={
            'backgroundColor': PRIMARY_COLOR,  # CasualHero primary color
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'fontFamily': 'Inter, sans-serif'
        },
        style_data_conditional=(
            # Data bars using diverging color scale (Power BI style)
            # Bars are 60% width - thinner than full cell
            # Create gradient bars for positive values (green on right side)
            [
                {
                    'if': {
                        'filter_query': f'{{Weekly_Sales_Var_Pct}} >= {i} && {{Weekly_Sales_Var_Pct}} < {i+5}',
                        'column_id': 'Weekly_Sales_Var_Pct'
                    },
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*30}%, white {50 + (i+2.5)/100*30}%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*30}%, #FFB6C1 {50 - (i+2.5)/100*30}%, #FFB6C1 50%, white 50%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*30}%, white {50 + (i+2.5)/100*30}%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*30}%, #FFB6C1 {50 - (i+2.5)/100*30}%, #FFB6C1 50%, white 50%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*30}%, white {50 + (i+2.5)/100*30}%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*30}%, #FFB6C1 {50 - (i+2.5)/100*30}%, #FFB6C1 50%, white 50%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white 50%, #90EE90 50%, #90EE90 {50 + (i+2.5)/100*30}%, white {50 + (i+2.5)/100*30}%)',
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
                    'background': f'linear-gradient(90deg, white 0%, white {50 - (i+2.5)/100*30}%, #FFB6C1 {50 - (i+2.5)/100*30}%, #FFB6C1 50%, white 50%)',
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
        # Table card
        html.Div(
            className="content-card",
            children=[
                # Card header with title and actions
                html.Div(
                    style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'marginBottom': '20px',
                        'paddingBottom': '15px',
                        'borderBottom': '1px solid #E0E0E0'
                    },
                    children=[
                        html.H4(
                            f"FY{fiscal_year} Week {fiscal_week} - Year over Year Comparison",
                            style={'margin': '0', 'color': '#333'}
                        ),
                        html.Div([
                            html.Button(
                                [html.I(className="fas fa-sync-alt", style={'marginRight': '6px'}), "Refresh"],
                                style={
                                    'padding': '6px 12px',
                                    'marginRight': '10px',
                                    'fontSize': '13px',
                                    'backgroundColor': 'white',
                                    'border': '1px solid #E0E0E0',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'transition': 'all 200ms ease'
                                }
                            ),
                            html.Button(
                                [html.I(className="fas fa-cog", style={'marginRight': '6px'}), "Settings"],
                                style={
                                    'padding': '6px 12px',
                                    'marginRight': '10px',
                                    'fontSize': '13px',
                                    'backgroundColor': 'white',
                                    'border': '1px solid #E0E0E0',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'transition': 'all 200ms ease'
                                }
                            ),
                            html.Button(
                                [html.I(className="fas fa-envelope", style={'marginRight': '6px'}), "Email"],
                                style={
                                    'padding': '6px 12px',
                                    'marginRight': '10px',
                                    'fontSize': '13px',
                                    'backgroundColor': 'white',
                                    'border': '1px solid #E0E0E0',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'transition': 'all 200ms ease'
                                }
                            ),
                            html.Button(
                                [html.I(className="fas fa-download", style={'marginRight': '6px'}), "Download"],
                                style={
                                    'padding': '6px 12px',
                                    'fontSize': '13px',
                                    'backgroundColor': 'white',
                                    'border': '1px solid #E0E0E0',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'transition': 'all 200ms ease'
                                }
                            ),
                        ], style={'display': 'flex'})
                    ]
                ),

                # Table
                table
            ]
        )
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
