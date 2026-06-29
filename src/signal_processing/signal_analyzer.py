"""
signal_analyzer.py - A program to analyze signals
"""

import math
import numpy as np
import scipy as sp

RMS_MIN = 1.e-7

def get_rms(xs: np.ndarray):
    return math.sqrt(np.dot(xs, xs)/len(xs))

def get_pwr(xs: np.ndarray):
    return 20. * math.log10(max(get_rms(xs),RMS_MIN))

def rms2db(rms: float):
    return 20. * math.log10(max(rms,RMS_MIN))

def db2rms(pwr: float):
    return math.pow(10., pwr / 20.0) 