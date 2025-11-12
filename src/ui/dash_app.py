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
        raw_df = query_all_transactions(db, years=2)  # Reduced to 2 years for 8GB RAM (MVP)

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

            /* Selected cells - light blue instead of orange */
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td.focused,
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td.cell--selected,
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td.active {
                background-color: #E8F4F8 !important;
                border: 1px solid #2C5F7C !important;
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

# Top Header (Simplified - MVP)
header = html.Div(
    className="casualhero-header",
    children=[
        # Left side: Logo and company
        html.Div([
            html.Span("Snowflake Gelato", style={'fontSize': '20px', 'fontWeight': '600', 'color': '#333', 'marginRight': '20px'}),
            html.Span("BI Platform", style={'fontSize': '16px', 'fontWeight': '400', 'color': '#666'}),
        ], style={'display': 'flex', 'alignItems': 'center'}),

        # Right side: Data refresh info
        html.Div([
            html.Div([
                html.I(className="fas fa-database", style={'color': '#666', 'marginRight': '8px'}),
                html.Span("Data refreshed: ", style={'fontSize': '14px', 'color': '#999'}),
                html.Span("Daily at 9:30 AM", style={'fontSize': '14px', 'color': '#666', 'fontWeight': '500'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginRight': '20px'}),
            html.Div([
                html.I(className="fas fa-calendar", style={'color': '#666', 'marginRight': '8px'}),
                html.Span(f"{date.today().strftime('%d %b %Y')}", style={'fontSize': '14px', 'color': '#666', 'fontWeight': '500'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ]
)

# Left Sidebar Navigation (Simplified - MVP)
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
                    [html.I(className="fas fa-chart-line"), html.Span("Weekly Report")],
                    href="/weekly-report",
                    className="nav-item",
                    id="nav-weekly-report"
                ),
                # Monthly Report - Coming soon
                html.Div(
                    [html.I(className="fas fa-calendar-alt"), html.Span("Monthly Report"), html.Span(" (soon)", style={'fontSize': '11px', 'color': '#999', 'marginLeft': '5px'})],
                    className="nav-item",
                    style={'color': '#999', 'cursor': 'default'}
                ),
            ]
        ),

        # Settings
        html.Div(
            className="nav-section",
            children=[
                html.Div("SETTINGS", className="section-title"),
                html.Div(
                    [html.I(className="fas fa-cog"), html.Span("Preferences")],
                    className="nav-item",
                    style={'color': '#999', 'cursor': 'default'}
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
    """Home page layout - Clean MVP style"""
    today = date.today()
    current_fy = get_fiscal_year(today)
    current_week = get_fiscal_week(today)

    return html.Div([
        # Welcome section
        html.Div([
            html.H2("Welcome to Snowflake Gelato BI", style={'marginBottom': '8px', 'color': '#333'}),
            html.P(f"Today is FY{current_fy} Week {current_week}", style={'color': '#666', 'fontSize': '16px', 'marginBottom': '30px'}),
        ]),

        # Quick Stats Cards
        html.Div([
            # Total Orders
            html.Div(
                className="content-card",
                style={'flex': '1', 'marginRight': '20px', 'textAlign': 'center', 'padding': '30px 20px'},
                children=[
                    html.I(className="fas fa-receipt", style={'fontSize': '40px', 'color': ACCENT_COLOR, 'marginBottom': '15px'}),
                    html.H5("Total Orders", style={'color': '#999', 'fontSize': '13px', 'marginBottom': '8px', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                    html.H2(f"{df['Order_Number'].n_unique():,}", style={'color': '#333', 'margin': '0', 'fontFamily': 'Roboto', 'fontSize': '32px'})
                ]
            ),
            # Total Sales
            html.Div(
                className="content-card",
                style={'flex': '1', 'marginRight': '20px', 'textAlign': 'center', 'padding': '30px 20px'},
                children=[
                    html.I(className="fas fa-pound-sign", style={'fontSize': '40px', 'color': '#28a745', 'marginBottom': '15px'}),
                    html.H5("Total Sales", style={'color': '#999', 'fontSize': '13px', 'marginBottom': '8px', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                    html.H2(f"£{df['Order_Net_Sales'].sum():,.0f}", style={'color': '#333', 'margin': '0', 'fontFamily': 'Roboto', 'fontSize': '32px'})
                ]
            ),
            # Establishments
            html.Div(
                className="content-card",
                style={'flex': '1', 'textAlign': 'center', 'padding': '30px 20px'},
                children=[
                    html.I(className="fas fa-store", style={'fontSize': '40px', 'color': PRIMARY_COLOR, 'marginBottom': '15px'}),
                    html.H5("Locations", style={'color': '#999', 'fontSize': '13px', 'marginBottom': '8px', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                    html.H2(f"{df['Establishment'].n_unique()}", style={'color': '#333', 'margin': '0', 'fontFamily': 'Roboto', 'fontSize': '32px'})
                ]
            ),
        ], style={'display': 'flex', 'gap': '0', 'marginBottom': '30px'}),

        # Reports section
        html.Div([
            html.H3("Reports", style={'marginBottom': '20px', 'color': '#333', 'fontSize': '20px'}),

            # Weekly Report card (clickable)
            dcc.Link(
                href='/weekly-report',
                style={'textDecoration': 'none'},
                children=html.Div(
                    className="content-card",
                    style={'cursor': 'pointer', 'marginBottom': '15px'},
                    children=[
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-chart-line", style={'fontSize': '32px', 'color': PRIMARY_COLOR, 'marginRight': '20px'}),
                            ], style={'flex': '0 0 auto'}),
                            html.Div([
                                html.H4("Weekly Report", style={'margin': '0 0 8px 0', 'color': '#333', 'fontSize': '18px'}),
                                html.P("Year-over-year sales comparison, 4W averages, order volumes, and ATV analysis",
                                      style={'margin': '0', 'color': '#666', 'fontSize': '14px', 'lineHeight': '1.5'}),
                            ], style={'flex': '1'}),
                            html.I(className="fas fa-arrow-right", style={'fontSize': '20px', 'color': '#CCC'}),
                        ], style={'display': 'flex', 'alignItems': 'center'}),
                    ]
                )
            ),

            # Monthly Report card (disabled)
            html.Div(
                className="content-card",
                style={'opacity': '0.5', 'cursor': 'not-allowed'},
                children=[
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-calendar-alt", style={'fontSize': '32px', 'color': '#999', 'marginRight': '20px'}),
                        ], style={'flex': '0 0 auto'}),
                        html.Div([
                            html.H4(["Monthly Report ", html.Span("(Coming Soon)", style={'fontSize': '14px', 'color': '#999', 'fontWeight': 'normal'})],
                                   style={'margin': '0 0 8px 0', 'color': '#999', 'fontSize': '18px'}),
                            html.P("Monthly performance analysis with trends and comparisons",
                                  style={'margin': '0', 'color': '#999', 'fontSize': '14px', 'lineHeight': '1.5'}),
                        ], style={'flex': '1'}),
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                ]
            ),
        ]),
    ])


def weekly_report_layout():
    """Weekly Report page layout - Clean MVP style"""
    # Get available fiscal years and weeks
    available_years = sorted(df['Fiscal_Year'].unique().to_list(), reverse=True)
    current_fy = available_years[0] if available_years else 2026

    available_weeks = sorted(
        df.filter(pl.col('Fiscal_Year') == current_fy)['Fiscal_Week'].unique().to_list()
    )
    current_week = available_weeks[-1] if available_weeks else 1

    return html.Div([
        # Page header with title and description
        html.Div([
            html.H2("Weekly Report", style={'marginBottom': '5px', 'color': '#333'}),
            html.P("Year-over-year sales comparison with variance analysis", style={'color': '#666', 'fontSize': '14px', 'marginBottom': '25px'}),
        ]),

        # Filters card (Clean style)
        html.Div(
            className="filters-bar",
            children=[
                html.Div([
                    # Fiscal Year selector
                    html.Div([
                        html.Label("Fiscal Year", style={'fontSize': '13px', 'fontWeight': '500', 'color': '#666', 'marginBottom': '5px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='fiscal-year-dropdown',
                            options=[{'label': f'FY{year}', 'value': year} for year in available_years],
                            value=current_fy,
                            clearable=False,
                            style={'width': '120px'}
                        ),
                    ], style={'marginRight': '20px'}),

                    # Week selector
                    html.Div([
                        html.Label("Week", style={'fontSize': '13px', 'fontWeight': '500', 'color': '#666', 'marginBottom': '5px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='fiscal-week-dropdown',
                            options=[{'label': f'Week {week}', 'value': week} for week in available_weeks],
                            value=current_week,
                            clearable=False,
                            style={'width': '120px'}
                        ),
                    ]),
                ], style={'display': 'flex', 'alignItems': 'flex-end'}),
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
    """Route pages based on URL (Simplified MVP structure)"""
    if pathname == '/weekly-report':
        return weekly_report_layout()
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

    try:
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
            # Variance percentages - convert to percentage (handle None/null properly)
            pl.when(pl.col('Weekly_Sales_Var_Pct').is_null())
            .then(None)
            .otherwise(pl.col('Weekly_Sales_Var_Pct') * 100)
            .alias('Weekly_Sales_Var_Pct'),

            pl.when(pl.col('FourWeek_Avg_Var_Pct').is_null())
            .then(None)
            .otherwise(pl.col('FourWeek_Avg_Var_Pct') * 100)
            .alias('FourWeek_Avg_Var_Pct'),

            pl.when(pl.col('Volume_Var_Pct').is_null())
            .then(None)
            .otherwise(pl.col('Volume_Var_Pct') * 100)
            .alias('Volume_Var_Pct'),

            pl.when(pl.col('ATV_Var_Pct').is_null())
            .then(None)
            .otherwise(pl.col('ATV_Var_Pct') * 100)
            .alias('ATV_Var_Pct'),
        ])

        # Convert to pandas for DataTable
        df_pandas = formatted_report.to_pandas()

        # First, identify which cells should hide variance (before converting to blanks)
        numeric_cols = ['Current_Year_Sales', 'Last_Year_Sales', 'Current_Year_4W_Avg', 'Last_Year_4W_Avg',
                        'Current_Year_Vol', 'Last_Year_Vol', 'Current_Year_ATV', 'Last_Year_ATV']

        variance_mapping = {
            'Weekly_Sales_Var_Pct': ('Current_Year_Sales', 'Last_Year_Sales'),
            'FourWeek_Avg_Var_Pct': ('Current_Year_4W_Avg', 'Last_Year_4W_Avg'),
            'Volume_Var_Pct': ('Current_Year_Vol', 'Last_Year_Vol'),
            'ATV_Var_Pct': ('Current_Year_ATV', 'Last_Year_ATV')
        }

        # Set variance to None where either current or last year is 0/null (BEFORE converting to blanks)
        for var_col, (current_col, last_col) in variance_mapping.items():
            mask = (df_pandas[current_col] == 0) | (df_pandas[last_col] == 0) | \
                   df_pandas[current_col].isna() | df_pandas[last_col].isna()
            df_pandas.loc[mask, var_col] = None

        # Now replace 0 values with blank for display
        for col in numeric_cols:
            df_pandas[col] = df_pandas[col].replace(0, '')

        # Group company names - show company only on first row of each group
        # and indent establishment names
        prev_company = None
        for idx in df_pandas.index:
            current_company = df_pandas.loc[idx, 'Company']

            # Indent establishment name
            df_pandas.loc[idx, 'Establishment'] = '    ' + df_pandas.loc[idx, 'Establishment']

            # Blank out company name if same as previous row
            if current_company == prev_company:
                df_pandas.loc[idx, 'Company'] = ''
            prev_company = current_company

        # Calculate max absolute value for each variance column (for relative bar scaling)
        # This makes bars "pop" more by scaling to the actual data range
        # For diverging bars: center=0, scale by max absolute value
        variance_scales = {}
        for var_col in variance_mapping.keys():
            valid_values = df_pandas[var_col].dropna()
            if len(valid_values) > 0:
                max_abs = valid_values.abs().max()
                # Handle edge case where all values are zero
                if max_abs == 0:
                    max_abs = 5  # Default scale
                variance_scales[var_col] = max_abs
            else:
                variance_scales[var_col] = 1

        # Create scaled columns (-100 to +100) for bar widths
        # Scale based on max absolute value so bars fill more of the cell
        # Multiply by 2 to make bars even more prominent (50% width at max value)
        for var_col in variance_mapping.keys():
            max_abs = variance_scales[var_col]
            df_pandas[f'{var_col}_Scaled'] = df_pandas[var_col].apply(
                lambda x: (x / max_abs * 100 * 2) if pd.notna(x) else None  # *2 makes bars larger
            )

        # Create display columns for variance percentages with bracket notation for negatives
        # Don't show variance or bars if variance is None (already handled above)
        for var_col, (current_col, last_col) in variance_mapping.items():
            df_pandas[f'{var_col}_Display'] = df_pandas.apply(
                lambda row: '' if (row[current_col] == '' or row[last_col] == '' or pd.isna(row[var_col]))
                            else (f'({abs(row[var_col]):.2f})' if row[var_col] < 0 else f'{row[var_col]:.2f}'),
                axis=1
            )

        # Create DataTable with conditional formatting
        table = dash_table.DataTable(
            data=df_pandas.to_dict('records'),
            columns=[
                {'name': 'Company', 'id': 'Company'},
                {'name': 'Establishment', 'id': 'Establishment'},
                {'name': 'Current Year Sales', 'id': 'Current_Year_Sales', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': 'Last Year Sales', 'id': 'Last_Year_Sales', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': 'Sales Var %', 'id': 'Weekly_Sales_Var_Pct_Display', 'type': 'text'},
                {'name': 'Current 4W Avg', 'id': 'Current_Year_4W_Avg', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': 'Last 4W Avg', 'id': 'Last_Year_4W_Avg', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': '4W Avg Var %', 'id': 'FourWeek_Avg_Var_Pct_Display', 'type': 'text'},
                {'name': 'Current Vol', 'id': 'Current_Year_Vol', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': 'Last Vol', 'id': 'Last_Year_Vol', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': 'Vol Var %', 'id': 'Volume_Var_Pct_Display', 'type': 'text'},
                {'name': 'Current ATV', 'id': 'Current_Year_ATV', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'Last ATV', 'id': 'Last_Year_ATV', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'ATV Var %', 'id': 'ATV_Var_Pct_Display', 'type': 'text'},
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '12px'
            },
            style_header={
                'color': '#000000',  # Black text
                'fontWeight': 'bold',
                'textAlign': 'center',
                'fontFamily': 'Inter, sans-serif'
            },
            style_data_conditional=(
                # Data bars using diverging color scale (Power BI style)
                # Bars are 41% height, centered vertically, text right-aligned
                # Green bars: #00B050 (positive variance), Red bars: #FF0000 (negative variance)
                # Text color: Black for all values
                # SCALED values: bars fill more of cell based on relative range in column
                # Create gradient bars for positive values (green on right side)
                [
                    {
                        'if': {
                            'filter_query': f'{{Weekly_Sales_Var_Pct_Scaled}} >= {i} && {{Weekly_Sales_Var_Pct_Scaled}} < {i+10}',
                            'column_id': 'Weekly_Sales_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white 50%, #00B050 50%, #00B050 {50 + (i+5)*0.5}%, white {50 + (i+5)*0.5}%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                # Negative values (red on left side)
                [
                    {
                        'if': {
                            'filter_query': f'{{Weekly_Sales_Var_Pct_Scaled}} >= {-i-10} && {{Weekly_Sales_Var_Pct_Scaled}} < {-i}',
                            'column_id': 'Weekly_Sales_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white {50 - (i+5)*0.5}%, #FF0000 {50 - (i+5)*0.5}%, #FF0000 50%, white 50%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                # FourWeek_Avg variance (scaled)
                [
                    {
                        'if': {
                            'filter_query': f'{{FourWeek_Avg_Var_Pct_Scaled}} >= {i} && {{FourWeek_Avg_Var_Pct_Scaled}} < {i+10}',
                            'column_id': 'FourWeek_Avg_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white 50%, #00B050 50%, #00B050 {50 + (i+5)*0.5}%, white {50 + (i+5)*0.5}%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                [
                    {
                        'if': {
                            'filter_query': f'{{FourWeek_Avg_Var_Pct_Scaled}} >= {-i-10} && {{FourWeek_Avg_Var_Pct_Scaled}} < {-i}',
                            'column_id': 'FourWeek_Avg_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white {50 - (i+5)*0.5}%, #FF0000 {50 - (i+5)*0.5}%, #FF0000 50%, white 50%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                # Volume variance (scaled)
                [
                    {
                        'if': {
                            'filter_query': f'{{Volume_Var_Pct_Scaled}} >= {i} && {{Volume_Var_Pct_Scaled}} < {i+10}',
                            'column_id': 'Volume_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white 50%, #00B050 50%, #00B050 {50 + (i+5)*0.5}%, white {50 + (i+5)*0.5}%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                [
                    {
                        'if': {
                            'filter_query': f'{{Volume_Var_Pct_Scaled}} >= {-i-10} && {{Volume_Var_Pct_Scaled}} < {-i}',
                            'column_id': 'Volume_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white {50 - (i+5)*0.5}%, #FF0000 {50 - (i+5)*0.5}%, #FF0000 50%, white 50%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                # ATV variance (scaled)
                [
                    {
                        'if': {
                            'filter_query': f'{{ATV_Var_Pct_Scaled}} >= {i} && {{ATV_Var_Pct_Scaled}} < {i+10}',
                            'column_id': 'ATV_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white 50%, #00B050 50%, #00B050 {50 + (i+5)*0.5}%, white {50 + (i+5)*0.5}%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                [
                    {
                        'if': {
                            'filter_query': f'{{ATV_Var_Pct_Scaled}} >= {-i-10} && {{ATV_Var_Pct_Scaled}} < {-i}',
                            'column_id': 'ATV_Var_Pct_Display'
                        },
                        'background': f'linear-gradient(to top, white 0%, white 29.5%, transparent 29.5%, transparent 70.5%, white 70.5%, white 100%), linear-gradient(90deg, white 0%, white {50 - (i+5)*0.5}%, #FF0000 {50 - (i+5)*0.5}%, #FF0000 50%, white 50%)',
                        'color': '#000000',
                        'fontWeight': 'bold',
                        'textAlign': 'right'
                    }
                    for i in range(0, 200, 10)
                ] +
                # Override rules: Remove ALL bars when display value is blank OR variance is 0
                # These come last so they override any bar styling above
                [
                    {
                        'if': {
                            'filter_query': '{Weekly_Sales_Var_Pct_Display} = ""',
                            'column_id': 'Weekly_Sales_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{Weekly_Sales_Var_Pct} is blank',
                            'column_id': 'Weekly_Sales_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{FourWeek_Avg_Var_Pct_Display} = ""',
                            'column_id': 'FourWeek_Avg_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{FourWeek_Avg_Var_Pct} is blank',
                            'column_id': 'FourWeek_Avg_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{Volume_Var_Pct_Display} = ""',
                            'column_id': 'Volume_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{Volume_Var_Pct} is blank',
                            'column_id': 'Volume_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{ATV_Var_Pct_Display} = ""',
                            'column_id': 'ATV_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
                    {
                        'if': {
                            'filter_query': '{ATV_Var_Pct} is blank',
                            'column_id': 'ATV_Var_Pct_Display'
                        },
                        'background': 'white',
                        'color': '#000000',
                        'textAlign': 'right'
                    },
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

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in update_weekly_report: {error_trace}")
        return html.Div([
            html.H4("Error generating report", style={'color': 'red'}),
            html.P(f"Error: {str(e)}"),
            html.Pre(error_trace, style={'fontSize': '10px', 'backgroundColor': '#f5f5f5', 'padding': '10px'})
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
