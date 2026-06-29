import numpy as np
import soundfile as sf

# Define constants
WAVE_FORMAT = "WAV"
WAVE_PCM_S8 = "PCM_S8"
WAVE_PCM_U8 = "PCM_U8"
WAVE_PCM_16 = "PCM_16"
WAVE_PCM_24 = "PCM_24"
WAVE_PCM_32 = "PCM_32"
WAVE_PCM_FLOAT = "FLOAT"
WAVE_PCM_DOUBLE = "DOUBLE"

def read_wav(file_path):
    """
    Reads an audio signal in wave format and returns the audio data and sampling rate.
    
    Returns:
        data (np.ndarray): Audio signal scaled between -1.0 and 1.0.
        samplerate (int): The sample rate of the file.
    """
    # soundfile natively detects the format and codec context when reading
    data, samplerate = sf.read(file_path, dtype='float32')
    return data, samplerate


def write_wav(file_path, data, samplerate, subtype=WAVE_PCM_16):
    """
    Writes an audio signal to a wave file with the subtype
    
    Parameters:
        file_path (str): Destination path (typically ends in .ogg or .opus)
        data (np.ndarray): Audio signal array.
        samplerate (int): Target sampling rate.
        subtuype (str): default = PCM_16
    """

    sf.write(
        file=file_path,
        data=data,
        samplerate=samplerate,
        format=WAVE_FORMAT,
        subtype=subtype
    )


def read_opus(file_path):
    """
    Reads an Ogg Opus file and returns the audio data and sampling rate.
    
    Returns:
        file_path (str): Destination path (typically ends in .ogg or .opus)
    """
    # soundfile natively detects the format and codec context when reading
    data, samplerate = sf.read(file_path, dtype='float32')
    return data, samplerate


def write_opus(file_path, data, samplerate):
    """
    Writes an audio signal to an Ogg container encoded with the Opus codec.
    
    Parameters:
        file_path (str): Destination path (typically ends in .ogg or .opus)
        data (np.ndarray): Audio signal array.
        samplerate (int): Target sampling rate.
    """
    # For Opus, we must force the OGG container and the OPUS subtype
    sf.write(
        file=file_path,
        data=data,
        samplerate=samplerate,
        format='OGG',
        subtype='OPUS'
    )


# --- Example Usage & Verification Run ---
if __name__ == "__main__":
    output_filename = "test_speech_opus.ogg"
    
    # 1. Create a dummy audio signal (e.g., 2 seconds of a 440 Hz standard pitch A tone)
    print("Generating a test signal...")
    fs = 48000  # Opus loves 48kHz native audio
    t = np.linspace(0, 2.0, int(2.0 * fs), endpoint=False)
    simulated_audio = np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    
    try:
        # 2. Test Writing
        print(f"Writing signal to Ogg-Opus format: {output_filename}")
        write_opus(output_filename, simulated_audio, fs)
        print("Write successful!")
        
        # 3. Test Reading
        print(f"Reading back the file: {output_filename}")
        loaded_data, sample_rate = read_opus(output_filename)
        
        print("\n--- File Summary ---")
        print(f"Sample Rate : {sample_rate} Hz")
        print(f"Total Shapes: {loaded_data.shape}")
        print(f"Duration    : {len(loaded_data) / sample_rate:.2f} seconds")
        print("--------------------")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nTroubleshooting Note: If you get a 'Subtype not available' error,")
        print("it means your system's underlying libsndfile library was compiled")
        print("without libopus tracking enabled.")

def process_ogg_file(input_path, output_path):
    print(f"--- Reading: {input_path} ---")
    
    # 1. Read the .ogg file
    # 'float32' automatically scales the audio amplitude between -1.0 and 1.0
    data, sample_rate = sf.read(input_path, dtype='float32')
    
    # Extract audio properties
    duration = len(data) / sample_rate
    channels = 1 if len(data.shape) == 1 else data.shape[1]
    
    print(f"Sample Rate : {sample_rate} Hz")
    print(f"Channels    : {channels} ({'Mono' if channels == 1 else 'Stereo'})")
    print(f"Duration    : {duration:.2f} seconds")
    print(f"Data Type   : {data.dtype}")
    
    # 2. Simple Signal Manipulation (Example: Attenuate the volume by half)
    print("\nProcessing signal (reducing volume by 50%)...")
    modified_data = data * 0.5
    
    # 3. Write the signal back out as an .ogg file
    print(f"--- Writing: {output_path} ---")
    
    # For .ogg, we explicitly set the format to 'OGG' and the subtype to 'VORBIS'
    sf.write(
        file=output_path,
        data=modified_data,
        samplerate=sample_rate,
        format='OGG',
        subtype='VORBIS'
    )
    print("File saved successfully.")

if __name__ == "__main__":
    # Replace these with your actual file paths
    input_ogg = "input_audio.ogg"
    output_ogg = "output_attenuated.ogg"
    
    # Dummy run generation if you don't have an ogg file handy to test
    # This creates a 2-second 440Hz sine wave tone and saves it as input_audio.ogg
    try:
        sr = 44100
        t = np.linspace(0, 2, 2 * sr, endpoint=False)
        dummy_signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        sf.write(input_ogg, dummy_signal, sr, format='OGG', subtype='VORBIS')
    except Exception as e:
        print(f"Could not generate dummy file: {e}")

    # Run the Read/Write process
    try:
        process_ogg_file(input_ogg, output_ogg)
    except Exception as e:
        print(f"Error during file I/O: {e}")