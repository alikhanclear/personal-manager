"""
Personal Finance Manager - Dash UI

Tabs:
1. Import & Categorize - Upload CSVs, apply rules, run AI categorization
2. Review & Correct - Review AI suggestions, confirm categories, create rules
3. Statistics - View spending analysis and trends
4. Rules - View and manage all categorization rules
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
            # Import & Categorize Tab
            dbc.Tab(label="📥 Import & Categorize", children=[

                # Step 1: Upload
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Step 1: Upload Transactions", className="mb-3"),

                        dcc.Upload(
                            id='upload-csv',
                            children=dbc.Button(
                                ["📤 Upload CSV File"],
                                color="primary",
                                size="lg",
                            ),
                            multiple=False
                        ),

                        html.Div(id='upload-status', className="mt-3"),
                    ])
                ], className="mt-3 mb-3"),

                # Step 2: Apply Rules
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Step 2: Apply Rules (Fast)", className="mb-3"),
                        html.P("Apply rule-based categorization first. This is instant and free.",
                               className="text-muted small"),

                        dbc.Button(
                            "📋 Apply Rules",
                            id="btn-apply-rules",
                            color="success",
                            size="lg",
                            className="me-2",
                        ),

                        html.Div(id='rules-status', className="mt-3"),
                    ])
                ], className="mb-3"),

                # Step 3: Apply AI
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Step 3: Apply AI (Fast!)", className="mb-3"),
                        html.P("Processes 50 transactions per API call. Typically completes in 5-15 seconds.",
                               className="text-muted small"),

                        dbc.Button(
                            "🤖 Start AI Categorization",
                            id="btn-start-ai",
                            color="primary",
                            size="lg",
                            className="mb-3",
                        ),

                        # Status display
                        html.Div(id='ai-status-display', className="mt-3"),
                    ])
                ], className="mb-3"),

                # Quick Status Refresh
                dbc.Card([
                    dbc.CardBody([
                        dbc.Button(
                            "🔄 Refresh Status",
                            id="btn-refresh-import-status",
                            color="secondary",
                            size="sm",
                        ),
                        html.Div(id='import-status-display', className="mt-3"),
                    ])
                ], className="mb-3"),

            ]),

            # Review Tab
            dbc.Tab(label="📋 Review & Correct", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("AI Categorization Review", className="mt-3 mb-3"),
                        html.P("Review categorizations, correct any mistakes, and create rules for future transactions.", className="text-muted"),

                        # Auto-refresh interval (every 5 seconds)
                        dcc.Interval(
                            id='review-refresh-interval',
                            interval=5*1000,  # 5 seconds in milliseconds
                            n_intervals=0
                        ),

                        # Controls
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Show:"),
                                dcc.Dropdown(
                                    id='review-filter',
                                    options=[
                                        {'label': '📋 Rule Matched (Auto-categorized)', 'value': 'rule_matched'},
                                        {'label': '🤖 AI Suggestions (Needs Review)', 'value': 'ai_suggested'},
                                        {'label': '❓ Uncategorized Only', 'value': 'uncategorized'},
                                        {'label': '✓ Confirmed', 'value': 'confirmed'},
                                        {'label': '📊 All Transactions', 'value': 'all'},
                                    ],
                                    value='rule_matched',
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
                                        {'label': '100', 'value': 100},
                                    ],
                                    value=25,
                                    clearable=False,
                                ),
                            ], width=3),
                            dbc.Col([
                                dbc.Button(
                                    "🔄 Refresh",
                                    id="btn-refresh-review",
                                    color="secondary",
                                    size="sm",
                                    className="mt-4",
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
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "🔄 Refresh Statistics",
                            id="btn-refresh-stats",
                            color="secondary",
                            size="sm",
                            className="mt-3 mb-3",
                        ),
                    ], width=12),
                ]),
                html.Div(id='stats-content', className="mt-3"),
            ]),

            # Rules Tab
            dbc.Tab(label="📝 Rules", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Categorization Rules", className="mt-3 mb-3"),
                        html.P("All rules are shown below. Scroll down to see all rules.", className="text-muted"),

                        dbc.Button(
                            "🔄 Refresh Rules",
                            id="btn-refresh-rules",
                            color="secondary",
                            size="sm",
                            className="mb-3",
                        ),

                        # Auto-refresh interval (every 10 seconds)
                        dcc.Interval(
                            id='rules-refresh-interval',
                            interval=10*1000,  # 10 seconds
                            n_intervals=0
                        ),

                        # Rules list
                        html.Div(id='all-rules-list', className="mt-3"),

                    ], width=12),
                ]),
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
    Input('upload-csv', 'contents'),
    State('upload-csv', 'filename'),
)
def handle_csv_upload(contents, filename):
    """Handle CSV file upload."""
    if contents is None:
        raise PreventUpdate

    try:
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

        # Get stats
        stats = db.get_statistics()
        uncategorized = len([t for t in db.get_transactions() if not t.category or t.category == "Uncategorized"])

        return dbc.Alert([
            html.H5("✓ Upload Complete", className="alert-heading"),
            html.Hr(),
            html.P([
                f"📄 File: {filename}",
                html.Br(),
                f"✓ Imported: {inserted} transactions",
                html.Br(),
                f"📊 Total in database: {stats['total_transactions']}",
                html.Br(),
                f"❓ Uncategorized: {uncategorized}",
            ]),
            html.P("👇 Now proceed to Step 2: Apply Rules", className="mb-0 small text-muted"),
        ], color="success")

    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error: {str(e)}",
        ], color="danger")


@callback(
    Output('rules-status', 'children'),
    Input('btn-apply-rules', 'n_clicks'),
    prevent_initial_call=True,
)
def apply_rules(n_clicks):
    """Apply rule-based categorization only (fast)."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Get uncategorized transactions
        all_transactions = db.get_transactions()
        uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

        if len(uncategorized) == 0:
            return dbc.Alert("All transactions are already categorized!", color="info")

        # Get categorizer
        categorizer = get_categorizer()

        # Categorize with rules ONLY (no AI)
        results = categorizer.categorize_batch(uncategorized, use_ai_fallback=False)

        # Save results
        categorizer.save_transaction_categories(results)

        # Calculate remaining
        remaining = results['uncategorized'] + results['ai_categorized']

        return dbc.Alert([
            html.H5("✓ Rules Applied", className="alert-heading"),
            html.Hr(),
            html.P([
                f"📋 {results['rule_matched']} matched by rules (FREE)",
                html.Br(),
                f"❓ {remaining} remaining (need AI)",
            ]),
            html.P("👇 Proceed to Step 3: Apply AI for remaining transactions",
                   className="mb-0 small text-muted") if remaining > 0 else None,
        ], color="success")

    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")


