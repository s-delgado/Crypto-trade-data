import backtrader as bt
from backtrader.indicators.mabase import MovAv
from backtrader.indicators.deviation import StandardDeviation

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


class BollingerBands(bt.Indicator):
    '''
    Defined by John Bollinger in the 80s. It measures volatility by defining
    upper and lower bands at distance x standard deviations

    Formula:
      - midband = SimpleMovingAverage(close, period)
      - topband = midband + devfactor * StandardDeviation(data, period)
      - botband = midband - devfactor * StandardDeviation(data, period)

    See:
      - http://en.wikipedia.org/wiki/Bollinger_Bands
    '''
    alias = ('BBands',)

    lines = ('mid', 'top', 'bot',)
    params = (('period', 20), ('devfactor', 2.0), ('movav', MovAv.Simple),)

    plotinfo = dict(subplot=False)
    plotlines = dict(
        mid=dict(ls='--'),
        top=dict(_samecolor=True),
        bot=dict(_samecolor=True),
    )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.devfactor]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        self.lines.mid = ma = self.p.movav(self.data.lines.close(-1), period=self.p.period)
        stddev = self.p.devfactor * StandardDeviation(self.data.lines.close(-1), ma, period=self.p.period, movav=self.p.movav)
        self.lines.top = ma + stddev
        self.lines.bot = ma - stddev

        super(BollingerBands, self).__init__()