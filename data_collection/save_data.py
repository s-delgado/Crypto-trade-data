from arctic import Arctic
import arctic
from datetime import datetime, timedelta
from data_collection.binance_trades import fetch_binance_trades, trade_verifier
import pandas as pd
import sys


def store_trade_data(market, symbol, start_date, end_date):

    if market == 'futures':
        api_url = 'https://fapi.binance.com/fapi/v1/aggTrades'  # Binance futures
        lib_name = 'binance_futures'
    elif market == 'exchange':
        api_url = 'https://api.binance.com/api/v3/aggTrades'  # Binance exchange
        lib_name = 'binance_exchange'
    else:
        raise Exception('Wrong market choose between futures & exchange')
        exit()

    # Connect to MONGODB
    store = Arctic('mongodb://127.0.0.1:27017')

    # Access the library
    try:
        library = store[lib_name]
    except arctic.exceptions.LibraryNotFoundException:
        print('Library not found, initializing library')
        store.initialize_library(lib_name, lib_type=arctic.VERSION_STORE)
        library = store[lib_name]

    # Starting dates
    from_date = start_date
    to_date = start_date + timedelta(days=1)

    # Check for existing data
    if library.has_symbol(symbol):
        item = library.read(symbol, date_range=arctic.date.DateRange(start_date, None))  # limit by date
        df = item.data
        last_timestamp = df.index.max().to_pydatetime()
    else:
        last_timestamp = from_date

    # Correcting for existing data
    if last_timestamp > from_date:
        from_date = last_timestamp + timedelta(milliseconds=1)
        to_date = from_date + timedelta(days=1)

    # Main loop
    while to_date <= end_date:
        df = fetch_binance_trades(api_url, symbol, from_date, to_date)
        trade_verifier(df, symbol, market)
        df['datetime'] = pd.to_datetime(df['T'], unit='ms')
        df.set_index('datetime', inplace=True)
        df.drop(columns=['T'], inplace=True)
        columns = ['aggtradeID', 'price', 'quantity', 'first_tradeID', 'last_tradeID', 'maker']
        if df.shape[1] == 7:
            columns.append('best_price_match')
        df.columns = columns
        library.append(symbol, df, metadata={'source': 'binance'}, prune_previous_version=True, upsert=True)

        # Update to new interval
        from_date += timedelta(days=1)
        to_date += timedelta(days=1)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise Exception('arguments format: <market> <symbol> <start_date>')
        exit()
    market = sys.argv[1]
    symbol = sys.argv[2]
    start_date = datetime.strptime(sys.argv[3], '%d/%m/%Y')

    # market = 'exchange'
    # symbol = 'BTCUSDT'
    # start_date = datetime(2020, 1, 1)

    end_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
    store_trade_data(market, symbol, start_date, end_date)