@callback(
    Output('import-status-display', 'children'),
    Input('btn-refresh-import-status', 'n_clicks'),
    prevent_initial_call=True,
)
def refresh_import_status(n_clicks):
    """Refresh and display current database status."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Get current stats
        stats = db.get_statistics()
        all_transactions = db.get_transactions()

        # Count by status
        rule_matched = len([t for t in all_transactions if t.category and t.category != "Uncategorized" and t.category_confidence == 1.0])
        ai_categorized = len([t for t in all_transactions if t.category and t.category != "Uncategorized" and t.category_confidence is not None and t.category_confidence < 1.0])
        uncategorized = len([t for t in all_transactions if not t.category or t.category == "Uncategorized"])

        return dbc.Alert([
            html.H5("📊 Current Status", className="alert-heading"),
            html.Hr(),
            html.P([
                f"📊 Total Transactions: {stats['total_transactions']}",
                html.Br(),
                f"✓ Rule Matched: {rule_matched}",
                html.Br(),
                f"🤖 AI Categorized: {ai_categorized}",
                html.Br(),
                f"❓ Uncategorized: {uncategorized}",
                html.Br(),
                f"📁 Categories: {stats['total_categories']}",
            ]),
        ], color="info")

    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")


@callback(
    Output('ai-status-display', 'children'),
    Input('btn-start-ai', 'n_clicks'),
    prevent_initial_call=True,
)
def run_ai_categorization(n_clicks):
    """Run AI categorization inline (fast with batching!)."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Get uncategorized transactions
        all_transactions = db.get_transactions()
        uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

        if len(uncategorized) == 0:
            return dbc.Alert([
                html.H5("ℹ️ No Work Needed", className="alert-heading"),
                html.P("All transactions are already categorized!"),
            ], color="info")

        # Get categorizer
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return dbc.Alert([
                html.H5("❌ Missing API Key", className="alert-heading"),
                html.P("ANTHROPIC_API_KEY not found in .env file."),
                html.P("Please add your Anthropic API key to continue.", className="small text-muted"),
            ], color="danger")

        categorizer = get_categorizer()

        # Show starting message
        print(f"\n{'='*60}")
        print(f"Starting AI categorization for {len(uncategorized)} transactions...")
        print(f"{'='*60}")

        # Run categorization (with batch processing!)
        import time
        start_time = time.time()

        results = categorizer.categorize_batch(
            uncategorized,
            use_ai_fallback=True,
            ai_batch_size=50  # 50 transactions per API call
        )

        # Save results
        categorizer.save_transaction_categories(results)

        elapsed_secs = time.time() - start_time

        # Return success message
        return dbc.Alert([
            html.H5("✓ AI Categorization Complete!", className="alert-heading"),
            html.Hr(),
            html.P([
                f"⏱️ Completed in {elapsed_secs:.1f} seconds",
                html.Br(),
                f"📋 {results['rule_matched']:,} matched by rules (FREE)",
                html.Br(),
                f"🤖 {results['ai_categorized']:,} categorized by AI",
                html.Br(),
                f"❓ {results['uncategorized']:,} still uncategorized",
                html.Br(),
                f"💰 Estimated cost: ${results['total_cost_usd']:.4f}",
            ]),
            html.P("👉 Go to 'Review & Correct' tab to review AI suggestions",
                   className="mb-0 small text-muted"),
        ], color="success")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"❌ AI Categorization Error:")
        print(error_details)
        print(f"{'='*60}\n")

        return dbc.Alert([
            html.H5("❌ Error During Categorization", className="alert-heading"),
            html.P(str(e)),
            html.Hr(),
            html.P("Check the terminal/console for detailed error information.", className="small text-muted"),
        ], color="danger")


