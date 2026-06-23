import sounddevice as sd
import numpy as np
import wave
import time

# --- Configuration ---
SAMPLE_RATE = 48000  # Standard CD quality audio
DURATION = 3.0       # Seconds to record
OUTPUT_FILENAME = "record_echo_test.wav"

print("🎙️ Mac Mini Parrot Simulator: Saving to WAV")
print("------------------------------------------")

try:
    # 1. Recording
    print(f"1. Recording for {DURATION} seconds... Speak now!")
    audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()  # Wait until the recording is finished
    print("🛑 Recording stopped.")

    # 2. Convert and Save to WAV
    print(f"💾 Saving recording to '{OUTPUT_FILENAME}'...")
    
    # Sounddevice records in float32 (-1.0 to 1.0). 
    # We must convert this to 16-bit integers (-32768 to 32767) for a standard WAV file.
    audio_data_int16 = (audio_data * 32767).astype(np.int16)
    
    # Open the wave file layout context
    with wave.open(OUTPUT_FILENAME, 'wb') as wav_file:
        wav_file.setnchannels(1)           # Mono
        wav_file.setsampwidth(2)           # 2 bytes per sample (16-bit)
        wav_file.setframerate(SAMPLE_RATE) # 48000 Hz
        wav_file.writeframes(audio_data_int16.tobytes())
        
    print("✅ File saved successfully!")

    time.sleep(0.5)

    # 3. Playback
    print("2. Playing back what I heard...")
    sd.play(audio_data, SAMPLE_RATE)
    sd.wait()  # Wait until the playback is finished
    print("✅ Playback finished!")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")
    print("Tip: Check if your microphone is connected and your Terminal has Microphone permissions in macOS System Settings.")