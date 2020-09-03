import backtrader.feeds as btfeeds
from datetime import datetime
import backtrader as bt
import numpy as np


class CommInfoFractional(bt.CommissionInfo):
    def getsize(self, price, cash):
        '''Returns fractional size for cash operation @price'''
        return self.p.leverage * (cash / price)


class GenericCSV(btfeeds.GenericCSVData):

    params = (('dtformat', '%Y-%m-%d %H:%M:%S'),
              ('timeframe', bt.TimeFrame.Minutes),
              ('compression', 1),
              ('fromdate', datetime(2017, 1, 1)),
              ('todate', datetime(2020, 12, 30)),
              ('datetime', 0),
              ('open', 1),
              ('high', 2),
              ('low', 3),
              ('close', 4),
              ('volume', 5),
              ('openinterest', -1))


class PriceChange(bt.Indicator):
    '''
      Measures the change of the current value with respect to that
      of period bars ago
    '''
    # alias = ('PctChange',)
    lines = ('pricechange',)

    # Fancy plotting name
    # plotlines = dict(pctchange=dict(_name='%change'))

    # update value to standard for Moving Averages
    params = (('period', 1),)

    def __init__(self):
        self.lines.pricechange = self.data - self.data(-self.p.period)


class Cap(bt.Indicator):
    '''
      Cap the maximum and minimum values
    '''

    lines = ('capped',)

    params = (('capmin', -20), ('capmax', 20))

    def next(self):
        if self.data[0] < self.p.capmin:
            self.lines.capped[0] = self.p.capmin
        elif self.data[0] > self.p.capmax:
            self.lines.capped[0] = self.p.capmax
        else:
            self.lines.capped[0] = self.data[0]


def ewmac_forecast_scalar(Lfast, Lslow, fsdict):
    """
    Function to return the forecast scalar (table 49 of the book)

    Only defined for certain values
    """

    lkey = "l%d_%d" % (Lfast, Lslow)

    if lkey in fsdict:
        return fsdict[lkey]
    else:
        print("Warning: No scalar defined for Lfast=%d, Lslow=%d, using default of 1.0" % (Lfast, Lslow))
        return 1.0


class ForecastScalers(bt.Indicator):
    alias = ('ArithmeticMean', 'Mean',)
    lines = ('av',)

    # def next(self):
    #     if len(self.data.get(size=10)) > 0:
    #         self.line[0] = math.fsum(self.data.get(size=len(self.data))) / len(self.data)

    def once(self, start, end):
        src = self.data.array
        dst = self.line.array

        for i in range(start, end):
            seg = src[start:i + 1]
            dst[i] = round(10 / np.nanmedian(np.abs(seg)), 2)


class EWMAC(bt.Indicator):

    lines = ('forecast',)

    params = (('fast_period', 16),
              ('slow_period', 16*4),
              ('vol_lookback', 36),
              ('scale', True))

    def __init__(self, scalars=None):
        self.scalars = scalars
        slow = bt.indicators.ExponentialMovingAverage(period=self.p.slow_period)
        fast = bt.indicators.ExponentialMovingAverage(period=self.p.fast_period)
        crossover = fast - slow
        returns = PriceChange(period=1, plot=False)
        stdev_returns = bt.indicators.StandardDeviation(returns, period=self.p.vol_lookback,
                                                        movav=bt.indicators.ExponentialMovingAverage, subplot=True)

        if self.p.scale:
            f_scalar = ewmac_forecast_scalar(self.p.fast_period, self.p.slow_period, self.scalars)
            forecast = (crossover / stdev_returns) * f_scalar
            forecast = Cap(forecast)
        else:
            forecast = (crossover / stdev_returns)

        self.l.forecast = forecast


class PositionObserver(bt.observer.Observer):
    lines = ('value',)

    plotinfo = dict(plot=True, subplot=True, plotlinelabels=True)

    # plotlines = dict(
    #     created=dict(marker='*', markersize=8.0, color='lime', fillstyle='full'),
    #     expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full')
    # )

    def next(self):
        # self.lines.position[0] = self._owner.position.size
        self.lines.value[0] = self.datas[0].close[0] * self._owner.position.size







