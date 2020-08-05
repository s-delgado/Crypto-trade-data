import pandas as pd
from shiftedrenko import shiftedrenko
from matplotlib import pyplot as plt
from datetime import datetime

# data = pd.read_csv('data/candles/BTCUSDT-1m-data.csv.zip')
# df = data[data.timestamp >= '2020-07-17'].copy()
# df['date'] = pd.to_datetime(df.timestamp)
# df.drop('timestamp', axis=1, inplace=True)
# df.set_index('date', inplace=True)
# df.head()
#
# plt.figure(figsize=(10, 10))
# df.close.plot()

prices = pd.Series([1,1,2,-5, -6, -8])

# Get optimal brick size based
# optimal_brick = pyrenko.renko().set_brick_size(auto=False, HLC_history=df[["high", "low", "close"]])

# Build Renko chart
renko_obj_atr = shiftedrenko()
print('Set brick size to optimal: ', renko_obj_atr.set_brick_size(brick_size=8, shift_pct=0.125))
renko_obj_atr.build_history(prices=prices)

renko_obj_atr.plot_renko()

print(renko_obj_atr.renko_prices)
print(renko_obj_atr.renko_directions)

# for i in range(len(renko_obj_atr.renko_prices)):
#
#     print(renko_obj_atr.renko_prices[i], renko_obj_atr.renko_directions[i])