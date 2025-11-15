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
                # Step 1: Upload CSV
                dbc.Row([
                    dbc.Col([
                        html.H4("Step 1: Upload CSV File", className="mt-3 mb-3"),

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

                    ], width=12),
                ]),

                html.Hr(className="my-4"),

                # Step 2: Categorize
                dbc.Row([
                    dbc.Col([
                        html.H4("Step 2: Categorize Transactions", className="mb-3"),
                        html.P("After uploading, click below to categorize your transactions using rules and AI.", className="text-muted"),

                        dbc.Button(
                            "🔄 Categorize Imported Transactions",
                            id="btn-categorize",
                            color="success",
                            size="lg",
                            className="mt-2 mb-3",
                            disabled=True,
                        ),

                        html.Div(id='categorization-status', className="mt-3"),

                    ], width=12),
                ]),
            ]),

            # Review Tab
            dbc.Tab(label="📋 Review & Correct", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("AI Categorization Review", className="mt-3 mb-3"),
                        html.P("Review AI suggestions, correct any mistakes, and create rules for future transactions.", className="text-muted"),

                        # Controls
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Show:"),
                                dcc.Dropdown(
                                    id='review-filter',
                                    options=[
                                        {'label': '⚠️ Needs Review (AI suggestions)', 'value': 'needs_review'},
                                        {'label': '❓ Uncategorized Only', 'value': 'uncategorized'},
                                        {'label': '✓ Confirmed', 'value': 'confirmed'},
                                        {'label': '📋 All Transactions', 'value': 'all'},
                                    ],
                                    value='needs_review',
                                    clearable=False,
                                ),
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Items per page:"),
                                dcc.Dropdown(
                                    id='review-page-size',
                                    options=[
                                        {'label': '10', 'value': 10},
                                        {'label': '25', 'value': 25},
                                        {'label': '50', 'value': 50},
                                    ],
                                    value=10,
                                    clearable=False,
                                ),
                            ], width=3),
                        ], className="mb-4"),

                        # Transaction review list
                        html.Div(id='review-list-container'),

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
    Output('review-list-container', 'children'),
    Input('review-filter', 'value'),
    Input('review-page-size', 'value'),
)
def update_review_list(filter_value, page_size):
    """Update the review list of transactions."""
    # Get all transactions
    transactions = db.get_transactions()

    if len(transactions) == 0:
        return dbc.Alert("No transactions found. Import a CSV file first.", color="info")

    # Apply filter
    if filter_value == 'needs_review':
        filtered = [t for t in transactions if t.category and not t.category_confirmed and t.category != "Uncategorized"]
    elif filter_value == 'uncategorized':
        filtered = [t for t in transactions if not t.category or t.category == "Uncategorized"]
    elif filter_value == 'confirmed':
        filtered = [t for t in transactions if t.category_confirmed]
    else:  # all
        filtered = transactions

    if len(filtered) == 0:
        return dbc.Alert(f"No transactions match filter: {filter_value}", color="info")

    # Limit to page size
    display_transactions = filtered[:page_size]

    # Get all categories for dropdown
    categories = db.get_categories()
    category_options = [{'label': f"{cat.icon} {cat.name}", 'value': cat.name} for cat in sorted(categories, key=lambda x: x.name)]

    # Build cards for each transaction
    cards = []
    for txn in display_transactions:
        # Confidence badge
        if txn.category_confidence:
            conf_pct = int(txn.category_confidence * 100)
            if conf_pct >= 90:
                conf_color = "success"
            elif conf_pct >= 70:
                conf_color = "warning"
            else:
                conf_color = "danger"
            confidence_badge = dbc.Badge(f"{conf_pct}% confidence", color=conf_color, className="ms-2")
        else:
            confidence_badge = None

        # Amount color
        amount_color = "danger" if txn.amount < 0 else "success"

        card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Left: Transaction details
                    dbc.Col([
                        html.H6(txn.description[:60], className="mb-2"),
                        html.Small([
                            html.Span(f"{txn.date.strftime('%d %b %Y')}", className="text-muted me-3"),
                            html.Span(f"£{txn.amount:,.2f}", className=f"text-{amount_color} fw-bold me-3"),
                            html.Span(f"{txn.account_name}", className="text-muted"),
                        ]),
                    ], width=12, lg=6),

                    # Right: Category selection
                    dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Category:", className="small text-muted mb-1"),
                                dcc.Dropdown(
                                    id={'type': 'category-dropdown', 'index': txn.id},
                                    options=category_options,
                                    value=txn.category,
                                    clearable=False,
                                    className="mb-2",
                                ),
                                html.Div([
                                    html.Small(f"AI suggested: {txn.category}", className="text-muted") if txn.category else None,
                                    confidence_badge,
                                ]) if not txn.category_confirmed else html.Small("✓ Confirmed", className="text-success"),
                            ], width=12),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "✓ Confirm",
                                    id={'type': 'confirm-btn', 'index': txn.id},
                                    color="primary",
                                    size="sm",
                                    className="me-2",
                                ),
                                dbc.Button(
                                    "✓ Confirm & Create Rule",
                                    id={'type': 'confirm-rule-btn', 'index': txn.id},
                                    color="success",
                                    size="sm",
                                ),
                            ], width=12),
                        ], className="mt-2"),
                    ], width=12, lg=6),
                ]),
            ])
        ], className="mb-3")

        cards.append(card)

    # Summary
    summary = html.Div([
        html.P(f"Showing {len(display_transactions)} of {len(filtered)} transactions", className="text-muted mb-3"),
    ])

    return [summary] + cards


