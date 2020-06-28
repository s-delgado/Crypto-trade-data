import backtrader as bt
from utils import GenericCSV_SVM


class svmH(bt.Indicator):

    lines = ('svmHigh',)

    params = (('lag', -12),)

    plotinfo = dict(plot=True, subplot=False)

    def __init__(self):
        lagged = self.data.lines.svmHigh(1)
        self.lines.svmHigh = bt.indicators.Highest(lagged, period=24)


class svmL(bt.Indicator):

    lines = ('svmLow',)

    params = (('lag', -12),)

    plotinfo = dict(plot=True, subplot=False)

    def __init__(self):
        lagged = self.data.lines.svmLow(1)
        self.lines.svmLow = bt.indicators.Lowest(lagged, period=24)


# Create a Stratey
class SVMStrategy(bt.Strategy):
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
        self.buyprice = None
        self.buycomm = None

        self.svmH = svmH()
        self.svmL = svmL()


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
        self.log('Close: %.2f, svmH: %.2f, svmL: %.2f' % (self.dataclose[0], self.svmH[0], self.svmL[0]))
        # self.log('' % self.svmH[0])
        # self.log('' % self.svmL[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            if self.dataclose[0] > self.svmH:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()

            if self.dataclose[0] < self.svmL:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()

        if self.position.size == 1 and self.dataclose[0] < self.svmL:
            self.order = self.sell(size=2)


        elif self.position.size == -1 and self.dataclose[0] > self.svmH:
            self.order = self.buy(size=2)




if __name__ == '__main__':

    cerebro = bt.Cerebro()

    cerebro.addstrategy(SVMStrategy)

    data = GenericCSV_SVM(dataname='candles_svm.csv')

    cerebro.adddata(data)

    cerebro.broker.set_cash(1000000)
    cerebro.broker.setcommission(commission=0.1/100)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()


