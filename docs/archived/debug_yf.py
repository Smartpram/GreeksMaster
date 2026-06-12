import yfinance as yf
import pandas as pd

df = yf.download('INFY.NS', start='2024-01-01', end='2026-06-09', progress=False)
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print("Index type:", type(df.index[0]))
print("Close column type:", type(df['Close']))
print("Close[0]:", type(df['Close'].iloc[0]), df['Close'].iloc[0])
print("Using loc:", df.loc[df.index[1], 'Close'], type(df.loc[df.index[1], 'Close']))
