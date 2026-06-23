import os
import wave
import json
import subprocess
import time
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import ollama

class PollyEngine:
    def __init__(self, state_callback=None):
        self.state_callback = state_callback
        self.is_running = False
        
        # --- Configuration ---
        self.PLAYBACK_FILE = "parrot_english.wav"
        self.RECORD_OUTPUT_FILE = "parrot_temp_input.wav"
        self.PARROT_VOICE = "Alex"
        self.HISTORY_FILE = "history.json"
        self.MODEL_NAME = "phi3"
        self.WAKE_WORDS = ["parrot", "pirate"]
        self.EXIT_WORDS = ["goodbye", "exit", "stop", "quit"]
        
        self.recognizer = sr.Recognizer()
        self.conversation_history = []
        
        # Initialize resources and persistent memory
        self._load_audio_resources()
        self._load_history()

    def _load_audio_resources(self):
        if not os.path.exists(self.PLAYBACK_FILE):
            raise FileNotFoundError(f"❌ Error: {self.PLAYBACK_FILE} not found!")

        with wave.open(self.PLAYBACK_FILE, 'rb') as wf:
            self.sample_rate = wf.getframerate()
            playback_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0
        
        self.extended_playback = np.pad(playback_data, (int(1.0 * self.sample_rate), int(2.5 * self.sample_rate)), mode='constant')

    def _load_history(self):
        """Loads conversation history from disk or creates a fresh baseline prompt."""
        system_prompt = {
            'role': 'system',
            'content': (
                'You are a cheeky, witty pirate parrot named Polly. Respond to the user in a short single sentence. '
                'You must include classic parrot sounds, but you MUST spell them phonetically as "wawk!" or "Squawk!" '
                'so the voice synthesizer pronounces them correctly. Never type "awk".'
            )
        }
        
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    self.conversation_history = json.load(f)
                print("💾 Persistent history restored successfully from disk.")
                # Ensure system prompt is always enforced at the top
                if not self.conversation_history or self.conversation_history[0]['role'] != 'system':
                    self.conversation_history.insert(0, system_prompt)
            except Exception as e:
                print(f"⚠️ Error reading history.json, starting fresh: {e}")
                self.conversation_history = [system_prompt]
        else:
            self.conversation_history = [system_prompt]

    def _save_history(self):
        """Writes current multi-turn history out to the local JSON file."""
        try:
            with open(self.HISTORY_FILE, 'w') as f:
                json.dump(self.conversation_history, f, indent=4)
        except Exception as e:
            print(f"⚠️ Failed to save history to disk: {e}")

    def speak_like_a_parrot(self, text):
        """
        Audio Enhancement Layer:
        Uses macOS 'say' tuning flags to alter speech rate and tone.
        '[[rate 230]]' speeds up the utterance to sound hyperactive/bird-like.
        '[[pitch 65]]' pushes Alex's fundamental frequency higher to mimic a smaller vocal tract.
        """
        # Strip out emojis if any before passing to internal speech commands
        clean_text = text.replace("🦜", "").replace("💬", "").strip()
        enhanced_string = f"[[rate 200]] [[pitch 65]] {clean_text}"
        
        # Execute the native command line audio process
        subprocess.run(["say", "-v", f"{self.PARROT_VOICE}", enhanced_string])        

    def set_state(self, state_name):
        if self.state_callback:
            self.state_callback(state_name)

    def listen_for_wake_word(self):
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
        self.is_running = True
        
        while self.is_running:
            self.set_state("sleeping")
            status = self.listen_for_wake_word()
            
            if status == "exit" or not self.is_running:
                print("👋 Shutdown command caught.")
                self.speak_like_a_parrot("wawk! Goodbye matey! Fly away now!")
                exit_ui_callback()
                break
                
            if status == "wake":
                self.set_state("listening")
                recorded_data = sd.playrec(self.extended_playback, samplerate=self.sample_rate, channels=1, dtype='float32')
                time.sleep(1.0) 
                sd.wait() 

                recorded_data_int16 = (recorded_data * 32767).astype(np.int16)
                with wave.open(self.RECORD_OUTPUT_FILE, 'wb') as out_wf:
                    out_wf.setnchannels(1)
                    out_wf.setsampwidth(2)
                    out_wf.setframerate(self.sample_rate)
                    out_wf.writeframes(recorded_data_int16.tobytes())

                self.set_state("processing")
                try:
                    with sr.AudioFile(self.RECORD_OUTPUT_FILE) as source:
                        processed_audio = self.recognizer.record(source)
                        user_text = self.recognizer.recognize_google(processed_audio)
                    print(f"👤 Dialogue text parsed: \"{user_text}\"")
                    
                    if any(word in user_text.lower() for word in self.EXIT_WORDS):
                        self.speak_like_a_parrot("wawk! Goodbye matey!")
                        exit_ui_callback()
                        break

                    self.conversation_history.append({'role': 'user', 'content': user_text})
                    self._save_history()

                    self.set_state("thinking")
                    response = ollama.chat(model=self.MODEL_NAME, messages=self.conversation_history)
                    parrot_reply = response['message']['content']
                    print(f"🦜 Polly: {parrot_reply}")

                    self.conversation_history.append({'role': 'assistant', 'content': parrot_reply})
                    
                    # Manage long-term context window while keeping the system instruction intact
                    if len(self.conversation_history) > 9:
                        self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-8:]
                    self._save_history()

                    self.set_state("speaking")
                    self.speak_like_a_parrot(parrot_reply)

                except sr.UnknownValueError:
                    print("⚠️ Dialogue STT couldn't isolate words.")
                    self.set_state("speaking")
                    self.speak_like_a_parrot("wawk! Polly heard nothing but the rolling waves!")
                
                if os.path.exists(self.RECORD_OUTPUT_FILE):
                    try: os.remove(self.RECORD_OUTPUT_FILE)
                    except: pass
                
                time.sleep(1.0)

    def stop(self):
        self.is_running = False
        if os.path.exists(self.RECORD_OUTPUT_FILE):
            try: os.remove(self.RECORD_OUTPUT_FILE)
            except: pass