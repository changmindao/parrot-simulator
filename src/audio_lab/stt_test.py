import os
import wave
import subprocess
import time
import sounddevice as sd
import numpy as np
import speech_recognition as sr

# --- Configuration ---
SAMPLE_RATE = 48000
DURATION = 3.5
TEMP_FILE = "parrot_temp.wav"
PARROT_VOICE = "Alex"  
#
# Alex                en_US    # Most people recognize me by my voice.
# Alice               it_IT    # Salve, mi chiamo Alice e sono una voce italiana.
# Alva                sv_SE    # Hej, jag heter Alva. Jag är en svensk röst.
# Amelie              fr_CA    # Bonjour, je m’appelle Amelie. Je suis une voix canadienne.
# Anna                de_DE    # Hallo, ich heiße Anna und ich bin eine deutsche Stimme.

recognizer = sr.Recognizer()

print("🦜 Parrot Engine: Speech-to-text test")
print("---------------------------------------")

try:
    # 1. Record the voice token
    print(f"🎙️ Listening for {DURATION} seconds... Speak now!")
    audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    print("🛑 Stopped listening.")

    # 2. Save temporarily to disk for processing
    audio_data_int16 = (audio_data * 32767).astype(np.int16)
    with wave.open(TEMP_FILE, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_data_int16.tobytes())

    # 3. Speech-to-Text Analysis
    print("🤔 Processing audio signals...")
    with sr.AudioFile(TEMP_FILE) as source:
        # Load audio data into the speech recognition engine
        processed_audio = recognizer.record(source)
        
        # Recognize using Google's free speech synthesis engine
        user_text = recognizer.recognize_google(processed_audio)
        print(f"👤 You said: \"{user_text}\"")

    time.sleep(0.5)

    # 4. Text-to-Speech (The Parrot Squawk)
    print(f"🦜 Parrot responses via macOS '{PARROT_VOICE}' engine...")
    # Using native macOS terminal 'say' utility via subprocess
    subprocess.run(["say", "-v", PARROT_VOICE, f"Awk! {user_text}! Polly wants a cracker!"])

except sr.UnknownValueError:
    print("❌ Parrot Error: Audio signal unintelligible. Speak closer to the webcam microphone.")
except sr.RequestError as e:
    print(f"❌ Network Error: Could not connect to the recognition service; check connection: {e}")
except Exception as e:
    print(f"❌ System Error: {e}")
finally:
    # Cleanup temp file
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)