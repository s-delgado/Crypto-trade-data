import backtrader.feeds as btfeeds
from datetime import  datetime
import backtrader as bt


class GenericCSV(btfeeds.GenericCSVData):

    # lines = ('svmHigh', 'svmLow')
    # add date filter

    params = (('dtformat', '%Y-%m-%d %H:%M:%S'),
              ('timeframe', bt.TimeFrame.Minutes),
              ('compression', 60),
              ('fromdate', datetime(2019, 1, 1)),
              ('todate', datetime(2020, 8, 30)),
              ('datetime', 0),
              ('open', 1),
              ('high', 2),
              ('low', 3),

              ('close', 4),
              ('volume', 5),
              # ('svmHigh', 6),
              # ('svmLow', 7),
              ('openinterest', -1))
