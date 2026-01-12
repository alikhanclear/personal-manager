"""
Simple test to verify DataTable dropdown works
"""
import dash
from dash import dash_table, html
import dash_bootstrap_components as dbc

# Create simple test data
data = [
    {'id': 1, 'Pattern': 'TESCO', 'Category': 'Groceries', 'Priority': 10},
    {'id': 2, 'Pattern': 'AMAZON', 'Category': 'Shopping', 'Priority': 5},
    {'id': 3, 'Pattern': 'STARBUCKS', 'Category': 'Dining Out', 'Priority': 8},
]

# Category options for dropdown
category_options = [
    {'label': 'Groceries', 'value': 'Groceries'},
    {'label': 'Shopping', 'value': 'Shopping'},
    {'label': 'Dining Out', 'value': 'Dining Out'},
    {'label': 'Transport', 'value': 'Transport'},
    {'label': 'Entertainment', 'value': 'Entertainment'},
]

# Columns with dropdown
columns = [
    {'name': 'Pattern', 'id': 'Pattern', 'editable': True},
    {'name': 'Category', 'id': 'Category', 'editable': True, 'presentation': 'dropdown'},
    {'name': 'Priority', 'id': 'Priority', 'editable': True, 'type': 'numeric'},
]

# Create app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Dropdown Test", className="mt-3 mb-3"),
    html.P("Click on a Category cell to see the dropdown", className="text-muted mb-3"),

    dash_table.DataTable(
        id='test-table',
        data=data,
        columns=columns,
        editable=True,
        row_deletable=True,
        dropdown={
            'Category': {
                'options': category_options,
                'clearable': False,
            }
        },
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'fontSize': '14px',
        },
        style_header={
            'backgroundColor': '#343a40',
            'color': 'white',
            'fontWeight': 'bold',
        },
    ),

    html.P("Instructions: Click on any Category cell (e.g., 'Groceries') to edit it. You should see a dropdown.",
           className="mt-3 text-info"),
], fluid=True)

if __name__ == '__main__':
    print("=" * 60)
    print("Dropdown Test App")
    print("=" * 60)
    print("Server: http://localhost:8051/")
    print("=" * 60)
    print("\nCategory dropdown options configured:", category_options)
    app.run(debug=True, host='0.0.0.0', port=8051)
