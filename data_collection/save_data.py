from arctic import Arctic
import arctic
import pandas as pd
from data_collection.functions import get_all_binance_futures
from binance.client import Client
import os

os.environ['db_url'] = 'mongodb+srv://admin:FjSNbgv0wQEHDcrecuOIg30PFE9j@gg-cluster.ldnwj.mongodb.net/GG-Cluster?retryWrites=true&w=majority'

binance_client = Client(api_key=os.environ['binance_apikey'], api_secret=os.environ['binance_secret'])

# Connect to MONGODB
store = Arctic(os.environ['db_url'])

# Access the library
try:
    library = store['binance_futures']
except arctic.exceptions.LibraryNotFoundException:
    print('Library not found, initializing library')
    store.initialize_library('binance_futures', lib_type=arctic.VERSION_STORE)
    library = store['binance_futures']

# Load some data
symbols = ['BTCUSDT']

# split for loop into different threads
for symbol in symbols:
    if library.has_symbol(symbol):
        item = library.read(symbol)
        df = item.data
    else:
        df = None

    df = get_all_binance_futures(df, 'BTCUSDT', '1m', binance_client)
    library.append('BTCUSDT', df, metadata={'source': 'binance'}, prune_previous_version=True, upsert=True)




# Load old data
# df = pd.read_csv('data/candles/BTCUSDT-1m-futures-data.csv.zip')
# df['timestamp'] = pd.to_datetime(df.timestamp)
# df.set_index('timestamp', inplace=True)
# # library.delete('BTCUSDT')
# library.write('BTCUSDT', df, metadata={'source': 'binance'})

# store.delete_library('binance_futures')
# store.list_libraries()
#
# library.read_audit_log('BTCUSDT')

