import backtrader.feeds as btfeeds
from datetime import datetime
import backtrader as bt


class GenericCSV(btfeeds.GenericCSVData):

    params = (('dtformat', '%Y-%m-%d %H:%M:%S'),
              ('timeframe', bt.TimeFrame.Minutes),
              ('compression', 1),
              ('fromdate', datetime(2020, 1, 1)),
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


class EWMAC(bt.Indicator):

    lines = ('slow', 'fast', 'crossover', 'std', 'forecast',)
    # plotlines = dict(slow=dict(plot=True),
    #                  std=dict(subplot=True))

    params = (('slow_period', 4),
              ('fast_period', 16),
              ('std_lookback', 25),
              ('ewm_std', False))

    def __init__(self):
        self.lines.slow = bt.indicators.ExponentialMovingAverage(period=self.params.slow_period, plot=False)
        self.lines.fast = bt.indicators.ExponentialMovingAverage(period=self.params.fast_period, plot=False)
        self.lines.crossover = self.lines.fast - self.lines.slow
        if self.params.ewm_std:
            self.lines.std = bt.indicators.StandardDeviation(period=self.params.std_lookback,
                                                             movav=bt.indicators.ExponentialMovingAverage, plot=False)
        else:
            self.lines.std = bt.indicators.StandardDeviation(period=self.params.std_lookback, plot=False)

        self.forecast = self.lines.crossover / self.lines.std


