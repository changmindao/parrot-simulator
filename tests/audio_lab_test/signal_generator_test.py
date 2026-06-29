"""
signal_generator_test.py - A program to test signal_generator.py
"""
import math
import numpy as np
from src.signal_processing import signal_generator as sg
from src.signal_processing import signal_analyzer as sa
from src.utility import soundfile_runner as sr

def test_generate_sinewave():
    frequency = 1000
    filename = f"tone_{frequency}hz.wav"
    target_db = -10.0
    print(f'filename = {filename}')
    print(f'target_db = {target_db}')
    xs = sg.generate_sinewave(filename, frequency, target_db)
    rms = sa.get_rms(xs)
    print(f"RMS : {rms} ")
    pwr = sa.get_pwr(xs)
    print(f"Power : {pwr} [dBov]")


def main():
    test_generate_sinewave()


if __name__ == "__main__":
    main()




