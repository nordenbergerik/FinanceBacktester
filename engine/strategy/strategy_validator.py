from pydantic import ValidationError

from engine.strategy.strategy_schema import StrategySchema

def validate_strategy(strategy):
    """
    Validate the strategy dictionary against the StrategySchema.
    Raises a ValidationError if the strategy is invalid.
    """
    try:
        StrategySchema(**strategy)
    except ValidationError as e:
        raise ValueError(f"Invalid strategy: {e}")