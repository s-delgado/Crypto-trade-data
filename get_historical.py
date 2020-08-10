# IMPORTS
import pandas as pd
import math
import os.path
import time
from binance.client import Client
from datetime import timedelta, datetime
from dateutil import parser
from bitmex import bitmex
from keys import keys
from tqdm import tqdm


# CONSTANTS
binsizes = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
batch_size = 750
bitmex_client = bitmex(test=False, api_key=keys['bitmex']['apiKey'], api_secret=keys['bitmex']['secret'])
binance_client = Client(api_key=keys['binance']['apiKey'], api_secret=keys['binance']['secret'])


# FUNCTIONS
def minutes_of_new_data(symbol, kline_size, data, source):
    if len(data) > 0:
        old = parser.parse(data["timestamp"].iloc[-1])
    elif source == "binance":
        old = datetime.strptime('1 Jan 2017', '%d %b %Y')
    elif source == "bitmex":
        old = bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=kline_size, count=1, reverse=False).result()[0][0]['timestamp']
    if source == "binance":
        new = pd.to_datetime(binance_client.get_klines(symbol=symbol, interval=kline_size)[-1][0], unit='ms')
    if source == "bitmex":
        new = bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=kline_size, count=1, reverse=True).result()[0][0]['timestamp']
    return old, new


def get_all_binance(symbol, kline_size, save = False):
    filename = 'data/candles/%s-%s-data.csv.zip' % (symbol, kline_size)
    if os.path.isfile(filename):
        data_df = pd.read_csv(filename)
    else:
        data_df = pd.DataFrame()
    oldest_point, newest_point = minutes_of_new_data(symbol, kline_size, data_df, source = "binance")
    delta_min = (newest_point - oldest_point).total_seconds()/60
    available_data = math.ceil(delta_min/binsizes[kline_size])
    if oldest_point == datetime.strptime('1 Jan 2017', '%d %b %Y'):
        print('Downloading all available %s data for %s. Be patient..!' % (kline_size, symbol))
    else:
        print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.' % (delta_min, symbol, available_data, kline_size))
    klines = binance_client.get_historical_klines(symbol,
                                                  kline_size,
                                                  oldest_point.strftime("%d %b %Y %H:%M:%S"),
                                                  newest_point.strftime("%d %b %Y %H:%M:%S"),
                                                  limit=1000)
    data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    if len(data_df) > 0:
        temp_df = pd.DataFrame(data)
        data_df = data_df.append(temp_df)
    else:
        data_df = data
    data_df.set_index('timestamp', inplace=True)
    if save:
        data_df.to_csv(filename)
    print('All caught up..!')
    return data_df

def get_all_binance_futures(symbol, kline_size, save = False):
    filename = 'data/candles/%s-%s-futures-data.csv.zip' % (symbol, kline_size)
    if os.path.isfile(filename):
        data_df = pd.read_csv(filename)
    else:
        data_df = pd.DataFrame()
    oldest_point, newest_point = minutes_of_new_data(symbol, kline_size, data_df, source = "binance")
    delta_min = (newest_point - oldest_point).total_seconds()/60
    available_data = math.ceil(delta_min/binsizes[kline_size])
    if oldest_point == datetime.strptime('1 Jan 2017', '%d %b %Y'):
        print('Downloading all available %s data for %s. Be patient..!' % (kline_size, symbol))
    else:
        print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.' % (delta_min, symbol, available_data, kline_size))

    klines = binance_client.get_historical_futures_klines(symbol,
                                                          kline_size,
                                                          oldest_point.strftime("%d %b %Y %H:%M:%S"),
                                                          newest_point.strftime("%d %b %Y %H:%M:%S"))
    data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    if len(data_df) > 0:
        temp_df = pd.DataFrame(data)
        data_df = data_df.append(temp_df)
    else:
        data_df = data
    data_df.set_index('timestamp', inplace=True)
    if save:
        data_df.to_csv(filename)
    print('All caught up..!')
    return data_df

def get_all_bitmex(symbol, kline_size, save = False):
    filename = 'data/candles/%s-%s-bitmex-data.csv.zip' % (symbol, kline_size)
    if os.path.isfile(filename):
        data_df = pd.read_csv(filename)
    else:
        data_df = pd.DataFrame()
    oldest_point, newest_point = minutes_of_new_data(symbol, kline_size, data_df, source="bitmex")
    delta_min = (newest_point - oldest_point).total_seconds()/60
    available_data = math.ceil(delta_min/binsizes[kline_size])
    rounds = math.ceil(available_data / batch_size)
    if rounds > 0:
        print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data in %d rounds.' % (delta_min, symbol, available_data, kline_size, rounds))
        for round_num in tqdm(range(rounds)):
            time.sleep(1)
            new_time = (oldest_point + timedelta(minutes = round_num * batch_size * binsizes[kline_size]))
            data = bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=kline_size, count=batch_size, startTime=new_time).result()[0]
            temp_df = pd.DataFrame(data)
            data_df = data_df.append(temp_df)
    data_df.set_index('timestamp', inplace=True)
    if save and rounds > 0:
        data_df.to_csv(filename)
    print('All caught up..!')
    return data_df





### Get exchange data
# tickers = binance_client.get_all_tickers()
# symbols = []
# # wanted = ['EUR', 'USD', 'BTC', 'ETH', 'USDT']
# wanted = ['BTCUSDT']
# for t in tickers:
#     symbol = t['symbol']
#     if any(w in symbol for w in wanted):
#         symbols.append(symbol)
#
# kline_size = '1m'
# for symbol in tqdm(symbols):
#     filename = 'data/candles/%s-%s-data.csv.zip' % (symbol, kline_size)
#     if os.path.isfile(filename):
#         continue
#     get_all_binance(symbol, kline_size, save=True)



### Get futures data
# wanted = ['EUR', 'USD', 'BTC', 'ETH', 'USDT']
wanted = ['BTCUSDT']
futures_info = binance_client.futures_exchange_info()
sym_info = futures_info['symbols']
symbols = []

for symbol in sym_info:
    symbol = symbol['symbol']
    if any(w in symbol for w in wanted):
        symbols.append(symbol)

kline_size = '1m'
for symbol in tqdm(symbols):
    filename = 'data/candles/%s-%s-futures-data.csv.zip' % (symbol, kline_size)
    if os.path.isfile(filename):
        continue
    get_all_binance_futures(symbol, kline_size, save=True)


# df = pd.read_csv('data/candles/BTCUSDT-1m-futures-data.csv.zip')