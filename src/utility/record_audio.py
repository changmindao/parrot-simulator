import argparse
import sys
import sounddevice as sd
import soundfile as sf
import numpy as np

def record_audio(output_file, sample_rate, channels, dtype, duration):
    print("=" * 60)
    print(f"[*] Recording Target: '{output_file}'")
    print(f"    -> Sample Rate: {sample_rate} Hz")
    print(f"    -> Channels:    {channels}")
    print(f"    -> Data Type:   {dtype}")
    
    if duration == float('inf'):
        print(f"    -> Mode:        Continuous (Press Ctrl+C to stop and save)")
    else:
        print(f"    -> Mode:        Timed Duration ({duration} seconds)")
    print("=" * 60)
    
    print("\n🔴 RECORDING ACTIVE... Speak into the line now.")
    
    try:
        if duration == float('inf'):
            # Continuous recording loop using an un-bounded stream
            recorded_chunks = []
            
            # Callback function to harvest blocks from hardware clock
            def callback(indata, frames, time, status):
                if status:
                    print(status, file=sys.stderr)
                recorded_chunks.append(indata.copy())
            
            with sd.InputStream(samplerate=sample_rate, channels=channels, dtype=dtype, callback=callback):
                while True:
                    sd.sleep(100)  # Sleep thread briefly while callback collects audio
                    
        else:
            # Fixed duration recording blocking execution until completion
            recording = sd.rec(
                int(duration * sample_rate), 
                samplerate=sample_rate, 
                channels=channels, 
                dtype=dtype
            )
            sd.wait()  # Block until the sound card finishes recording
            audio_data = recording

    except KeyboardInterrupt:
        print("\n[!] Recording stopped by user interrupt.")
        if duration == float('inf'):
            if len(recorded_chunks) == 0:
                print("❌ No audio frames captured. File not saved.")
                return
            audio_data = np.concatenate(recorded_chunks, axis=0)
        else:
            print("❌ Fixed recording interrupted prematurely. File not saved.")
            return

    # Export to disk using soundfile
    print(f"[*] Writing samples to disk...")
    # Map dtype string to soundfile subtype formats
    sf_subtype = 'PCM_16' if dtype == 'int16' else 'FLOAT'
    
    sf.write(output_file, audio_data, sample_rate, subtype=sf_subtype)
    print(f"🎉 Success! Audio cleanly recorded to '{output_file}'")
    return audio_data, sample_rate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Precision audio recording utility using sounddevice.")
    
    # Required positional argument
    parser.add_argument("output", type=str, help="Path to save the output .wav file")
    
    # Optional arguments with specified defaults
    parser.add_argument("-r", "--rate", type=int, default=48000, help="Sample rate in Hz (default: 48000)")
    parser.add_argument("-c", "--channels", type=int, default=1, help="Number of audio channels (default: 1)")
    parser.add_argument("-t", "--type", type=str, default="int16", choices=["int16", "float32"], 
                        help="Data type encoding format (default: int16)")
    parser.add_argument("-d", "--duration", type=str, default="10", 
                        help="Duration in seconds, or 'inf' for infinite manual recording (default: 10)")
    
    args = parser.parse_args()
    
    # Process duration parameter conversion
    try:
        duration_val = float('inf') if args.duration.lower() in ['inf', 'infinite', 'continuous'] else float(args.duration)
    except ValueError:
        print("❌ Error: Duration argument must be a valid number or 'inf'.")
        sys.exit(1)
        
    record_audio(
        output_file=args.output,
        sample_rate=args.rate,
        channels=args.channels,
        dtype=args.type,
        duration=duration_val
    )