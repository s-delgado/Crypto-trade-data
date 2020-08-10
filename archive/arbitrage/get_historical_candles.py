import ccxt
import pandas as pd
from keys import keys
from datetime import datetime
from matplotlib import pyplot as plt

epoch = datetime.utcfromtimestamp(0)


def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0


all_exchanges = ccxt.exchanges

# exchanges = ['binance', 'bitfinex', 'bittrex', 'bitvavo', 'bytetrade', 'eterbase', 'ftx', 'idex', 'kraken', 'upbit',
#              'wavesexchange']
exchanges = ['binance', 'kraken']

prices = pd.DataFrame()

for exchange_id in exchanges:
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        # 'apiKey': keys[exchange_id]['apiKey'],
        # 'secret': keys[exchange_id]['secret'],
        'timeout': 30000,
        'enableRateLimit': True,
    })
    symbol = 'BTC/EUR'
    exchange.loadMarkets()
    markets = exchange.markets.keys()
    if symbol in markets:
        market = exchange.markets[symbol]
        fee = market['taker']
        if exchange.has['fetchOHLCV']:
            if exchange.has['fetchOHLCV'] == 'emulated':
                print('Warning!')
            start = int(unix_time_millis(datetime(2020, 7, 7)))
            data = exchange.fetch_ohlcv(symbol, '1m', since=start)

            df = pd.DataFrame(data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['timestamp'] = pd.to_datetime(df.timestamp, unit='ms')
            df.set_index('timestamp', inplace=True)
            prices[exchange_id] = df.Close
            prices[exchange_id+'_fee'] = df.Close * fee



prices['diff'] = prices.binance - prices.kraken

fig, (ax0, ax1, ax2, ax3) = plt.subplots(4,1, sharex=True)
ax0.plot(prices.binance)
ax0.plot(prices.kraken)
ax1.plot(prices['diff'])
ax2.plot(prices.binance_fee + prices.kraken_fee)
ax3.plot(prices['diff'] - (prices.binance_fee + prices.kraken_fee))

