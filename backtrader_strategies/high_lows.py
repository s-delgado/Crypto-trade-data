import backtrader as bt
from archive.svm_box_functions.utils import GenericCSV_SVM
import pandas as pd

"""
First try for this strategy.
1.- When a new series of consecutive highest high appears buy
2.- Sell when Close price is the same as the lowest low

"""

# Create a Stratey
class HL_Strategy(bt.Strategy):
    # params = (('ewmperiod', 15),)

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.start_trade = None
        self.end_trade = None

        self.previous_limit = None

        self.trail_price = None
        self.buyprice = None
        self.buycomm = None

        self.redline = None
        self.blueline = None

        n = 12

        # self.laghighs = bt.indicators.Highest(self.data.lines.close(-n), period=n, subplot=False, plot=True)
        # self.highs = bt.indicators.Highest(self.data.lines.close, period=n, subplot=False, plot=True)
        # self.lows = bt.indicators.Lowest(self.data.lines.close, period=n, subplot=False, plot=True)

        # self.TR = bt.indicators.TrueRange()
        # self.ATR = bt.indicators.AverageTrueRange()
        # self.RSI = bt.indicators.RSI()
        # self.ADX = bt.indicators.DirectionalIndicator()
        # self.bband = BollingerBands(period=n, devfactor=2)
        # self.slope = Slope()
        self.slow = bt.indicators.ExponentialMovingAverage(period=64*4)
        self.fast = bt.indicators.ExponentialMovingAverage(period=64)

        # self.avg = self.highs + self.lows

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
        # Simply log the closing price of the series from the reference
        self.log('Position: %.0f, Close: %.2f' % (self.position.size, self.dataclose[0]))

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            # self.order.price = self.bband.lines.top * 1.0
          
            return


        # if self.dataclose < self.bband.lines.bot and not self.position:
        #     self.redline = True
        #
        # if self.dataclose > self.bband.lines.top and self.position:
        #     self.blueline = True

        # if self.dataclose > self.bband.lines.mid and not self.position and self.redline:
        #     # BUY, BUY, BUY!!! (with all possible default parameters)
        #     self.log('BUY CREATE, %.2f' % self.dataclose[0])
        #     # Keep track of the created order to avoid a 2nd order
        #     self.order = self.buy()

        if not self.position:

            if self.fast > self.slow and self.fast[-1] <= self.slow[-1]:
                self.order = self.buy()
                # self.end_trade = self.sell(size=1, exectype=bt.Order.StopTrail, trailpercent=0.05)
                self.log('BUY CREATE, %.2f' % self.order.created.price)

            if self.fast < self.slow and self.fast[-1] >= self.slow[-1]:
                self.order = self.sell()
                # self.end_trade = self.buy(size=1, exectype=bt.Order.StopTrail, trailpercent=0.05)
                self.log('SELL CREATE, %.2f' % self.order.created.price)

        # if self.dataclose > self.bband.lines.top * 1.01 and not self.position:
        #     # BUY, BUY, BUY!!! (with all possible default parameters)
        #     self.log('BUY CREATE, %.2f' % self.dataclose[0])
        #     # Keep track of the created order to avoid a 2nd order
        #     self.order = self.buy()

        # if self.dataclose <= self.bband.lines.mid and self.position:
        #     # SELL, SELL, SELL!!! (with all possible default parameters)
        #     self.log('SELL CREATE, %.2f' % self.dataclose[0])
        #     self.blueline = False
        #     self.redline = False
        #     # Keep track of the created order to avoid a 2nd order
        #     self.order = self.sell()

        # Check if we are in the market
        # if not self.position:

            # if self.dataclose[0] > self.laghighs * 1.01 \
            #         and self.dataclose[0] > self.dataclose[-1] * 1.01\
            #         and self.highs > self.laghighs:
            #     self.start_trade = self.buy(size=1)
            #     self.trail_price = self.start_trade.created.price
            #     self.end_trade = self.sell(size=1, exectype=bt.Order.StopTrail, trailpercent=0.01)
            #     self.log('BUY CREATE, %.2f, TRAIL PRICE %.2f' % (self.dataclose[0], self.trail_price))

            # if self.dataclose[0] < self.lows * 0.99:
            #     self.start_trade = self.sell(size=1)
            #     self.trail_price = self.start_trade.created.price
            #     self.end_trade = self.buy(size=1, exectype=bt.Order.StopTrail, trailpercent=0.05)
            #     self.log('SELL CREATE, %.2f, TRAIL PRICE %.2f' % (self.dataclose[0], self.trail_price))

        if self.position.size > 0:
            if self.fast < self.slow:
                # self.cancel(self.end_trade)
                self.order = self.sell(size=2)

        if self.position.size < 0:
            if self.fast > self.slow:
                # self.cancel(self.end_trade)
                self.order = self.buy(size=2)








if __name__ == '__main__':

    cerebro = bt.Cerebro()

    cerebro.addstrategy(HL_Strategy)
    df = pd.read_csv('data/candles/BTCUSDT-1m-futures-data.csv.zip')
    df.to_csv('data/candles/BTCUSDT-1m-futures-data.csv', index=False)
    data = GenericCSV_SVM(dataname='data/candles/BTCUSDT-1m-futures-data.csv')

    # Convert to Renko
    data.addfilter(bt.filters.Renko, size=1, align=10)
    cerebro.adddata(data)



    cerebro.broker.set_cash(1000000)
    cerebro.broker.setcommission(commission=0.1/100)

    # wr = bt.WriterFile(out='logs.csv')
    cerebro.addwriter(bt.WriterFile, csv=True, out='logs.csv')



    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()


