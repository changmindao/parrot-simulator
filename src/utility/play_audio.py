import sys
import soundfile as sf
import sounddevice as sd

def play_audio(file_path):
    # soundfile automatically detects sample type (int16, int24, float32) from the header
    data, sample_rate = sf.read(file_path, dtype='float32')
    
    print(f"[*] Playing {file_path} flawlessly...")
    # sounddevice automatically handles channel layout and formats the output stream safely
    sd.play(data, sample_rate)
    sd.wait() # Wait until the file finishes playing
    print("[*] Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python play_audio.py <path_to_file.wav>")
        sys.exit(1)
        
    play_audio(sys.argv[1])