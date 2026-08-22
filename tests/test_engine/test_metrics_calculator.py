from datetime import date

import numpy as np
import pandas as pd
import pytest

from engine.metrics_calculator import MetricsCalculator


def test_cagr_calculates_growth_over_period():
    returns = pd.Series([0.0, 0.10])

    result = MetricsCalculator.cagr(returns, date(2024, 1, 1), date(2025, 1, 1))

    assert result == pytest.approx(10.0, abs=0.2)


def test_cagr_rejects_invalid_date_types_and_formats():
    returns = pd.Series([0.0, 0.01])

    with pytest.raises(ValueError, match="Date string must be in YYYY-MM-DD format"):
        MetricsCalculator.cagr(returns, "01-01-2024", "2025-01-01")

    with pytest.raises(ValueError, match="end_date must be a string, date, or datetime"):
        MetricsCalculator.cagr(returns, "2024-01-01", 2025)


def test_sharpe_returns_zero_for_constant_returns_and_rejects_empty_input():
    assert MetricsCalculator.sharpe(pd.Series([0.01, 0.01, 0.01])) == 0.0

    with pytest.raises(ValueError, match="at least one value"):
        MetricsCalculator.sharpe([])


def test_max_drawdown_returns_largest_peak_to_trough_loss():
    returns = pd.Series([0.10, -0.20, 0.05])

    assert MetricsCalculator.max_drawdown(returns) == pytest.approx(0.20)


def test_beta_and_alpha_match_known_linear_relationship():
    market_returns = pd.Series([0.01, 0.02, 0.03, 0.04])
    asset_returns = 2 * market_returns + 0.01

    assert MetricsCalculator.beta(asset_returns, market_returns) == pytest.approx(2.0)
    assert MetricsCalculator.alpha(asset_returns, market_returns) == pytest.approx(0.01)


def test_calmar_ratio_combines_cagr_and_drawdown():
    returns = pd.Series([0.0, 0.10, -0.05])

    result = MetricsCalculator.calmar_ratio(returns, "2024-01-01", "2025-01-01")

    expected_cagr = MetricsCalculator.cagr(returns, "2024-01-01", "2025-01-01")
    expected_drawdown = MetricsCalculator.max_drawdown(returns)
    assert result == pytest.approx(expected_cagr / expected_drawdown)
