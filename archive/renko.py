import pandas as pd
from archive.shiftedrenko import shiftedrenko
from matplotlib import pyplot as plt

data = pd.read_csv('data/candles/BTCUSDT-1m-data.csv.zip')
df = data[data.timestamp >= '2020-07-10'].copy()
df['date'] = pd.to_datetime(df.timestamp)
df.drop('timestamp', axis=1, inplace=True)
df.set_index('date', inplace=True)
df.head()

plt.figure(figsize=(10, 10))
df.close.plot()

prices = pd.Series([1,1,2,-5, -7,2,1,0,-5,-4,-2, 20])

# Get optimal brick size based
# optimal_brick = pyrenko.renko().set_brick_size(auto=False, HLC_history=df[["high", "low", "close"]])

# Build Renko chart
renko_obj_atr = shiftedrenko()
print('Set brick size to optimal: ', renko_obj_atr.set_brick_size(brick_size=10, shift_pct=0.125))
renko_obj_atr.build_history(prices=df.close)

renko_obj_atr.plot_renko()

# print(renko_obj_atr.renko_prices)
# print(renko_obj_atr.renko_directions)
#
# for i in range(len(renko_obj_atr.renko_prices)):
#
#     print(renko_obj_atr.renko_prices[i], renko_obj_atr.renko_directions[i])