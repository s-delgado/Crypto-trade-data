import backtrader as bt
from utils import GenericCSV_SVM


class OnBalanceVolume(bt.Indicator):
    '''
    REQUIREMENTS
    ----------------------------------------------------------------------
    Investopedia:
    ----------------------------------------------------------------------
    https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:on_balance_volume_obv

    1. If today's closing price is higher than yesterday's closing price,
       then: Current OBV = Previous OBV + today's volume

    2. If today's closing price is lower than yesterday's closing price,
       then: Current OBV = Previous OBV - today's volume

    3. If today's closing price equals yesterday's closing price,
       then: Current OBV = Previous OBV
    ----------------------------------------------------------------------
    '''

    alias = 'OBV'
    lines = ('obv',)

    plotlines = dict(
        obv=dict(
            _name='OBV',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):

        # Plot a horizontal Line
        self.plotinfo.plotyhlines = [0]

    def nextstart(self):
        # We need to use next start to provide the initial value. This is because
        # we do not have a previous value for the first calcuation. These are
        # known as seed values.

        # Create some aliases
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = v[0]

        elif c[0] < c[-1]:
            obv[0] = -v[0]
        else:
            obv[0] = 0

    def next(self):
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = obv[-1] + v[0]
        elif c[0] < c[-1]:
            obv[0] = obv[-1] - v[0]
        else:
            obv[0] = obv[-1]


class Slope(bt.Indicator):
    packages = (('pandas', 'pd'),
                ('sklearn.linear_model', 'lm'),
                ('numpy', 'np'))
    lines = ('slope',)
    params = (('period', 5),)

    def init(self):
        self.addminperiod(self.params.period)

    def next(self):
        y = pd.Series(self.data.close.get(size=self.p.period))
        # ema = bt.indicators.ExponentialMovingAverage(period=self.p.period)
        # y = pd.Series(ema.get(size=self.p.period))
        if len(y) == 0:
            self.lines.slope[0] = np.nan
            # self.lines.intercept[0] = np.nan
        elif len(y) == self.p.period:
            X = np.arange(self.p.period).reshape(-1, 1)
            ols = lm.LinearRegression(fit_intercept=True).fit(X,y)
            (slope, intercept) = ols.coef_[0], ols.intercept_
            self.lines.slope[0] = np.rad2deg(np.arctan(slope))
            # self.lines.intercept[0] = intercept


class svmH(bt.Indicator):

    lines = ('svmHigh',)

    params = (('lag', -12),)

    plotinfo = dict(plot=True, subplot=False)

    def __init__(self):
        # highs = bt.indicators.Highest(self.data.lines.svmHigh, period=12)
        # self.lines.svmHigh = highs
        # self.lines.svmHigh = bt.indicators.ExponentialMovingAverage(self.data.lines.svmHigh(-12), period=10)
        self.lines.svmHigh = bt.indicators.Highest(self.data.lines.svmHigh(-24), period=24)


class svmL(bt.Indicator):

    lines = ('svmLow',)

    params = (('lag', -12),)

    plotinfo = dict(plot=True, subplot=False)

    def __init__(self):
        self.lines.svmLow = bt.indicators.Lowest(self.data.lines.svmLow(-24), period=24)



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
        self.lowside = None
        self.highside = None
        self.trail_price = None
        self.buyprice = None
        self.buycomm = None

        self.svmH = svmH()
        self.svmL = svmL()


        # self.EMA = bt.indicators.ExponentialMovingAverage()
        self.Slope = Slope(subplot=True)
        # self.OBV = OnBalanceVolume(subplot=True)
        self.RSI = bt.indicators.RSI(subplot=True)


        # self.ATR = bt.indicators.ATR(subplot=True)

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
        self.log('Position: %.0f, Close: %.2f, svmH: %.2f, svmL: %.2f, OLS: %.2f' % (self.position.size, self.dataclose[0],
                                                                                     self.svmH[0], self.svmL[0], self.Slope[0]))
        # self.log('' % self.svmH[0])
        # self.log('' % self.svmL[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            if (self.dataclose[0] > self.dataclose[-1]
                    and self.dataclose[0] > self.svmH * 1.01
                    and self.Slope > 60
                    and self.RSI >= 70
            ):
                self.order = self.buy(size=1)
                self.trail_price = self.order.created.price
                self.highside = self.sell(size=1, exectype=bt.Order.StopTrail, trailpercent=0.05)
                self.log('BUY CREATE, %.2f, TRAIL PRICE %.2f' % (self.dataclose[0], self.trail_price))

            # if (self.dataclose[0] < self.dataclose[-1]
            #         and self.dataclose[0] < self.svmH * 0.99
            #         and self.Slope < -60
            #         and self.RSI <= 30
            # ):
            #     self.order = self.sell(size=1)
            #     self.trail_price = self.order.created.price
            #     self.highside = self.buy(size=1, exectype=bt.Order.StopTrail, trailpercent=0.02)
            #     self.log('BUY CREATE, %.2f, TRAIL PRICE %.2f' % (self.dataclose[0], self.trail_price))

        if self.position.size > 0:
            if self.dataclose[0] < self.svmH:
                self.cancel(self.highside)
                self.order = self.sell(size=1)

        # if self.position.size < 0:
        #     if self.dataclose[0] > self.svmL:
        #         self.cancel(self.highside)
        #         self.order = self.buy(size=1)



            # if self.dataclose[0] < self.svmL:
            #     self.order = self.sell(size=1)
            #     self.trail_price = self.order.created.price
            #     self.order2 = self.buy(size=1, exectype=bt.Order.StopTrail, trailpercent=0.02)
            #     self.trail_price = self.order2.created.price
            #     self.log('SELL CREATE, %.2f, TRAIL PRICE %.2f' % (self.dataclose[0], self.trail_price))
        # else:
        #     print('rhrh')

        # if self.position

        # if self.position.size == 1 and self.dataclose[0] < self.svmL:
        #     self.order = self.sell(size=2, exectype=bt.Order.StopTrail, trailamount=5)
        #
        # elif self.position.size == -1 and self.dataclose[0] > self.svmH:
        #     self.order = self.buy(size=2, exectype=bt.Order.StopTrail, trailamount=5)


if __name__ == '__main__':

    cerebro = bt.Cerebro()

    cerebro.addstrategy(SVMStrategy)

    data = GenericCSV_SVM(dataname='candles_svm15min.csv')

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


