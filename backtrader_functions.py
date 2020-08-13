import backtrader.feeds as btfeeds
from datetime import datetime
import backtrader as bt


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

    def once(self, start, end):
        array = self.lines.capped.array

        for i in range(start, end):
            if self.data[0] < self.p.capmin:
                array[i] = self.p.capmin
            elif self.data[0] > self.p.capmax:
                array[i] = self.p.capmax
            else:
                array[i] = self.data[0]




def ewmac_forecast_scalar(Lfast, Lslow):
    """
    Function to return the forecast scalar (table 49 of the book)

    Only defined for certain values
    """

    fsdict = dict(l2_8=56.48, l4_16=29.09, l8_32=15.20, l16_64=8.41, l32_128=4.31, l64_256=2.27)
    lkey = "l%d_%d" % (Lfast, Lslow)

    if lkey in fsdict:
        return fsdict[lkey]
    else:
        print("Warning: No scalar defined for Lfast=%d, Lslow=%d, using default of 1.0" % (Lfast, Lslow))
        return 1.0





class EWMAC(bt.Indicator):

    lines = ('forecast',)

    params = (('fast_period', 16),
              ('slow_period', 16*4),
              ('vol_lookback', 36),
              ('ewm_std', True),
              ('scale', True))

    def __init__(self):
        slow = bt.indicators.ExponentialMovingAverage(period=self.p.slow_period)
        fast = bt.indicators.ExponentialMovingAverage(period=self.p.fast_period)
        crossover = fast - slow
        # self.crossover = bt.LinePlotterIndicator(crossover, name='crossover', subplot=False)
        returns = PriceChange(period=1, plot=False)
        if self.params.ewm_std:
            stdev_returns = bt.indicators.StandardDeviation(returns, period=self.p.vol_lookback,
                                                            movav=bt.indicators.ExponentialMovingAverage, subplot=True)
        else:
            stdev_returns = bt.indicators.StandardDeviation(returns, period=self.p.vol_lookback, subplot=True)

        if self.p.scale:
            f_scalar = ewmac_forecast_scalar(self.p.fast_period, self.p.slow_period)
            forecast = (crossover / stdev_returns) * f_scalar
            # cap_forecast = Cap(forecast)
        else:
            forecast = (crossover / stdev_returns)

        self.l.forecast = forecast