@callback(
    Output('all-rules-list', 'children'),
    Input('rules-refresh-interval', 'n_intervals'),  # Auto-refresh every 10s
    Input('btn-refresh-rules', 'n_clicks'),  # Manual refresh
)
def display_all_rules(n_intervals, n_clicks):
    """Display all categorization rules in a scrollable list."""
    try:
        # Load rules from database
        rules = db.get_rules()

        if len(rules) == 0:
            return dbc.Alert("No rules found. Rules will be created automatically when you confirm transactions and create rules.", color="info")

        # Create table data
        rules_data = []
        for r in sorted(rules, key=lambda x: (-x.priority, x.pattern)):
            # Handle created_at safely
            created_date = "N/A"
            if hasattr(r, 'created_at') and r.created_at:
                try:
                    created_str = str(r.created_at)
                    if 'T' in created_str:
                        created_date = created_str.split('T')[0]
                    elif len(created_str) >= 10:
                        created_date = created_str[:10]
                    else:
                        created_date = created_str
                except:
                    created_date = "N/A"

            rules_data.append({
                'Pattern': r.pattern,
                'Category': r.category_id,
                'Priority': r.priority,
                'Created': created_date,
            })

        rules_df = pd.DataFrame(rules_data)

        # Create table with ALL rows visible (no pagination)
        table = dash_table.DataTable(
            data=rules_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in rules_df.columns],
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': '70vh',  # 70% of viewport height for scrolling
            },
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '14px',
                'minWidth': '120px',
            },
            style_header={
                'backgroundColor': '#343a40',
                'color': 'white',
                'fontWeight': 'bold',
                'position': 'sticky',
                'top': 0,
                'zIndex': 1,
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa',
                }
            ],
            # NO PAGINATION - show all rows
            page_action='none',
            sort_action='native',
            filter_action='native',
        )

        content = html.Div([
            dbc.Alert([
                html.Strong(f"Total Rules: {len(rules)}", className="me-2"),
                html.Span("| Sorted by Priority (High → Low)", className="text-muted small"),
            ], color="light", className="mb-3"),
            table,
            html.P("💡 Tip: You can sort and filter columns by clicking on headers. All rules are shown without pagination.",
                   className="mt-3 small text-muted"),
        ])

        return content

    except Exception as e:
        # Return error message if something goes wrong
        return dbc.Alert([
            html.H5("❌ Error Loading Rules", className="alert-heading"),
            html.P(f"Error: {str(e)}"),
            html.P("Try clicking the Refresh button to reload.", className="small text-muted"),
        ], color="danger")


@callback(
    Output('review-list-container', 'children'),
    Input('review-filter', 'value'),
    Input('review-page-size', 'value'),
    Input('review-refresh-interval', 'n_intervals'),
    Input('btn-refresh-review', 'n_clicks'),
)
def update_review_list(filter_value, page_size, n_intervals, n_clicks):
    """Update the review list of transactions."""
    # Get all transactions
    transactions = db.get_transactions()

    if len(transactions) == 0:
        return dbc.Alert("No transactions found. Import a CSV file first.", color="info")

    # Apply filter
    if filter_value == 'rule_matched':
        # Rule matched: has category, confidence = 1.0 (rules), not confirmed
        filtered = [t for t in transactions if t.category and t.category_confidence == 1.0 and not t.category_confirmed and t.category != "Uncategorized"]
    elif filter_value == 'ai_suggested':
        # AI suggested: has category, confidence < 1.0 (AI), not confirmed
        filtered = [t for t in transactions if t.category and t.category_confidence and t.category_confidence < 1.0 and not t.category_confirmed and t.category != "Uncategorized"]
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

    # Summary with filter description
    filter_descriptions = {
        'rule_matched': '📋 Rule Matched (Auto-categorized)',
        'ai_suggested': '🤖 AI Suggestions (Needs Review)',
        'uncategorized': '❓ Uncategorized',
        'confirmed': '✓ Confirmed',
        'all': '📊 All Transactions',
    }

    summary = html.Div([
        dbc.Alert([
            html.Strong(f"{filter_descriptions.get(filter_value, 'Transactions')}: "),
            f"Showing {len(display_transactions)} of {len(filtered)} total",
        ], color="light", className="mb-3"),
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

    # Update transaction with confidence=1.0 (manually confirmed)
    db.update_transaction_category(txn_id, category, confirmed=True, confidence=1.0)
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

    # Update transaction with confidence=1.0 (manually confirmed)
    db.update_transaction_category(txn_id, category, confirmed=True, confidence=1.0)

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
    Input('stats-content', 'id'),  # Dummy input for initial load
    Input('btn-refresh-stats', 'n_clicks'),  # Manual refresh
)
def update_stats(_, n_clicks):
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
