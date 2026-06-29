"""
signal_generator.py - A program to generate signals
"""

import math
import numpy as np
import scipy as sp
from src.utility import soundfile_runner as sr

SAMPLE_RATE_8k = 8000
SAMPLE_RATE_16k = 16000
SAMPLE_RATE_24k = 24000
SAMPLE_RATE_48k = 48000
SAMPLE_RATE_DEFAULT = SAMPLE_RATE_48k

LEVEL_ACTIVE_MAX = -10. # dBov
LEVEL_ACTIVE_NOMINAL = -26.
LEVEL_ACTIVE_MIN = -60.
LEVEL_SILENCE = -90.

DURATION_MIN = 1.0 # second
DURATION_NOMINAL = 10.
DURATION_MAX = 60.

def generate_white_noise(filename, 
                         target_db, 
                         duration=DURATION_NOMINAL,
                         fs=SAMPLE_RATE_DEFAULT):
    """
    Generates a white noise and save in the filename
    """
    # Calculate total samples
    num_samples = int(duration * fs)
    
    # Convert target dBov back to a linear peak amplitude floor
    amplitude = 10 ** (target_db / 20.0)
    
    # Generate uniform white noise scaled precisely to that peak amplitude
    xs = np.random.uniform(-amplitude, amplitude, num_samples).astype(np.float32)
    
    # Save the file
    sr.write_wav(filename, xs, fs)
    print(f"Save noise signal in '{filename}' perfectly calibrated to {target_db} dBov.")
    return xs


def generate_sinewave(filename,
                      frequency, 
                      target_db=LEVEL_ACTIVE_NOMINAL, 
                      duration=DURATION_NOMINAL,
                      fs=SAMPLE_RATE_DEFAULT):
    a = 10 ** (target_db / 20.0) * math.sqrt(2.0)
    n_sample = int(duration * fs)
    t = np.array(range(n_sample)) / fs
    xs = a * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    sr.write_wav(filename, xs, fs)
    print(f"Save noise signal in '{filename}' perfectly calibrated to {target_db} dBov.")
    return xs