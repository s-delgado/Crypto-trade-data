import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn import svm
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV
from indicators import STO, STOK, rsi, roc, atr, ma
from utils import get_splits, get_candles


# Set parameters
candle_freq = '5min'  # Aggregation time for candles
base_k = int(60/5)  # Look back window for technical indicators
n = base_k  # Forecasting window for SVM's
train_size = 1000
test_size = 288

parameters = {
    "epsilon": [0.001, 0.0001, 1e-5],
    "kernel": ["rbf"],
    "C": [100, 500, 1000],
    "gamma": [1e-6, 1e-5, 1e-4, 1e-3]
    }

# Pre-process data and add technical indicators
original = pd.read_csv('BTCUSDT-1m-data.csv')
original['timestamp'] = pd.to_datetime(original.timestamp)
original = original[original.timestamp >= '2019-01-01']
original.set_index('timestamp', inplace=True)

df = get_candles(original, candle_freq)


# Features
df['ATR'] = atr(df, base_k)
df['MA'] = ma(df, base_k)
df['RSI'] = rsi(df, base_k)
df['ROC'] = roc(df, base_k)
df['STOK'] = STOK(df)
df['STOD'] = STO(df, base_k)

# Scale all to -1/1 range
ix = df.index
scaler = MinMaxScaler((-1, 1))
scaler.fit(df)
cols = df.columns
arr = scaler.transform(df)
df = pd.DataFrame(arr, columns=cols, index=ix)

# Targets: Min/Max price in n-1 days in the future a total of n days
df['yH'] = df.Close.shift(-n+1).rolling(n, min_periods=n).max()
df['yL'] = df.Close.shift(-n+1).rolling(n, min_periods=n).min()


# Create clean DF with only the Features and the targets
df = df.dropna()
X = df[['yL', 'yH', 'Close', 'ATR', 'MA', 'RSI', 'ROC', 'STOK', 'STOD']].copy()

# Set n and create training examples for SVM: Each training example n past days including the current one.
lags = n
cols = ['Close', 'ATR', 'MA', 'RSI', 'ROC', 'STOK', 'STOD']
for col in cols:
    for i in range(1, lags):
        X[col+'_'+str(i)] = X[col].shift(i)
X = X.dropna()
yL = X.yL
yH = X.yH
X.drop(['yL', 'yH'], axis=1, inplace=True)


# Get training windows
splits = get_splits(train_size, test_size, X)

resultH = pd.DataFrame()
resultL = pd.DataFrame()

for key, val in splits.items():
    X_train, X_test = X.iloc[val['train'], :], X.iloc[val['test'], :]
    yH_train, yH_test = yH.iloc[val['train']], yH.iloc[val['test']]
    yL_train, yL_test = yL.iloc[val['train']], yL.iloc[val['test']]


    # Train SVM
    gridH = GridSearchCV(svm.SVR(), parameters, verbose=1, cv=3, scoring='neg_mean_squared_error')
    gridH.fit(X_train, yH_train)
    r = pd.DataFrame(gridH.cv_results_)
    r = r[r.rank_test_score == 1]
    yhatH = gridH.predict(X_test)
    r['MSE'] = mean_squared_error(yH_test, yhatH)
    resultH = pd.concat([resultH, r])

    gridL = GridSearchCV(svm.SVR(), parameters, verbose=1, cv=3, scoring='neg_mean_squared_error')
    gridL.fit(X_train, yL_train)
    r = pd.DataFrame(gridL.cv_results_)
    r = r[r.rank_test_score == 1]
    yhatL = gridL.predict(X_test)
    r['MSE'] = mean_squared_error(yL_test, yhatL)
    resultL = pd.concat([resultL, r])

    # Record optimal parameter results

    #
    print(mean_squared_error(yH_test, yhatH))
    print(mean_squared_error(yL_test, yhatL))

    plt_df = X_test.copy()
    plt_df['yhatH'] = yhatH
    plt_df['yhatL'] = yhatL

    fig, (ax1) = plt.subplots(1, 1, sharex=True)
    ax1.plot(plt_df.yhatH.shift(n//2), label='High')
    ax1.plot(plt_df.yhatL.shift(n//2), label='Low')
    ax1.plot(plt_df.Close, color='k', label='Close')
    # ax2.plot(plt_df.RSI)
    plt.legend()
    plt.show()

    if key == 4:
        break


