from functions import read_csv
import  pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math
from mercury.renko import Renko

sign = lambda x: math.copysign(1, x)


class Arenko:
    def __init__(self, brick_size):
        self.source_prices = []
        self.renko_prices = []
        self.renko_directions = []
        self.brick_size = brick_size

    def __renko_rule(self, last_price):
        # Get the gap between two prices
        gap = float(last_price - self.renko_prices[-1])
        is_new_brick = False
        start_brick = 0
        num_new_bars = 0

        # When we have some gap in prices
        if abs(gap) > self.brick_size/2:
            # Forward any direction (up or down)
            num_new_bars = abs(gap / self.brick_size)
            rem = num_new_bars % 1
            if rem == 0:
                num_new_bars = int(num_new_bars)
            elif rem <= 0.5:
                num_new_bars = math.floor(num_new_bars)
            elif rem > 0.5:
                num_new_bars = math.ceil(num_new_bars)
            is_new_brick = True
            start_brick = 0

        if is_new_brick:
            # Add each brick
            for d in range(start_brick, np.abs(num_new_bars)):
                self.renko_prices.append(self.renko_prices[-1] + self.brick_size * np.sign(gap))
                self.renko_directions.append(np.sign(gap))

        return num_new_bars

    # Getting renko on history
    def build_history(self, prices):
        if len(prices) > 0:
            # Init by start values
            self.source_prices = prices
            self.renko_prices.append(prices.iloc[0])
            self.renko_directions.append(0)

            # For each price in history
            for p in self.source_prices[1:]:
                self.__renko_rule(p)

        return len(self.renko_prices)

    # Getting next renko value for last price
    def do_next(self, last_price):
        if len(self.renko_prices) == 0:
            self.source_prices.append(last_price)
            self.renko_prices.append(last_price)
            self.renko_directions.append(0)
            return 1
        else:
            self.source_prices.append(last_price)
            return self.__renko_rule(last_price)

    def evaluate(self, method='simple'):
        balance = 0
        sign_changes = 0
        price_ratio = len(self.source_prices) / len(self.renko_prices)

        if method == 'simple':
            for i in range(2, len(self.renko_directions)):
                if self.renko_directions[i] == self.renko_directions[i - 1]:
                    balance = balance + 1
                else:
                    balance = balance - 2
                    sign_changes = sign_changes + 1

            if sign_changes == 0:
                sign_changes = 1

            score = balance / sign_changes
            if score >= 0 and price_ratio >= 1:
                score = np.log(score + 1) * np.log(price_ratio)
            else:
                score = -1.0

            return {'balance': balance, 'sign_changes:': sign_changes,
                    'price_ratio': price_ratio, 'score': score}

    def get_renko_prices(self):
        return self.renko_prices

    def get_renko_directions(self):
        return self.renko_directions

    def plot_renko(self, col_up='g', col_down='r'):
        fig, ax = plt.subplots(1, figsize=(20, 10))
        ax.set_title('Renko chart')
        ax.set_xlabel('Renko bars')
        ax.set_ylabel('Price')

        # Calculate the limits of axes
        ax.set_xlim(0.0,
                    len(self.renko_prices) + 1.0)
        ax.set_ylim(np.min(self.renko_prices) - 3.0 * self.brick_size,
                    np.max(self.renko_prices) + 3.0 * self.brick_size)

        # Plot each renko bar
        for i in range(1, len(self.renko_prices)):
            # Set basic params for patch rectangle
            col = col_up if self.renko_directions[i] == 1 else col_down
            x = i
            y = self.renko_prices[i] - (self.brick_size / 2)
            height = self.brick_size

            # Draw bar with params
            ax.add_patch(
                patches.Rectangle(
                    (x, y),  # (x,y)
                    1.0,  # width
                    self.brick_size,  # height
                    facecolor=col
                )
            )

        # plt.show()

# def arenko(brick_size, wave):
#     half_step = brick_size / 2
#
#     ini_start_time = wave.index[0]
#     ini_price = wave[0]
#
#     bricks = []
#     bricks.append(round(ini_price, 0))
#
#     for i, sample in enumerate(wave):
#         change = sample - bricks[-1]
#
#         if abs(change) > half_step:
#             direction = sign(change)
#             num_step_changes = abs(change / brick_size)
#             rem = num_step_changes % 1
#             if rem == 0:
#                 num_step_changes = int(num_step_changes)
#             elif rem <= 0.5:
#                 num_step_changes = math.floor(num_step_changes)
#             elif rem > 0.5:
#                 num_step_changes = math.ceil(num_step_changes)
#
#             for i in range(1, num_step_changes + 1):
#                 bricks.append(bricks[-1] + brick_size * direction)
#     return bricks

df = read_csv('/Users/sebastian/GoldenEye/data/candles/BTCUSDT-1m-data.csv.zip')
wave = df.close[-2000:-1000]
brick_sizes = [25]

plt.figure()
plt.plot(wave)
plt.show()



for br in brick_sizes:
    ar = Arenko(brick_size=br)
    ar.build_history(wave)
    # plt.figure()
    ar.plot_renko()
    plt.show()





# r = Renko()
# r.set_brick_size(brick_size=25, auto=False)
# r.build_history(wave)
# r.plot_renko()