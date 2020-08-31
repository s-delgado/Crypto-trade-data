import backtrader as bt
from backtrader_functions import EWMAC, Cap, PriceChange, CommInfoFractional, PositionObserver
import pandas as pd
import numpy as np
from functions import get_candles, load_csv_candles, emwac, get_scalars
import math
from datetime import datetime


# Create a Stratey
class TrendStrategy(bt.Strategy):

    params = (('fast_period', 2),
              ('vol_lookback', 35),
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

        self.previous_subsystem_position = 0
        self.subsystem_position = 0

        self.scale = True
        self.forecasts = [EWMAC(plot=True,
                                fast_period=self.p.fast_period ** x,
                                slow_period=self.p.fast_period ** x * 4,
                                vol_lookback=self.p.vol_lookback,
                                scale=self.scale,
                                scalars=scalars
                                ) for x in range(init_period, init_period+variations)]

        cforecast = self.forecasts[0] * fw[0, 0] + self.forecasts[1] * fw[0, 1] + self.forecasts[2] * fw[0, 2]
        self.cforecast = Cap(cforecast * fdm)

        self.block_value = self.dataclose * (1/100) * min_contract_size
        # bt.LinePlotterIndicator(self.block_value, name='block_value')

        returns = PriceChange(period=1, plot=False)
        # bt.LinePlotterIndicator(returns, name='returns')
        returnvol = bt.indicators.StandardDeviation(returns,
                                                    period=self.p.vol_lookback,
                                                    movav=bt.indicators.ExponentialMovingAverage,
                                                    subplot=True)
        # bt.LinePlotterIndicator(returnvol, name='returnvol')
        pct_vol = 100 * (returnvol / self.dataclose)
        bt.LinePlotterIndicator(pct_vol, name='returnvolpct')
        self.instrument_currency_volatility = pct_vol * self.block_value
        # bt.LinePlotterIndicator(self.instrument_currency_volatility, name='instrument_currency_volatility')

        # annualised_cash_vol_target = pct_volatility_target * self.stats.broker.value

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.6f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.6f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if trade.justopened:
            self.log('Trade Opened  - Size %.6f @Price %.6f' % (trade.size, trade.price))
        elif trade.isclosed:
            self.log('Trade Closed  - Profit %.6f' % (trade.pnlcomm,))

        else:  # trade updated
            self.log('Trade Updated - Size %.6f @Price %.2f' % (trade.size, trade.price))

    def next(self):
        dt = self.data.datetime.datetime()
        trading_capital = self.stats.broker.value[0]
        annualised_cash_vol_target = pct_volatility_target * trading_capital
        daily_cash_volatility_target = annualised_cash_vol_target / math.sqrt(365*24)

        vol_scalar = (daily_cash_volatility_target / self.instrument_currency_volatility[0])


        # Positions in btc
        self.previous_subsystem_position = self.subsystem_position
        self.subsystem_position = round(((self.cforecast[0] * vol_scalar)/10) * min_contract_size, 3)
        # self.subsystem_position = vol_scalar

        # Positions in cryptucurrency
        position = self.position.size
        desired_position = self.subsystem_position

        change = desired_position - position

        position_value = self.dataclose[0] * self.position.size

        if abs(desired_position * self.dataclose[0]) > trading_capital * max_capital_usage:
            desired_position = round((trading_capital * max_capital_usage * np.sign(desired_position)) / self.dataclose[0], 3)
        # Simply log the closing price of the series from the reference
        txt = []
        txt += [' Position: %.6f' % (position,)]
        txt += [' Subsystem Position: %.6f' % (self.subsystem_position,)]
        txt += [' Close: %.2f' % (self.dataclose[0],)]
        txt += [' Position value: %.2f' % (position_value,)]
        if position>0:
            txt += [' change pct: %.2f' % ((change/position)*100,)]
        txt += [' ICV: %.2f' % (self.instrument_currency_volatility[0],)]
        txt += [' vol_scalar: %.2f' % (vol_scalar,)]
        txt += [' Forecast: %.2f' % (self.cforecast[0],)]
        # txt += [' Previous Subsystem Position: %.2f' % (self.previous_subsystem_position,)]

        # txt += ['Position: %.6f' % (self.position.size,)]
        # txt += ['Position: %.6f' % (self.position.size,)]

        self.log(','.join(txt))

        # if dt == datetime(2020,7,27,16,0,0,0) or dt == dt == datetime(2020,7,27,15,0,0,0):
        #     print('stop')

        if change != 0:
            if position == 0 or (abs(change / position) > 0.3):  # Position inertia of 10%

                self.order = self.order_target_size(target=desired_position)
                if change > 0:
                    self.log('Enter Long')

                if change < 0:
                    self.log('Enter Short')


if __name__ == '__main__':
    # Prepare data
    filename = 'data/BTCUSDT.csv'
    df = load_csv_candles(filename)
    # df = df[df.index >= '2018-01-01']
    freq = 'H'
    df = get_candles(df, freq).dropna()
    # df['close'] = df.close
    # Calculate forecast scalars
    if freq == 'H':
        init_period = 4 # 2**%
    else:
        init_period = 1
    variations = 3

    scalars, forecasts = get_scalars(df, init_period, variations)
    print(scalars)
    corr = forecasts.corr()
    print(corr)

    # Calcs
    commission = 0.04 / 100
    min_contract_size = 0.001
    # df['block_value'] = min_contract_size * df.close * (1 / 100)
    # df['returnvol'] = df.close.diff().ewm(span=35, min_periods=35).std()
    # df['pct_vol'] = 100 * (df.returnvol / df.close)
    # df['icv'] = df.pct_vol * df.block_value
    # print(df.pct_vol.mean(), df.icv.mean())
    #
    # annualised_cash_vol_target = pct_volatility_target * initial_trading_capital
    # daily_cash_volatility_target = annualised_cash_vol_target / math.sqrt(365 * 24)
    #
    # vol_scalar = (daily_cash_volatility_target / df.icv)

    # Positions in btc

    # self.subsystem_position = round(((self.cforecast[0] * vol_scalar) / 10) * min_contract_size, 3)

    # df['instrument_currency_volatility'] = df.block_value * (df.daily_price_vol/df.close) * 100
    # df['annualized_icv'] = math.sqrt(365) * df.instrument_currency_volatility
    # df['trade_cost'] = min_contract_size * df.close * commission
    # df['sr_cost'] = 2 * df.trade_cost / df.annualized_icv
    # df[['trade_cost', 'sr_cost']].plot()
    # print(df.sr_cost.mean())

    # Forecast weights
    fw = np.array([[0.42, 0.16, 0.42]])

    # Forecast diversification multiplier
    fdm = 1 / math.sqrt(np.matmul(fw, np.matmul(corr.values, fw.T)))

    # Volatility targeting
    pct_volatility_target = 0.1
    initial_trading_capital = 1000
    max_capital_usage = 0.5
    # annualised_cash_vol_target = pct_volatility_target * initial_trading_capital
    # daily_cash_volatility_target = annualised_cash_vol_target / math.sqrt(365)


    # Cerebro
    cerebro = bt.Cerebro(tradehistory=True)
    cerebro.addstrategy(TrendStrategy)

    if freq == 'H':
        data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, compression=60)
    else:
        data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Days, compression=1)
    cerebro.adddata(data)

    cerebro.broker.set_cash(initial_trading_capital)
    # cerebro.broker.setcommission(commission=commission)
    cerebro.broker.addcommissioninfo(CommInfoFractional(commission=commission))

    cerebro.addobserver(PositionObserver)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    thestrats = cerebro.run()

    thestrat = thestrats[0]

    print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis())

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()




