import os
import sys
import time
import subprocess
import threading
import numpy as np
import pyaudio

# --- DEFAULT CONFIGURATION CONSTANTS ---
DEFAULT_MODE_ASR = "speech_recognition"
DEFAULT_MODE_LLM = "ollama"
DEFAULT_MODE_TTS = "mac_say"

SAMPLE_RATE = 48000
CHUNK_SIZE = 512
ENERGY_THRESHOLD = 0.02
ENERGY_THRESHOLD_ACTIVE = 0.01
ENERGY_THRESHOLD_INACTIVE = 0.05


class ParrotEngine:
    def __init__(self, mode_asr=DEFAULT_MODE_ASR, mode_llm=DEFAULT_MODE_LLM, mode_tts=DEFAULT_MODE_TTS):
        """Initializes the pluggable Parrot execution state engine."""
        self.mode_asr = mode_asr
        self.mode_llm = mode_llm
        self.mode_tts = mode_tts
        
        self.state_callback = None
        self.is_running = False
        self.is_speaking = False 
        self.listener_thread = None
        
        # Internal state indicator tracking for the FSM flow
        self.current_state = "sleeping"
        
        print(f"[*] Parrot Engine Initialized")
        print(f"    - ASR Mode: {self.mode_asr}")
        print(f"    - LLM Mode: {self.mode_llm}")
        print(f"    - TTS Mode: {self.mode_tts}\n")

    def set_state(self, state_name):
        """Safely signals state updates back to the Tkinter GUI thread."""
        self.current_state = state_name
        if self.state_callback:
            self.state_callback(state_name)

    def speak(self, text):
        """Dynamically synthesizes text using system subprocesses."""
        self.is_speaking = True  
        self.set_state("speaking")
        print(f"[Parrot Speaker]: '{text}'")
        
        try:
            if self.mode_tts == "mac_say":
                subprocess.run(["say", "-r", "180", text], check=True)
            elif self.mode_tts == "espeak":
                subprocess.run(["espeak", text], check=True)
            else:
                raise NotImplementedError(f"TTS Mode '{self.mode_tts}' is not supported.")
        finally:
            # Drop down handled conditionally by the listen loop lifecycle
            time.sleep(0.1) 
            self.is_speaking = False  

    def mock_asr_process(self):
        """Simulates processing frame buffer decoding delay."""
        self.set_state("processing")
        time.sleep(0.15) 
        return "decoded user voice string"

    def mock_llm_process(self, prompt):
        """Simulates Ollama local inference generation window."""
        self.set_state("thinking")
        time.sleep(0.45)
        return "The capital of France is Paris."

    def _listen_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        # --- THE TIME-BASED COOLDOWN COUNTER ---
        # Keeps track of how many real-time hardware chunks to ignore after speaking
        cooldown_chunks = 0
        
        try:
            while self.is_running:
                # This read() acts as our perfect 10.67ms hardware timer lock
                raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # 1. If Polly is currently speaking, drop the data
                if self.is_speaking:
                    continue
                    
                # 2. New Cooldown Guard: Count down in real hardware time (10.67ms per chunk)
                if cooldown_chunks > 0:
                    cooldown_chunks -= 1
                    continue  # Safely ignore this chunk while the audio line clears
                    
                audio_chunk = np.frombuffer(raw_data, dtype=np.float32)
                rms_energy = np.sqrt(np.mean(audio_chunk**2))
                
                if rms_energy > ENERGY_THRESHOLD:
                    if self.current_state == "sleeping":
                        self.set_state("listening")
                        time.sleep(0.5)  # Let wake phrase finish
                        
                        self.set_state("wake_up")
                        print("[Event]: Wake-Up Word Decoded!")
                        self.speak("I am Polly. What's up?")
                        
                        # --- SET THE COOLDOWN ---
                        # Force the engine to ignore everything for the next 30 chunks (~320ms)
                        cooldown_chunks = 30 
                        
                        self.set_state("woken_sleeping")
                        print("[State]: Alert & waiting for command query...")
                        
                    elif self.current_state == "woken_sleeping":
                        self.set_state("listening")
                        time.sleep(1.2)  # Let command payload finish
                        print("[Event]: Command Query Decoded!")
                        
                        user_text = self.mock_asr_process()
                        llm_response = self.mock_llm_process(user_text)
                        
                        self.speak(llm_response)
                        
                        # --- SET THE COOLDOWN ---
                        # Force a reset cooldown before allowing another wake word
                        cooldown_chunks = 30
                        
                        self.set_state("sleeping")
                        print("[State]: Cycle complete. Returning to baseline sleep.")
                        
                time.sleep(0.001)

        except Exception as e:
            print(f"❌ Error in listening thread: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("[*] Audio hardware stream released safely.")

    def run_pipeline(self, destroy_callback=None):
        """Launches the detached recorder loop process thread."""
        self.is_running = True
        self.set_state("sleeping")
        
        self.listener_thread = threading.Thread(target=self._listen_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def stop(self):
        """Stops the audio background execution thread cleanly."""
        print("[*] Stopping background pipelines...")
        self.is_running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)


if __name__ == "__main__":
    parrot = ParrotEngine()
    parrot.run_pipeline()
    
    print("\n" + "="*60)
    print("  CLI INTERACTIVE CONTROLLER ACTIVE")
    print("  - Short & Long listening loops operating concurrently.")
    print("  - Press [C] or [Q] to exit safely.")
    print("="*60 + "\n")
    
    try:
        while True:
            user_input = input("Command -> ").strip().lower()
            if user_input in ['c', 'q']:
                parrot.stop()
                break
    except (KeyboardInterrupt, SystemExit):
        parrot.stop()
        
    sys.exit(0)