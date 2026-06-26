import numpy as np
from src.utility.pyaudio_runner import play_and_record


CHUNK_SIZE = 1024
INPUT_DEVICE = 2
OUTPUT_DEVICE = 2

def generate_noise_burst(duration=1.0, burst_duration=0.5, sample_rate=48000, amplitude=0.5):
    """Generates a short white noise burst followed by silence."""
    num_samples = int(sample_rate * duration)
    burst_samples = int(sample_rate * burst_duration)
    signal = np.zeros(num_samples, dtype=np.float32)
    
    rng = np.random.default_rng(42)
    signal[:burst_samples] = rng.uniform(-1.0, 1.0, burst_samples) * amplitude
    return signal

def calculate_latency(stimulus, recording, sample_rate):
    """Computes cross-correlation to find the exact hardware alignment peak."""
    correlation = np.correlate(recording, stimulus, mode='full')
    center_idx = len(stimulus) - 1
    
    peak_idx = np.argmax(np.abs(correlation))
    delay_samples = peak_idx - center_idx
    delay_ms = (delay_samples / sample_rate) * 1000
    
    print("\n" + "="*50)
    print("     HARDWARE LOOPBACK CALIBRATION REPORT")
    print("="*50)
    print(f"Calculated Loopback Delay: {delay_samples} samples")
    print(f"Absolute Round-Trip Time:  {delay_ms:.3f} ms")
    print("="*50)
    
    return delay_samples, delay_ms

if __name__ == "__main__":
    fs = 48000
    stimulus_noise = generate_noise_burst(duration=1.0, burst_duration=0.1, sample_rate=fs)
    
    print("Please connect a physical loopback cable from your Output to your Input channel.")
    input("Press Enter once the physical loopback path is connected to start verification...")
    
    # Run using the new external helper module function
    recorded_noise = play_and_record(stimulus_noise, 
                                     sample_rate=fs, 
                                     chunk_size=CHUNK_SIZE,
                                     input_idx=INPUT_DEVICE,
                                     output_idx=OUTPUT_DEVICE,
                                     )
    
    # Calculate exact offsets
    samples, ms = calculate_latency(stimulus_noise, recorded_noise, sample_rate=fs)