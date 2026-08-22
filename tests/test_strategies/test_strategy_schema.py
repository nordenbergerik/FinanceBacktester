import pytest
from pydantic import ValidationError

from engine.strategy.strategy_schema import Condition, RuleGroup, StrategySchema


def test_strategy_schema_builds_nested_rule_models():
    strategy = StrategySchema(
        name="RSI strategy",
        description="Test strategy",
        entry_rules=RuleGroup(
            logic="AND",
            conditions=[
                Condition(
                    indicator="RSI",
                    params={"period": 14},
                    operator="<",
                    target_type="value",
                    target_value=30,
                )
            ],
        ),
        exit_rules=RuleGroup(
            conditions=[
                Condition(
                    indicator="PRICE",
                    operator=">",
                    target_type="indicator",
                    target_value="SMA_20",
                )
            ],
        ),
    )

    assert strategy.entry_rules.logic == "AND"
    assert strategy.exit_rules.logic == "AND"
    assert strategy.entry_rules.conditions[0].target_value == 30


def test_strategy_schema_rejects_invalid_condition_values():
    with pytest.raises(ValidationError):
        Condition(
            indicator="RSI",
            operator="!=",
            target_type="value",
            target_value=30,
        )

    with pytest.raises(ValidationError):
        Condition(
            indicator="RSI",
            operator="<",
            target_type="unsupported",
            target_value=30,
        )
