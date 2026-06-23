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
MODEL_NAME = "phi3"
WAKE_WORDS = ["parrot", "pirate"]  # The wake-up words to activate the AI brain
EXIT_WORDS = ["goodbye", "exit", "stop", "quit"] # the words to exit the loop

recognizer = sr.Recognizer()

# Load the initial "Parrot" prompt audio into memory
if not os.path.exists(PLAYBACK_FILE):
    print(f"❌ Error: {PLAYBACK_FILE} not found! Please generate it first.")
    exit()

with wave.open(PLAYBACK_FILE, 'rb') as wf:
    sample_rate = wf.getframerate()
    playback_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0

extended_playback = np.pad(playback_data, (int(1.0 * sample_rate), int(2.5 * sample_rate)), mode='constant')

print("🦜 Parrot Engine: Wake-Up Word Activation Mode")
print(f"🤫 Say '{WAKE_WORDS[0].upper()}' to wake up the parrot simulation.")
print("👉 Press Ctrl+C to exit.")
print("--------------------------------------------------")

conversation_history = [
    {
        'role': 'system',
        'content': (
            'You are a cheeky, witty pirate parrot named Polly. Respond to the user in a short single sentence. '
            'You must include classic parrot sounds, but you MUST spell them phonetically as "wawk!" or "Squawk!" '
            'so the voice synthesizer pronounces them correctly. Never type "awk".'
        )
    }
]
def listen_for_wake_word():
    """Listens continuously in short bursts for the wake-up word."""
    with sr.Microphone() as source:
        # Calibrate background noise briefly so ambient hum doesn't trigger it
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while True:
            try:
                print("💤 System sleeping... listening for wake word...")
                # phrase_time_limit keeps the listening window tight and responsive
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=2.5)
                text = recognizer.recognize_google(audio).lower()
                print(f"👂 Heard passive audio: '{text}'")
                
                # 1. Global Exit Check while sleeping
                if any(word in text for word in EXIT_WORDS):
                    print("👋 Voice exit command caught in sleep mode.")
                    return "exit"
                
                # 2. Wake Word Check
                if any(word in text for word in WAKE_WORDS):
                    print("🔥 [WOKE UP] Wake word matched successfully!")
                    return True

            except sr.UnknownValueError:
                # Normal background ambient noise that couldn't be parsed as words
                continue
            except Exception as e:
                print(f"⚠️ Passive listening notice: {e}")
                time.sleep(1)

try:
    while True:
        # --- STAGE 1: Passive Wake Word / Exit Wait ---
        status = listen_for_wake_word()
        
        if status == "exit":
            subprocess.run(["say", "-v", PARROT_VOICE, "Ahwk! Goodbye matey! Fly away now!"])
            break  # Breaks the main while loop to exit the program cleanly
        
        if status:
            # --- STAGE 2: Active Full-Duplex Dialogue ---
            print("\n⚡ [ACTIVE DIALOGUE] Starting conversation cycle...")
            recorded_data = sd.playrec(extended_playback, samplerate=sample_rate, channels=1, dtype='float32')
            
            time.sleep(1.0)
            print("🔊 [PLAYING ARCHIVE] 'Parrot' audio prompt fired...")
            sd.wait() 
            print("🛑 [STOPPED] Recording finished. Processing...")

            # Export raw buffer to temporary file
            recorded_data_int16 = (recorded_data * 32767).astype(np.int16)
            with wave.open(RECORD_OUTPUT_FILE, 'wb') as out_wf:
                out_wf.setnchannels(1)
                out_wf.setsampwidth(2)
                out_wf.setframerate(sample_rate)
                out_wf.writeframes(recorded_data_int16.tobytes())

            # Speech-To-Text processing
            try:
                with sr.AudioFile(RECORD_OUTPUT_FILE) as source:
                    processed_audio = recognizer.record(source)
                    user_text = recognizer.recognize_google(processed_audio)
                print(f"👤 Dialogue text parsed: \"{user_text}\"")
                
                # Add user message to history
                conversation_history.append({'role': 'user', 'content': user_text})

                # Local AI Brain Inference (Ollama)
                print(f"🧠 Consulting local AI ({MODEL_NAME})...")
                response = ollama.chat(model=MODEL_NAME, messages=conversation_history)
                
                parrot_reply = response['message']['content']
                print(f"🦜 Parrot thoughts: {parrot_reply}")

                # Add parrot response to history
                conversation_history.append({'role': 'assistant', 'content': parrot_reply})
                
                # Keep conversation history slim
                if len(conversation_history) > 7:
                    conversation_history = [conversation_history[0]] + conversation_history[-6:]

                # Text-to-Speech Response
                print(f"💬 Parrot speaking...")
                subprocess.run(["say", "-v", PARROT_VOICE, parrot_reply])

            except sr.UnknownValueError:
                print("⚠️ Dialogue STT couldn't isolate words. Returning to sleep mode.")
            
            # Short cooldown pause before returning to passive sleeping state
            time.sleep(1.5)

except KeyboardInterrupt:
    print("\n🛑 Program interrupted manually via terminal. Exiting clean.")
finally:
    if os.path.exists(RECORD_OUTPUT_FILE):
        os.remove(RECORD_OUTPUT_FILE)
    print("✨ Loop terminated.")