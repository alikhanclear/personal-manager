"""
Personal Finance Manager - Dash UI

Simple, clean interface for:
- CSV import (NatWest format)
- Transaction categorization (rules + AI)
- Manual review and correction
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import base64
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback, ALL, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import polars as pl
import pandas as pd

from src.data.database import FinanceDatabase
from src.data.csv_parser import NatWestParser
from src.data.importer import TransactionImporter
from src.data.models import Category, Transaction
from src.core.categorizer import HybridCategorizer
from src.core.rule_engine import create_default_rules
from config.default_categories import DEFAULT_CATEGORIES


# ============================================================================
# Configuration
# ============================================================================

DB_PATH = Path(__file__).parent / "data" / "finance.db"
DB_PATH.parent.mkdir(exist_ok=True)

# Initialize database
db = FinanceDatabase(DB_PATH)

# Global state
APP_STATE = {
    "categorizer": None,
    "transactions": [],
    "uncategorized_count": 0,
}


# ============================================================================
# Initialize App
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.title = "Personal Finance Manager"


# ============================================================================
# Helper Functions
# ============================================================================

def initialize_categories_and_rules():
    """Initialize categories and default rules if database is empty."""
    categories = db.get_categories()

    if len(categories) == 0:
        print("Initializing categories and rules...")

        # Add categories
        category_map = {}
        for name, parent_name, color, icon, budget in DEFAULT_CATEGORIES:
            parent_id = category_map.get(parent_name) if parent_name else None
            category = Category(
                name=name,
                parent_id=parent_id,
                color=color,
                icon=icon,
                budget_monthly=budget,
            )
            db.insert_category(category)
            category_map[name] = category.name

        # Add default rules
        rules = create_default_rules(category_map)
        for rule in rules:
            db.insert_rule(rule)

        print(f"✓ Created {len(category_map)} categories and {len(rules)} rules")

    return db.get_categories()


def get_categorizer():
    """Get or create categorizer instance."""
    # Ensure categories and rules are initialized
    initialize_categories_and_rules()

    if APP_STATE["categorizer"] is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        APP_STATE["categorizer"] = HybridCategorizer(
            db,
            ai_api_key=api_key,
            enable_ai=bool(api_key)
        )
    return APP_STATE["categorizer"]


# ============================================================================
# Layout
# ============================================================================

def create_layout():
    """Create main application layout."""

    # Initialize categories
    initialize_categories_and_rules()

    # Get stats
    stats = db.get_statistics()

    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("💰 Personal Finance Manager", className="mb-0"),
                html.P("Import, categorize, and analyze your transactions",
                       className="text-muted mb-0"),
            ], width=8),
            dbc.Col([
                html.Div([
                    html.Small("Total Transactions", className="d-block text-muted"),
                    html.H3(f"{stats['total_transactions']:,}", className="mb-0"),
                ], className="text-end"),
            ], width=4),
        ], className="mb-4 mt-3"),

        html.Hr(),

        # Tabs
        dbc.Tabs([
            # Import Tab
            dbc.Tab(label="📥 Import", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Upload CSV File", className="mt-3 mb-3"),

                        dcc.Upload(
                            id='upload-csv',
                            children=html.Div([
                                html.I(className="fas fa-cloud-upload-alt fa-3x mb-2"),
                                html.Br(),
                                'Drag and Drop or ',
                                html.A('Select NatWest CSV File')
                            ]),
                            style={
                                'width': '100%',
                                'height': '200px',
                                'lineHeight': '200px',
                                'borderWidth': '2px',
                                'borderStyle': 'dashed',
                                'borderRadius': '10px',
                                'textAlign': 'center',
                                'backgroundColor': '#f8f9fa',
                            },
                            multiple=False
                        ),

                        html.Div(id='upload-status', className="mt-3"),

                        html.Div([
                            dbc.Button(
                                "Categorize Imported Transactions",
                                id="btn-categorize",
                                color="primary",
                                className="mt-3",
                                disabled=True,
                            ),
                        ]),

                        html.Div(id='categorization-status', className="mt-3"),

                    ], width=12),
                ]),
            ]),

            # Review Tab
            dbc.Tab(label="📋 Review", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Transaction Review", className="mt-3 mb-3"),

                        # Filters
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Filter by Category"),
                                dcc.Dropdown(
                                    id='filter-category',
                                    options=[{'label': 'All Categories', 'value': 'all'}],
                                    value='all',
                                    clearable=False,
                                ),
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Filter by Status"),
                                dcc.Dropdown(
                                    id='filter-status',
                                    options=[
                                        {'label': 'All', 'value': 'all'},
                                        {'label': 'Needs Review', 'value': 'unconfirmed'},
                                        {'label': 'Confirmed', 'value': 'confirmed'},
                                        {'label': 'Uncategorized', 'value': 'uncategorized'},
                                    ],
                                    value='unconfirmed',
                                    clearable=False,
                                ),
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Search"),
                                dbc.Input(
                                    id='search-text',
                                    type='text',
                                    placeholder='Search description...',
                                ),
                            ], width=4),
                        ], className="mb-3"),

                        # Transaction table
                        html.Div(id='transaction-table-container'),

                    ], width=12),
                ]),
            ]),

            # Stats Tab
            dbc.Tab(label="📊 Statistics", children=[
                html.Div(id='stats-content', className="mt-3"),
            ]),
        ]),

        # Footer
        html.Hr(className="mt-5"),
        html.Div([
            html.Small([
                f"Database: {DB_PATH.name} | ",
                html.Span(id='footer-stats'),
            ], className="text-muted"),
        ], className="text-center mb-3"),

    ], fluid=True)


app.layout = create_layout


# ============================================================================
# Callbacks
# ============================================================================

@callback(
    Output('upload-status', 'children'),
    Output('btn-categorize', 'disabled'),
    Input('upload-csv', 'contents'),
    State('upload-csv', 'filename'),
)
def handle_csv_upload(contents, filename):
    """Handle CSV file upload."""
    print(f"[DEBUG] Upload callback triggered. filename={filename}")

    if contents is None:
        raise PreventUpdate

    try:
        print(f"[DEBUG] Processing upload...")
        # Parse uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Save to temp file
        temp_file = Path(__file__).parent / "data" / "temp_upload.csv"
        temp_file.write_bytes(decoded)

        # Parse and import
        parser = NatWestParser()
        transactions = parser.parse_file(temp_file)

        # Import to database
        importer = TransactionImporter(db)
        inserted = db.insert_transactions_bulk(transactions)

        # Clean up
        temp_file.unlink()

        return (
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully imported {inserted} transactions from {filename}",
            ], color="success"),
            False  # Enable categorize button
        )

    except Exception as e:
        return (
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error: {str(e)}",
            ], color="danger"),
            True  # Keep button disabled
        )


@callback(
    Output('categorization-status', 'children'),
    Input('btn-categorize', 'n_clicks'),
    prevent_initial_call=True,
)
def categorize_transactions(n_clicks):
    """Categorize imported transactions."""
    print(f"[DEBUG] Categorize button clicked! n_clicks={n_clicks}")

    if n_clicks is None:
        print("[DEBUG] n_clicks is None, preventing update")
        raise PreventUpdate

    try:
        print("[DEBUG] Starting categorization...")
        # Get all transactions
        all_transactions = db.get_transactions()
        print(f"[Categorization] Total transactions in DB: {len(all_transactions)}")

        # Get uncategorized transactions
        uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]
        print(f"[Categorization] Uncategorized: {len(uncategorized)}")

        if len(uncategorized) == 0:
            if len(all_transactions) == 0:
                return dbc.Alert("No transactions found in database. Please import a CSV file first.", color="warning")
            else:
                return dbc.Alert("All transactions are already categorized!", color="info")

        # Get categorizer (this also initializes categories and rules)
        categorizer = get_categorizer()

        # Check rules and categories
        stats = categorizer.get_statistics()
        print(f"[Categorization] Rules: {stats['total_rules']}, Categories: {stats['total_categories']}")

        # Categorize
        print(f"[Categorization] Starting categorization of {len(uncategorized)} transactions...")
        results = categorizer.categorize_batch(uncategorized, use_ai_fallback=True)
        print(f"[Categorization] Results: {results['rule_matched']} rules, {results['ai_categorized']} AI, {results['uncategorized']} uncategorized")

        # Save results
        categorizer.save_transaction_categories(results)

        # Build status message
        rule_count = results['rule_matched']
        ai_count = results['ai_categorized']
        uncategorized_count = results['uncategorized']
        cost = results['total_cost_usd']

        APP_STATE["uncategorized_count"] = uncategorized_count

        return dbc.Alert([
            html.H5("✓ Categorization Complete", className="alert-heading"),
            html.Hr(),
            html.P([
                f"📋 {rule_count} matched by rules (FREE)",
                html.Br(),
                f"🤖 {ai_count} categorized by AI (${cost:.4f})",
                html.Br(),
                f"❓ {uncategorized_count} still uncategorized",
            ]),
        ], color="success")

    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")


@callback(
    Output('transaction-table-container', 'children'),
    Input('filter-category', 'value'),
    Input('filter-status', 'value'),
    Input('search-text', 'value'),
)
def update_transaction_table(category_filter, status_filter, search_text):
    """Update transaction table based on filters."""

    # Get all transactions
    transactions = db.get_transactions()

    if len(transactions) == 0:
        return dbc.Alert("No transactions found. Import a CSV file to get started.", color="info")

    # Apply filters
    filtered = transactions

    if status_filter == 'unconfirmed':
        filtered = [t for t in filtered if not t.category_confirmed]
    elif status_filter == 'confirmed':
        filtered = [t for t in filtered if t.category_confirmed]
    elif status_filter == 'uncategorized':
        filtered = [t for t in filtered if not t.category or t.category == "Uncategorized"]

    if category_filter and category_filter != 'all':
        filtered = [t for t in filtered if t.category == category_filter]

    if search_text:
        search_lower = search_text.lower()
        filtered = [t for t in filtered if search_lower in t.description.lower()]

    # Convert to DataFrame
    data = []
    for t in filtered:
        data.append({
            'Date': t.date.isoformat(),
            'Description': t.description,
            'Amount': f"£{t.amount:,.2f}",
            'Category': t.category or "Uncategorized",
            'Confidence': f"{(t.category_confidence or 0)*100:.0f}%" if t.category_confidence else "N/A",
            'Confirmed': '✓' if t.category_confirmed else '✗',
            'Account': t.account_name,
        })

    if len(data) == 0:
        return dbc.Alert("No transactions match the current filters.", color="info")

    df = pd.DataFrame(data)

    # Create table
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'system-ui',
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'borderBottom': '2px solid #dee2e6',
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Amount', 'filter_query': '{Amount} contains "-"'},
                'color': '#dc3545',
            },
            {
                'if': {'column_id': 'Confirmed', 'filter_query': '{Confirmed} eq "✓"'},
                'color': '#28a745',
            },
        ],
        page_size=20,
        sort_action='native',
        filter_action='native',
    )

    return html.Div([
        html.P(f"Showing {len(filtered):,} of {len(transactions):,} transactions"),
        table,
    ])


@callback(
    Output('filter-category', 'options'),
    Input('filter-category', 'value'),  # Dummy input to trigger
)
def update_category_dropdown(_):
    """Update category dropdown with available categories."""
    categories = db.get_categories()
    options = [{'label': 'All Categories', 'value': 'all'}]

    # Get top-level categories only
    top_level = [c for c in categories if c.parent_id is None]
    for cat in sorted(top_level, key=lambda x: x.name):
        options.append({'label': f"{cat.icon} {cat.name}", 'value': cat.name})

    return options


@callback(
    Output('stats-content', 'children'),
    Input('stats-content', 'id'),  # Dummy input
)
def update_stats(_):
    """Update statistics page."""
    stats = db.get_statistics()
    categorizer = get_categorizer()
    cat_stats = categorizer.get_statistics()

    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{stats['total_transactions']:,}", className="text-primary"),
                    html.P("Total Transactions"),
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{stats['total_categories']}", className="text-success"),
                    html.P("Categories"),
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{cat_stats['total_rules']}", className="text-info"),
                    html.P("Active Rules"),
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{cat_stats['rule_coverage_percent']:.1f}%", className="text-warning"),
                    html.P("Rule Coverage"),
                ])
            ])
        ], width=3),
    ])


@callback(
    Output('footer-stats', 'children'),
    Input('footer-stats', 'id'),  # Dummy input
)
def update_footer(_):
    """Update footer statistics."""
    stats = db.get_statistics()
    return f"{stats['total_transactions']:,} transactions | {stats['total_categories']} categories"


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("Personal Finance Manager")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print(f"Server: http://localhost:8050/")
    print("=" * 80)

    app.run(debug=True, host='0.0.0.0', port=8050)
