from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

StrategyId = Literal["mock", "rsi_mean_reversion", "sma_trend", "ema_momentum"]


class BacktestRequest(BaseModel):
	"""Inputs accepted by the backtest API."""

	symbol: str = Field(min_length=1, max_length=8, pattern=r"^[A-Za-z0-9.\-^]+$")
	start_date: date
	end_date: date
	cash: float = Field(gt=0)
	strategy: StrategyId = "mock"


class StrategySummary(BaseModel):
	"""Metadata for a strategy available to the frontend."""

	id: StrategyId
	name: str
	description: str


class BacktestResponse(BaseModel):
	"""Serializable outputs from one completed backtest."""

	symbol: str
	strategy: str
	start_date: date
	end_date: date
	metrics: dict[str, float]
	dates: list[date]
	prices: list[float]
	portfolio_values: list[float]
