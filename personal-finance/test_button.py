"""
Simple test to verify the categorize button callback works.

This creates a minimal Dash app with just a button and text output
to test if callbacks are working properly.
"""
import dash
from dash import html, dbc, Input, Output, callback
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Button Callback Test"),
    html.Hr(),

    dbc.Button("Click Me to Test", id="test-button", color="primary", className="mb-3"),

    html.Div(id="test-output", className="mt-3"),

    html.P("If the button works, you should see a message appear below when you click it.", className="text-muted mt-3"),
], className="mt-5")


@callback(
    Output('test-output', 'children'),
    Input('test-button', 'n_clicks'),
    prevent_initial_call=True,
)
def test_callback(n_clicks):
    """Test callback - should trigger when button is clicked."""
    print(f"[TEST] Button clicked! n_clicks={n_clicks}")

    if n_clicks is None:
        print("[TEST] n_clicks is None")
        raise PreventUpdate

    return dbc.Alert(f"✓ Button callback works! Clicked {n_clicks} times.", color="success")


if __name__ == '__main__':
    print("=" * 80)
    print("BUTTON CALLBACK TEST")
    print("=" * 80)
    print("Open http://localhost:8051/")
    print("Click the button and watch this terminal for debug output")
    print("=" * 80)

    app.run(debug=True, host='0.0.0.0', port=8051)
