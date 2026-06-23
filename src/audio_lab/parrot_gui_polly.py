import os
import wave
import subprocess
import time
import threading
import tkinter as tk
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import ollama

class PollyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🦜 Polly Simulator")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # --- Audio & AI Configuration ---
        self.PLAYBACK_FILE = "parrot_english.wav"
        self.RECORD_OUTPUT_FILE = "parrot_temp_input.wav"
        self.PARROT_VOICE = "Alex"
        self.MODEL_NAME = "phi3"
        self.WAKE_WORDS = ["parrot", "pirat"]
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
        
        # Load the initial "Parrot" prompt audio into memory
        if not os.path.exists(self.PLAYBACK_FILE):
            print(f"❌ Error: {self.PLAYBACK_FILE} not found! Please generate it first.")
            self.root.destroy()
            return

        with wave.open(self.PLAYBACK_FILE, 'rb') as wf:
            self.sample_rate = wf.getframerate()
            playback_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0
        
        self.extended_playback = np.pad(playback_data, (int(1.0 * self.sample_rate), int(2.5 * self.sample_rate)), mode='constant')

        # --- UI State Configuration ---
        self.states = {
            "sleeping": {"bg": "#2C3E50", "text": "#ECF0F1", "status": "💤 Polly is resting..."},
            "listening": {"bg": "#E74C3C", "text": "#FFFFFF", "status": "🔴 Listening! Speak now..."},
            "thinking": {"bg": "#F39C12", "text": "#FFFFFF", "status": "🧠 Polly is thinking..."},
            "speaking": {"bg": "#2ECC71", "text": "#FFFFFF", "status": "💬 Polly is squawking..."}
        }
        
        # --- Build UI Layout ---
        self.main_frame = tk.Frame(self.root, bg=self.states["sleeping"]["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.avatar_label = tk.Label(self.main_frame, text="🦜", font=("Arial", 72), bg=self.main_frame["bg"])
        self.avatar_label.pack(pady=40)
        
        self.status_label = tk.Label(
            self.main_frame, 
            text=self.states["sleeping"]["status"], 
            font=("Arial", 14, "bold"), 
            fg=self.states["sleeping"]["text"], 
            bg=self.main_frame["bg"]
        )
        self.status_label.pack(pady=10)
        
        # Handle clean window close if user clicks the red "X"
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # --- Start the Engine ---
        print("🦜 Core Audio Loop starting in background thread...")
        self.is_running = True
        self.worker_thread = threading.Thread(target=self.main_audio_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def set_ui_state(self, state_name):
        """Thread-safe UI state updater using root.after to prevent Tkinter race conditions."""
        if state_name in self.states:
            config = self.states[state_name]
            # Schedule execution on the main thread
            self.root.after(0, lambda: self._update_ui_elements(config))

    def _update_ui_elements(self, config):
        """Performs actual widget property updates on the main thread."""
        self.main_frame.config(bg=config["bg"])
        self.avatar_label.config(bg=config["bg"])
        self.status_label.config(text=config["status"], fg=config["text"], bg=config["bg"])

    def listen_for_wake_word(self):
        """Passively streams audio from mic. Intercepts exits or wake words."""
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
                    continue  # Timeout allows loop to check if self.is_running is still True
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"⚠️ Passive listening notice: {e}")
                    time.sleep(1)
        return "stop"

    def main_audio_loop(self):
        """Background pipeline running decoupled from the UI framework."""
        while self.is_running:
            self.set_ui_state("sleeping")
            status = self.listen_for_wake_word()
            
            if status == "exit" or not self.is_running:
                print("👋 Shutdown command caught.")
                subprocess.run(["say", "-v", self.PARROT_VOICE, "wawk! Goodbye matey! Fly away now!"])
                self.root.after(0, self.root.destroy)
                break
                
            if status == "wake":
                # 1. Full-Duplex Playback/Record
                self.set_ui_state("listening")
                recorded_data = sd.playrec(self.extended_playback, samplerate=self.sample_rate, channels=1, dtype='float32')
                time.sleep(1.0) # wait for padding
                sd.wait() 

                # 2. Export WAV file
                recorded_data_int16 = (recorded_data * 32767).astype(np.int16)
                with wave.open(self.RECORD_OUTPUT_FILE, 'wb') as out_wf:
                    out_wf.setnchannels(1)
                    out_wf.setsampwidth(2)
                    out_wf.setframerate(self.sample_rate)
                    out_wf.writeframes(recorded_data_int16.tobytes())

                # 3. Speech-to-Text
                self.set_ui_state("thinking")
                try:
                    with sr.AudioFile(self.RECORD_OUTPUT_FILE) as source:
                        processed_audio = self.recognizer.record(source)
                        user_text = self.recognizer.recognize_google(processed_audio)
                    print(f"👤 Dialogue text parsed: \"{user_text}\"")
                    
                    if any(word in user_text.lower() for word in self.EXIT_WORDS):
                        subprocess.run(["say", "-v", self.PARROT_VOICE, "wawk! Goodbye matey!"])
                        self.root.after(0, self.root.destroy)
                        break

                    self.conversation_history.append({'role': 'user', 'content': user_text})

                    # 4. Local AI Inference
                    response = ollama.chat(model=self.MODEL_NAME, messages=self.conversation_history)
                    parrot_reply = response['message']['content']
                    print(f"🦜 Polly: {parrot_reply}")

                    self.conversation_history.append({'role': 'assistant', 'content': parrot_reply})
                    if len(self.conversation_history) > 7:
                        self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]

                    # 5. Output response
                    self.set_ui_state("speaking")
                    subprocess.run(["say", "-v", self.PARROT_VOICE, parrot_reply])

                except sr.UnknownValueError:
                    print("⚠️ Dialogue STT couldn't isolate words.")
                    self.set_ui_state("speaking")
                    subprocess.run(["say", "-v", self.PARROT_VOICE, "wawk! Polly heard nothing but the rolling waves!"])
                
                # Clean temp audio file
                if os.path.exists(self.RECORD_OUTPUT_FILE):
                    os.remove(self.RECORD_OUTPUT_FILE)
                
                time.sleep(1.0)

    def on_closing(self):
        """Cleans up pipeline state when application window is manually shut down."""
        print("🛑 Closing window, cleaning up audio pipelines...")
        self.is_running = False
        if os.path.exists(self.RECORD_OUTPUT_FILE):
            try: os.remove(self.RECORD_OUTPUT_FILE)
            except: pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PollyGUI(root)
    root.mainloop()