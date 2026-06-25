import numpy as np
import time
import os
import soundfile as sf
# Import your validated hardware execution runner
from pyaudio_runner import play_and_record

# --- CALIBRATION CONSTANTS ---
LOOPBACK_DELAY_MS = 23.479  # Your measured round-trip driver latency constant
SAMPLE_RATE = 48000

class ParrotSimulatorHarness:
    def __init__(self, mode_asr="speech_recognition", mode_llm="ollama", mode_tts="mac_say"):
        """
        Initializes the pluggable architecture configurations for the testing matrix.
        """
        self.mode_asr = mode_asr
        self.mode_llm = mode_llm
        self.mode_tts = mode_tts
        
    def generate_tts_stimulus(self, text):
        """
        Synthesizes raw text into an audio waveform array based on selected TTS mode.
        """
        if self.mode_tts == "mac_say":
            # For the local 'mac_say' baseline, we route TTS to a temporary file
            temp_file = "temp_stimulus.wav"
            # Using macOS native 'say' utility configured for high-quality standard rate
            os.system(f"say -r 180 --data-format=LEF32@48000 -o {temp_file} '{text}'")
            
            data, fs = sf.read(temp_file)
            os.remove(temp_file) # Clean up file system residue
            return data
        else:
            raise NotImplementedError(f"TTS Engine '{self.mode_tts}' not yet implemented.")

    def run_performance_test(self, wake_phrase="Hey Polly", command_phrase="Tell me a joke"):
        print("\n" + "="*60)
        print("  INITIATING BLACK-BOX HARNESS ENGINE")
        print("="*60)
        
        # 1. Synthesize the baseline stimulus phrases dynamically
        print("[*] Generating dynamic TTS audio signals...")
        wake_audio = self.generate_tts_stimulus(wake_phrase)
        command_audio = self.generate_tts_stimulus(command_phrase)
        
        # 2. Build out a continuous testing timeline script
        # 3 seconds of buffer silence gives the parrot time to finish its waking statement
        silence_buffer = np.zeros(int(SAMPLE_RATE * 3.0), dtype=np.float32)
        full_stimulus = np.concatenate([wake_audio, silence_buffer, command_audio])
        
        # Calculate exactly when each audio trigger *finishes* playing relative to t=0
        wake_end_time = len(wake_audio) / SAMPLE_RATE
        command_start_time = wake_end_time + 3.0
        command_end_time = command_start_time + (len(command_audio) / SAMPLE_RATE)

        # 3. Fire full-duplex hardware audio sweep
        print("[*] Streaming audio playback and recording environment response...")
        t_start_harness = time.perf_counter()
        recorded_response = play_and_record(full_stimulus, sample_rate=SAMPLE_RATE, chunk_size=512)
        
        # 4. Energy Envelope Processing (10ms windows)
        hop_size = int(SAMPLE_RATE * 0.01)
        win_size = int(SAMPLE_RATE * 0.02)
        num_frames = (len(recorded_response) - win_size) // hop_size
        
        energy = np.array([
            np.sqrt(np.mean(recorded_response[i*hop_size : i*hop_size + win_size]**2))
            for i in range(num_frames)
        ])
        timeline = np.array([(i * hop_size + (win_size / 2)) / SAMPLE_RATE for i in range(num_frames)])
        
        # Noise gate threshold (Adjust based on lab background noise floor)
        noise_threshold = np.max(energy) * 0.12
        
        # 5. Extract Timings relative to playback landmarks (compensating for driver overhead)
        hardware_offset_sec = LOOPBACK_DELAY_MS / 1000.0
        
        wake_latency = None
        reply_latency = None
        
        # Scan for wake reply onset
        for idx, e in enumerate(energy):
            t_event = timeline[idx]
            # Must happen after wake word ends, but before the next command fires
            if (wake_end_time + hardware_offset_sec) < t_event < command_start_time:
                if e > noise_threshold:
                    wake_latency = (t_event - wake_end_time - hardware_offset_sec) * 1000
                    break
                    
        # Scan for verbal response query loop completion
        for idx, e in enumerate(energy):
            t_event = timeline[idx]
            # Must happen after command query phrase finishes playing out
            if t_event > (command_end_time + hardware_offset_sec):
                if e > noise_threshold:
                    reply_latency = (t_event - command_end_time - hardware_offset_sec) * 1000
                    break

        # --- Performance Metric Evaluation Logger ---
        print("\n" + "="*60)
        print("          DYNAMIC HARNESS AUTOMATION REPORT")
        print("="*60)
        print(f"ASR Pipeline Mode:  {self.mode_asr}")
        print(f"LLM Reasoning Mode: {self.mode_llm}")
        print(f"TTS Synthesis Mode: {self.mode_tts}")
        print("-" * 60)
        
        if wake_latency:
            print(f" -> Wake-Up Reaction Latency:   {wake_latency:.1f} ms")
        else:
            print(" -> Wake-Up Reaction Latency:   FAILED (Threshold not crossed)")
            
        if reply_latency:
            print(f" -> Loop Processing Latency:    {reply_latency:.1f} ms")
        else:
            print(" -> Loop Processing Latency:    FAILED (Reply not crossed)")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Initialize the modular testing harness using default configurations
    harness = ParrotSimulatorHarness(
        mode_asr="speech_recognition",
        mode_llm="ollama",
        mode_tts="mac_say"
    )
    
    # Run a fully dynamic automated diagnostic suite
    harness.run_performance_test(
        wake_phrase="Hey Polly", 
        command_phrase="What is the capital of France?"
    )