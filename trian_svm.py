import pandas as pd
from matplotlib import pyplot as plt
import numpy as np


def get_candles(DF, freq):
    df = DF.copy()
    groups = df.groupby(pd.Grouper(freq=freq))
    open = groups.open.first()
    high = groups.high.max()
    low = groups.low.min()
    close = groups.close.last()
    volume = groups.trades.sum()

    candles = pd.concat([open, high, low, close, volume], axis=1)
    candles.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return candles


def atr(DF, n):
    df = DF.copy()
    df['H-L'] = abs(df.High - df.Low)
    df['H-C'] = abs(df.High - df.Close)
    df['L-C'] = abs(df.Low - df.Close)
    df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
    df['ATR'] = df.TR.rolling(n).mean()
    return df.ATR


def rsi(DF, n):
    """function to calculate RSI"""
    df = DF.copy()
    delta = df["Close"].diff().dropna()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    rs = up.ewm(span=n, min_periods=n - 1).mean() / down.abs().ewm(span=n, min_periods=n - 1).mean()
    return 100 - 100 / (1 + rs)


def ma(DF, n):
    """function to calculate MA"""
    df = DF.copy()
    return df.Close.rolling(n).mean()


def roc(df, n, price='Close'):
    """
    Rate of Change
    """
    M = df[price].diff(n - 1)
    N = df[price].shift(n - 1)
    return pd.Series(M / N, name='ROC_' + str(n))



# def fastK(DF, n):
#     """Function to calculate FastK"""
#     df = DF.copy()
#     lowestlow = df.Close.rolling(n).min()
#     highesthigh = df.Close.rolling(n).max()
#     return ((df.Close - lowestlow)/(highesthigh - lowestlow)) * 100

def STOK(df):
    """
    Stochastic oscillator %K
    """
    return pd.Series((df['Close'] - df['Low']) / (df['High'] - df['Low']), name='SO%k')

# def slowK(DF, n):
#     """Function to calculate SlowK"""
#     df = DF.copy()
#     return df.fastK.rolling(n).mean()


def STO(df, n):
    """
    Stochastic oscillator %D
    """
    SOk = STOK(df)
    return pd.Series(SOk.ewm(span=n, min_periods=n - 1).mean(), name='SO%d_' + str(n))


original = pd.read_csv('BTCUSDT-1m-data.csv')
original['timestamp'] = pd.to_datetime(original.timestamp)
original = original[original.timestamp >= '2019-01-01']
original.set_index('timestamp', inplace=True)

df = get_candles(original, '15min')

base_k = 30

# Features
df['ATR'] = atr(df, base_k)
df['MA'] = ma(df, base_k)
df['RSI'] = rsi(df, base_k)
df['ROC'] = roc(df, base_k)
df['STOK'] = STOK(df)
df['STOD'] = STO(df, base_k/2)

# Targets: Min/Max price in n-1 days in the future a total of n days
n = 30
df['yH'] = df.Close.shift(-n+1).rolling(n, min_periods=n).max()
df['yL'] = df.Close.shift(-n+1).rolling(n, min_periods=n).min()

# Create clean DF with only the Features and the targets
X = df[['Close', 'ATR', 'MA', 'RSI', 'ROC', 'STOK', 'STOD']]
yL = df.yL
yH = df.yH

# Set n and create training examples for SVM: Each training example n past days including the current one.




# Split into Training/Test Sets

# Train SVM






fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax1.plot(df[['Close']].iloc[-300:])
ax1.plot(df[['MA']].iloc[-300:])
ax2.plot(df.STOK.iloc[-300:])
ax2.plot(df.STOD.iloc[-300:])
