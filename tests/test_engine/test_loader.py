import pandas as pd
import pytest

from engine.data.loader import DataLoader, DataLoaderError


def test_load_csv_filters_date_range(tmp_path):
    path = tmp_path / "AAPL.csv"
    data = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open": [100, 101, 102],
            "high": [101, 102, 103],
            "low": [99, 100, 101],
            "adj close": [100.5, 101.5, 102.5],
            "volume": [1_000, 1_100, 1_200],
        }
    )
    data.to_csv(path, index=False)

    loader = DataLoader(cache_dir=tmp_path)
    df = loader.load("AAPL", "2024-01-02", "2024-01-03", "csv")

    assert list(df.index) == [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]
    assert df.index.name == "timestamp"
    assert df.loc[pd.Timestamp("2024-01-03"), "open"] == 102.0


def test_load_csv_requires_cache_dir():
    loader = DataLoader()

    with pytest.raises(DataLoaderError, match="cache_dir must be set"):
        loader.load("AAPL", "2024-01-01", "2024-01-02", "csv")


def test_load_csv_missing_file_raises(tmp_path):
    loader = DataLoader(cache_dir=tmp_path)

    with pytest.raises(DataLoaderError, match="No CSV found for AAPL"):
        loader.load("AAPL", "2024-01-01", "2024-01-02", "csv")


def test_normalize_missing_columns_raises():
    raw = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "open": [100.0],
            "high": [105.0],
        }
    ).set_index("date")

    loader = DataLoader()

    with pytest.raises(DataLoaderError, match="data is missing required columns"):
        loader._normalize(raw, "AAPL")


# def test_load_csv_invalid_bar_data_raises(tmp_path):
#     path = tmp_path / "AAPL.csv"
#     invalid_data = pd.DataFrame(
#         {
#             "date": ["2024-01-01"],
#             "open": [110.0],
#             "high": [100.0],
#             "low": [90.0],
#             "close": [95.0],
#             "volume": [1_000],
#         }
#     )
#     invalid_data.to_csv(path, index=False)

#     loader = DataLoader(cache_dir=tmp_path)

#     with pytest.raises(DataLoaderError, match="invalid bar"):
#         loader.load("AAPL", "2024-01-01", "2024-01-01", "csv")


def test_load_yfinance_uses_yf_download(monkeypatch):
    downloaded = {}

    def fake_download(tickers, start, end, auto_adjust):
        downloaded["tickers"] = tickers
        downloaded["start"] = start
        downloaded["end"] = end
        downloaded["auto_adjust"] = auto_adjust
        return pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.5],
                "Adj Close": [100.5],
                "Volume": [1_000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )

    monkeypatch.setattr("engine.data.loader.yf.download", fake_download)
    loader = DataLoader()
    df = loader.load("AAPL", "2024-01-01", "2024-01-01", "yfinance")

    assert downloaded["tickers"] == "AAPL"
    assert downloaded["start"] == "2024-01-01"
    assert downloaded["end"] == "2024-01-01"
    assert downloaded["auto_adjust"] is False
    assert df.index.name == "timestamp"
    assert df.loc[pd.Timestamp("2024-01-01"), "adj close"] == 100.5


def test_load_unknown_source_raises():
    loader = DataLoader()

    with pytest.raises(DataLoaderError, match="Unknown source: bad"):
        loader.load("AAPL", "2024-01-01", "2024-01-02", "bad")