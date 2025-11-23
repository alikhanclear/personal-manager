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

# Custom CSS to fix DataTable dropdown rendering issues
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Fix for DataTable dropdown menus being clipped */
            .dash-table-container {
                overflow: visible !important;
            }
            .dash-table-container .dash-spreadsheet-container {
                overflow: visible !important;
                max-height: none !important;
            }
            .dash-table-container .dash-spreadsheet {
                overflow: visible !important;
            }
            .dash-table-container .dash-spreadsheet-inner {
                overflow: visible !important;
            }
            /* Force dropdown menus to appear above everything */
            .Select-menu-outer {
                z-index: 9999 !important;
                position: absolute !important;
            }
            /* Alternative dropdown class */
            .dash-dropdown {
                z-index: 9999 !important;
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
            category_map[name] = category.id

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
        api_key = os.getenv("APP_ANTHROPIC_API_KEY")
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
                        html.P("Processes 30 transactions per API call. Typically completes in 5-15 seconds.",
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

                        # Clear refresh instruction
                        dbc.Alert([
                            html.Strong("💡 Important: "),
                            "This table does NOT auto-refresh. After uploading transactions, applying rules, or running AI categorization, ",
                            html.Strong("click the '🔄 Refresh' button below"),
                            " to see the latest data. Your checkbox selections will be preserved across pages.",
                        ], color="info", dismissable=True, className="mb-3"),

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
                                    value='ai_suggested',
                                    clearable=False,
                                ),
                            ], width=4),
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
                                    value=50,
                                    clearable=False,
                                ),
                            ], width=2),
                            dbc.Col([
                                dbc.Button(
                                    "🔄 Refresh",
                                    id="btn-refresh-review",
                                    color="secondary",
                                    size="sm",
                                    className="mt-4",
                                ),
                            ], width=2),
                            dbc.Col([
                                dbc.Button(
                                    "📥 Export to Excel",
                                    id="btn-export-excel",
                                    color="success",
                                    size="sm",
                                    className="mt-4",
                                ),
                                dcc.Download(id="download-excel"),
                            ], width=3),
                        ], className="mb-4"),

                        # Batch action buttons
                        dbc.Row([
                            dbc.Col([
                                html.Label("Selection Controls:", className="small text-muted mb-1"),
                                dbc.Checklist(
                                    id='toggle-select-all',
                                    options=[{'label': ' Select All / Clear All', 'value': 'selected'}],
                                    value=[],
                                    switch=True,
                                    className="mt-1",
                                ),
                            ], width=3),
                            dbc.Col([
                                html.Label("Batch Actions:", className="small text-muted mb-1"),
                                dbc.ButtonGroup([
                                    dbc.Button(
                                        "✓ Confirm Selected",
                                        id="btn-batch-confirm",
                                        color="primary",
                                        size="sm",
                                    ),
                                    dbc.Button(
                                        "✓ Confirm & Create Rules",
                                        id="btn-batch-confirm-rule",
                                        color="success",
                                        size="sm",
                                    ),
                                ]),
                            ], width=5),
                            dbc.Col([
                                html.Span(id="batch-action-status", className="small mt-2 d-block"),
                            ], width=4),
                        ], className="mb-3"),

                        # Pagination controls
                        dbc.Row([
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button("← Previous", id="btn-prev-page", color="secondary", size="sm", disabled=True),
                                    dbc.Button("Next →", id="btn-next-page", color="secondary", size="sm"),
                                ]),
                                html.Span(id="page-info", className="ms-3 text-muted small"),
                            ], width=8, className="mb-3"),
                            dbc.Col([
                                dbc.Checklist(
                                    id='review-case-insensitive',
                                    options=[{'label': ' Ignore Case (Case-Insensitive)', 'value': 'ignore_case'}],
                                    value=['ignore_case'],  # Default: case-insensitive
                                    className="mb-1",
                                    switch=True,
                                ),
                            ], width=4, className="text-end"),
                        ]),

                        # Transaction review table
                        html.Div(id='review-table-container'),

                        # Store for current page number
                        dcc.Store(id='current-page', data=1),

                        # Store for selected transaction IDs (preserved across pages)
                        dcc.Store(id='selected-transaction-ids', data=[]),

                        # Store for editing transaction ID
                        dcc.Store(id='editing-transaction-id', data=None),

                        # Inline dropdown for category editing (appears near clicked cell)
                        html.Div(
                            id='review-inline-dropdown-container',
                            children=[
                                html.Div([
                                    html.Strong("Edit Category:", className="mb-2 d-block"),
                                    html.Small("Select a category to apply:", className="text-muted d-block mb-2"),
                                    dcc.Dropdown(
                                        id='review-inline-category-dropdown',
                                        clearable=False,
                                        placeholder="Select category...",
                                        className="mb-2",
                                    ),
                                    html.Div(id='review-batch-info', className="small text-info mb-2"),
                                    html.Div([
                                        dbc.Button("Cancel", id="review-inline-cancel-btn", color="secondary", size="sm", className="me-2"),
                                        dbc.Button("Save", id="review-inline-save-btn", color="primary", size="sm"),
                                    ]),
                                ]),
                            ],
                            style={
                                'position': 'fixed',
                                'top': '200px',
                                'left': '50%',
                                'transform': 'translateX(-50%)',
                                'zIndex': 9999,
                                'width': '320px',
                                'display': 'none',  # Hidden by default
                                'backgroundColor': 'white',
                                'padding': '15px',
                                'border': '2px solid #1976d2',
                                'borderRadius': '8px',
                                'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                            },
                        ),

                    ], width=12),
                ]),
            ]),

            # Review Duplicates Tab
            dbc.Tab(label="🔍 Review Duplicates", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Review Potential Duplicates", className="mt-3 mb-3"),
                        html.P("These transactions have the same date, description, amount, and account as existing transactions. Decide whether to keep both or dismiss as duplicates.", className="text-muted"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "🔄 Refresh Duplicates",
                                    id="btn-refresh-duplicates",
                                    color="secondary",
                                    size="sm",
                                    className="mb-3",
                                ),
                            ], width=2),
                            dbc.Col([
                                html.Div(id='duplicates-count', className="mb-3"),
                            ], width=10),
                        ]),

                        # Duplicates table
                        html.Div(id='duplicates-table-container'),

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
                        html.P("Click a Category cell to edit with dropdown. Pattern and Priority are editable inline.", className="text-muted"),

                        # Button row - all aligned
                        dbc.Row([
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button("➕ Add New Rule", id="btn-add-rule", color="success", size="sm"),
                                    dbc.Button("🔄 Refresh", id="btn-refresh-rules", color="secondary", size="sm"),
                                    dbc.Button("🗑️ Delete Selected", id="btn-delete-selected-rules", color="danger", size="sm"),
                                    dbc.Button("🔁 Re-categorize ALL", id="btn-reapply-all-rules", color="warning", size="sm"),
                                    dbc.Button("📥 Export to Excel", id="btn-export-rules", color="info", size="sm"),
                                ], className="mb-3"),
                                dcc.Download(id="download-rules"),
                            ], width=12),
                        ]),

                        # Force re-categorize option
                        dbc.Row([
                            dbc.Col([
                                dbc.Checklist(
                                    id='force-recategorize',
                                    options=[{'label': ' Force Re-categorize (Override Confirmed Transactions)', 'value': 'force'}],
                                    value=[],  # Default: OFF (protect confirmed)
                                    className="mb-3",
                                    switch=True,
                                ),
                            ], width=6),
                            dbc.Col([
                                html.Small([
                                    "⚠️ When enabled, ",
                                    html.Strong("ALL"),
                                    " transactions will be re-categorized, including confirmed ones. ",
                                    "Use this to fix mistakes or apply new rules to everything."
                                ], className="text-warning"),
                            ], width=6),
                        ]),

                        # Modal for adding new rule
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle("Add New Rule")),
                            dbc.ModalBody([
                                dbc.Label("Pattern (text to match in description)"),
                                dbc.Input(id="new-rule-pattern", placeholder="e.g., NETFLIX, TESCO, TFL", className="mb-3"),
                                dbc.Label("Category"),
                                dcc.Dropdown(id="new-rule-category", placeholder="Select category...", className="mb-3"),
                                dbc.Label("Priority (optional, default: 10)"),
                                dbc.Input(id="new-rule-priority", type="number", value=10, className="mb-3"),
                            ]),
                            dbc.ModalFooter([
                                dbc.Button("Cancel", id="btn-cancel-add-rule", color="secondary", size="sm"),
                                dbc.Button("Add Rule", id="btn-save-new-rule", color="success", size="sm"),
                            ]),
                        ], id="modal-add-rule", is_open=False),

                        # Dangerous operations row
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "🗑️ Purge All Transactions",
                                    id="btn-purge-transactions",
                                    color="danger",
                                    size="sm",
                                    className="mb-3",
                                ),
                            ], width=3),
                            dbc.Col([
                                html.Small("⚠️ This will delete ALL transactions but preserve rules and categories", className="text-danger"),
                            ], width=9),
                        ]),

                        # Status message for re-apply all rules
                        html.Div(id='reapply-rules-status', className="mb-3"),

                        # Filter instructions
                        dbc.Alert([
                            html.Strong("Excel-like Filtering:", className="me-2"),
                            html.Br(),
                            html.Small([
                                "Use operators in filter boxes: ",
                                html.Code('contains "text"', className="bg-light px-1"),
                                " | ",
                                html.Code('= "exact"', className="bg-light px-1"),
                                " | ",
                                html.Code('!= "not"', className="bg-light px-1"),
                                " | ",
                                html.Code('> 50', className="bg-light px-1"),
                                " | ",
                                html.Code('< 100', className="bg-light px-1"),
                            ], className="text-muted"),
                        ], color="info", className="mb-3", dismissable=True),

                        # Rules list
                        html.Div(id='all-rules-list', className="mt-3"),

                        # Inline dropdown for category editing (appears near clicked cell)
                        html.Div(
                            id='inline-dropdown-container',
                            children=[
                                html.Div([
                                    html.Strong("Edit Category:", className="mb-2 d-block"),
                                    dcc.Dropdown(
                                        id='inline-category-dropdown',
                                        clearable=False,
                                        placeholder="Select category...",
                                        className="mb-2",
                                    ),
                                    html.Div([
                                        dbc.Button("Cancel", id="inline-cancel-btn", color="secondary", size="sm", className="me-2"),
                                        dbc.Button("Save", id="inline-save-btn", color="primary", size="sm"),
                                    ]),
                                ]),
                            ],
                            style={
                                'position': 'fixed',
                                'top': '200px',
                                'left': '50%',
                                'transform': 'translateX(-50%)',
                                'zIndex': 9999,
                                'width': '300px',
                                'display': 'none',  # Hidden by default
                                'backgroundColor': 'white',
                                'padding': '15px',
                                'border': '2px solid #1976d2',
                                'borderRadius': '8px',
                                'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                            }
                        ),

                        # Store for current editing rule
                        dcc.Store(id='editing-rule-id', data=None),

                    ], width=12),
                ]),
            ]),
        ]),

        # Confirmation Modal for Purge
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirm Purge All Transactions")),
            dbc.ModalBody([
                html.P([
                    html.Strong("This will permanently delete ALL transactions from the database!"),
                ], className="text-danger"),
                html.Hr(),
                html.P("What will be deleted:"),
                html.Ul([
                    html.Li("All transaction records"),
                    html.Li("All categorization data"),
                ]),
                html.P("What will be preserved:"),
                html.Ul([
                    html.Li("All rules"),
                    html.Li("All categories"),
                ], className="text-success"),
                html.Hr(),
                html.P([
                    html.Strong("Are you sure you want to continue?"),
                ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="purge-cancel", className="me-2", color="secondary"),
                dbc.Button("Yes, Delete All Transactions", id="purge-confirm", color="danger"),
            ]),
        ], id="purge-modal", is_open=False),

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
        result = db.insert_transactions_bulk(transactions)

        # Clean up
        temp_file.unlink()

        # Get stats
        stats = db.get_statistics()
        uncategorized = len([t for t in db.get_transactions() if not t.category or t.category == "Uncategorized"])

        # Build alert message
        msg_parts = [
            f"📄 File: {filename}",
            html.Br(),
            f"✓ Imported: {result['inserted']} new transactions",
            html.Br(),
            f"📊 Total in database: {stats['total_transactions']}",
            html.Br(),
            f"❓ Uncategorized: {uncategorized}",
        ]

        # Add duplicate warning if any
        if result['duplicates'] > 0:
            msg_parts.extend([
                html.Br(),
                html.Span(f"⚠️ Potential duplicates: {result['duplicates']}", className="text-warning fw-bold"),
            ])

        alert_color = "warning" if result['duplicates'] > 0 else "success"

        alert_children = [
            html.H5("✓ Upload Complete", className="alert-heading"),
            html.Hr(),
            html.P(msg_parts),
        ]

        # Add next steps
        if result['duplicates'] > 0:
            alert_children.append(
                html.P("👉 Review potential duplicates in the 'Review Duplicates' tab", className="mb-0 small")
            )
        else:
            alert_children.append(
                html.P("👇 Now proceed to Step 2: Apply Rules", className="mb-0 small text-muted")
            )

        return dbc.Alert(alert_children, color=alert_color)

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
    """Apply rule-based categorization ONLY to uncategorized transactions (preserves AI categorizations)."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Get ONLY uncategorized transactions (preserve existing categorizations)
        all_transactions = db.get_transactions()
        uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

        if len(all_transactions) == 0:
            return dbc.Alert("No transactions found. Import a CSV file first.", color="info")

        if len(uncategorized) == 0:
            return dbc.Alert([
                html.H5("ℹ️ No Work Needed", className="alert-heading"),
                html.P("All transactions are already categorized!"),
                html.P("If you want to re-apply rules to ALL transactions (this will overwrite AI categorizations), you'll need to use a different approach.", className="small text-muted"),
            ], color="info")

        # Get categorizer
        categorizer = get_categorizer()

        # Categorize ONLY uncategorized transactions with rules
        # This preserves existing AI categorizations
        results = categorizer.categorize_batch(uncategorized, use_ai_fallback=False)

        # Save results
        categorizer.save_transaction_categories(results)

        # Get updated counts
        all_transactions_updated = db.get_transactions()
        still_uncategorized = len([t for t in all_transactions_updated if not t.category or t.category == "Uncategorized"])

        return dbc.Alert([
            html.H5("✓ Rules Applied to Uncategorized Transactions", className="alert-heading"),
            html.Hr(),
            html.P([
                f"📊 Processed: {len(uncategorized)} uncategorized transactions",
                html.Br(),
                f"📋 {results['rule_matched']} matched by rules (FREE)",
                html.Br(),
                f"❓ {still_uncategorized} still uncategorized (need AI)",
            ]),
            html.P("💡 Existing AI categorizations were preserved. Go to 'Review & Correct' tab to see results.",
                   className="mb-0 small text-muted"),
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
        api_key = os.getenv("APP_ANTHROPIC_API_KEY")
        if not api_key:
            return dbc.Alert([
                html.H5("❌ Missing API Key", className="alert-heading"),
                html.P("APP_ANTHROPIC_API_KEY not found in .env file."),
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
            ai_batch_size=30  # 30 transactions per API call (more reliable)
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
    Input('btn-refresh-rules', 'n_clicks'),  # Manual refresh only
)
def display_all_rules(n_clicks):
    """Display all categorization rules in a scrollable list with Excel-like filtering."""
    try:
        # Default to case-insensitive filtering
        case_sensitive = False
        # Load rules from database
        rules = db.get_rules()

        if len(rules) == 0:
            return dbc.Alert("No rules found. Rules will be created automatically when you confirm transactions and create rules.", color="info")

        # Get all categories for dropdown
        categories = db.get_categories()
        category_options = [{'label': cat.name, 'value': cat.name} for cat in sorted(categories, key=lambda x: x.name)]

        # Create UUID -> Name lookup for display
        category_lookup = {cat.id: cat.name for cat in categories}

        # Debug: Print category options
        print(f"[DEBUG] Category dropdown options: {category_options}")

        # Create table data with row numbers and rule IDs
        rules_data = []
        for idx, r in enumerate(sorted(rules, key=lambda x: (-x.priority, x.pattern)), 1):
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

            # Convert category_id (UUID) to category name for display
            category_name = category_lookup.get(r.category_id, r.category_id)

            rules_data.append({
                'rule_id': r.id,  # Hidden column for updates/deletes
                'Row #': idx,
                'Pattern': r.pattern,
                'Category': category_name,
                'Priority': r.priority,
                'Created': created_date,
            })

        rules_df = pd.DataFrame(rules_data)

        # Define columns with editability
        # Note: rule_id is in the data but not in columns (hidden from user)
        # Category is read-only - click to open modal with dropdown
        columns = [
            {'name': 'Row #', 'id': 'Row #', 'editable': False},
            {'name': 'Pattern', 'id': 'Pattern', 'editable': True},
            {
                'name': 'Category (Click to Edit)',
                'id': 'Category',
                'editable': False,  # Read-only, use modal to edit
            },
            {'name': 'Priority', 'id': 'Priority', 'editable': True, 'type': 'numeric'},
            {'name': 'Created', 'id': 'Created', 'editable': False},
        ]

        # Create table with ALL rows visible (no pagination) and Excel-like filtering
        table = dash_table.DataTable(
            id='rules-table',
            data=rules_df.to_dict('records'),
            columns=columns,
            editable=True,  # Make table editable (except Category)
            row_deletable=True,  # Add delete button for each row
            row_selectable='multi',  # Enable checkboxes for multi-select
            selected_rows=[],  # Start with no rows selected
            style_table={
                'overflowX': 'auto',
                # Removed overflowY to prevent clipping dropdown menus
                'maxHeight': '70vh',  # 70% of viewport height for scrolling
            },
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '14px',
                'minWidth': '120px',
                'overflow': 'visible',  # Allow dropdowns to extend beyond cell
            },
            style_header={
                'backgroundColor': '#343a40',
                'color': 'white',
                'fontWeight': 'bold',
                'position': 'sticky',
                'top': 0,
                'zIndex': 10,  # Increased from 1 to prevent dropdown overlap issues
            },
            style_data={
                'overflow': 'visible',  # Allow dropdown menus to extend beyond row
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa',
                },
                {
                    'if': {'column_id': 'Category'},
                    'backgroundColor': '#e3f2fd',  # Light blue to indicate clickable
                    'cursor': 'pointer',
                    'textDecoration': 'underline',
                    'color': '#1976d2',  # Blue text
                }
            ],
            # NO PAGINATION - show all rows
            page_action='none',
            sort_action='native',
            filter_action='native',
            # Excel-like filtering with case sensitivity control
            filter_options={
                'case': 'sensitive' if case_sensitive else 'insensitive',
                'placeholder_text': 'Filter...',
            },
        )

        # Status message about case sensitivity
        case_status = "Case-Sensitive" if case_sensitive else "Case-Insensitive"

        content = html.Div([
            dbc.Alert([
                html.Strong(f"Total Rules: {len(rules)}", className="me-2"),
                html.Span(f"| Sorted by Priority (High -> Low) | Filtering: {case_status}", className="text-muted small"),
            ], color="light", className="mb-3"),
            table,
            dbc.Alert([
                html.Strong("💡 Editing Rules:", className="me-2"),
                html.Br(),
                "• Click any cell in Pattern, Category, or Priority columns to edit",
                html.Br(),
                "• Changes are saved automatically",
                html.Br(),
                "• Click the ❌ button to delete a rule",
                html.Br(),
                "• After editing, go to 'Import & Categorize' tab and click 'Apply Rules' to recategorize all transactions",
            ], color="success", className="mt-3 mb-3", dismissable=True),
            html.P([
                "Filter Tip: Type in the filter boxes below column headers. ",
                "Use operators like: ",
                html.Code('contains "text"'),
                ", ",
                html.Code('= "exact"'),
                ", ",
                html.Code('> 10'),
            ], className="mt-3 small text-muted"),
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
    Output('rules-table', 'data', allow_duplicate=True),
    Input('rules-table', 'data'),
    State('rules-table', 'data_previous'),
    prevent_initial_call=True,
)
def save_rule_edits(current_data, previous_data):
    """Save rule edits to database when table is edited or rows are deleted."""
    if current_data is None or previous_data is None:
        raise PreventUpdate

    try:
        # Convert to dictionaries keyed by rule_id for easy comparison
        current_rules = {row['rule_id']: row for row in current_data if 'rule_id' in row}
        previous_rules = {row['rule_id']: row for row in previous_data if 'rule_id' in row}

        # Find deleted rules
        deleted_ids = set(previous_rules.keys()) - set(current_rules.keys())
        for rule_id in deleted_ids:
            db.delete_rule(rule_id)
            print(f"[Rules] Deleted rule: {rule_id}")

        # Find updated rules
        for rule_id, current_row in current_rules.items():
            if rule_id in previous_rules:
                previous_row = previous_rules[rule_id]
                # Check if any field changed
                if (current_row['Pattern'] != previous_row['Pattern'] or
                    current_row['Category'] != previous_row['Category'] or
                    current_row['Priority'] != previous_row['Priority']):

                    # Update the rule
                    db.update_rule(
                        rule_id=rule_id,
                        pattern=current_row['Pattern'],
                        category_id=current_row['Category'],
                        priority=int(current_row['Priority']),
                    )
                    print(f"[Rules] Updated rule: {rule_id} - Pattern: '{current_row['Pattern']}', Category: {current_row['Category']}, Priority: {current_row['Priority']}")

        return current_data

    except Exception as e:
        print(f"[Rules] Error saving edits: {e}")
        import traceback
        traceback.print_exc()
        # Return previous data if error
        return previous_data if previous_data else current_data


@callback(
    Output('review-table-container', 'children'),
    Output('page-info', 'children'),
    Output('btn-prev-page', 'disabled'),
    Output('btn-next-page', 'disabled'),
    Input('review-filter', 'value'),
    Input('review-page-size', 'value'),
    Input('current-page', 'data'),
    Input('btn-refresh-review', 'n_clicks'),
    Input('review-case-insensitive', 'value'),
    State('selected-transaction-ids', 'data'),
)
def update_review_table(filter_value, page_size, current_page, n_clicks, case_insensitive_value, selected_txn_ids):
    """Update the review table of transactions with checkboxes for batch operations."""
    # Get all transactions
    transactions = db.get_transactions()

    if len(transactions) == 0:
        return dbc.Alert("No transactions found. Import a CSV file first.", color="info"), "", True, True

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
        return dbc.Alert(f"No transactions match filter: {filter_value}", color="info"), "", True, True

    # Show ALL filtered transactions (no pagination - fixes search issue)
    display_transactions = filtered
    total_transactions = len(filtered)

    # Page info text (no pagination)
    page_info = f"Showing all {total_transactions} transactions"

    # Disable pagination buttons (not used)
    prev_disabled = True
    next_disabled = True

    # Get all categories for dropdown
    categories = db.get_categories()
    category_options = [{'label': cat.name, 'value': cat.name} for cat in sorted(categories, key=lambda x: x.name)]

    # Check if case-insensitive filtering is enabled
    case_insensitive = 'ignore_case' in (case_insensitive_value or [])

    # Build table data
    table_data = []
    for idx, txn in enumerate(display_transactions, 1):
        # Sequential row number
        row_number = idx

        # Confidence display
        conf_display = ""
        if txn.category_confidence is not None:
            conf_pct = int(txn.category_confidence * 100)
            conf_display = f"{conf_pct}%"

        # Status
        status = "✓ Confirmed" if txn.category_confirmed else ("🤖 AI" if txn.category_confidence and txn.category_confidence < 1.0 else "📋 Rule")

        table_data.append({
            'transaction_id': txn.id,
            '#': row_number,
            'Date': txn.date.strftime('%d %b %Y'),
            'Description': txn.description[:50] + ('...' if len(txn.description) > 50 else ''),
            'Amount': f"£{txn.amount:,.2f}",
            'Category': txn.category if txn.category else 'Uncategorized',
            'Confidence': conf_display,
            'Status': status,
        })

    # Create DataFrame
    df = pd.DataFrame(table_data)

    # Map selected transaction IDs to current page row indices
    selected_txn_ids = selected_txn_ids or []
    selected_rows = []
    for idx, row in enumerate(table_data):
        if row['transaction_id'] in selected_txn_ids:
            selected_rows.append(idx)

    # Define columns with editability
    # Note: filter_options={'case': 'insensitive'} is set based on toggle
    columns = [
        {'name': '#', 'id': '#', 'editable': False, 'type': 'numeric'},
        {'name': 'Date', 'id': 'Date', 'editable': False, 'filter_options': {'case': 'insensitive'} if case_insensitive else {}},
        {'name': 'Description', 'id': 'Description', 'editable': False, 'filter_options': {'case': 'insensitive'} if case_insensitive else {}},
        {'name': 'Amount', 'id': 'Amount', 'editable': False},
        {
            'name': 'Category (Click to Edit)',
            'id': 'Category',
            'editable': False,  # Read-only, use modal to edit
            'filter_options': {'case': 'insensitive'} if case_insensitive else {}
        },
        {'name': 'Confidence', 'id': 'Confidence', 'editable': False},
        {'name': 'Status', 'id': 'Status', 'editable': False, 'filter_options': {'case': 'insensitive'} if case_insensitive else {}},
    ]

    # Create table with checkboxes
    table = dash_table.DataTable(
        id='review-transactions-table',
        data=df.to_dict('records'),
        columns=columns,
        editable=False,  # No inline editing, use modal
        row_selectable='multi',
        selected_rows=selected_rows,
        style_table={
            'overflowX': 'auto',
            'maxHeight': '70vh',  # 70% of viewport height for scrolling
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '14px',
            'fontFamily': 'Century Gothic, Arial, sans-serif',
            'color': '#2F4F4F',  # Charcoal grey (dark slate grey)
            'minWidth': '100px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        },
        style_cell_conditional=[
            {
                'if': {'column_id': '#'},
                'width': '200px',
                'minWidth': '200px',
                'maxWidth': '200px',
            },
        ],
        style_header={
            'backgroundColor': '#343a40',
            'color': 'white',
            'fontWeight': 'bold',
            'fontFamily': 'Century Gothic, Arial, sans-serif',
            'position': 'sticky',
            'top': 0,
            'zIndex': 10,
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa',
            },
            {
                'if': {'filter_query': '{Status} = "✓ Confirmed"'},
                'backgroundColor': '#d4edda',  # Light green for confirmed
            },
            {
                'if': {'column_id': 'Category'},
                'backgroundColor': '#e3f2fd',  # Light blue to indicate clickable
                'cursor': 'pointer',
                'textDecoration': 'underline',
                'color': '#1976d2',  # Blue text
            }
        ],
        page_action='none',  # Pagination handled externally
        sort_action='native',
        filter_action='native',
        css=[
            {
                'selector': '.dash-spreadsheet-container .dash-spreadsheet-inner input[type="checkbox"]',
                'rule': 'width: 20px !important; height: 20px !important; margin: 4px;'
            },
            {
                'selector': '.dash-spreadsheet .dash-select-cell',
                'rule': 'width: 200px !important; min-width: 200px !important; max-width: 200px !important;'
            },
            {
                'selector': '.dash-spreadsheet .dash-select-header',
                'rule': 'width: 200px !important; min-width: 200px !important; max-width: 200px !important;'
            }
        ],
    )

    # Summary with filter description
    filter_descriptions = {
        'rule_matched': '📋 Rule Matched (Auto-categorized)',
        'ai_suggested': '🤖 AI Suggestions (Needs Review)',
        'uncategorized': '❓ Uncategorized',
        'confirmed': '✓ Confirmed',
        'all': '📊 All Transactions',
    }

    summary = dbc.Alert([
        html.Strong(f"{filter_descriptions.get(filter_value, 'Transactions')}: "),
        f"Showing {len(display_transactions)} of {len(filtered)} total",
        html.Br(),
        html.Small("💡 Tip: Select rows using checkboxes, then use batch action buttons above", className="text-muted"),
    ], color="light", className="mb-3")

    return html.Div([summary, table]), page_info, prev_disabled, next_disabled


@callback(
    Output('current-page', 'data'),
    Input('btn-prev-page', 'n_clicks'),
    Input('btn-next-page', 'n_clicks'),
    Input('review-filter', 'value'),  # Reset to page 1 when filter changes
    Input('review-page-size', 'value'),  # Reset to page 1 when page size changes
    State('current-page', 'data'),
    prevent_initial_call=True,
)
def handle_pagination(prev_clicks, next_clicks, filter_value, page_size, current_page):
    """Handle Previous/Next button clicks."""
    triggered_id = ctx.triggered_id

    if triggered_id == 'btn-prev-page':
        return max(1, current_page - 1)
    elif triggered_id == 'btn-next-page':
        return current_page + 1
    elif triggered_id in ['review-filter', 'review-page-size']:
        # Reset to page 1 when filter or page size changes
        return 1

    return current_page


@callback(
    Output('selected-transaction-ids', 'data'),
    Input('review-transactions-table', 'selected_rows'),
    State('review-transactions-table', 'data'),
    State('selected-transaction-ids', 'data'),
    prevent_initial_call=True,
)
def update_selected_transaction_ids(selected_rows, table_data, current_selected_ids):
    """Store selected transaction IDs to preserve selections across pages."""
    if table_data is None:
        raise PreventUpdate

    # Get transaction IDs from current page
    current_page_txn_ids = [row['transaction_id'] for row in table_data]

    # Start with existing selections
    all_selected_ids = set(current_selected_ids or [])

    # Remove any IDs from current page that are not selected
    all_selected_ids -= set(current_page_txn_ids)

    # Add newly selected IDs from current page
    if selected_rows:
        for idx in selected_rows:
            if idx < len(table_data):
                all_selected_ids.add(table_data[idx]['transaction_id'])

    return list(all_selected_ids)


@callback(
    Output('selected-transaction-ids', 'data', allow_duplicate=True),
    Input('toggle-select-all', 'value'),
    State('review-transactions-table', 'data'),
    prevent_initial_call=True,
)
def handle_select_all_toggle(toggle_value, table_data):
    """Handle Select All / Clear All toggle.

    When toggle is ON (checked): Select all rows on current page
    When toggle is OFF (unchecked): Clear all selections

    NOTE: Does NOT auto-refresh the table.
    """
    if not table_data:
        raise PreventUpdate

    # Toggle is ON - select all on current page
    if toggle_value and 'selected' in toggle_value:
        # Get all transaction IDs from current page
        current_page_txn_ids = [row['transaction_id'] for row in table_data]
        return current_page_txn_ids

    # Toggle is OFF - clear all selections
    else:
        return []


@callback(
    Output('review-inline-dropdown-container', 'style'),
    Output('review-inline-category-dropdown', 'options'),
    Output('review-inline-category-dropdown', 'value'),
    Output('editing-transaction-id', 'data'),
    Output('review-batch-info', 'children'),
    Input('review-transactions-table', 'active_cell'),
    State('review-transactions-table', 'data'),
    State('selected-transaction-ids', 'data'),
    prevent_initial_call=True,
)
def show_review_inline_dropdown(active_cell, table_data, selected_txn_ids):
    """Show inline dropdown when user clicks on a Category cell."""
    if not active_cell:
        raise PreventUpdate

    # Check if clicked cell is in Category column
    if active_cell['column_id'] != 'Category':
        raise PreventUpdate

    # Get the row data
    row_idx = active_cell['row']
    row_data = table_data[row_idx]

    # Get categories for dropdown
    categories = db.get_categories()
    category_options = [{'label': cat.name, 'value': cat.name} for cat in sorted(categories, key=lambda x: x.name)]

    # Get current values
    txn_id = row_data['transaction_id']
    current_category = row_data['Category']

    # Check if multiple rows are selected
    selected_txn_ids = selected_txn_ids or []
    batch_info = ""
    if len(selected_txn_ids) > 1:
        batch_info = f"ℹ️ Batch mode: Will update {len(selected_txn_ids)} selected transactions"
        print(f"[Review Inline] Batch mode: {len(selected_txn_ids)} transactions selected")
    else:
        print(f"[Review Inline] Single mode: Transaction {txn_id}")

    # Show container
    visible_style = {
        'position': 'fixed',
        'top': '200px',
        'left': '50%',
        'transform': 'translateX(-50%)',
        'zIndex': 9999,
        'width': '320px',
        'display': 'block',
        'backgroundColor': 'white',
        'padding': '15px',
        'border': '2px solid #1976d2',
        'borderRadius': '8px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
    }

    return visible_style, category_options, current_category, txn_id, batch_info


@callback(
    Output('review-inline-dropdown-container', 'style', allow_duplicate=True),
    Input('review-inline-cancel-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def hide_review_inline_dropdown(n_clicks):
    """Hide dropdown when Cancel is clicked."""
    if n_clicks is None:
        raise PreventUpdate

    hidden_style = {
        'position': 'fixed',
        'top': '200px',
        'left': '50%',
        'transform': 'translateX(-50%)',
        'zIndex': 9999,
        'width': '320px',
        'display': 'none',
        'backgroundColor': 'white',
        'padding': '15px',
        'border': '2px solid #1976d2',
        'borderRadius': '8px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
    }

    return hidden_style


@callback(
    Output('review-inline-dropdown-container', 'style', allow_duplicate=True),
    Output('batch-action-status', 'children', allow_duplicate=True),
    Input('review-inline-save-btn', 'n_clicks'),
    State('editing-transaction-id', 'data'),
    State('review-inline-category-dropdown', 'value'),
    State('selected-transaction-ids', 'data'),
    prevent_initial_call=True,
)
def save_review_category_change(n_clicks, clicked_txn_id, new_category, selected_txn_ids):
    """Save category change when Save button is clicked.

    If multiple rows are selected, applies to ALL selected transactions.
    Otherwise, only applies to the clicked transaction.

    NOTE: Does NOT auto-refresh the table. User must click 'Refresh' button manually.
    """
    if n_clicks is None or not clicked_txn_id or not new_category:
        raise PreventUpdate

    try:
        selected_txn_ids = selected_txn_ids or []

        # Check if multiple rows are selected (batch mode)
        if len(selected_txn_ids) > 1:
            # BATCH MODE: Apply to all selected transactions
            print(f"[Review Inline] Batch category edit: Applying '{new_category}' to {len(selected_txn_ids)} selected transactions")

            for txn_id in selected_txn_ids:
                db.update_transaction_category(txn_id, new_category, confirmed=False, confidence=None)

            print(f"[Review Inline] Updated {len(selected_txn_ids)} transactions to '{new_category}'")
            status_msg = dbc.Badge(f"✓ Updated {len(selected_txn_ids)} transactions to '{new_category}'. Click 'Refresh' to see changes.", color="success")
        else:
            # SINGLE MODE: Only update the clicked transaction
            db.update_transaction_category(clicked_txn_id, new_category, confirmed=False, confidence=None)
            print(f"[Review Inline] Single category edit: {clicked_txn_id} -> {new_category}")
            status_msg = dbc.Badge(f"✓ Category changed to '{new_category}'. Click 'Refresh' to see changes.", color="success")

        # Flush database to ensure changes are persisted immediately
        print(f"[Review Inline] Database update complete. User must click 'Refresh' to see changes.")

        # Hide dropdown WITHOUT triggering refresh
        # User must manually click 'Refresh' button to see changes
        hidden_style = {
            'position': 'fixed',
            'top': '200px',
            'left': '50%',
            'transform': 'translateX(-50%)',
            'zIndex': 9999,
            'width': '320px',
            'display': 'none',
            'backgroundColor': 'white',
            'padding': '15px',
            'border': '2px solid #1976d2',
            'borderRadius': '8px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
        }

        return hidden_style, status_msg

    except Exception as e:
        print(f"[Review Inline] Error saving category: {e}")
        import traceback
        traceback.print_exc()
        error_msg = dbc.Badge(f"❌ Error: {str(e)}", color="danger")
        raise PreventUpdate


@callback(
    Output('batch-action-status', 'children'),
    Output('selected-transaction-ids', 'data', allow_duplicate=True),
    Input('btn-batch-confirm', 'n_clicks'),
    State('selected-transaction-ids', 'data'),
    prevent_initial_call=True,
)
def batch_confirm(n_clicks, selected_txn_ids):
    """Confirm selected transactions in bulk (across all pages).

    NOTE: Does NOT auto-refresh. User must click 'Refresh' button to see changes.
    """
    if not selected_txn_ids or len(selected_txn_ids) == 0:
        return dbc.Badge("⚠️ No rows selected", color="warning"), dash.no_update

    try:
        # Confirm each selected transaction by ID
        for txn_id in selected_txn_ids:
            txn = db.get_transaction(txn_id)
            if txn:
                # Update transaction with confidence=1.0 (manually confirmed)
                db.update_transaction_category(txn_id, txn.category, confirmed=True, confidence=1.0)
                print(f"[Batch Confirm] {txn_id} -> {txn.category}")

        # Clear selections WITHOUT triggering refresh
        return dbc.Badge(f"✓ Confirmed {len(selected_txn_ids)} transactions. Click 'Refresh' to update table.", color="success"), []

    except Exception as e:
        print(f"[Batch Confirm] Error: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Badge(f"❌ Error: {str(e)}", color="danger"), dash.no_update


@callback(
    Output('batch-action-status', 'children', allow_duplicate=True),
    Output('selected-transaction-ids', 'data', allow_duplicate=True),
    Input('btn-batch-confirm-rule', 'n_clicks'),
    State('selected-transaction-ids', 'data'),
    prevent_initial_call=True,
)
def batch_confirm_and_create_rules(n_clicks, selected_txn_ids):
    """Confirm selected transactions and create rules (one per unique pattern).

    NOTE: Does NOT auto-refresh. User must click 'Refresh' button to see changes.
    """
    if not selected_txn_ids or len(selected_txn_ids) == 0:
        return dbc.Badge("⚠️ No rows selected", color="warning"), dash.no_update

    try:
        categorizer = get_categorizer()

        # Track unique patterns to avoid duplicate rule creation
        unique_patterns = {}  # pattern -> (category, category_id)

        # Step 1: Confirm all transactions and collect unique patterns
        for txn_id in selected_txn_ids:
            txn = db.get_transaction(txn_id)
            if not txn:
                continue

            # Update transaction with confidence=1.0 (manually confirmed)
            db.update_transaction_category(txn_id, txn.category, confirmed=True, confidence=1.0)

            # Extract pattern from transaction
            suggested_rule = categorizer.suggest_rule_from_transaction(txn, txn.category)
            pattern = suggested_rule.pattern

            # Store unique pattern (last one wins if multiple)
            if pattern not in unique_patterns:
                unique_patterns[pattern] = {
                    'category': txn.category,
                    'category_id': suggested_rule.category_id,
                }
                print(f"[Batch Confirm+Rule] Pattern '{pattern}' -> {txn.category}")

        # Step 2: Create rules for unique patterns only
        rules_created = 0
        for pattern, info in unique_patterns.items():
            try:
                from src.data.models import Rule
                rule = Rule(
                    pattern=pattern,
                    category_id=info['category_id'],
                    priority=15,  # User rules have higher priority
                )
                db.insert_rule(rule)
                rules_created += 1
                print(f"[Batch Confirm+Rule] Created rule: '{pattern}' -> {info['category']}")
            except Exception as e:
                print(f"[Batch Confirm+Rule] Failed to create rule '{pattern}': {e}")

        # Clear selections WITHOUT triggering refresh
        return dbc.Badge(
            f"✓ Confirmed {len(selected_txn_ids)} transactions, created {rules_created} rules. Click 'Refresh' to update table.",
            color="success"
        ), []

    except Exception as e:
        print(f"[Batch Confirm+Rule] Error: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Badge(f"❌ Error: {str(e)}", color="danger"), dash.no_update


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


@callback(
    Output('download-excel', 'data'),
    Input('btn-export-excel', 'n_clicks'),
    prevent_initial_call=True,
)
def export_to_excel(n_clicks):
    """Export all transactions to Excel with categories and metadata."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Get all transactions
        all_transactions = db.get_transactions()

        if len(all_transactions) == 0:
            return None

        # Convert to DataFrame with all useful fields (including Row #)
        export_data = []
        for idx, txn in enumerate(all_transactions, 1):
            export_data.append({
                'Row #': idx,
                'Date': txn.date.strftime('%Y-%m-%d') if hasattr(txn.date, 'strftime') else str(txn.date),
                'Description': txn.description,
                'Amount': txn.amount,
                'Balance': txn.balance,
                'Account Number': txn.account_number,
                'Transaction Type': txn.transaction_type if hasattr(txn, 'transaction_type') else '',
                'Category': txn.category if txn.category else 'Uncategorized',
                'Confidence': txn.category_confidence if txn.category_confidence is not None else '',
                'Confirmed': 'Yes' if txn.category_confirmed else 'No',
                'Transaction ID': txn.id,
            })

        df = pd.DataFrame(export_data)

        # Create Excel file in memory
        from io import BytesIO
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transactions')

            # Auto-adjust column widths
            worksheet = writer.sheets['Transactions']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'transactions_{timestamp}.xlsx'

        return dcc.send_bytes(output.getvalue(), filename)

    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return None


