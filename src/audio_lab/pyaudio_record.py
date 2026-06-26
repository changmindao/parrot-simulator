import sys
import os
import time
import soundfile as sf
import pyaudio
import numpy as np

# --- DEFAULT HARDWARE CONFIGURATION ---
SAMPLE_RATE = 48000
CHUNK_SIZE = 512
CHANNELS = 1  
DEFAULT_DURATION_SEC = 10.0  # Added: 10-second fallback safety net

def record_wav_file(output_path, duration_seconds=DEFAULT_DURATION_SEC):
    """
    Records audio from the line-in hardware channel and saves it cleanly as a float32 WAV.
    Passing float('inf') or a manual break lets it run continuously.
    """
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
    except Exception as e:
        print(f"❌ Error opening audio input device: {e}")
        p.terminate()
        return

    print("="*60)
    print(f"[*] Recording Target: '{output_path}'")
    print(f"    -> Sample Rate: {SAMPLE_RATE} Hz")
    print(f"    -> Format:      32-bit Float PCM (Mono)")
    
    # Render descriptive status based on incoming duration configuration
    if duration_seconds == float('inf') or duration_seconds is None:
        print(f"    -> Mode:        Continuous (Press Ctrl+C to stop and save)")
        max_chunks = None
    else:
        print(f"    -> Mode:        Timed Duration ({duration_seconds} seconds)")
        max_chunks = int((SAMPLE_RATE / CHUNK_SIZE) * duration_seconds)
    print("="*60)
    
    recorded_chunks = []
    print("\n🔴 RECORDING ACTIVE... Speak into the line now.")
    
    try:
        chunk_count = 0
        while True:
            raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_chunk = np.frombuffer(raw_data, dtype=np.float32)
            recorded_chunks.append(audio_chunk)
            
            chunk_count += 1
            if max_chunks and chunk_count >= max_chunks:
                print("\n[*] Target duration reached.")
                break
                
    except KeyboardInterrupt:
        print("\n[!] Recording stopped by user interrupt.")
        
    finally:
        print("[*] Flushing hardware buffers and cleaning up stream...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    if len(recorded_chunks) == 0:
        print("❌ No audio frames captured. File not saved.")
        return
        
    full_audio_data = np.concatenate(recorded_chunks, axis=0)
    
    print(f"[*] Writing {len(full_audio_data)} samples to disk...")
    sf.write(output_path, full_audio_data, SAMPLE_RATE, subtype='FLOAT')
    print(f"🎉 Success! Audio cleanly recorded to '{output_path}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Default (10s): python record_audio.py <output_file.wav>")
        print("  Custom Timed:  python record_audio.py <output_file.wav> <duration_seconds>")
        print("  Continuous:    python record_audio.py <output_file.wav> inf")
        sys.exit(1)
        
    target_file = sys.argv[1]
    
    # Parse duration input, defaulting to 10.0 seconds if left blank
    target_duration = DEFAULT_DURATION_SEC
    if len(sys.argv) >= 3:
        val = sys.argv[2].strip().lower()
        if val in ['inf', 'infinite', 'continuous']:
            target_duration = float('inf')
        else:
            try:
                target_duration = float(val)
            except ValueError:
                print("❌ Error: Duration must be a number of seconds or 'inf'.")
                sys.exit(1)
            
    record_wav_file(target_file, target_duration)