import numpy as np
import soundfile as sf
import pyaudio
import time

CHUNK_SIZE = 1024
INPUT_DEVICE = 2
OUTPUT_DEVICE = 2
INPUT_FILE = "chirp_sweep.wav"
OUTPUT_FILE = "record_sweep.wav"

def run_full_duplex_measurement(
    input_device=INPUT_DEVICE,
    output_device=OUTPUT_DEVICE,
    input_file=INPUT_FILE,
    output_file=OUTPUT_FILE,
    chunk_size=CHUNK_SIZE,
):
    """
    Executes a simultaneous playback and recording measurement loop via PyAudio (PortAudio).
    Streams data seamlessly between a WAV file and hardware buffers.
    """
    # 1. Open the original stimulus file to read properties and data
    with sf.SoundFile(input_file, 'r') as sf_in:
        sample_rate = sf_in.samplerate
        channels = sf_in.channels
        
        # Read the complete continuous matrix into a float32 array
        # PyAudio maps natively to np.float32 for seamless processing
        stimulus_data = sf_in.read(dtype='float32')
        
    print(f"Loaded stimulus: {len(stimulus_data)} frames, {sample_rate}Hz, {channels} ch")
    
    # Track stream indices for the playback thread pointer
    playback_ptr = 0
    total_frames = len(stimulus_data)
    
    # Store incoming chunk fragments dynamically
    recorded_chunks = []
    
    # 2. Define the Real-Time Background Audio Callback Function
    def full_duplex_callback(in_data, frame_count, time_info, status):
        nonlocal playback_ptr
        
        if status:
            print(f"Stream Warning Flags Flagged: {status}")
            
        # --- Handle Incoming Capture Data (ADC) ---
        if in_data:
            # Append raw byte chunk to list for post-processing
            recorded_chunks.append(in_data)
            
        # --- Handle Outgoing Playback Data (DAC) ---
        remainder = total_frames - playback_ptr
        
        if remainder <= 0:
            # Entire stimulus array spent; write zero pad and tell PortAudio to terminate
            out_data = np.zeros(frame_count * channels, dtype=np.float32).tobytes()
            return (out_data, pyaudio.paComplete)
            
        elif remainder < frame_count:
            # In the final block fragment; pad remaining buffer slots with silence
            frames_to_read = remainder
            chunk = stimulus_data[playback_ptr : playback_ptr + frames_to_read]
            
            # Pad array up to expected buffer chunk width
            pad_size = frame_count - frames_to_read
            padded_chunk = np.concatenate([chunk, np.zeros(pad_size * channels, dtype=np.float32)])
            out_bytes = padded_chunk.tobytes()
            
            playback_ptr += frames_to_read
            return (out_bytes, pyaudio.paContinue)
            
        else:
            # Normal full-chunk playback state
            chunk = stimulus_data[playback_ptr : playback_ptr + frame_count]
            out_bytes = chunk.tobytes()
            
            playback_ptr += frame_count
            return (out_bytes, pyaudio.paContinue)

    # 3. Instantiate the Audio System Framework
    p = pyaudio.PyAudio()
    
    # --- HW Interfacing Note ---
    # For local testing via your Focusrite Scarlett or similar interface:
    # If necessary, pass: input_device_index=X, output_device_index=Y 
    # to target specific hardware configurations directly.

    # 4. Open the Unified Full-Duplex Hardware Channel Stream
    stream = p.open(
        format=pyaudio.paFloat32,     # Maintain native float pipeline mapping
        channels=channels,
        rate=sample_rate,
        input=True,                   # Turn on ADC recording
        output=True,                  # Turn on DAC playback
        input_device_index=input_device,         # input audio device index 
        output_device_index=output_device,       # output audio device index 
        frames_per_buffer=chunk_size,
        stream_callback=full_duplex_callback  # Explicitly trigger non-blocking processing thread
    )
    print("\nInitializing Full-Duplex Audio Loop...")
    stream.start_stream()
    
    # 5. Keep the Main Thread Awake While the Background Worker executes I/O tasks
    while stream.is_active():
        # Calculate current run completion percentage for the terminal display
        progress = (playback_ptr / total_frames) * 100 if total_frames > 0 else 0
        print(f"Measuring Hardware Pipeline Progression... {progress:5.1f}% Complete", end='\r')
        time.sleep(0.1)
        
    print("\nMeasurement Completed. Tearing down audio hardware streams safely...")
    
    # 6. Housekeeping: Close up low-level open threads cleanly
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 7. Post-Process and Merge Captured Byte Arrays
    # Standardize flat continuous byte strings back into structural numpy matrix blocks
    raw_recorded_bytes = b"".join(recorded_chunks)
    recorded_signal = np.frombuffer(raw_recorded_bytes, dtype=np.float32)
    
    # 8. Save the acoustic response array out using soundfile 
    # (Matches size of your multi-channel layout)
    sf.write(output_file, recorded_signal, sample_rate, subtype='FLOAT')
    print(f"Success: Acoustic measurement saved completely to: '{output_file}'")
    
    return recorded_signal

if __name__ == "__main__":
    # Test execution assuming stimulus file is generated in root workspace directory
    try:
        response_vector = run_full_duplex_measurement()
    except FileNotFoundError:
        print(f"Error: fail to find input_file {INPUT_FILE}.")