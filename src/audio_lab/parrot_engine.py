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
ENERGY_THRESHOLD = 0.02  # Noise gate for incoming line-level signal


class ParrotEngine:
    def __init__(self, mode_asr=DEFAULT_MODE_ASR, mode_llm=DEFAULT_MODE_LLM, mode_tts=DEFAULT_MODE_TTS):
        """Initializes the pluggable Parrot execution state engine."""
        self.mode_asr = mode_asr
        self.mode_llm = mode_llm
        self.mode_tts = mode_tts
        
        # UI state callback hook
        self.state_callback = None
        self.is_running = False
        
        # --- THE KEY TRACKING FLAG ---
        # True when the parrot is actively speaking to prevent feedback loops
        self.is_speaking = False 
        
        print(f"[*] Parrot Engine Initialized")
        print(f"    - ASR Mode: {self.mode_asr}")
        print(f"    - LLM Mode: {self.mode_llm}")
        print(f"    - TTS Mode: {self.mode_tts}\n")

    def set_state(self, state_name):
        """Safely signals state updates back to the Tkinter GUI thread."""
        if self.state_callback:
            self.state_callback(state_name)

    def speak(self, text):
        """Dynamically synthesizes text using system subprocesses."""
        self.is_speaking = True  # Block the recording loop from listening
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
            self.set_state("sleeping")
            # Small cooldown cushion to let mechanical/electrical echo subside
            time.sleep(0.1) 
            self.is_speaking = False  # Unblock the recording loop

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
        """Background thread loop dedicated entirely to recording input."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        has_woken_up = False
        
        try:
            while self.is_running:
                raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # If the player engine is running text-to-speech, completely 
                # ignore incoming audio chunks to break the loopback oscillation.
                if self.is_speaking:
                    continue
                    
                audio_chunk = np.frombuffer(raw_data, dtype=np.float32)
                rms_energy = np.sqrt(np.mean(audio_chunk**2))
                
                if rms_energy > ENERGY_THRESHOLD:
                    if not has_woken_up:
                        self.set_state("listening")
                        time.sleep(0.5)  # Let the host finish speaking
                        print("[Event]: Wake-Up Signal Detected on Line-In!")
                        
                        # Trigger execution (will set self.is_speaking = True)
                        self.speak("I am Polly. What's up?")
                        has_woken_up = True
                    else:
                        self.set_state("listening")
                        time.sleep(1.0)  # Let the host finish speaking
                        print("[Event]: Command Request Detected on Line-In...")
                        
                        user_text = self.mock_asr_process()
                        llm_response = self.mock_llm_process(user_text)
                        
                        # Trigger execution (will set self.is_speaking = True)
                        self.speak(llm_response)
                        has_woken_up = False
                        
                time.sleep(0.001)
                
        except Exception as e:
            print(f"❌ Error in listening thread: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def run_pipeline(self, destroy_callback=None):
        """
        Launches the detached recorder loop process thread and returns immediately
        to keep the calling thread (like Tkinter or the CLI main input) completely unblocked.
        """
        self.is_running = True
        
        print("="*60)
        print("  PARROT ENGINE SUT RUNNING (Awaiting Host Audio Triggers)")
        print("="*60)
        
        self.set_state("sleeping")
        
        # Spin up the recording path completely independently
        self.listener_thread = threading.Thread(target=self._listen_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        

    def stop(self):
        """Stops the audio background execution thread."""
        self.is_running = False

if __name__ == "__main__":
    parrot = ParrotEngine()
    parrot.run_pipeline()
    
    print("\n" + "="*60)
    print("  CLI INTERACTIVE CONTROLLER ACTIVE")
    print("  - Audio pipeline is running asynchronously in the background.")
    print("  - To terminate the test rig safely, press [C] or [Q] and hit Enter.")
    print("="*60 + "\n")
    
    # Use the main thread to capture terminal keyboard inputs cleanly
    try:
        while True:
            user_input = input("Command -> ").strip().lower()
            if user_input in ['c', 'q']:
                print("\n[*] Termination key detected. Powering down pipelines...")
                parrot.stop()
                break
            else:
                print(f"[*] Unknown command '{user_input}'. Press 'c' or 'q' to exit.")
    except (KeyboardInterrupt, SystemExit):
        parrot.stop()
        
    print("[*] Exit complete. Goodbye!")
    sys.exit(0)