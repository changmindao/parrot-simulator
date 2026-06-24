import pyaudio

def list_hardware_indices():
    p = pyaudio.PyAudio()
    
    print("\n" + "="*60)
    print("   AVAILABLE SOUND DEVICES (PyAudio)")
    print("="*60)
    
    total_devices = p.get_device_count()
    
    for i in range(total_devices):
        try:
            device_info = p.get_device_info_by_index(i)
            name = device_info.get('name')
            inputs = device_info.get('maxInputChannels', 0)
            outputs = device_info.get('maxOutputChannels', 0)
            sample_rate = int(device_info.get('defaultSampleRate', 0))
            
            # Print entries that match physical capabilities
            if inputs > 0 or outputs > 0:
                print(f"Index [{i}]: {name}")
                print(f"   -> Max Inputs:  {inputs}")
                print(f"   -> Max Outputs: {outputs}")
                print(f"   -> Native Rate: {sample_rate} Hz")
                print("-" * 50)
        except Exception as e:
            continue
            
    p.terminate()

if __name__ == "__main__":
    list_hardware_indices()