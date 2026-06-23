import os
import wave
import subprocess
import time
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import ollama

# --- Configuration ---
PLAYBACK_FILE = "parrot_english.wav"
RECORD_OUTPUT_FILE = "parrot_temp_input.wav"
PARROT_VOICE = "Alex"
MODEL_NAME = "phi3"  # Ensure you ran 'ollama run phi3' in terminal first

recognizer = sr.Recognizer()

print("🦜 Parrot Engine: Milestone 3 (Local LLM Active)")
print("--------------------------------------------------")

try:
    # 1. Full Duplex Audio Loop (Same as Milestone 2)
    with wave.open(PLAYBACK_FILE, 'rb') as wf:
        sample_rate = wf.getframerate()
        playback_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0

    extended_playback = np.pad(playback_data, (int(1.0 * sample_rate), int(5.0 * sample_rate)), mode='constant')
    
    print("\n⚡ [STARTING] Audio loop initialized...")
    recorded_data = sd.playrec(extended_playback, samplerate=sample_rate, channels=1, dtype='float32')
    
    time.sleep(1.0)
    print("🔊 [PLAYING] 'Parrot' audio prompt...")
    sd.wait()  # Wait for user to finish speaking during trailing silence
    print("🛑 [STOPPED] Recording finished.")

    # 2. Export to WAV
    recorded_data_int16 = (recorded_data * 32767).astype(np.int16)
    with wave.open(RECORD_OUTPUT_FILE, 'wb') as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(sample_rate)
        out_wf.writeframes(recorded_data_int16.tobytes())

    # 3. Speech-To-Text
    print("\n🤔 Processing speech...")
    with sr.AudioFile(RECORD_OUTPUT_FILE) as source:
        processed_audio = recognizer.record(source)
        user_text = recognizer.recognize_google(processed_audio)
        print(f"👤 You said: \"{user_text}\"")

    # 4. Local AI Brain Inference (Ollama)
    print(f"🧠 Consulting local AI ({MODEL_NAME})...")
    
    response = ollama.chat(model=MODEL_NAME, messages=[
        {
            'role': 'system',
            'content': 'You are a cheeky, witty pirate parrot named Polly. Respond to the user in a short single sentence. You must include classic parrot sounds like "Awk!" or "Squawk!" or ask for a cracker.'
        },
        {
            'role': 'user',
            'content': user_text
        }
    ])
    
    parrot_reply = response['message']['content']
    print(f"🦜 Parrot thoughts: {parrot_reply}")

except sr.UnknownValueError:
    parrot_reply = "Awk! Polly heard nothing but the wind!"
    print("⚠️ STT couldn't isolate words.")
except Exception as e:
    parrot_reply = "Awk! My brain is scrambled!"
    print(f"❌ Error: {e}")
finally:
    if os.path.exists(RECORD_OUTPUT_FILE):
        os.remove(RECORD_OUTPUT_FILE)
        
    # 5. Text-to-Speech Response
    print(f"\n💬 Parrot speaking...")
    subprocess.run(["say", "-v", PARROT_VOICE, parrot_reply])
    print("✨ Cycle complete.")