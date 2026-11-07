from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Union, List, Optional

OperatorType = Literal["<", ">", "==", "<=", ">="]
IndicatorName = Literal["PRICE", "SMA", "EMA", "RSI", "MACD", "BOLLINGER_UPPER", "BOLLINGER_MIDDLE", "BOLLINGER_LOWER"]

class IndicatorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: Optional[int] = Field(default=None, description="Window size for a single-period indicator")
    fast_period: Optional[int] = Field(default=None, description="Fast MACD EMA window")
    slow_period: Optional[int] = Field(default=None, description="Slow MACD EMA window")
    signal_period: Optional[int] = Field(default=None, description="MACD signal EMA window")
    num_std_dev: Optional[float] = Field(default=None, description="Bollinger band standard deviation multiplier")
    component: Optional[Literal["macd", "signal", "histogram"]] = Field(
        default=None,
        description="MACD series to compare",
    )

# Model for a single condition (e.g., RSI < 30)
class Condition(BaseModel):
    indicator: IndicatorName = Field(description="Indicator to be evaluated")
    params: IndicatorParams = Field(default_factory=IndicatorParams, description="Parameters for the indicator")
    operator: OperatorType = Field(description="Comparison operator")
    target_type: Literal["value", "indicator"] = Field(description="Whether comparison is against a fixed value or another indicator")
    target_value: Union[float, str] = Field(description="Numeric threshold (e.g., 30) or the name of another indicator (e.g., 'SMA_200')")

# Rule set for entry or exit
class RuleGroup(BaseModel):
    logic: Literal["AND", "OR"] = Field(default="AND", description="How conditions should be combined")
    conditions: List[Condition]

# Risk management rules
class RiskRules(BaseModel):
    stop_loss_pct: Optional[float] = Field(None, description="Stop loss percentage, e.g. 0.02 for 2%")
    take_profit_pct: Optional[float] = Field(None, description="Take profit percentage, e.g. 0.05 for 5%")
    position_size: float = Field(default=1.0, description="Portion of capital to invest (0.0 - 1.0)")

# Main model for the entire strategy
class StrategySchema(BaseModel):
    name: str = Field(description="Name of the strategy")
    description: str = Field(description="Short description of the logic")
    entry_rules: RuleGroup = Field(description="Conditions for entering a position (Buy)")
    exit_rules: RuleGroup = Field(description="Conditions for exiting a position (Sell)")
    risk_management: RiskRules = Field(default_factory=RiskRules)

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