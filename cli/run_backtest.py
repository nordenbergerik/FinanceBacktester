from engine.data.loader import DataLoader

loader = DataLoader()
df = loader.load("AAPL", start="2023-01-01", end="2023-06-01")
print(df.head())