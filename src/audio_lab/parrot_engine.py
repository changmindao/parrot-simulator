import os
import wave
import subprocess
import time
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import ollama

class PollyEngine:
    def __init__(self, state_callback=None):
        """
        Initializes the low-level audio pipeline and AI core.
        state_callback: A function pointer used to update the UI state.
        """
        self.state_callback = state_callback
        self.is_running = False
        
        # --- Audio & AI Configuration ---
        self.PLAYBACK_FILE = "parrot_english.wav"
        self.RECORD_OUTPUT_FILE = "parrot_temp_input.wav"
        self.PARROT_VOICE = "Alex"
        self.MODEL_NAME = "phi3"
        self.WAKE_WORD = "parrot"  
        self.WAKE_WORDS = ["parrot", "pirate"]
        self.EXIT_WORDS = ["goodbye", "exit", "stop", "quit"]
        
        self.recognizer = sr.Recognizer()
        self.conversation_history = [
            {
                'role': 'system',
                'content': (
                    'You are a cheeky, witty pirate parrot named Polly. Respond to the user in a short single sentence. '
                    'You must include classic parrot sounds, but you MUST spell them phonetically as "wawk!" or "Squawk!" '
                    'so the voice synthesizer pronounces them correctly. Never type "awk".'
                )
            }
        ]
        
        self._load_audio_resources()

    def _load_audio_resources(self):
        """Reads the pristine baseline file and constructs the front/back padding arrays."""
        if not os.path.exists(self.PLAYBACK_FILE):
            raise FileNotFoundError(f"❌ Error: {self.PLAYBACK_FILE} not found!")

        with wave.open(self.PLAYBACK_FILE, 'rb') as wf:
            self.sample_rate = wf.getframerate()
            playback_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0
        
        # Sandwich playback signal between 1.0s and 2.5s buffers of silence
        self.extended_playback = np.pad(playback_data, (int(1.0 * self.sample_rate), int(2.5 * self.sample_rate)), mode='constant')

    def set_state(self, state_name):
        """Safely passes execution states back up to the UI engine if a hook exists."""
        if self.state_callback:
            self.state_callback(state_name)

    def listen_for_wake_word(self):
        """Passively samples mic frames checking for wake or exit phrases."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            while self.is_running:
                try:
                    audio = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=2.5)
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"👂 Heard passive audio: '{text}'")
                    
                    if any(word in text for word in self.EXIT_WORDS):
                        return "exit"
                    if any(word in text for word in self.WAKE_WORDS):
                        return "wake"
                except sr.WaitTimeoutError:
                    continue  
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"⚠️ Passive listening notice: {e}")
                    time.sleep(1)
        return "stop"

    def run_pipeline(self, exit_ui_callback):
        """Main operational core loop designed to run inside a detached worker thread."""
        self.is_running = True
        
        while self.is_running:
            self.set_state("sleeping")
            status = self.listen_for_wake_word()
            
            if status == "exit" or not self.is_running:
                print("👋 Shutdown command caught.")
                subprocess.run(["say", "-v", self.PARROT_VOICE, "wawk! Goodbye matey! Fly away now!"])
                exit_ui_callback()
                break
                
            if status == "wake":
                # 1. Full-Duplex Playback/Record Loop
                self.set_state("listening")
                recorded_data = sd.playrec(self.extended_playback, samplerate=self.sample_rate, channels=1, dtype='float32')
                time.sleep(1.0) 
                sd.wait() 

                # 2. Export Master Buffer to Temp Disk Audio
                recorded_data_int16 = (recorded_data * 32767).astype(np.int16)
                with wave.open(self.RECORD_OUTPUT_FILE, 'wb') as out_wf:
                    out_wf.setnchannels(1)
                    out_wf.setsampwidth(2)
                    out_wf.setframerate(self.sample_rate)
                    out_wf.writeframes(recorded_data_int16.tobytes())

                # 3. Speech-to-Text Interpretation
                self.set_state("thinking")
                try:
                    with sr.AudioFile(self.RECORD_OUTPUT_FILE) as source:
                        processed_audio = self.recognizer.record(source)
                        user_text = self.recognizer.recognize_google(processed_audio)
                    print(f"👤 Dialogue text parsed: \"{user_text}\"")
                    
                    if any(word in user_text.lower() for word in self.EXIT_WORDS):
                        subprocess.run(["say", "-v", self.PARROT_VOICE, "wawk! Goodbye matey!"])
                        exit_ui_callback()
                        break

                    self.conversation_history.append({'role': 'user', 'content': user_text})

                    # 4. Local AI Context Inference via Ollama
                    response = ollama.chat(model=self.MODEL_NAME, messages=self.conversation_history)
                    parrot_reply = response['message']['content']
                    print(f"🦜 Polly: {parrot_reply}")

                    self.conversation_history.append({'role': 'assistant', 'content': parrot_reply})
                    if len(self.conversation_history) > 7:
                        self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]

                    # 5. Core Voice Synthesis Response
                    self.set_state("speaking")
                    subprocess.run(["say", "-v", self.PARROT_VOICE, parrot_reply])

                except sr.UnknownValueError:
                    print("⚠️ Dialogue STT couldn't isolate words.")
                    self.set_state("speaking")
                    subprocess.run(["say", "-v", self.PARROT_VOICE, "wawk! Polly heard nothing but the rolling waves!"])
                
                # Cleanup Temporary Assets
                if os.path.exists(self.RECORD_OUTPUT_FILE):
                    try: os.remove(self.RECORD_OUTPUT_FILE)
                    except: pass
                
                time.sleep(1.0)

    def stop(self):
        """Toggles execution control flags off for thread termination."""
        self.is_running = False
        if os.path.exists(self.RECORD_OUTPUT_FILE):
            try: os.remove(self.RECORD_OUTPUT_FILE)
            except: pass