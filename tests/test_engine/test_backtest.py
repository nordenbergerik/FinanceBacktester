import numpy as np
import pandas as pd
import pytest

import engine.backtest as backtest_module
from engine.backtest import Backtest
from engine.backtest_config import BacktestConfig
from engine.data.loader import DataLoader
from engine.strategy.base import Strategy


class FakeStrategy(Strategy):
    def __init__(self, signals):
        self.signals = signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(self.signals, index=df.index)


class DummyFigure:
    def __init__(self):
        self.traces = []

    def add_scatter(self, **kwargs):
        self.traces.append(kwargs)


class DummyPlot:
    def line(self, title=None):
        return DummyFigure()


class FakeLoader(DataLoader):
    def __init__(self, data_by_symbol):
        self.data_by_symbol = data_by_symbol

    def load(self, symbol, start, end):
        if symbol not in self.data_by_symbol:
            raise AssertionError(f"Unexpected symbol: {symbol}")
        return self.data_by_symbol[symbol]


def test_backtest_run_builds_expected_portfolio_and_buy_and_hold(monkeypatch):
    prices = pd.DataFrame(
        {"close": [100.0, 110.0, 121.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )
    market_prices = pd.DataFrame(
        {"close": [200.0, 198.0, 202.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )

    monkeypatch.setattr(backtest_module, "DataLoader", lambda: FakeLoader({"TEST": prices, "^GSPC": market_prices}))
    monkeypatch.setattr(backtest_module, "px", DummyPlot())

    metrics_called = {}

    def fake_calculate_metrics(self, daily_returns, market_returns, start_date, end_date):
        metrics_called["daily_returns"] = daily_returns.tolist()
        metrics_called["market_returns"] = market_returns.tolist()
        metrics_called["start_date"] = start_date
        metrics_called["end_date"] = end_date
        return {"alpha": 0.5, "beta": 1.2}

    monkeypatch.setattr(backtest_module.Backtest, "calculate_metrics", fake_calculate_metrics)

    strategy = FakeStrategy([1, 0, 0])
    config = BacktestConfig(
        strategy=strategy,
        symbol="TEST",
        loader=FakeLoader({"TEST": prices, "^GSPC": market_prices}),
        start_date="2024-01-01",
        end_date="2024-01-03",
        cash=100.0,
    )
    backtest = Backtest(config)
    result = backtest.run()

    np.testing.assert_allclose(backtest.portfolio_value, [100.0, 110.0, 121.0])
    assert result.return_buyandhold == pytest.approx(21.0)
    assert list(result.dates) == list(prices.index)
    assert result.metrics == {"alpha": 0.5, "beta": 1.2}
    assert metrics_called["start_date"] == pd.to_datetime("2024-01-01").date()
    assert metrics_called["end_date"] == pd.to_datetime("2024-01-03").date()


def test_calculate_metrics_uses_metrics_calculator(monkeypatch):
    monkeypatch.setattr(backtest_module.MetricsCalculator, "cagr", lambda daily_returns, start_date, end_date: 11.11)
    monkeypatch.setattr(backtest_module.MetricsCalculator, "sharpe", lambda daily_returns, risk_free_rate: 2.22)
    monkeypatch.setattr(backtest_module.MetricsCalculator, "max_drawdown", lambda daily_returns: 0.33)
    monkeypatch.setattr(backtest_module.MetricsCalculator, "alpha", lambda asset_returns, market_returns, risk_free_rate: 0.44)
    monkeypatch.setattr(backtest_module.MetricsCalculator, "beta", lambda asset_returns, market_returns: 0.55)

    config = BacktestConfig(
        strategy=FakeStrategy([0]),
        symbol="TEST",
        start_date="2024-01-01",
        end_date="2024-01-03",
        cash=100.0,
    )
    backtest = Backtest(config)
    metrics = backtest.calculate_metrics(
        daily_returns=pd.Series([0.0, 0.01, 0.02]),
        market_returns=pd.Series([0.0, 0.005, 0.01]),
        start_date="2024-01-01",
        end_date="2024-01-03",
    )

    assert metrics == {
        "cagr": 11.11,
        "sharpe": 2.22,
        "max_drawdown": 0.33,
        "alpha": 0.44,
        "beta": 0.55,
    }


def test_cagr_accepts_date_objects():
    from engine.metrics_calculator import MetricsCalculator

    returns = pd.Series([0.0, 0.01, 0.02])
    start = pd.to_datetime("2024-01-01").date()
    end = pd.to_datetime("2024-01-03").date()

    cagr_value = MetricsCalculator.cagr(returns, start, end)

    assert isinstance(cagr_value, float)


def test_set_start_date_and_end_date_accepts_valid_strings():
    config = BacktestConfig(
        strategy=FakeStrategy([0]),
        symbol="TEST",
        start_date="2024-01-01",
        end_date="2024-01-02",
        cash=100.0,
    )
    backtest = Backtest(config)
    backtest.set_start_date("2024-02-01")
    backtest.set_end_date("2024-02-28")

    assert backtest.start_date == "2024-02-01"
    assert backtest.end_date == "2024-02-28"


@pytest.mark.parametrize("invalid_date", ["2024-02-30", "not-a-date", "2024/02/01"])
def test_set_start_date_rejects_invalid_string(invalid_date):
    config = BacktestConfig(
        strategy=FakeStrategy([0]),
        symbol="TEST",
        start_date="2024-01-01",
        end_date="2024-01-02",
        cash=100.0,
    )
    backtest = Backtest(config)

    with pytest.raises(ValueError, match="Date string must be in YYYY-MM-DD format"):
        backtest.set_start_date(invalid_date)
