import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv('data/candles/BTCUSDT-1m-data.csv.zip')
df1['timestamp'] = pd.to_datetime(df1.timestamp, format='%Y-%m-%d %H:%M:%S')
df1.set_index('timestamp', inplace=True)

df2 = pd.read_csv('data/candles/BTCUSDT-1m-futures-data.csv.zip')
df2['timestamp'] = pd.to_datetime(df2.timestamp, format='%Y-%m-%d %H:%M:%S')
df2.set_index('timestamp', inplace=True)


print(df1.index.min(), df2.index.min())

df1 = df1[df1.index < df2.index.min()]

df = pd.concat([df1, df2])

plt.figure()
# plt.plot(df1.close)
# plt.plot(df2.close)
plt.plot(df.close)

df.reset_index().to_csv('data/BTCUSDT.csv', index=False)