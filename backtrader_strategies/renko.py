import backtrader as bt
from backtrader_functions import GenericCSV, EWMAC, PriceChange
import pandas as pd
import numpy as np


# Create a Stratey
class Renko(bt.Strategy):

    params = (('slow_period', 128*4),
              ('fast_period', 128),
              ('std_lookback', 36),
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

        self.slow = bt.indicators.ExponentialMovingAverage(period=self.params.slow_period)
        self.fast = bt.indicators.ExponentialMovingAverage(period=self.params.fast_period)
        # crossover = self.fast - self.slow
        # self.crossover = bt.LinePlotterIndicator(crossover, name='crossover', subplot=False)
        # returns = PriceChange(period=1, plot=False)
        # if self.params.ewm_std:
        #     self.std = bt.indicators.StandardDeviation(returns, period=self.params.std_lookback,
        #                                                movav=bt.indicators.ExponentialMovingAverage, subplot=True)
        # else:
        #     self.std = bt.indicators.StandardDeviation(returns, period=self.params.std_lookback, subplot=True)
        #
        # forecast = (crossover / self.std) * 8.4
        # self.forecast = bt.LinePlotterIndicator(forecast, name='forecast', subplot=True)
        self.forecast = EWMAC(plot=True, slow_period=self.p.slow_period, fast_period=self.p.fast_period)


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
        pass
        # Simply log the closing price of the series from the reference
        # self.log('Position: %.0f, Close: %.2f, Fast: %.2f, Slow: %.2f, Forecast: %.2f' % (self.position.size,
        #                                                                                   self.dataclose[0],
        #                                                                                   self.fast[0],
        #                                                                                   self.slow[0],
        #                                                                                   self.forecast[0],
        #                                                                                      ))
        # record = pd.DataFrame(np.array([[self.data.datetime.datetime(),
        #                                  self.position.size,
        #                                  self.dataclose[0],
        #                                  self.fast[0],
        #                                  self.slow[0],
        #                                  self.forecast[0]]]),
        #                       columns=['timestamp', 'position', 'close', 'fast', 'slow', 'forecast'])
        #
        # self.record = self.record.append(record)
        EMWA
        if not self.position:

            if self.fast > self.slow and self.fast[-1] <= self.slow[-1]:
                self.order = self.buy()
                self.log('BUY CREATE, %.2f' % self.order.created.price)

            if self.fast < self.slow and self.fast[-1] >= self.slow[-1]:
                self.order = self.sell()
                self.log('SELL CREATE, %.2f' % self.order.created.price)

        if self.position.size > 0:
            if self.fast < self.slow:
                self.order = self.sell(size=2)

        if self.position.size < 0:
            if self.fast > self.slow:
                self.order = self.buy(size=2)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    cerebro.addstrategy(Renko)
    data0 = GenericCSV(dataname='data/BTCUSDT-truncated.csv')
    data0.addfilter(bt.filters.Renko, size=15, align=10)
    # cerebro.resampledata(data0, timeframe=bt.TimeFrame.Minutes, compression=60)
    cerebro.adddata(data0)
    cerebro.broker.set_cash(100000)
    cerebro.broker.setcommission(commission=0.04 / 100)
    # cerebro.addwriter(bt.WriterFile, csv=True, out='logs.csv')

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(10 / np.nanmean(cerebro.runningstrats[0].forecast.array))

    cerebro.plot(style='candles')


