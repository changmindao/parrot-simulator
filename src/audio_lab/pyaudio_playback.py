# TODO: fix clipping sound
import sys
import os
import soundfile as sf
import pyaudio
import numpy as np

def play_wav_file(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        return

    print(f"[*] Loading '{file_path}'...")
    
    # Force soundfile to read strictly as float32 array
    data, sample_rate = sf.read(file_path, dtype='float32')
    
    # Handle channel geometry
    channels = 1 if len(data.shape) == 1 else data.shape[1]
    
    print(f"    -> Sample Rate: {sample_rate} Hz")
    print(f"    -> Channels:    {channels}")

    p = pyaudio.PyAudio()
    
    # Open output stream matching the 48kHz Float32 hardware spec
    stream = p.open(
        format=pyaudio.paFloat32,
        channels=channels,
        rate=sample_rate,
        output=True
    )
    
    print("[*] Streaming clean line out... Press Ctrl+C to stop.")
    
    # Stream data using a clean chunk size
    chunk_size = 512
    try:
        # Step through the numpy array directly instead of converting the whole block to bytes at once
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            # Ensure the chunk is contiguous in memory and in float32 format
            clean_bytes = chunk.astype(np.float32).tobytes()
            stream.write(clean_bytes)
            
    except KeyboardInterrupt:
        print("\n[!] Playback interrupted.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("[*] Playback finished. Hardware released.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python play_audio.py <path_to_file.wav>")
        sys.exit(1)
        
    play_wav_file(sys.argv[1])