@callback(
    Output('download-rules', 'data'),
    Input('btn-export-rules', 'n_clicks'),
    prevent_initial_call=True,
)
def export_rules_to_excel(n_clicks):
    """Export all rules to Excel with row numbers."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Get all rules
        rules = db.get_rules()

        if len(rules) == 0:
            return None

        # Convert to DataFrame with row numbers
        export_data = []
        for idx, r in enumerate(sorted(rules, key=lambda x: (-x.priority, x.pattern)), 1):
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

            export_data.append({
                'Row #': idx,
                'Pattern': r.pattern,
                'Category': r.category_id,
                'Priority': r.priority,
                'Created': created_date,
            })

        df = pd.DataFrame(export_data)

        # Create Excel file in memory
        from io import BytesIO
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Rules')

            # Auto-adjust column widths
            worksheet = writer.sheets['Rules']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'rules_{timestamp}.xlsx'

        return dcc.send_bytes(output.getvalue(), filename)

    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return None


@callback(
    Output('reapply-rules-status', 'children'),
    Input('btn-reapply-all-rules', 'n_clicks'),
    State('force-recategorize', 'value'),
    prevent_initial_call=True,
)
def reapply_all_rules(n_clicks, force_recategorize_value):
    """Re-apply rules to transactions.

    By default, preserves confirmed transactions.
    If 'Force Re-categorize' is enabled, overwrites ALL transactions including confirmed ones.
    """
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Check if force mode is enabled
        force_mode = 'force' in (force_recategorize_value or [])

        # Get ALL transactions
        all_transactions = db.get_transactions()

        if len(all_transactions) == 0:
            return dbc.Alert("No transactions found.", color="info")

        # Get categorizer
        categorizer = get_categorizer()

        # Categorize transactions with rules ONLY (no AI)
        # Pass force_mode to categorizer
        results = categorizer.categorize_batch(
            all_transactions,
            use_ai_fallback=False,
            force_recategorize=force_mode
        )

        # Save results
        categorizer.save_transaction_categories(results)

        # Get updated stats
        all_transactions_updated = db.get_transactions()
        rule_matched = len([t for t in all_transactions_updated if t.category and t.category != "Uncategorized" and t.category_confidence == 1.0])
        uncategorized = len([t for t in all_transactions_updated if not t.category or t.category == "Uncategorized"])

        # Build status message
        mode_msg = "🔥 FORCE MODE: Overwrote ALL transactions including confirmed ones" if force_mode else "✓ Protected confirmed transactions"

        return dbc.Alert([
            html.H5("✓ Re-applied Rules Successfully", className="alert-heading"),
            html.Hr(),
            html.P([
                f"📊 Total transactions: {len(all_transactions)}",
                html.Br(),
                f"🔄 Processed: {results['total']}",
                html.Br(),
                f"📋 Matched by rules: {rule_matched}",
                html.Br(),
                f"❓ Still uncategorized: {uncategorized}",
                html.Br(),
                html.Br(),
                html.Strong(mode_msg, className="text-info" if force_mode else "text-success"),
            ]),
        ], color="warning" if force_mode else "success")

    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")


@callback(
    Output('reapply-rules-status', 'children', allow_duplicate=True),
    Output('btn-refresh-rules', 'n_clicks', allow_duplicate=True),
    Input('btn-delete-selected-rules', 'n_clicks'),
    State('rules-table', 'data'),
    State('rules-table', 'selected_rows'),
    prevent_initial_call=True,
)
def delete_selected_rules(n_clicks, table_data, selected_rows):
    """Delete selected rules from the database."""
    if n_clicks is None or not selected_rows or not table_data:
        raise PreventUpdate

    try:
        # Get the Rule IDs of selected rows
        selected_rule_ids = [table_data[i]['Rule ID'] for i in selected_rows]

        print(f"[Delete Rules] Deleting {len(selected_rule_ids)} selected rules...")

        # Delete each rule from database
        import sqlite3
        DB_PATH = Path(__file__).parent / "data" / "finance.db"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for rule_id in selected_rule_ids:
            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            print(f"[Delete Rules] Deleted rule: {rule_id}")

        conn.commit()
        conn.close()

        print(f"[Delete Rules] Successfully deleted {len(selected_rule_ids)} rules")

        # Trigger table refresh by incrementing refresh button clicks
        return dbc.Alert([
            html.H5(f"✓ Deleted {len(selected_rule_ids)} Rules", className="alert-heading"),
            html.P("The selected rules have been permanently deleted from the database."),
        ], color="success"), 1

    except Exception as e:
        print(f"[Delete Rules] Error: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error deleting rules: {str(e)}", color="danger"), dash.no_update


@callback(
    Output('modal-add-rule', 'is_open'),
    Output('new-rule-category', 'options'),
    Input('btn-add-rule', 'n_clicks'),
    Input('btn-cancel-add-rule', 'n_clicks'),
    Input('btn-save-new-rule', 'n_clicks'),
    State('modal-add-rule', 'is_open'),
    prevent_initial_call=True,
)
def toggle_add_rule_modal(btn_add, btn_cancel, btn_save, is_open):
    """Open/close the Add New Rule modal and populate category dropdown."""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Get categories for dropdown
    categories = db.get_categories()
    category_options = [{'label': cat.name, 'value': cat.id} for cat in categories]

    if button_id == 'btn-add-rule':
        return True, category_options  # Open modal
    else:
        return False, category_options  # Close modal


@callback(
    Output('reapply-rules-status', 'children', allow_duplicate=True),
    Output('btn-refresh-rules', 'n_clicks', allow_duplicate=True),
    Output('new-rule-pattern', 'value'),
    Output('new-rule-category', 'value'),
    Output('new-rule-priority', 'value'),
    Input('btn-save-new-rule', 'n_clicks'),
    State('new-rule-pattern', 'value'),
    State('new-rule-category', 'value'),
    State('new-rule-priority', 'value'),
    prevent_initial_call=True,
)
def save_new_rule(n_clicks, pattern, category_id, priority):
    """Save a new rule to the database."""
    if n_clicks is None:
        raise PreventUpdate

    try:
        # Validation
        if not pattern or not pattern.strip():
            return dbc.Alert("Error: Pattern cannot be empty", color="danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if not category_id:
            return dbc.Alert("Error: Please select a category", color="danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Create new rule
        from src.data.models import Rule
        new_rule = Rule(
            pattern=pattern.strip(),
            category_id=category_id,
            priority=priority if priority else 10,
        )

        # Save to database
        db.insert_rule(new_rule)

        print(f"[Add Rule] Created new rule: '{pattern}' -> {category_id} (Priority: {priority})")

        # Clear form and refresh table
        return dbc.Alert([
            html.H5("✓ Rule Created", className="alert-heading"),
            html.P(f"Pattern: '{pattern}' successfully added to rules."),
        ], color="success"), 1, "", None, 10  # Reset form

    except Exception as e:
        print(f"[Add Rule] Error: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error creating rule: {str(e)}", color="danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update


@callback(
    Output('inline-dropdown-container', 'style'),
    Output('inline-category-dropdown', 'options'),
    Output('inline-category-dropdown', 'value'),
    Output('editing-rule-id', 'data'),
    Input('rules-table', 'active_cell'),
    State('rules-table', 'data'),
    prevent_initial_call=True,
)
def show_inline_dropdown(active_cell, table_data):
    """Show inline dropdown when user clicks on a Category cell."""
    if not active_cell:
        raise PreventUpdate

    # Check if clicked cell is in Category column
    if active_cell['column_id'] != 'Category':
        raise PreventUpdate

    # Get the row data
    row_idx = active_cell['row']
    row_data = table_data[row_idx]

    # Get categories for dropdown
    categories = db.get_categories()
    category_options = [{'label': cat.name, 'value': cat.name} for cat in sorted(categories, key=lambda x: x.name)]

    # Get current values
    rule_id = row_data['rule_id']
    current_category = row_data['Category']

    print(f"[Inline] Showing dropdown for rule: {rule_id}, Category: {current_category}")

    # Show container
    visible_style = {
        'position': 'fixed',
        'top': '200px',
        'left': '50%',
        'transform': 'translateX(-50%)',
        'zIndex': 9999,
        'width': '300px',
        'display': 'block',
        'backgroundColor': 'white',
        'padding': '15px',
        'border': '2px solid #1976d2',
        'borderRadius': '8px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
    }

    return visible_style, category_options, current_category, rule_id


@callback(
    Output('inline-dropdown-container', 'style', allow_duplicate=True),
    Input('inline-cancel-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def hide_inline_dropdown(n_clicks):
    """Hide dropdown when Cancel is clicked."""
    if n_clicks is None:
        raise PreventUpdate

    hidden_style = {
        'position': 'fixed',
        'top': '200px',
        'left': '50%',
        'transform': 'translateX(-50%)',
        'zIndex': 9999,
        'width': '300px',
        'display': 'none',
        'backgroundColor': 'white',
        'padding': '15px',
        'border': '2px solid #1976d2',
        'borderRadius': '8px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
    }

    return hidden_style


@callback(
    Output('inline-dropdown-container', 'style', allow_duplicate=True),
    Output('btn-refresh-rules', 'n_clicks'),
    Input('inline-save-btn', 'n_clicks'),
    State('editing-rule-id', 'data'),
    State('inline-category-dropdown', 'value'),
    State('rules-table', 'data'),
    prevent_initial_call=True,
)
def save_inline_category_change(n_clicks, rule_id, new_category, table_data):
    """Save category change when Save button is clicked."""
    if n_clicks is None or not rule_id or not new_category:
        raise PreventUpdate

    try:
        # Find the rule in table_data to get other values
        rule_row = next((row for row in table_data if row['rule_id'] == rule_id), None)
        if not rule_row:
            print(f"[Inline] Error: Could not find rule {rule_id}")
            raise PreventUpdate

        # Update the rule in database
        db.update_rule(
            rule_id=rule_id,
            pattern=rule_row['Pattern'],
            category_id=new_category,
            priority=int(rule_row['Priority']),
        )

        print(f"[Inline] Saved: Rule {rule_id} -> Category: {new_category}")

        # Hide dropdown and trigger refresh
        hidden_style = {
            'position': 'fixed',
            'top': '200px',
            'left': '50%',
            'transform': 'translateX(-50%)',
            'zIndex': 9999,
            'width': '300px',
            'display': 'none',
            'backgroundColor': 'white',
            'padding': '15px',
            'border': '2px solid #1976d2',
            'borderRadius': '8px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
        }

        return hidden_style, 1  # Hide dropdown and refresh table

    except Exception as e:
        print(f"[Inline] Error saving category: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate


@callback(
    Output('duplicates-table-container', 'children'),
    Output('duplicates-count', 'children'),
    Input('btn-refresh-duplicates', 'n_clicks'),
    prevent_initial_call=False,
)
def load_duplicates_table(n_clicks):
    """Load and display potential duplicates."""
    try:
        # Get pending duplicates
        duplicates = db.get_potential_duplicates(include_resolved=False)

        if len(duplicates) == 0:
            return dbc.Alert("✓ No pending duplicates to review!", color="success"), html.Span(f"Pending: 0", className="text-success")

        # Build table data
        table_data = []
        for dup in duplicates:
            table_data.append({
                'duplicate_id': dup.id,
                'Date': dup.date.strftime('%Y-%m-%d'),
                'Description': dup.description,
                'Amount': f"£{dup.amount:,.2f}",
                'Account': dup.account_name,
                'Detected': dup.detected_at.strftime('%Y-%m-%d %H:%M'),
            })

        # Create table with action buttons
        table = dash_table.DataTable(
            id='duplicates-table',
            columns=[
                {'name': 'Date', 'id': 'Date'},
                {'name': 'Description', 'id': 'Description'},
                {'name': 'Amount', 'id': 'Amount'},
                {'name': 'Account', 'id': 'Account'},
                {'name': 'Detected', 'id': 'Detected'},
            ],
            data=table_data,
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            row_selectable='multi',
            selected_rows=[],
        )

        # Action buttons
        buttons = dbc.Row([
            dbc.Col([
                dbc.Button("✓ Keep Both Selected", id="btn-keep-both", color="success", size="sm", className="me-2"),
                dbc.Button("✗ Dismiss Selected", id="btn-dismiss-duplicates", color="danger", size="sm"),
            ], className="mt-3 mb-3"),
        ])

        count_msg = html.Span(f"Pending: {len(duplicates)}", className="text-warning fw-bold")

        return html.Div([buttons, table]), count_msg

    except Exception as e:
        print(f"Error loading duplicates: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error: {str(e)}", color="danger"), html.Span("Error", className="text-danger")


@callback(
    Output('duplicates-table-container', 'children', allow_duplicate=True),
    Output('duplicates-count', 'children', allow_duplicate=True),
    Input('btn-keep-both', 'n_clicks'),
    State('duplicates-table', 'selected_rows'),
    State('duplicates-table', 'data'),
    prevent_initial_call=True,
)
def keep_both_selected(n_clicks, selected_rows, table_data):
    """Keep both transactions for selected duplicates."""
    if not selected_rows or len(selected_rows) == 0:
        raise PreventUpdate

    try:
        for idx in selected_rows:
            duplicate_id = table_data[idx]['duplicate_id']
            db.keep_both_duplicate(duplicate_id)

        # Reload table
        duplicates = db.get_potential_duplicates(include_resolved=False)

        if len(duplicates) == 0:
            return dbc.Alert("✓ No pending duplicates to review!", color="success"), html.Span(f"Pending: 0", className="text-success")

        # Rebuild table (same logic as load_duplicates_table)
        table_data = []
        for dup in duplicates:
            table_data.append({
                'duplicate_id': dup.id,
                'Date': dup.date.strftime('%Y-%m-%d'),
                'Description': dup.description,
                'Amount': f"£{dup.amount:,.2f}",
                'Account': dup.account_name,
                'Detected': dup.detected_at.strftime('%Y-%m-%d %H:%M'),
            })

        table = dash_table.DataTable(
            id='duplicates-table',
            columns=[
                {'name': 'Date', 'id': 'Date'},
                {'name': 'Description', 'id': 'Description'},
                {'name': 'Amount', 'id': 'Amount'},
                {'name': 'Account', 'id': 'Account'},
                {'name': 'Detected', 'id': 'Detected'},
            ],
            data=table_data,
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            row_selectable='multi',
            selected_rows=[],
        )

        buttons = dbc.Row([
            dbc.Col([
                dbc.Button("✓ Keep Both Selected", id="btn-keep-both", color="success", size="sm", className="me-2"),
                dbc.Button("✗ Dismiss Selected", id="btn-dismiss-duplicates", color="danger", size="sm"),
            ], className="mt-3 mb-3"),
        ])

        count_msg = html.Span(f"Pending: {len(duplicates)}", className="text-warning fw-bold")

        return html.Div([buttons, table]), count_msg

    except Exception as e:
        print(f"Error keeping duplicates: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate


@callback(
    Output('duplicates-table-container', 'children', allow_duplicate=True),
    Output('duplicates-count', 'children', allow_duplicate=True),
    Input('btn-dismiss-duplicates', 'n_clicks'),
    State('duplicates-table', 'selected_rows'),
    State('duplicates-table', 'data'),
    prevent_initial_call=True,
)
def dismiss_selected(n_clicks, selected_rows, table_data):
    """Dismiss selected duplicates (keep original only)."""
    if not selected_rows or len(selected_rows) == 0:
        raise PreventUpdate

    try:
        for idx in selected_rows:
            duplicate_id = table_data[idx]['duplicate_id']
            db.resolve_duplicate(duplicate_id, 'dismissed')

        # Reload table (same logic)
        duplicates = db.get_potential_duplicates(include_resolved=False)

        if len(duplicates) == 0:
            return dbc.Alert("✓ No pending duplicates to review!", color="success"), html.Span(f"Pending: 0", className="text-success")

        table_data = []
        for dup in duplicates:
            table_data.append({
                'duplicate_id': dup.id,
                'Date': dup.date.strftime('%Y-%m-%d'),
                'Description': dup.description,
                'Amount': f"£{dup.amount:,.2f}",
                'Account': dup.account_name,
                'Detected': dup.detected_at.strftime('%Y-%m-%d %H:%M'),
            })

        table = dash_table.DataTable(
            id='duplicates-table',
            columns=[
                {'name': 'Date', 'id': 'Date'},
                {'name': 'Description', 'id': 'Description'},
                {'name': 'Amount', 'id': 'Amount'},
                {'name': 'Account', 'id': 'Account'},
                {'name': 'Detected', 'id': 'Detected'},
            ],
            data=table_data,
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            row_selectable='multi',
            selected_rows=[],
        )

        buttons = dbc.Row([
            dbc.Col([
                dbc.Button("✓ Keep Both Selected", id="btn-keep-both", color="success", size="sm", className="me-2"),
                dbc.Button("✗ Dismiss Selected", id="btn-dismiss-duplicates", color="danger", size="sm"),
            ], className="mt-3 mb-3"),
        ])

        count_msg = html.Span(f"Pending: {len(duplicates)}", className="text-warning fw-bold")

        return html.Div([buttons, table]), count_msg

    except Exception as e:
        print(f"Error dismissing duplicates: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate


@callback(
    Output('purge-modal', 'is_open'),
    Input('btn-purge-transactions', 'n_clicks'),
    Input('purge-cancel', 'n_clicks'),
    State('purge-modal', 'is_open'),
    prevent_initial_call=True,
)
def toggle_purge_modal(purge_click, cancel_click, is_open):
    """Toggle purge confirmation modal."""
    return not is_open


@callback(
    Output('reapply-rules-status', 'children', allow_duplicate=True),
    Output('purge-modal', 'is_open', allow_duplicate=True),
    Input('purge-confirm', 'n_clicks'),
    prevent_initial_call=True,
)
def execute_purge(confirm_click):
    """Execute purge of all transactions (preserves rules and categories)."""
    if confirm_click is None:
        raise PreventUpdate

    try:
        # Delete all transactions
        count = db.delete_all_transactions()

        # Close modal and show success message
        return dbc.Alert([
            html.H5("✓ All Transactions Purged", className="alert-heading"),
            html.Hr(),
            html.P([
                f"🗑️ Deleted {count} transactions",
                html.Br(),
                "✓ Rules preserved",
                html.Br(),
                "✓ Categories preserved",
            ]),
            html.P([
                html.Strong("Next step: "),
                "Upload a new CSV file to import fresh transactions. ",
                "Your existing rules will be automatically applied.",
            ], className="mb-0 small"),
        ], color="success"), False

    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger"), False


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
