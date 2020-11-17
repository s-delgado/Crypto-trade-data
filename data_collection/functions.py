import pandas as pd
import math
from datetime import datetime


# CONSTANTS
binsizes = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
batch_size = 750


def minutes_of_new_data(symbol, kline_size, data, client):
    if len(data) > 0:
        old = data["timestamp"].iloc[-1]
    else:
        old = datetime.strptime('1 Jan 2017', '%d %b %Y')
    new = pd.to_datetime(client.get_klines(symbol=symbol, interval=kline_size)[-1][0], unit='ms')
    return old, new


def get_all_binance_futures(df, symbol, kline_size, client):
    if df is None:
        data_df = pd.DataFrame()
    else:
        data_df = df.copy()
        data_df = data_df.reset_index()
    oldest_point, newest_point = minutes_of_new_data(symbol, kline_size, data_df, client)
    delta_min = (newest_point - oldest_point).total_seconds()/60
    available_data = math.ceil(delta_min/binsizes[kline_size])
    if oldest_point == datetime.strptime('1 Jan 2017', '%d %b %Y'):
        print('Downloading all available %s data for %s. Be patient..!' % (kline_size, symbol))
    else:
        print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.' % (delta_min, symbol, available_data, kline_size))

    klines = client.get_historical_futures_klines(symbol,
                                                  kline_size,
                                                  oldest_point.strftime("%d %b %Y %H:%M:%S"),
                                                  newest_point.strftime("%d %b %Y %H:%M:%S"))
    data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                         'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    if len(data_df) > 0:
        temp_df = pd.DataFrame(data)
        data_df = data_df.append(temp_df)
    else:
        data_df = data
    data_df.set_index('timestamp', inplace=True)
    return data_df
