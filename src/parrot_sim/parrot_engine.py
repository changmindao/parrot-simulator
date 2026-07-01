import os
import sys
import time
import subprocess
import threading
from collections import deque # Double-Ended Queue
import numpy as np
import soundfile as sf
import pyaudio

# Ensure our VAD function is accessible
from src.signal_processing.voice_activity_detector import get_voice_activity_timestamps as gvat

# --- CONFIGURATION CONSTANTS ---
DEFAULT_MODE_ASR = "speech_recognition"
DEFAULT_MODE_LLM = "ollama"
DEFAULT_MODE_TTS = "mac_say"

SAMPLE_RATE = 48000
CHUNK_SIZE = 512

# Convert hop/frame settings to lookback sample sizes
WAKEWORD_FRAME_SAMPLES = 2.0 * SAMPLE_RATE
COMMAND_FRAME_SAMPLES = 3.0 * SAMPLE_RATE
HOP_SAMPLES = 1.0 * SAMPLE_RATE


class ParrotEngine:
    def __init__(self, mode_asr=DEFAULT_MODE_ASR, mode_llm=DEFAULT_MODE_LLM, mode_tts=DEFAULT_MODE_TTS):
        self.mode_asr = mode_asr
        self.mode_llm = mode_llm
        self.mode_tts = mode_tts
        
        self.state_callback = None
        self.is_running = False
        self.is_speaking = False 
        self.listener_thread = None
        self.current_state = "sleeping"
        
        print(f"[*] Parrot Engine Initialized with VAD")

    def set_state(self, state_name):
        self.current_state = state_name
        if self.state_callback:
            self.state_callback(state_name)

    def speak(self, text):
        self.is_speaking = True  
        self.set_state("speaking")
        print(f"[Parrot Speaker]: '{text}'")
        try:
            if self.mode_tts == "mac_say":
                subprocess.run(["say", "-r", "180", text], check=True)
            elif self.mode_tts == "espeak":
                subprocess.run(["espeak", text], check=True)
        finally:
            time.sleep(0.1) 
            self.is_speaking = False  

    def mock_asr_process(self):
        self.set_state("processing")
        time.sleep(2.0) 
        return "decoded user voice string"

    def mock_llm_process(self, prompt):
        self.set_state("thinking")
        time.sleep(3.0)
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
        
        # Max capacity matches our largest lookback window (3 seconds)
        audio_buffer = deque(maxlen=int(COMMAND_FRAME_SAMPLES))
        samples_since_last_hop = 0
        
        # Temp file path to hand over array buffers to soundfile-based VAD script safely
        temp_vad_path = "temp_vad_segment.wav"

        try:
            while self.is_running:
                raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                if self.is_speaking:
                    audio_buffer.clear()  # Don't listen to yourself
                    samples_since_last_hop = 0
                    continue
                    
                chunk = np.frombuffer(raw_data, dtype=np.float32)
                audio_buffer.extend(chunk)
                samples_since_last_hop += len(chunk)
                
                # Check if exactly 1 second (HOP_DURATION) of audio has accumulated
                if samples_since_last_hop >= HOP_SAMPLES:
                    samples_since_last_hop = 0  # Reset hop accumulator
                    
                    # Ensure we have enough audio context built up to analyze
                    current_buffer_len = len(audio_buffer)
                    
                    if self.current_state == "sleeping":
                        # --- CASE 1: WAKEWORD SEARCH (Look back 2 seconds) ---
                        if current_buffer_len >= WAKEWORD_FRAME_SAMPLES:
                            # Slice out the last 2 seconds from the rolling buffer
                            audio_data = np.array(list(audio_buffer))[-int(WAKEWORD_FRAME_SAMPLES):]
                            sf.write(temp_vad_path, audio_data, SAMPLE_RATE)
                            
                            vad_res = gvat(temp_vad_path)
                            # Extract the segments list from the VAD output
                            segments = vad_res["active_segments"]
                            
                            if segments:
                                last_segment_start, last_segment_duration = segments[-1]
                                last_segment_end = last_segment_start + last_segment_duration
                                
                                # Check if the speech segment has met the minimum duration
                                # AND check if the user stopped talking near the end of the 2-second window
                                # (e.g., last speech ended before the final 200ms of the buffer)
                                has_minimum_speech = vad_res["active_duration"] > 0.5
                                speech_has_ended = last_segment_end < 1.8  # 2.0s total frame - 200ms buffer
                                
                                if has_minimum_speech and speech_has_ended:
                                    print(f"[VAD Trigger]: Wakeword Active Time: {vad_res['active_duration']}s")
                                    self.set_state("wake_up")
                                    self.speak("I am Polly. What's up?")
                                    audio_buffer.clear()
                                    self.set_state("woken_sleeping")

                    elif self.current_state == "woken_sleeping":
                        # --- CASE 2: COMMAND SEARCH (Look back 3 seconds) ---
                        if current_buffer_len >= COMMAND_FRAME_SAMPLES:
                            audio_data = np.array(list(audio_buffer))
                            sf.write(temp_vad_path, audio_data, SAMPLE_RATE)
                            
                            vad_res = gvat(temp_vad_path)
                            
                            if vad_res["active_duration"] > 1.0:
                                print(f"[VAD Trigger]: Command Active Time: {vad_res['active_duration']}s")
                                self.set_state("listening")
                                
                                user_text = self.mock_asr_process()
                                llm_response = self.mock_llm_process(user_text)
                                self.speak(llm_response)
                                
                                audio_buffer.clear()
                                self.set_state("sleeping")

                time.sleep(0.001)

        except Exception as e:
            print(f"❌ Error in listening thread: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            if os.path.exists(temp_vad_path):
                os.remove(temp_vad_path)
            print("[*] Audio hardware stream released safely.")

    def run_pipeline(self, destroy_callback=None):
        self.is_running = True
        self.set_state("sleeping")
        self.listener_thread = threading.Thread(target=self._listen_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def stop(self):
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
            user_input = input("Command -> \n").strip().lower()
            if user_input in ['c', 'q']:
                parrot.stop()
                break
    except (KeyboardInterrupt, SystemExit):
        parrot.stop()
    sys.exit(0)