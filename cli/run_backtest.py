from engine.data.loader import DataLoader
from engine.strategy.examples.mockstrategy import Mockstrategy
from engine.backtest import Backtest

import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from datetime import date

# Initialize the app
app = dash.Dash(__name__)
app.title = "Stock Visualisation Dashboard"

# Define the layout
app.layout = html.Div([
    html.H1("Stock Visualisation Dashboard"),
    html.H4("Enter a stock symbol (e.g., AAPL):"),
    dcc.Input(id='input', value='AAPL', type='text'),
    html.Button('Run Backtest', id='run-button', n_clicks=0),
    html.H4(id='buy-and-hold-output', children=""),
    html.H4(id='metrics-output', children=""),
    html.Div(id='output-graph')
])

# Callback to update the graph
@app.callback(
    Output('output-graph', 'children'),
    Output('buy-and-hold-output', 'children'),
    Output('metrics-output', 'children'),
    [Input('run-button', 'n_clicks')],
    [Input('input', 'value')]
)
def update_graph(n_clicks, stock_symbol):
    if n_clicks > 0:  # Only run when button is clicked
        try:
            # Run backtest
            backtest = Backtest(
                strategy=Mockstrategy(),
                symbol=stock_symbol,
                start_date="2010-01-01",
                end_date="2023-06-01",
                cash=1000.0
            )
            backtest_result = backtest.run()
            return_buyandhold = backtest_result.return_buyandhold

            try:
                metrics_text = "\n".join(
                    f"{key}: {value:.4f}" if isinstance(value, float)
                    else f"{key}: {value}" if isinstance(value, (int, str))
                    else f"{key}: {str(value)}"
                    for key, value in backtest_result.metrics.items()
                    if not isinstance(value, Exception)  # Skip exceptions
                )
            except Exception as e:
                metrics_text = e

            return (
                html.Div([
                    dcc.Graph(figure=backtest_result.plot),
                ]),
                f"ROI of buy and hold: {return_buyandhold:.2f}%",
                f"Metrics: {metrics_text}"
            )

        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={'color': 'red'}), "", ""

    return html.Div("Click the button to run the backtest"), "", ""

# Run the app
if __name__ == '__main__':
    print("Starting Dash app... Open http://127.0.0.1:8050/")
    app.run(debug=True)