from fastapi import APIRouter, HTTPException

from api.schemas import BacktestRequest, BacktestResponse, StrategySummary
from engine.backtest import Backtest
from engine.backtest_config import BacktestConfig
from engine.data.loader import DataLoader
from engine.strategy.examples.mockstrategy import Mockstrategy
from engine.strategy.examples.presets import get_strategy_preset, list_strategy_presets
from engine.strategy.strategy_executor import StrategyExecutor


router = APIRouter(prefix="/api/backtests", tags=["backtests"])


@router.get("/strategies", response_model=list[StrategySummary])
def list_strategies() -> list[StrategySummary]:
	return [StrategySummary(**strategy) for strategy in list_strategy_presets()]


@router.post("", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest) -> BacktestResponse:
	"""Run a registered strategy for the requested asset and dates."""
	if request.start_date >= request.end_date:
		raise HTTPException(status_code=422, detail="start_date must be before end_date")

	try:
		preset = get_strategy_preset(request.strategy)
		strategy = Mockstrategy() if preset["kind"] == "mock" else StrategyExecutor(preset["strategy"])
		config = BacktestConfig(
			strategy=strategy,
			symbol=request.symbol.upper(),
			loader=DataLoader(),
			start_date=request.start_date,
			end_date=request.end_date,
			cash=request.cash,
		)
		backtest = Backtest(config)
		result = backtest.run()
	except Exception as error:
		raise HTTPException(status_code=502, detail=str(error)) from error

	metrics = {name: float(value) for name, value in result.metrics.items()}
	dates = [timestamp.date() for timestamp in result.dates]
	prices = [float(value) for value in result.stock_df["adj close"].tolist()]

	return BacktestResponse(
		symbol=config.symbol,
		strategy=request.strategy,
		start_date=request.start_date,
		end_date=request.end_date,
		metrics=metrics,
		dates=dates,
		prices=prices,
		portfolio_values=[float(value) for value in backtest.portfolio_value],
	)
