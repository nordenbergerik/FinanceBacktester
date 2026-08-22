from pydantic import ValidationError

from engine.strategy.strategy_schema import StrategySchema

def validate_strategy(strategy):
    """
    Validate the strategy dictionary against the StrategySchema.
    Raises a ValidationError if the strategy is invalid.
    """
    try:
        x = StrategySchema(**strategy)
        __validate_entry_exit_rules(strategy.get("entry_rules", {}))
        __validate_entry_exit_rules(strategy.get("exit_rules", {}))
        __validate_risk_management(strategy.get("risk_management", {}))
    except ValidationError as e:
        raise ValueError(f"Invalid strategy: {e}")
    

def __validate_entry_exit_rules(rules):
    """
    Validate the entry and exit rules of the strategy.
    Raises a ValueError if the rules are invalid.
    """
    if not isinstance(rules, dict):
        raise ValueError("Rules must be a dictionary.")
    
    if "logic" not in rules or "conditions" not in rules:
        raise ValueError("Rules must contain 'logic' and 'conditions' keys.")
    
    if rules["logic"] not in ["AND", "OR"]:
        raise ValueError("Logic must be either 'AND' or 'OR'.")
    
    if not isinstance(rules["conditions"], list) or len(rules["conditions"]) == 0:
        raise ValueError("Conditions must be a non-empty list.")
    
    for condition in rules["conditions"]:
        if not isinstance(condition, dict):
            raise ValueError("Each condition must be a dictionary.")
        
        required_keys = {"indicator", "params", "operator", "target_type", "target_value"}
        if not required_keys.issubset(condition.keys()):
            raise ValueError(f"Condition is missing required keys: {required_keys - set(condition.keys())}")    

def __validate_risk_management(risk_rules):
    """
    Validate the risk management rules of the strategy.
    Raises a ValueError if the risk rules are invalid.
    """
    if not isinstance(risk_rules, dict):
        raise ValueError("Risk management rules must be a dictionary.")
    
    if "stop_loss_pct" in risk_rules and not isinstance(risk_rules["stop_loss_pct"], (float, type(None))):
        raise ValueError("stop_loss_pct must be a float or None.")
    
    if "take_profit_pct" in risk_rules and not isinstance(risk_rules["take_profit_pct"], (float, type(None))):
        raise ValueError("take_profit_pct must be a float or None.")
    
    if "position_size" in risk_rules:
        position_size = risk_rules["position_size"]
        if not isinstance(position_size, float) or not (0.0 <= position_size <= 1.0):
            raise ValueError("position_size must be a float between 0.0 and 1.0.")