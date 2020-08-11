import pandas as pd
import backtrader.feeds as btfeeds
from datetime import datetime
import backtrader as bt


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


def get_splits(train_size, test_size, df):
    ixs = dict()

    test_starts_ix = [x for x in range(train_size, (len(df)//test_size + 2) * test_size, test_size)]
    for s in range(len(test_starts_ix)):
        ixs[s] = dict()
        start = test_starts_ix[s]
        ixs[s]['train'] = [x for x in range(start - train_size, start)]
        ixs[s]['test'] = [x for x in range(start, start + test_size) if x < len(df) - 1]
        assert len(ixs[s]['train']) == train_size
        if len(ixs[s]['test']) == 0:
            ixs.pop(s)
    return ixs


class GenericCSV_SVM(btfeeds.GenericCSVData):

    # lines = ('svmHigh', 'svmLow')
    # add date filter

    params = (('dtformat', '%Y-%m-%d %H:%M:%S'),
              ('timeframe', bt.TimeFrame.Minutes),
              ('compression', 60),
              ('fromdate', datetime(2020, 1, 1)),
              ('todate', datetime(2020, 8, 30)),
              ('datetime', 0),
              ('open', 1),
              ('high', 2),
              ('low', 3),

              ('close', 4),
              ('volume', 5),
              # ('svmHigh', 6),
              # ('svmLow', 7),
              ('openinterest', -1))

