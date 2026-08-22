from dataclasses import FrozenInstanceError
from datetime import date, datetime

import pytest

from engine.backtest_config import BacktestConfig
from engine.data.models import Bar
from engine.strategy.base import Strategy


class StubStrategy(Strategy):
    def generate_signals(self, df):
        raise NotImplementedError


def test_bar_calculates_typical_price_and_bullish_state():
    bar = Bar(
        symbol="TEST",
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1_000,
    )

    assert bar.typical_price == pytest.approx(101.6666666667)
    assert bar.is_bullish is True


def test_bar_rejects_invalid_ohlc_and_volume_values():
    with pytest.raises(ValueError, match="high .* cannot be less than low"):
        Bar("TEST", datetime(2024, 1, 1), 100, 90, 95, 98, 1)

    with pytest.raises(ValueError, match="open .* outside"):
        Bar("TEST", datetime(2024, 1, 1), 120, 110, 90, 100, 1)

    with pytest.raises(ValueError, match="close .* outside"):
        Bar("TEST", datetime(2024, 1, 1), 100, 110, 90, 120, 1)

    with pytest.raises(ValueError, match="volume cannot be negative"):
        Bar("TEST", datetime(2024, 1, 1), 100, 110, 90, 100, -1)


def test_bar_is_immutable():
    bar = Bar("TEST", datetime(2024, 1, 1), 100, 110, 90, 100, 1)

    with pytest.raises(FrozenInstanceError):
        bar.close = 101


def test_backtest_config_parses_string_dates_and_applies_defaults():
    config = BacktestConfig(
        strategy=StubStrategy(),
        symbol="TEST",
        start_date="2024-01-01",
        end_date="2024-01-31",
        cash=1_000.0,
    )

    assert config.start_date == date(2024, 1, 1)
    assert config.end_date == date(2024, 1, 31)
    assert config.shares == 0


@pytest.mark.parametrize("invalid_date", ["2024-02-30", "2024/01/01", "not-a-date"])
def test_backtest_config_rejects_invalid_date_strings(invalid_date):
    with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
        BacktestConfig(
            strategy=StubStrategy(),
            symbol="TEST",
            start_date=invalid_date,
            end_date="2024-01-31",
            cash=1_000.0,
        )
