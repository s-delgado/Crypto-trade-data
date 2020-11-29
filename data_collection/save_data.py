from arctic import Arctic
import arctic
from datetime import datetime, timedelta
from data_collection.binance_trades import fetch_binance_trades, trade_verifier
import pandas as pd


def store_trade_data(market, symbol, start_date, end_date):

    if market == 'futures':
        api_url = 'https://fapi.binance.com/fapi/v1/aggTrades'  # Binance futures
        lib_name = 'binance_futures'
    else:
        api_url = 'https://api.binance.com/api/v3/aggTrades'  # Binance exchange
        lib_name = 'binance_exchange'

    # Connect to MONGODB
    store = Arctic('mongodb://127.0.0.1:27017')

    # Access the library
    try:
        library = store[lib_name]
    except arctic.exceptions.LibraryNotFoundException:
        print('Library not found, initializing library')
        store.initialize_library(lib_name, lib_type=arctic.VERSION_STORE)
        library = store[lib_name]

    # Check for existing data
    if library.has_symbol(symbol):
        item = library.read(symbol)
        df = item.data
        last_timestamp = df.index.max().to_pydatetime()

    # Starting dates
    from_date = start_date
    to_date = start_date + timedelta(days=1)

    # Correcting for existing data
    if last_timestamp > from_date:
        from_date = last_timestamp + timedelta(milliseconds=1)
        to_date = from_date + timedelta(days=1)

    # Main loop
    while to_date <= end_date:
        df = fetch_binance_trades(api_url, symbol, from_date, to_date)
        if trade_verifier(df):
            df['datetime'] = pd.to_datetime(df['T'], unit='ms')
            df.set_index('datetime', inplace=True)
            df.drop(columns=['T'], inplace=True)
            df.columns = ['aggtradeID', 'price', 'quantity', 'first_tradeID', 'last_tradeID', 'maker']
            library.append(symbol, df, metadata={'source': 'binance'}, prune_previous_version=True, upsert=True)

            # Update to new interval
            from_date += timedelta(days=1)
            to_date += timedelta(days=1)
        else:
            break


if __name__ == '__main__':
    # Initial parameters
    market = 'futures'
    symbol = 'BTCUSDT'
    start_date = datetime(2020, 1, 1)
    end_date = datetime.today().date() - timedelta(microseconds=1)
    store_trade_data(market, symbol, start_date, end_date)

