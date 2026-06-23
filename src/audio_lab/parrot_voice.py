import os
import wave
import subprocess
import time
import sounddevice as sd
import numpy as np
import speech_recognition as sr

# --- Configuration ---
PLAYBACK_FILE = "parrot_english.wav"
RECORD_OUTPUT_FILE = "parrot_temp_input.wav"
PARROT_VOICE = "Alex"

recognizer = sr.Recognizer()

print("🦜 Parrot Engine: Simultaneous Playback & Record")
print("--------------------------------------------------")

if not os.path.exists(PLAYBACK_FILE):
    print(f"❌ Error: {PLAYBACK_FILE} not found! Please generate it first.")
    exit()

try:
    # 1. Read the target playback file metadata via wave
    print(f"📖 Reading '{PLAYBACK_FILE}' format...")
    with wave.open(PLAYBACK_FILE, 'rb') as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        # Read raw frames and convert back to float32 for sounddevice
        playback_frames = wf.readframes(wf.getnframes())
        playback_data = np.frombuffer(playback_frames, dtype=np.int16).astype(np.float32) / 32767.0

    print(f"📊 File Info: {sample_rate}Hz, {channels} Channel(s), Duration: {len(playback_data)/sample_rate:.2f}s")

# 2. Simultaneous Playback & Record (Full Duplex with Front & Back Padding)
    pad_before_seconds = 1.0
    pad_after_seconds = 1.0
    
    pad_before_samples = int(pad_before_seconds * sample_rate)
    pad_after_samples = int(pad_after_seconds * sample_rate)
    
    # np.pad tuple format: ((pad_before, pad_after), mode)
    extended_playback = np.pad(
        playback_data, 
        (pad_before_samples, pad_after_samples), 
        mode='constant', 
        constant_values=0.0
    )
    
    # Calculate total duration for user visibility
    total_duration = len(extended_playback) / sample_rate
    print(f"\n⏱️ Total session duration: {total_duration:.2f} seconds")
    print("⚡ [STARTING] Audio loop initialized...")
    print("🤫 (1s Silence) - Keep quiet while mic baselines...")
    
    recorded_data = sd.playrec(
        extended_playback, 
        samplerate=sample_rate, 
        channels=1, 
        dtype='float32'
    )
    
    # Provide a simple console countdown/cue for the user
    time.sleep(pad_before_seconds)
    print("🔊 [PLAYING] 'Parrot' audio file outputting now...")
    
    sd.wait()  # Wait until the entire playback (including trailing silence) finishes
    print("🛑 [STOPPED] Playback and recording finished.")
    

    # 3. Export recorded buffer to a WAV file for the STT engine
    recorded_data_int16 = (recorded_data * 32767).astype(np.int16)
    with wave.open(RECORD_OUTPUT_FILE, 'wb') as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(sample_rate)
        out_wf.writeframes(recorded_data_int16.tobytes())

    # 4. Speech-To-Text processing on the fresh recording
    print("\n🤔 Processing recorded signal...")
    with sr.AudioFile(RECORD_OUTPUT_FILE) as source:
        processed_audio = recognizer.record(source)
        user_text = recognizer.recognize_google(processed_audio)
        print(f"👤 Speech-to-Text heard: \"{user_text}\"")

    time.sleep(0.5)

except sr.UnknownValueError:
    print("⚠️ STT Notice: Audio captured, but engine couldn't isolate intelligible words.")
except sr.RequestError as e:
    print(f"❌ Network Error: {e}")
except Exception as e:
    print(f"❌ System Error: {e}")

finally:
    # 5. Clean up temporary recording and say "What's up?"
    if os.path.exists(RECORD_OUTPUT_FILE):
        os.remove(RECORD_OUTPUT_FILE)
        
    print(f"\n💬 Parrot responding via macOS '{PARROT_VOICE}'...")
    subprocess.run(["say", "-v", PARROT_VOICE, "What's up?"])
    print("✨ Cycle complete.")