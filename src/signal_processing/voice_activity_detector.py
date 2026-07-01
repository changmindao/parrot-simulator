import argparse
import os
import numpy as np
import soundfile as sf
from src.signal_processing import signal_analyzer as sa

LEVEL_ACTIVE_THRD = -25.0  # dBov
LEVEL_ACTIVE_MIN = -60.0  # dBov
HANGOVER_TIME = 0.2  # second
FRAME_DURATION = 0.03  # second
HOP_DURATION = 0.01  # second

def get_voice_activity_timestamps(audio_path, 
                                  threshold_db=LEVEL_ACTIVE_THRD, 
                                  frame_duration=FRAME_DURATION, 
                                  hop_duration=HOP_DURATION):
    """
    Detects active voice segments using soundfile and numpy.
    """
    # 1. Load the audio file
    y, sr = sf.read(audio_path, dtype='float32')
    total_duration = len(y) / sr
    hop_length = int(hop_duration * sr)
    frame_length = int(frame_duration * sr)

    # Initial default output structure
    vad_output = {
        "active_level": -100.0,      
        "total_duration": total_duration,      
        "active_duration": 0.0,      
        "active_ratio": 0.0,      
        "active_segments": []  
    }

    if total_duration * 2 < FRAME_DURATION:
        print(f"[VAD Notice] Signal duration ({total_duration:.2f}s) is too short.")
        return vad_output

    # Check channels safely using squeeze
    num_channels = y.shape[1] if y.ndim > 1 else 1
    if num_channels == 1:  
        y = y.squeeze()  # Fixed: Use squeeze instead of flatten
    else: 
        raise ValueError(f"The VAD engine only accepts mono signals. Found {num_channels} channels.")
        
    # 3. Check minimum power limit
    global_rms_db = sa.get_pwr(y)
    if global_rms_db < LEVEL_ACTIVE_MIN:
        print(f"[VAD Notice] File power ({global_rms_db:.2f} dBov) is below LEVEL_ACTIVE_MIN.")
        return vad_output

    # 4. Compute Short-Time Energy / RMS
    rms = []
    times = []
    for i in range(0, len(y) - frame_length, hop_length):
        frame = y[i:i + frame_length]
        energy = np.sqrt(np.mean(frame**2)) + 1e-10 
        rms.append(energy)
        times.append(i / sr)
        
    rms = np.array(rms)
    times = np.array(times)
    rms_db = 20 * np.log10(rms / np.max(rms))
    
    # 5. Extract Raw Segments (Using distinct [start, end] values first)
    is_active = rms_db > threshold_db
    raw_segments = []
    in_speech = False
    start_time = 0.0
    
    for i, active in enumerate(is_active):
        current_time = times[i]
        if active and not in_speech:
            start_time = float(current_time)
            in_speech = True
        elif not active and in_speech:
            end_time = float(current_time + frame_duration)
            raw_segments.append([start_time, end_time])
            in_speech = False
            
    if in_speech:
        raw_segments.append([start_time, float(total_duration)])
        
    if not raw_segments:
        return vad_output

    # --- NEW: Merge gaps smaller than PAUSE_DURATION_MIN ---
    merged_raw_segments = [raw_segments[0]]
    for current in raw_segments[1:]:
        prev_start, prev_end = merged_raw_segments[-1]
        curr_start, curr_end = current
        
        # If the silence gap is smaller than hangover time, extend the previous segment
        if (curr_start - prev_end) < HANGOVER_TIME:
            merged_raw_segments[-1][1] = curr_end
        else:
            merged_raw_segments.append(current)
    # --------------------------------------------------------

    # 6. Convert to final [start, duration] format and calculate metrics
    act_segments = []
    act_duration = 0.0
    for start, end in merged_raw_segments:
        duration = round(end - start, 3)
        act_segments.append([round(start, 3), duration])
        act_duration += duration

    act_ratio = round(act_duration / total_duration, 4)

    # Calculate active level (RMS of speech frames only)
    active_frame_energies = [r**2 for r, active in zip(rms, is_active) if active]
    active_rms = np.sqrt(np.mean(active_frame_energies))
    act_level = round(float(20 * np.log10(max(active_rms, 1e-7))), 2)
    
    # Construct final dictionary
    vad_output = {
        "active_level": act_level,      
        "total_duration": round(float(total_duration), 3),  
        "active_duration": round(float(act_duration), 3),   
        "active_ratio": min(act_ratio, 1.0),      
        "active_segments": act_segments   
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
        print(f"Total Duration = {vad_output["total_duration"]}")
        print(f"Active Duration = {vad_output["active_duration"]}")
        print(f"Active Ratio = {vad_output["active_ratio"]}")
        print(f"Active Voice Segments [t_start, t_duration]:")
        print(active_segments)
        print(f"Total active segments found: {len(active_segments)}\n")
        
    except Exception as e:
        print(f"Error: {e}")