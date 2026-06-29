"""
soundfile_runner_test.py - A program to test soundfile_runner.py
"""
import math
import numpy as np
from src.utility import soundfile_runner as sr

def test_write_wav():
    wave_filename = "sinewave.wav"
    print("Generating a sinewave signal...")
    a = math.sqrt(0.5)
    fs = 48000  # 48kHz native audio
    t = np.linspace(0, 2.0, int(2.0 * fs), endpoint=False)
    xs = a * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    print(f"Writing signal in wav format: {wave_filename}")
    sr.write_wav(wave_filename, xs, fs)
    print("Write successful!")

def test_read_wav():
    wave_filename = "sinewave.wav"
    print(f"Reading wave file: {wave_filename}")
    xs, fs = sr.read_wav(wave_filename)
    
    print("\n--- File Summary ---")
    print(f"Sample Rate : {fs} Hz")
    print(f"Total Shapes: {xs.shape}")
    print(f"Duration    : {len(xs) / fs:.2f} seconds")
    print("--------------------")
        

def test_write_opus():

# --- Example Usage & Verification Run ---
    output_filename = "test_speech_opus.ogg"
    
    # 1. Create a dummy audio signal (e.g., 2 seconds of a 440 Hz standard pitch A tone)
    print("Generating a test signal...")
    fs = 48000  # Opus loves 48kHz native audio
    t = np.linspace(0, 2.0, int(2.0 * fs), endpoint=False)
    simulated_audio = np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    
    try:
        # 2. Test Writing
        print(f"Writing signal to Ogg-Opus format: {output_filename}")
        sr.write_opus(output_filename, simulated_audio, fs)
        print("Write successful!")
        
        # 3. Test Reading
        print(f"Reading back the file: {output_filename}")
        loaded_data, sample_rate = sr.read_opus(output_filename)
        
        print("\n--- File Summary ---")
        print(f"Sample Rate : {sample_rate} Hz")
        print(f"Total Shapes: {loaded_data.shape}")
        print(f"Duration    : {len(loaded_data) / sample_rate:.2f} seconds")
        print("--------------------")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nTroubleshooting Note: If you get a 'Subtype not available' error,")
        print("it means your system's underlying libsndfile library was compiled")
        print("without libopus tracking enabled.")

def test_read_opus():

# --- Example Usage & Verification Run ---
    output_filename = "sinewave.opus"
    
    # 1. Create a dummy audio signal (e.g., 2 seconds of a 440 Hz standard pitch A tone)
    print("Generating a test signal...")
    fs = 48000  # Opus loves 48kHz native audio
    t = np.linspace(0, 2.0, int(2.0 * fs), endpoint=False)
    simulated_audio = np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    
    try:
        # 2. Test Writing
        print(f"Writing signal to Ogg-Opus format: {output_filename}")
        sr.write_opus(output_filename, simulated_audio, fs)
        print("Write successful!")
        
        # 3. Test Reading
        print(f"Reading back the file: {output_filename}")
        loaded_data, sample_rate = sr.read_opus(output_filename)
        
        print("\n--- File Summary ---")
        print(f"Sample Rate : {sample_rate} Hz")
        print(f"Total Shapes: {loaded_data.shape}")
        print(f"Duration    : {len(loaded_data) / sample_rate:.2f} seconds")
        print("--------------------")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nTroubleshooting Note: If you get a 'Subtype not available' error,")
        print("it means your system's underlying libsndfile library was compiled")
        print("without libopus tracking enabled.")


def main():
    # test_write_opus()
    test_read_opus()
    # test_write_wav()
    # test_read_wav()


if __name__ == "__main__":
    main()