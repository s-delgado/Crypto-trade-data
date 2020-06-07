import os
from tqdm import tqdm
import psycopg2
import gzip

# Get files
trade_files = os.listdir('data/trade')
trade_files = ['data/trade/'+f for f in trade_files if f[-2:] == 'gz' and int(f.split('.')[0]) >= 20190101]
trade_files.sort()


# Connect
conn = psycopg2.connect(host="localhost", database="gg_db", user="gg_user", password="password")
cur = conn.cursor()
cur.execute("SELECT version();")
record = cur.fetchone()
print("You are connected to - ", record, "\n")

cur.execute("""
DROP TABLE IF EXISTS trades;

CREATE TABLE trades (
timestamp varchar,
symbol varchar,
side varchar,
size int,
price float,
tickDirection varchar,
trdMatchID varchar,
grossValue bigint,
homeNotional float,
foreignNotional float
);
""")
conn.commit()

# Insert
for file in tqdm(trade_files):
    with gzip.open(file, 'r') as f:
        next(f)  # Skip the header row.
        cur.copy_from(f, 'trades', null="", sep=',', columns=['timestamp', 'symbol', 'side', 'size', 'price',
                                                              'tickDirection', 'trdMatchID', 'grossValue',
                                                              'homeNotional', 'foreignNotional'])
    conn.commit()
    cur.execute("DELETE FROM trades WHERE symbol != 'XBTUSD'")
    conn.commit()
    # break
