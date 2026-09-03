from datetime import date

import pandas as pd
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import api.routes.backtests as backtests_module
from api.routes.backtests import list_strategies, run_backtest
from api.schemas import BacktestRequest
from engine.strategy.examples.presets import get_strategy_preset
from engine.strategy.strategy_executor import StrategyExecutor


@pytest.mark.parametrize("strategy_id", ["rsi_mean_reversion", "sma_trend", "ema_momentum"])
def test_strategy_presets_build_valid_executors(strategy_id):
    preset = get_strategy_preset(strategy_id)

    executor = StrategyExecutor(preset["strategy"])

    assert executor.strategy.name == preset["strategy"]["name"]


def test_strategy_list_matches_registered_presets():
    strategies = list_strategies()

    assert [strategy.id for strategy in strategies] == [
        "mock",
        "rsi_mean_reversion",
        "sma_trend",
        "ema_momentum",
    ]
    assert all(strategy.description for strategy in strategies)


@pytest.mark.parametrize(
    "payload",
    [
        {"symbol": "", "start_date": "2024-01-01", "end_date": "2024-01-02", "cash": 1000},
        {"symbol": "AAPL", "start_date": "2024-01-01", "end_date": "2024-01-02", "cash": 0},
        {"symbol": "AAPL", "start_date": "2024-01-01", "end_date": "2024-01-02", "cash": 1000, "strategy": "unknown"},
    ],
)
def test_backtest_request_rejects_invalid_values(payload):
    with pytest.raises(ValidationError):
        BacktestRequest(**payload)


def test_run_backtest_rejects_reversed_dates():
    request = BacktestRequest(
        symbol="AAPL",
        start_date="2024-01-02",
        end_date="2024-01-01",
        cash=1000,
    )

    with pytest.raises(HTTPException) as error:
        run_backtest(request)

    assert error.value.status_code == 422


def test_run_backtest_serializes_engine_result(monkeypatch):
    index = pd.to_datetime(["2024-01-01", "2024-01-02"])

    class FakeBacktest:
        def __init__(self, config):
            self.portfolio_value = [1000.0, 1015.0]

        def run(self):
            return type(
                "FakeResult",
                (),
                {
                    "metrics": {"sharpe": 1.25},
                    "dates": index,
                    "stock_df": pd.DataFrame({"adj close": [100.0, 101.5]}, index=index),
                },
            )()

    monkeypatch.setattr(backtests_module, "Backtest", FakeBacktest)

    result = run_backtest(
        BacktestRequest(
            symbol="aapl",
            start_date="2024-01-01",
            end_date="2024-01-02",
            cash=1000,
            strategy="sma_trend",
        )
    )

    assert result.symbol == "AAPL"
    assert result.strategy == "sma_trend"
    assert result.metrics == {"sharpe": 1.25}
    assert result.dates == [date(2024, 1, 1), date(2024, 1, 2)]
    assert result.prices == [100.0, 101.5]
    assert result.portfolio_values == [1000.0, 1015.0]
