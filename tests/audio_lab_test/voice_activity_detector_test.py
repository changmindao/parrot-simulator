"""
voice_activity_detector_test.py - A program to test voice_activity_detector.py
"""
import math
import numpy as np
from src.signal_processing import signal_generator as sg
from src.signal_processing import signal_analyzer as sa
from src.signal_processing import voice_activity_detector as vad
from src.utility import soundfile_runner as sr


def test_sinewave():
    wave_filename = "sinewave.wav"
    print(f"Reading wave file: {wave_filename}")
    # xs, fs = sr.read_wav(wave_filename)
    vad_output = vad.get_voice_activity_timestamps(wave_filename)
    active_segments  = vad_output["active_segments"]
    print(f"\n--- Processing: {wave_filename} ---")
    print(f"Active Level = {vad_output["active_level"]} [dBov]")
    print(f"Active Ratio = {vad_output["active_ratio"]}")
    print(f"Active Voice Segments [t_start, t_end]:")
    print(active_segments)
    print(f"Total active segments found: {len(active_segments)}\n")
        

def test_ambient_noise():
    filename = "ambient_noise.wav"
    target_db = -70.0
    print(f'filename = {filename}')
    print(f'target_db = {target_db}')
    sg.generate_white_noise(filename, target_db)
    vad_output = vad.get_voice_activity_timestamps(filename)
    active_segments  = vad_output["active_segments"]
    print(f"\n--- Processing: {filename} ---")
    print(f"Active Level = {vad_output["active_level"]} [dBov]")
    print(f"Active Ratio = {vad_output["active_ratio"]}")
    print(f"Active Voice Segments [t_start, t_end]:")
    print(active_segments)
    print(f"Total active segments found: {len(active_segments)}\n")
        

def test_room_noise():
    filename = "room_noise.wav"
    target_db = -50.0
    print(f'filename = {filename}')
    print(f'target_db = {target_db}')
    sg.generate_white_noise(filename, target_db)
    vad_output = vad.get_voice_activity_timestamps(filename)
    active_segments  = vad_output["active_segments"]
    print(f"\n--- Processing: {filename} ---")
    print(f"Active Level = {vad_output["active_level"]} [dBov]")
    print(f"Active Ratio = {vad_output["active_ratio"]}")
    print(f"Active Voice Segments [t_start, t_end]:")
    print(active_segments)
    print(f"Total active segments found: {len(active_segments)}\n")


def main():
    # ttest_sinewave()
    # test_ambient_noise()
    test_room_noise()


if __name__ == "__main__":
    main()
