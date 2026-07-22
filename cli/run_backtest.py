from engine.data.loader import DataLoader
from engine.strategy.examples.mockstrategy import Mockstrategy
from engine.backtest import Backtest

import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Initialize the app
app = dash.Dash(__name__)
app.title = "Stock Visualisation Dashboard"

# Define the layout
app.layout = html.Div([
    html.H1("Stock Visualisation Dashboard"),
    html.H4("Enter a stock symbol (e.g., AAPL):"),
    dcc.Input(id='input', value='AAPL', type='text'),
    html.Button('Run Backtest', id='run-button', n_clicks=0),
    html.Div(id='output-graph')
])

# Callback to update the graph
@app.callback(
    Output('output-graph', 'children'),
    [Input('run-button', 'n_clicks')],
    [Input('input', 'value')]
)
def update_graph(n_clicks, stock_symbol):
    if n_clicks > 0:  # Only run when button is clicked
        try:
            # Load data
            loader = DataLoader()
            df = loader.load(stock_symbol, start="2023-01-01", end="2023-06-01")

            # Run backtest
            backtest = Backtest(
                strategy=Mockstrategy(),
                symbol=stock_symbol,
                start_date="2023-01-01",
                end_date="2023-06-01",
                cash=1000.0
            )
            backtest_result = backtest.run()

            return html.Div([
                dcc.Graph(figure=backtest_result.price_curve),
                dcc.Graph(figure=backtest_result.roi_curve)
                # dcc.Graph(figure=roi_curve),
                # dcc.Graph(figure=price_curve)
            ])

        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={'color': 'red'})

    return html.Div("Click the button to run the backtest")

# Run the app
if __name__ == '__main__':
    print("Starting Dash app... Open http://127.0.0.1:8050/")
    app.run(debug=True)