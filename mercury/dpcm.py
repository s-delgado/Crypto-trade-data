import numpy as np


class DPCM(object):

    def __init__(self, diff_table, wave):
        self.diff_table = np.array(diff_table)
        self.wave = wave

    def encode(self):
        symbols = np.zeros(len(self.wave), dtype=np.uint)
        # symbols = []

        prediction = self.wave[0]
        for i, wav in enumerate(self.wave[1:]):
            diff = wav - prediction # current input - last prediction
            abs_error = np.abs(self.diff_table - diff)
            diff_index = np.argmin(abs_error)
            # if self.diff_table[diff_index] != 0:
            prediction = prediction + self.diff_table[diff_index] # previous prediction + current quantized difference
            symbols[i] = diff_index
            # symbols.append(diff_index)

        return symbols

    def decode(self, symbols):
        wave = np.zeros(len(symbols), dtype=np.double)
        prediction = self.wave[0]
        for i, diff_index in enumerate(symbols):
            prediction += self.diff_table[diff_index] # prediction = last prediction + current quantized difference
            wave[i] = prediction
        return wave


class AdaptiveDPCM(object):

    def __init__(self, ini_step_size, num_levels, multipliers, signal):
        self.ini_step_size = ini_step_size
        self.num_levels = num_levels
        self.multipliers = multipliers
        self.signal = signal

    def get_levels(self, step_size):
        levels = np.linspace(start=0, stop=self.num_levels * step_size, num=self.num_levels+1)
        levels = np.unique(np.hstack([levels, -levels]))
        return levels

    def encode(self):
        # History
        symbols = np.zeros(len(self.signal), dtype=np.uint)
        differences = np.zeros(len(self.signal))
        qdifferences = np.zeros(len(self.signal))
        step_sizes = np.zeros(len(self.signal))

        # Initial parameters
        prediction = self.signal[0]
        levels = self.get_levels(self.ini_step_size)
        step_size = self.ini_step_size
        assert len(levels) == len(self.multipliers)

        for i, sig in enumerate(self.signal[1:]):
            diff = sig - prediction     # current input - last prediction
            differences[i] = diff
            abs_error = np.abs(levels - diff)
            diff_index = np.argmin(abs_error)
            prediction = prediction + levels[diff_index]   # previous prediction + current quantized difference
            symbols[i] = diff_index
            qdiff = levels[diff_index]
            qdifferences[i] = qdiff
            step_sizes[i] = step_size   # record current step size
            if diff_index > 4:
                print('')
            step_size = step_size * self.multipliers[diff_index]    # update step_size
            levels = self.get_levels(step_size)     # update levels

        return symbols, step_sizes, differences, qdifferences

    def decode(self, symbols):
        signal = np.zeros(len(symbols), dtype=np.double)
        prediction = self.signal[0]
        levels = self.get_levels(self.ini_step_size)
        step_size = self.ini_step_size
        assert len(levels) == len(self.multipliers)

        for i, diff_index in enumerate(symbols):
            prediction += levels[diff_index] # prediction = last prediction + current quantized difference
            signal[i] = prediction
            step_size = step_size * self.multipliers[diff_index]  # update step_size
            levels = self.get_levels(step_size)  # update levels

        return signal

