import pandas as pd
import yfinance as yf
import numpy as np

from datetime import datetime, date
from pathlib import Path
from engine.data.models import Bar

class DataLoaderError(Exception):
    """Raised when data cannot be loaded or fails validation."""

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]

class DataLoader:
    """Load and validate OHLCV market data from external sources."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the loader with an optional local cache directory."""
        self.cache_dir = Path(cache_dir) if cache_dir else None

    def load(self, symbol: str, start: str | date | datetime, end: str | date | datetime, source: str = "yfinance") -> pd.DataFrame:
        """Load validated OHLCV data for a single symbol.

        Args:
            symbol: ticker to load, e.g. 'AAPL' or 'SPY'.
            start: inclusive start date.
            end: inclusive end date.
            source: 'yfinance' or 'csv'. For 'csv', looks for
                {cache_dir}/{symbol}.csv with columns
                date,open,high,low,close,volume.

        Returns:
            DataFrame indexed by DatetimeIndex ('timestamp'), with
            float columns: open, high, low, close, volume.
        """
        if source == "yfinance":
            raw = self._load_from_yfinance(symbol, start, end)
        elif source == "csv":
            raw = self._load_from_csv(symbol, start, end)
        else:
            raise DataLoaderError(f"Unknown source: {source}")
        df = self._normalize(raw, symbol)
        df = self._filter_date_range(df, start, end)
        self._validate_bars(df, symbol)
        return df
    
    #-- Sources --------------------------------------------------------------------------------------------------------
    def _load_from_yfinance(self, symbol: str, start: str | date | datetime, end: str | date | datetime) -> pd.DataFrame:
        """Download OHLCV data from yfinance for a given symbol and date range."""
        raw = yf.download(tickers=symbol, start=start, end=end)
        if raw.empty:
            raise DataLoaderError(f"No data returned for {symbol} between {start} and {end}")
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        return raw
    
    def _load_from_csv(self, symbol: str, start: str | date | datetime, end: str | date | datetime) -> pd.DataFrame:
        """Load OHLCV data from a local CSV file located in the cache directory."""
        if self.cache_dir is None:
            raise DataLoaderError("cache_dir must be set to use source='csv'")
        path = self.cache_dir / f"{symbol}.csv"
        if not path.exists():
            raise DataLoaderError(f"No CSV found for {symbol} at {path}")
        df = pd.read_csv(path, parse_dates=["date"], index_col="date")
        return df.loc[pd.Timestamp(start) : pd.Timestamp(end)]
                
    #-- Normalization --------------------------------------------------------------------------------------------------------
    def _normalize(self, raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Normalize raw market data into a clean OHLCV DataFrame."""
        df = raw.rename(columns={c: c.lower() for c in raw.columns})
        missing = {c for c in REQUIRED_COLUMNS if c not in df.columns}
        if missing:
            raise DataLoaderError(f"{symbol}: data is missing required columns: {missing}")
        df = df[REQUIRED_COLUMNS].copy()

        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "timestamp"

        df = df.sort_index()
        df = df[~df.index.duplicated(keep="first")]

        df = df.astype(float)
        if df[REQUIRED_COLUMNS].isna().any().any():
            before = len(df)
            df = df.dropna(subset=REQUIRED_COLUMNS)
            after = len(df)
            dropped = before - after
            if dropped:
                print(f"{symbol}: dropped {dropped} row(s) containing NaNs")
        return df   

    def _filter_date_range(self, df: pd.DataFrame, start: str | date | datetime, end: str | date | datetime) -> pd.DataFrame:
        """Return only rows whose timestamps fall within the requested range."""
        return df.loc[pd.Timestamp(start) : pd.Timestamp(end)]
    
    #-- Validation --------------------------------------------------------------------------------------------------------
    def _validate_bars(self, df: pd.DataFrame, symbol: str) -> None:
        """Round-trip every row through Bar to catch malformed OHLC data."""
        if df.empty:
            raise DataLoaderError(f"{symbol}: no data left after filtering/cleaning")
        errors: list[str] = []
        for timestamp, row in df.iterrows():
            try:
                Bar(
                    symbol=symbol,
                    timestamp=timestamp.to_pydatetime(),
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
            except ValueError as e:
                df.loc[timestamp, "close"] = np.nan