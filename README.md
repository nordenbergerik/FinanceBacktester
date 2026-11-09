# Finance Backtester

A modular Python backtesting platform with a FastAPI service and a lightweight browser frontend. It downloads historical market data, applies configurable trading strategies, and returns performance metrics and portfolio data through a documented HTTP API.

## Highlights

- Clean separation between market data loading, strategy execution, backtesting, metrics, and presentation.
- Pydantic validation for API requests, strategy definitions, dates, symbols, and capital.
- Historical data loaded through `yfinance`, normalized into validated OHLCV data, and aligned with an S&P 500 benchmark.
- Strategy presets for price momentum, RSI mean reversion, SMA trend following, and EMA momentum.
- AI-generated strategies validated against the same strategy schema and executed by the backtest engine.
- Performance metrics including buy-and-hold return, CAGR, Sharpe and Sortino ratios, maximum drawdown, alpha, beta, and Calmar ratio.
- Interactive Plotly performance chart comparing the stock, S&P 500 benchmark, and strategy cumulative returns.
- FastAPI endpoints with CORS support for the static frontend.
- Automated test coverage for the API contract, strategy presets, engine, indicators, and backtest behavior.

## Screenshots
![Project Screenshot](assets/images/Backtester-Homepage.png)
![Project Screenshot](assets/images/ai-studio.png)

## Architecture

```text
yfinance
	|
	v
DataLoader -> validated OHLCV DataFrame
	|
	v
Strategy / StrategyExecutor -> position signals
	|
	v
Backtest -> portfolio values, metrics, and performance chart
	|
	+-> FastAPI -> browser frontend
```

The core engine is independent of the web layer. A `BacktestConfig` describes a run, while `Backtest` performs the calculation and returns a `BacktestResult`, including a Plotly `performance_chart`. The API serializes the chart's Plotly data and layout to JSON for the frontend, which renders it with Plotly.js.

## Strategies

The frontend loads the available strategies from the backend at runtime:

| ID | Strategy | Logic |
| --- | --- | --- |
| `mock` | Mockstrategy | Example two-day price momentum strategy |
| `rsi_mean_reversion` | RSI mean reversion | Enters below RSI 30 and exits above RSI 70, with risk limits |
| `sma_trend` | SMA trend | Enters while price is above the 200-day SMA |
| `ema_momentum` | EMA momentum | Enters while price is above the 20-day EMA, with a stop loss |

Strategies using indicator conditions are validated by `StrategySchema` and executed by `StrategyExecutor`. This makes it possible to add new presets without changing the API or frontend contract.

The strategy schema only permits supported indicators (`PRICE`, `SMA`, `EMA`, `RSI`, `MACD`, and the Bollinger bands) and comparison operators (`<`, `>`, `==`, `<=`, `>=`). Indicator parameters are constrained to the fields understood by the executor: `period`, `fast_period`, `slow_period`, `signal_period`, `num_std_dev`, and `component`. Unsupported fields are rejected.

## API

Start a backtest with `POST /api/backtests`:

```json
{
  "symbol": "AAPL",
  "start_date": "2019-01-01",
  "end_date": "2024-01-01",
  "cash": 10000,
  "strategy": "rsi_mean_reversion"
}
```

Available strategies are returned by `GET /api/backtests/strategies`. A health check is available at `GET /health`, and interactive API documentation is served at `/docs`.

### Run a generated strategy

The AI Studio flow has two steps:

1. Send `{"prompt": "Buy when RSI is below 30 and sell when RSI is above 70"}` to `POST /api/backtests/generateStrategy`. The endpoint returns a strategy object validated against `StrategySchema`.
2. Send the usual backtest inputs to `POST /api/backtests`, passing that returned object as the `strategy` value.

For example:

```json
{
  "symbol": "AAPL",
  "start_date": "2019-01-01",
  "end_date": "2024-01-01",
  "cash": 10000,
  "strategy": {
    "name": "Generated RSI strategy",
    "description": "Buy below RSI 30 and sell above RSI 70.",
    "entry_rules": {
      "logic": "AND",
      "conditions": [
        {
          "indicator": "RSI",
          "params": {"period": 14},
          "operator": "<",
          "target_type": "value",
          "target_value": 30
        }
      ]
    },
    "exit_rules": {
      "logic": "OR",
      "conditions": [
        {
          "indicator": "RSI",
          "params": {"period": 14},
          "operator": ">",
          "target_type": "value",
          "target_value": 70
        }
      ]
    },
    "risk_management": {
      "stop_loss_pct": null,
      "take_profit_pct": null,
      "position_size": 1.0
    }
  }
}
```

`strategy` can be a preset ID such as `"rsi_mean_reversion"` or a generated strategy object. When an object is supplied, the API validates it and runs it through `StrategyExecutor`.

The browser UI follows the same flow: generate a strategy in **AI Studio**, then open **Configuration** and select **Run generated strategy**. The generated strategy is kept in browser `localStorage` for that site origin.

The strategy generator reads the API key from the backend environment variable `OPENAI_API_KEY`. For local development, create a `.env` file in the project root (keep it out of version control) containing:

```env
OPENAI_API_KEY=your_openai_api_key
```

Restart the backend after adding or changing the key. Never put the key in frontend code or send it to the browser.

The backtest response includes:

- The normalized symbol, selected strategy, and date range
- Calculated metrics
- Daily dates and adjusted closing prices
- Daily portfolio values
- A `performance_chart` object with Plotly `data` and `layout` for rendering the stock, benchmark, and strategy cumulative returns

The static frontend displays this chart after a successful backtest. It uses Plotly.js from the Plotly CDN, so the browser needs access to that CDN.

## Run Locally

The project requires Python 3.11 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
start-app
```

Open the frontend at [http://localhost:4173](http://localhost:4173). The API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

The `start-app` command launches both the FastAPI server and the static frontend. Press `Ctrl+C` to stop both processes.

## Test

```bash
python -m pytest -q
```

The test suite covers API request validation and response serialization, data models and loading, indicator calculations, strategy execution, backtest portfolio behavior, chart output, and metrics.

## Project Structure

```text
api/                  FastAPI application, schemas, and routes
cli/                  Application launcher
engine/               Backtest engine and strategy abstractions
engine/data/          Market data loading and validation
engine/strategy/      Strategy schemas, executor, and presets
indicators/           Technical indicator calculations
frontend/             Static browser interface
tests/                Automated tests by subsystem
```



## Scope and Next Steps

The current implementation is intentionally focused on a reliable single-run workflow. Natural next steps include persisted backtest history, transaction costs and slippage, richer chart serialization, asynchronous job execution for long data ranges, and HTTP-level API integration tests.