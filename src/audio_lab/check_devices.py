import sounddevice as sd
print(sd.query_devices())
print("\nDefault Input/Output:", sd.default.device)