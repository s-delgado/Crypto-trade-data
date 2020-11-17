import numpy as np


class DPCM(object):

    def __init__(self, diff_table):
        self.diff_table = np.array(diff_table)

    def encode(self, wave):
        symbols = np.zeros(len(wave), dtype=np.uint)

        prediction = 0
        for i, wav in enumerate(wave):
            diff = wav - prediction # current input - last prediction
            abs_error = np.abs(self.diff_table - diff)
            diff_index = np.argmin(abs_error)
            prediction = prediction + self.diff_table[diff_index] # previous prediction + current quantized difference
            symbols[i] = diff_index

        return symbols

    def decode(self, symbols):
        wave = np.zeros(len(symbols), dtype=np.double)
        prediction = 0
        for i, diff_index in enumerate(symbols):
            prediction += self.diff_table[diff_index] # prediction = last prediction + current quantized difference
            wave[i] = prediction
        return wave