@callback(
    Output({'type': 'confirm-btn', 'index': ALL}, 'disabled'),
    Input({'type': 'confirm-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'category-dropdown', 'index': ALL}, 'value'),
    State({'type': 'confirm-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def confirm_category(n_clicks_list, category_list, id_list):
    """Confirm category for a transaction."""
    if not any(n_clicks_list):
        raise PreventUpdate

    # Find which button was clicked
    clicked_idx = next((i for i, n in enumerate(n_clicks_list) if n), None)
    if clicked_idx is None:
        raise PreventUpdate

    txn_id = id_list[clicked_idx]['index']
    category = category_list[clicked_idx]

    # Update transaction
    db.update_transaction_category(txn_id, category, confirmed=True)
    print(f"[Review] Confirmed: {txn_id} → {category}")

    # Return disabled state (no changes needed, page will refresh)
    return [False] * len(n_clicks_list)


@callback(
    Output({'type': 'confirm-rule-btn', 'index': ALL}, 'disabled'),
    Input({'type': 'confirm-rule-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'category-dropdown', 'index': ALL}, 'value'),
    State({'type': 'confirm-rule-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def confirm_and_create_rule(n_clicks_list, category_list, id_list):
    """Confirm category and create a rule for future transactions."""
    if not any(n_clicks_list):
        raise PreventUpdate

    # Find which button was clicked
    clicked_idx = next((i for i, n in enumerate(n_clicks_list) if n), None)
    if clicked_idx is None:
        raise PreventUpdate

    txn_id = id_list[clicked_idx]['index']
    category = category_list[clicked_idx]

    # Get transaction to extract pattern
    txn = db.get_transaction(txn_id)
    if not txn:
        raise PreventUpdate

    # Update transaction
    db.update_transaction_category(txn_id, category, confirmed=True)

    # Create rule from transaction description
    categorizer = get_categorizer()
    suggested_rule = categorizer.suggest_rule_from_transaction(txn, category)

    # Add rule to database
    try:
        db.insert_rule(suggested_rule)
        print(f"[Review] Confirmed + Rule created: '{suggested_rule.pattern}' → {category}")
    except Exception as e:
        print(f"[Review] Failed to create rule: {e}")

    # Return disabled state (no changes needed, page will refresh)
    return [False] * len(n_clicks_list)


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
