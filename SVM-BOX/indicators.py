import pandas as pd


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


