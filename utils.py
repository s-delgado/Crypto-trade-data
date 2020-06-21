import pandas as pd


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

