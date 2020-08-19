import backtrader as bt
from backtrader_functions import EWMAC, Cap
import pandas as pd
import numpy as np
from functions import get_candles, load_csv_candles, emwac
import math


# Create a Stratey
class TrendStrategy(bt.Strategy):

    params = (
              ('fast_period', 2),
              ('vol_lookback', 36),
              ('ewm_std', True))

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.record = pd.DataFrame()

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.start_trade = None
        self.end_trade = None

        self.scale = True

        self.forecasts = [EWMAC(plot=True,
                                fast_period=self.p.fast_period ** x,
                                slow_period=self.p.fast_period ** x * 4,
                                vol_lookback=self.p.vol_lookback,
                                scale=self.scale,
                                scalars=scalars
                                ) for x in range(2, 5)]

        cforecast = self.forecasts[0] * fw[0, 0] + self.forecasts[1] * fw[0, 1] + self.forecasts[2] * fw[0, 2]
        self.cforecast = Cap(cforecast * fdm)
        # bt.LinePlotterIndicator(self.cforecast, name='Combined Forecast')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        f = 0
        # pass
        # Simply log the closing price of the series from the reference
        self.log('Position: %.0f, Close: %.2f, Forecast: %.2f' % (self.position.size,
                                                                  self.dataclose[0],
                                                                                          self.forecasts[f][0],
                                                                                             ))


        if not self.position:


            if self.cforecast == 20:
                self.order = self.buy()
                self.log('BUY CREATE, %.2f' % self.order.created.price)

            if self.cforecast == -20:
                self.order = self.sell()
                self.log('SELL CREATE, %.2f' % self.order.created.price)

        if self.position.size > 0:
            if self.cforecast < 20:
                self.order = self.sell(size=1)

        if self.position.size < 0:
            if self.cforecast > -20:
                self.order = self.buy(size=1)


if __name__ == '__main__':
    # Prepare data
    filename = 'data/BTCUSDT.csv'
    df = load_csv_candles(filename)
    df = get_candles(df, 'D')

    # Calculate forecast scalars
    emwa_periods = [2 ** x for x in range(2, 5)]
    scalars = dict()
    forecasts = pd.DataFrame()
    for fp in emwa_periods:
        forecast = emwac(df, fast_period=fp, vol_lookback=36)
        forecasts[fp] = forecast
        scalar = 10 / np.nanmean(forecast)
        scalars['l%.0f_%.0f' % (fp, 4*fp)] = round(scalar, 2)
    print(scalars)
    corr = forecasts.corr()
    print(corr)

    # Get standardized cost
    commission = 0.04 / 100
    # min_contract_size = 0.001
    # df['block_value'] = min_contract_size * df.close.ewm(span=36, min_periods=36).mean() * (1/100)
    # df['hourly_price_vol'] = df.close.pct_change().ewm(span=36, min_periods=36).std()
    # df['instrument_currency_volatility'] = df.block_value * df.hourly_price_vol
    # df['annualized_icv'] = math.sqrt(365) * df.instrument_currency_volatility
    # df['trade_cost'] = min_contract_size * df.close.ewm(span=36, min_periods=36).mean()  * commission
    # df['sr_cost'] = 2 * df.trade_cost / df.annualized_icv
    # df[['trade_cost', 'annualized_icv', 'sr_cost']].plot()
    # print(df.sr_cost.mean())

    # Forecast weights
    fw = np.array([[0.42, 0.16, 0.42]])

    # Forecast diversification multiplier
    fdm = 1 / math.sqrt(np.matmul(fw, np.matmul(corr.values, fw.T)))

    # Cerebro
    cerebro = bt.Cerebro(tradehistory=True)
    cerebro.addstrategy(TrendStrategy)

    data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Days, compression=1)
    cerebro.adddata(data)
    cerebro.broker.set_cash(100000)
    cerebro.broker.setcommission(commission=commission)
    # cerebro.addwriter(bt.WriterFile, csv=True, out='logs.csv')

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()


