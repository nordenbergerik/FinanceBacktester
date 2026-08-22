import pandas as pd
import pytest

from engine.strategy.strategy_executor import StrategyExecutor


def make_strategy(entry_conditions, exit_conditions, entry_logic="AND", exit_logic="OR", risk_management=None):
    return {
        "name": "Test strategy",
        "description": "Strategy used by unit tests",
        "entry_rules": {"logic": entry_logic, "conditions": entry_conditions},
        "exit_rules": {"logic": exit_logic, "conditions": exit_conditions},
        "risk_management": risk_management or {},
    }


def price_condition(operator, target_value, target_type="value"):
    return {
        "indicator": "PRICE",
        "params": {},
        "operator": operator,
        "target_type": target_type,
        "target_value": target_value,
    }


def test_entry_conditions_return_index_aligned_boolean_series():
    index = pd.date_range("2024-01-01", periods=3)
    prices = pd.DataFrame({"close": [99.0, 101.0, 100.0]}, index=index)
    executor = StrategyExecutor(
        make_strategy(
            [price_condition(">", 100), price_condition("<", 102)],
            [price_condition(">", 200)],
        )
    )

    result = executor.__evaluate_entry_conditions__(prices)

    pd.testing.assert_series_equal(result, pd.Series([False, True, False], index=index))
    assert result.dtype == bool


def test_or_logic_combines_conditions_row_by_row():
    prices = pd.DataFrame({"close": [99.0, 101.0, 103.0]})
    executor = StrategyExecutor(
        make_strategy(
            [price_condition("<", 100), price_condition(">", 102)],
            [price_condition(">", 200)],
            entry_logic="OR",
        )
    )

    assert executor.__evaluate_entry_conditions__(prices).tolist() == [True, False, True]


def test_indicator_target_and_sma_condition_are_evaluated():
    prices = pd.DataFrame({"close": [10.0, 12.0, 14.0]})
    executor = StrategyExecutor(
        make_strategy(
            [
                {
                    "indicator": "SMA",
                    "params": {"period": 2},
                    "operator": ">",
                    "target_type": "indicator",
                    "target_value": "EMA_2",
                }
            ],
            [price_condition(">", 100)],
        )
    )

    result = executor.__evaluate_entry_conditions__(prices)

    assert result.tolist() == [False, False, False]


def test_generate_signals_holds_position_until_exit():
    prices = pd.DataFrame({"close": [99.0, 101.0, 102.0, 104.0]})
    executor = StrategyExecutor(
        make_strategy(
            [price_condition(">", 100)],
            [price_condition(">", 103)],
        )
    )

    result = executor.generate_signals(prices)

    assert result.tolist() == [0.0, 1.0, 1.0, 0.0]
    assert result.index.equals(prices.index)


def test_risk_management_returns_triggers_and_position_size():
    prices = pd.DataFrame({"close": [100.0, 90.0, 100.0, 110.0]})
    executor = StrategyExecutor(
        make_strategy(
            [price_condition(">", 0)],
            [price_condition(">", 200)],
            risk_management={"stop_loss_pct": 0.05, "take_profit_pct": 0.05, "position_size": 0.5},
        )
    )

    stop_loss, take_profit, position_size = executor.__evaluate_risk_management__(prices)

    assert stop_loss.tolist() == [False, True, False, False]
    assert take_profit.tolist() == [False, False, True, True]
    assert position_size == 0.5


def test_invalid_logic_operator_is_rejected():
    executor = StrategyExecutor(
        make_strategy([price_condition(">", 100)], [price_condition(">", 200)])
    )

    with pytest.raises(ValueError, match="Invalid logic operator"):
        executor.__logic_operator__([pd.Series([True])], "XOR", pd.RangeIndex(1))
