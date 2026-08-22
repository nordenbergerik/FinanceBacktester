import pandas as pd

from engine.strategy.base import Strategy
from engine.strategy.strategy_schema import IndicatorName, StrategySchema, Condition
from engine.strategy.strategy_validator import validate_strategy
from indicators.bollinger import calculate_bollinger_bands
from indicators.ema import calculate_ema
from indicators.sma import calculate_sma
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd


class StrategyExecutor(Strategy):
    def __init__(self, strategy: dict):
        """Validate and store a dictionary-based trading strategy."""
        validate_strategy(strategy)
        self.strategy = StrategySchema(**strategy)

    def generate_signals(self, df: pd.DataFrame):
        """Generate position signals, including configured risk exits."""
        entry_conditions = self.__evaluate_entry_conditions__(df)
        exit_conditions = self.__evaluate_exit_conditions__(df)
        stop_loss, take_profit, _ = self.__evaluate_risk_management__(df)
        exit_conditions = exit_conditions | stop_loss | take_profit

        # Store the position state, so an entry is held until an exit occurs.
        positions = pd.Series(index=df.index, dtype="float64")
        positions.loc[entry_conditions] = 1.0
        positions.loc[exit_conditions] = 0.0
        return positions.ffill().fillna(0.0)

    def __evaluate_strategy__(self, df: pd.DataFrame) -> pd.Series:
        """Evaluate the strategy's entry conditions for the supplied prices."""
        return self.__evaluate_entry_conditions__(df)



    def __evaluate_entry_conditions__(self, df: pd.DataFrame) -> pd.Series:
        """Combine all configured entry conditions into one boolean series."""
        entry_conditions = self.strategy.entry_rules.conditions
        entry_logic_operator = self.strategy.entry_rules.logic
        entry_results = [self.__evaluate_condition__(df, cond) for cond in entry_conditions]
        return self.__logic_operator__(entry_results, entry_logic_operator, df.index)

    def __evaluate_exit_conditions__(self, df: pd.DataFrame) -> pd.Series:
        """Combine all configured exit conditions into one boolean series."""
        exit_conditions = self.strategy.exit_rules.conditions
        exit_logic_operator = self.strategy.exit_rules.logic
        exit_results = [self.__evaluate_condition__(df, cond) for cond in exit_conditions]
        return self.__logic_operator__(exit_results, exit_logic_operator, df.index)

    def __evaluate_risk_management__(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, float]:
        """Identify stop-loss and take-profit triggers from daily price returns."""
        closing_prices = df["close"]
        stop_loss_pct = self.strategy.risk_management.stop_loss_pct
        take_profit_pct = self.strategy.risk_management.take_profit_pct
        position_size = self.strategy.risk_management.position_size
        price_returns = closing_prices.pct_change().fillna(0)
        if stop_loss_pct is not None:
            stop_loss_triggered = price_returns < -stop_loss_pct
        else:
            stop_loss_triggered = pd.Series([False] * len(df), index=df.index)
        if take_profit_pct is not None:
            take_profit_triggered = price_returns > take_profit_pct
        else:
            take_profit_triggered = pd.Series([False] * len(df), index=df.index)
        return stop_loss_triggered, take_profit_triggered, position_size

    def __logic_operator__(self, results: list[pd.Series], operator: str, index) -> pd.Series:
        """Combine condition results row by row using AND or OR logic."""
        if not results:
            return pd.Series(False, index=index, dtype=bool)

        combined = pd.concat(results, axis=1)
        if operator == "AND":
            return combined.all(axis=1)
        elif operator == "OR":
            return combined.any(axis=1)
        else:
            raise ValueError(f"Invalid logic operator: {operator}. Expected 'AND' or 'OR'.")

    def __evaluate_condition__(self, df: pd.DataFrame, condition: Condition) -> pd.Series:
        """Evaluate one condition against prices or a calculated indicator."""
        if condition.indicator == "PRICE":
            values = df["close"]
        else:
            values = self.__calculate_indicator__(df, condition.indicator, condition.params)
            if isinstance(values, pd.DataFrame):
                component = condition.params.get("component", "macd")
                if component not in values:
                    raise ValueError(f"Invalid MACD component: '{component}'")
                values = values[component]

        if condition.target_type == "value":
            target = condition.target_value
        else:
            target_name, separator, target_period = str(condition.target_value).partition("_")
            if not separator or not target_period.isdigit():
                raise ValueError("Indicator targets must use the format 'INDICATOR_PERIOD'")
            target = self.__calculate_indicator__(
                df,
                target_name,
                {"period": int(target_period)},
            )

        comparisons = {
            "<": values < target,
            ">": values > target,
            "==": values == target,
            "<=": values <= target,
            ">=": values >= target,
        }
        return comparisons[condition.operator].fillna(False).astype(bool)

    def __calculate_indicator__(self, df: pd.DataFrame, indicator: IndicatorName, params: dict):
        """Dispatch an indicator name to its calculation function."""
        match indicator:
            case "SMA":
                return calculate_sma(prices=df["close"], window=params.get("period"))
            case "RSI":
                return calculate_rsi(prices=df["close"], window=params.get("period"))
            case "MACD":
                return calculate_macd(prices=df["close"], fast=params.get("fast_period", 12), slow=params.get("slow_period", 26), signal=params.get("signal_period", 9))
            case "EMA":
                return calculate_ema(prices=df["close"], window=params.get("period"))
            case "BOLLINGER_UPPER":
                return calculate_bollinger_bands(prices=df["close"], window=params.get("period"), num_std_dev=params.get("num_std_dev", 2))[0]
            case "BOLLINGER_MIDDLE":
                return calculate_bollinger_bands(prices=df["close"], window=params.get("period"), num_std_dev=params.get("num_std_dev", 2))[1]
            case "BOLLINGER_LOWER":
                return calculate_bollinger_bands(prices=df["close"], window=params.get("period"), num_std_dev=params.get("num_std_dev", 2))[2]
            case _:
                raise ValueError(
                    f"Invalid indicator: '{indicator}'. Expected one of: ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER_UPPER', 'BOLLINGER_MIDDLE', 'BOLLINGER_LOWER']"
                )

# EXAMPLE JSON
# {
#   "name": "RSI Mean Reversion",
#   "description": "Köp vid översålt läge över långsiktig trend",
#   "entry_rules": {
#     "logic": "AND",
#     "conditions": [
#       {
#         "indicator": "RSI",
#         "params": {"period": 14},
#         "operator": "<",
#         "target_type": "value",
#         "target_value": 30
#       },
#       {
#         "indicator": "PRICE",
#         "params": {},
#         "operator": ">",
#         "target_type": "indicator",
#         "target_value": "SMA_200"
#       }
#     ]
#   },
#   "exit_rules": {
#     "logic": "OR",
#     "conditions": [
#       {
#         "indicator": "RSI",
#         "params": {"period": 14},
#         "operator": ">",
#         "target_type": "value",
#         "target_value": 70
#       }
#     ]
#   },
#   "risk_management": {
#     "stop_loss_pct": 0.03,
#     "take_profit_pct": 0.08,
#     "position_size": 1.0
#   }
# }