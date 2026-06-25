import numpy as np
import pyaudio
import time

def play_and_record(stimulus_signal, sample_rate=48000, chunk_size=512, input_idx=None, output_idx=None):
    """
    Executes a simultaneous full-duplex playback and recording loop via PyAudio.
    
    Parameters:
        stimulus_signal (np.ndarray): 1D float32 array containing the audio to play.
        sample_rate (int): Audio sampling frequency in Hz.
        chunk_size (int): Buffer size per hardware I/O interrupt block.
        input_idx (int, optional): PortAudio device index for the microphone channel.
        output_idx (int, optional): PortAudio device index for the speaker channel.
        
    Returns:
        np.ndarray: A 1D float32 array containing the recorded acoustic response.
    """
    playback_ptr = 0
    total_frames = len(stimulus_signal)
    recorded_chunks = []
    
    # Define the low-latency background processing thread callback
    def duplex_callback(in_data, frame_count, time_info, status):
        nonlocal playback_ptr
        
        if in_data:
            recorded_chunks.append(in_data)
            
        remainder = total_frames - playback_ptr
        
        if remainder <= 0:
            # Signal complete; stream silence and signal PortAudio to stop
            out_bytes = np.zeros(frame_count, dtype=np.float32).tobytes()
            return (out_bytes, pyaudio.paComplete)
            
        elif remainder < frame_count:
            # Fragment boundary; pad out the remaining buffer chunk with zeros
            chunk = stimulus_signal[playback_ptr:]
            padded_chunk = np.concatenate([chunk, np.zeros(frame_count - remainder, dtype=np.float32)])
            playback_ptr += remainder
            return (padded_chunk.tobytes(), pyaudio.paContinue)
            
        else:
            # Standard continuous reading block
            chunk = stimulus_signal[playback_ptr : playback_ptr + frame_count]
            playback_ptr += frame_count
            return (chunk.tobytes(), pyaudio.paContinue)

    # Instantiate hardware bridge
    p = pyaudio.PyAudio()
    
    stream = p.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=sample_rate,
        input=True,
        output=True,
        input_device_index=input_idx,
        output_device_index=output_idx,
        frames_per_buffer=chunk_size,
        stream_callback=duplex_callback
    )
    
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.05)
        
    # Clean up and close streams safely
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Reassemble raw byte sequences back into a cohesive float32 numpy array
    recorded_signal = np.frombuffer(b"".join(recorded_chunks), dtype=np.float32)
    
    # Enforce strict length matching to align time dimensions perfectly
    return recorded_signal[:total_frames]