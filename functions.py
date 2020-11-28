import pandas as pd
import numpy as np


def load_csv_candles(filename):
    df = pd.read_csv(filename)
    df['timestamp'] = pd.to_datetime(df.timestamp)
    df.set_index('timestamp', inplace=True)
    return df

def read_csv(filename):
    df = pd.read_csv(filename)
    df['timestamp'] = pd.to_datetime(df.timestamp, format='%Y-%m-%d %H:%M:%S')
    df.set_index('timestamp', inplace=True)
    return df

def get_candles(DF, freq):
    df = DF.copy()
    groups = df.groupby(pd.Grouper(freq=freq))
    open = groups.open.first()
    high = groups.high.max()
    low = groups.low.min()
    close = groups.close.last()
    volume = groups.volume.sum()

    candles = pd.concat([open, high, low, close, volume], axis=1)
    candles.columns = ['open', 'high', 'low', 'close', 'volume']
    return candles


def cap_forecast(xrow, capmin, capmax):
    """
    Cap forecasts.

    """

    ## Assumes we have a single column
    x = xrow[0]

    if x < capmin:
        return capmin
    elif x > capmax:
        return capmax

    return x


def cap_series(xseries, capmin=-20.0,capmax=20.0):
    """
    Apply capping to each element of a time series
    For a long only investor, replace -20.0 with 0.0
    """
    return xseries.apply(cap_forecast, axis=1, args=(capmin, capmax))


def ewmac_forecast_scalar(Lfast, Lslow, fsdict):
    if fsdict is None:
        fsdict = dict()

    lkey = "l%d_%d" % (Lfast, Lslow)

    if lkey in fsdict:
        return fsdict[lkey]
    else:
        print
        "Warning: No scalar defined for Lfast=%d, Lslow=%d, using default of 1.0" % (Lfast, Lslow)
        return 1.0


def emwac(df, fast_period, vol_lookback, scalars=False, cap=False):
    slow_period = 4 * fast_period
    price = df.close

    fast_ewma = price.ewm(span=fast_period).mean()
    slow_ewma = price.ewm(span=slow_period).mean()

    raw_ewmac = fast_ewma - slow_ewma

    stdev_returns = (price - price.shift(1)).ewm(span=vol_lookback).std()
    forecast = raw_ewmac / stdev_returns

    if scalars:
        f_scalar = ewmac_forecast_scalar(fast_period, slow_period, scalars)
        forecast = forecast * f_scalar
    if cap:
        forecast = cap_series(forecast, capmin=-20.0, capmax=20.0)

    return forecast


def get_scalars(df, init_period, variations):
    emwa_periods = [2 ** x for x in range(init_period, init_period + variations)]
    scalars = dict()
    forecasts = pd.DataFrame()
    for fp in emwa_periods:
        forecast = emwac(df, fast_period=fp, vol_lookback=35)
        forecasts[fp] = forecast
        scalar = 10 / np.nanmedian(abs(forecast))
        scalars['l%.0f_%.0f' % (fp, 4 * fp)] = round(scalar, 2)
    return scalars, forecasts


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total,2)
    strike_rate = round((total_won / total_closed) * 100, 2)
    #Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Strike Rate','Win Streak', 'Losing Streak', 'PnL Net']
    r1 = [total_open, total_closed, total_won, total_lost]
    r2 = [strike_rate, win_streak, lose_streak, pnl_net]
    #Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    #Print the rows
    print_list = [h1,r1,h2,r2]
    row_format ="{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('',*row))
