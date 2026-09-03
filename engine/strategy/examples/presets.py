from copy import deepcopy


STRATEGY_PRESETS = {
    "mock": {
        "name": "Mockstrategy",
        "description": "Two-day price momentum example strategy.",
        "kind": "mock",
    },
    "rsi_mean_reversion": {
        "name": "RSI mean reversion",
        "description": "Buy below RSI 30 and exit above RSI 70.",
        "kind": "executor",
        "strategy": {
            "name": "RSI Mean Reversion",
            "description": "Buy below RSI 30 and exit above RSI 70.",
            "entry_rules": {
                "logic": "AND",
                "conditions": [{
                    "indicator": "RSI",
                    "params": {"period": 14},
                    "operator": "<",
                    "target_type": "value",
                    "target_value": 30,
                }],
            },
            "exit_rules": {
                "logic": "OR",
                "conditions": [{
                    "indicator": "RSI",
                    "params": {"period": 14},
                    "operator": ">",
                    "target_type": "value",
                    "target_value": 70,
                }],
            },
            "risk_management": {
                "stop_loss_pct": 0.03,
                "take_profit_pct": 0.08,
                "position_size": 1.0,
            },
        },
    },
    "sma_trend": {
        "name": "SMA trend",
        "description": "Stay long above the 200-day simple moving average.",
        "kind": "executor",
        "strategy": {
            "name": "SMA Trend",
            "description": "Stay long above the 200-day simple moving average.",
            "entry_rules": {
                "logic": "AND",
                "conditions": [{
                    "indicator": "PRICE",
                    "params": {},
                    "operator": ">",
                    "target_type": "indicator",
                    "target_value": "SMA_200",
                }],
            },
            "exit_rules": {
                "logic": "OR",
                "conditions": [{
                    "indicator": "PRICE",
                    "params": {},
                    "operator": "<",
                    "target_type": "indicator",
                    "target_value": "SMA_200",
                }],
            },
            "risk_management": {
                "stop_loss_pct": None,
                "take_profit_pct": None,
                "position_size": 1.0,
            },
        },
    },
    "ema_momentum": {
        "name": "EMA momentum",
        "description": "Follow price above the 20-day exponential moving average.",
        "kind": "executor",
        "strategy": {
            "name": "EMA Momentum",
            "description": "Follow price above the 20-day exponential moving average.",
            "entry_rules": {
                "logic": "AND",
                "conditions": [{
                    "indicator": "PRICE",
                    "params": {},
                    "operator": ">",
                    "target_type": "indicator",
                    "target_value": "EMA_20",
                }],
            },
            "exit_rules": {
                "logic": "OR",
                "conditions": [{
                    "indicator": "PRICE",
                    "params": {},
                    "operator": "<",
                    "target_type": "indicator",
                    "target_value": "EMA_20",
                }],
            },
            "risk_management": {
                "stop_loss_pct": 0.04,
                "take_profit_pct": None,
                "position_size": 1.0,
            },
        },
    },
}


def list_strategy_presets() -> list[dict[str, str]]:
    return [
        {"id": key, "name": value["name"], "description": value["description"]}
        for key, value in STRATEGY_PRESETS.items()
    ]


def get_strategy_preset(strategy_id: str) -> dict:
    try:
        return deepcopy(STRATEGY_PRESETS[strategy_id])
    except KeyError as error:
        raise ValueError(f"Unknown strategy: {strategy_id}") from error
