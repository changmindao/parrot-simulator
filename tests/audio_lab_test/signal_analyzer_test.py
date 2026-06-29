"""
signal_analyzer_test.py - A program to test signal_analyzer.py
"""
import math
import numpy as np
from src.signal_processing import signal_analyzer as sa
from src.utility import soundfile_runner as sr


def test_get_rms():
    wave_filename = "sinewave.wav"
    print(f"Reading wave file: {wave_filename}")
    xs, _ = sr.read_wav(wave_filename)
    rms = sa.get_rms(xs)
    print(f"RMS : {rms} ")


def test_get_pwr():
    wave_filename = "sinewave.wav"
    print(f"Reading wave file: {wave_filename}")
    xs, _ = sr.read_wav(wave_filename)
    pwr = sa.get_pwr(xs)
    print(f"PWR : {pwr} [dBov]")


def test_rms2db():
    rms = 0.0
    db = sa.rms2db(rms)
    print(f"db : {db} [dBov]")


def test_db2rms():
    db = -140.0
    rms = sa.db2rms(db)
    print(f"db : {db} [dBov]")
    print(f"rms : {rms} ")


def main():
    # test_get_rms()
    # test_get_pwr()
    # test_rms2db()
    test_db2rms()


if __name__ == "__main__":
    main()
