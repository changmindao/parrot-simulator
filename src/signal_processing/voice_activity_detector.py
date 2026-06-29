import argparse
import os
import numpy as np
import soundfile as sf
from src.signal_processing import signal_analyzer as sa

LEVEL_ACTIVE_MIN = -60.0  # dBov

def get_voice_activity_timestamps(audio_path, 
                                  threshold_db=-25, 
                                  frame_duration=0.03, 
                                  hop_duration=0.01):
    """
    Detects active voice segments using soundfile and numpy.
    
    Parameters:
    - threshold_db: DB threshold below the peak volume to consider as voice.
    - frame_duration: Window size in seconds (default 30ms)
    - hop_duration: Step size in seconds (default 10ms)
    """
    # VAD output if no voice activity
    act_level = -100.0  # Deep silence floor
    act_ratio = 0.0
    timestamps = []
    vad_output = {
        "active_level": act_level,      
        "active_ratio": act_ratio,      
        "active_segments": timestamps  
    }

    # 1. Load the audio file (soundfile automatically normalizes to -1.0 to 1.0 when reading float32)
    y, sr = sf.read(audio_path, dtype='float32')

    # Check the actual number of channels
    num_channels = y.shape[1] if y.ndim > 1 else 1
    
    if num_channels == 1:  # flatten it to 1D
        y = y.flatten()
    else: # more than 1 channel
        raise ValueError(
            f"The VAD engine only accepts mono signals. "
            f"The provided file has {num_channels} channels. "
            f"Please split or downmix channels before processing."
        )
        

    # 2. Calculate total RMS 
    global_rms_db = sa.get_pwr(y)

    # 3. Return empty list if the signal is not active
    if global_rms_db < LEVEL_ACTIVE_MIN:
        print(f"[VAD Notice] File power ({global_rms_db:.2f} dBov) is below LEVEL_ACTIVE_MIN.")
        return vad_output

    # 4. Calculate frame parameters
    frame_length = int(frame_duration * sr)
    hop_length = int(hop_duration * sr)
    
    # 5. Compute Short-Time Energy / RMS
    rms = []
    times = []
    for i in range(0, len(y) - frame_length, hop_length):
        frame = y[i:i + frame_length]
        # Calculate RMS energy
        energy = np.sqrt(np.mean(frame**2)) + 1e-10 # Epsilon prevents log(0)
        rms.append(energy)
        times.append(i / sr)
        
    rms = np.array(rms)
    times = np.array(times)
    
    # Convert RMS to Decibels relative to the peak energy in the file
    rms_db = 20 * np.log10(rms / np.max(rms))
    
    # 6. Find continuous segments above threshold
    is_active = rms_db > threshold_db
    
    timestamps = []
    in_speech = False
    start_time = 0.0
    
    for i, active in enumerate(is_active):
        current_time = times[i]
        if active and not in_speech:
            # Speech starts
            start_time = round(float(current_time), 3)
            in_speech = True
        elif not active and in_speech:
            # Speech ends
            end_time = round(float(current_time + frame_duration), 3)
            timestamps.append([start_time, end_time])
            in_speech = False
            
    # If file ends while someone is talking
    if in_speech:
        timestamps.append([start_time, round(len(y) / sr, 3)])
        
    
    # Calculate total file duration in seconds
    total_duration = len(y) / sr
    
    # Calculate active_ratio
    total_active_time = sum((end - start) for start, end in timestamps)
    act_ratio = round(total_active_time / total_duration, 4)  # e.g., 0.4532 (45.32%)

    # Calculate active level (RMS of speech frames only)
    # Assuming `rms` is your list of frame RMS values and `is_active` tracks their states
    active_frame_energies = [r**2 for r, active in zip(rms, is_active) if active]
        
    active_rms = np.sqrt(np.mean(active_frame_energies))
    act_level = round(float(20 * np.log10(max(active_rms, 1e-7))), 2)
    # print(f"active_level = {act_level}")
    # print(f"active_ratio = {act_ratio}")
    # Construct the final output dictionary
    vad_output = {
        "active_level": act_level,      # e.g., -18.45 (dBov)
        "active_ratio": act_ratio,      # e.g., 0.3521 (float)
        "active_segments": timestamps   # e.g., [[0.5, 2.1], [3.4, 5.0]]
    }
    
    return vad_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract active voice timestamps using soundfile.")
    parser.add_argument("audio_file", type=str, help="Path to input audio file (WAV, FLAC, OGG, etc.)")
    parser.add_argument("--threshold", type=int, default=-25, 
                        help="Threshold in dB below peak (e.g., -25). Closer to 0 is stricter.")

    args = parser.parse_args()

    try:
        vad_output = get_voice_activity_timestamps(args.audio_file, threshold_db=args.threshold)
        active_segments  = vad_output["active_segments"]
        print(f"\n--- Processing: {args.audio_file} ---")
        print(f"Active Level = {vad_output["active_level"]}")
        print(f"Active Ratio = {vad_output["active_ratio"]}")
        print(f"Active Voice Segments [t_start, t_end]:")
        print(active_segments)
        print(f"Total active segments found: {len(active_segments)}\n")
        
    except Exception as e:
        print(f"Error: {e}")