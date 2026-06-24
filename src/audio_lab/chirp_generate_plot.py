import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import chirp

def generate_log_sweep(
    filename="chirp_sweep.wav",
    sample_rate=48000,
    duration=5.0,
    f_start=20.0,
    f_end=20000.0,
    amplitude=0.5
):
    """Generates a logarithmic sine sweep stimulus and saves it to a WAV file."""
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    sweep_signal = chirp(t, f0=f_start, t1=duration, f1=f_end, method='logarithmic')
    sweep_signal = sweep_signal * amplitude
    
    sf.write(filename, sweep_signal, sample_rate, subtype='FLOAT')
    return t, sweep_signal

def plot_and_save_analysis(t, signal, sample_rate, output_image="sweep_analysis.png"):
    """
    Plots the time-domain waveform and the spectrogram stacked vertically
    for exact time-alignment, and saves the output to a PNG file.
    """
    # Create a vertical layout (2 rows, 1 column) with shared x-axis (Time)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("Generated Logarithmic Sine Sweep Analysis", fontsize=14, fontweight='bold')

    # Top Panel: Time-Domain Waveform
    ax1.plot(t, signal, color='tab:blue', linewidth=0.5)
    ax1.set_title("Time-Domain Waveform")
    ax1.set_ylabel("Amplitude (Normalized FS)")
    ax1.set_ylim(-1.1, 1.1)  # Clear view of headroom limits
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Bottom Panel: Spectrogram (Time-Frequency Domain)
    # NFFT=2048 matches standard audio resolution blocks
    ax2.specgram(signal, NFFT=2048, Fs=sample_rate, noverlap=1024, cmap='viridis')
    ax2.set_title("Spectrogram (Logarithmic Progression)")
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Frequency (Hz)")
    ax2.set_ylim(0, sample_rate / 2)  # Nyquist limit
    
    # Optional: Use symlog scaling on the y-axis to match human auditory perception
    ax2.set_yscale('symlog', linthresh=20) 

    # Clean layout adjusting and file compilation
    plt.tight_layout()
    
    # Save the plot out as a high-DPI PNG file for your documentation or reports
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    print(f"Success: Analysis plot saved as a vertical stack to '{output_image}'")
    
    plt.show()

if __name__ == "__main__":
    fs = 48000
    duration_secs = 5.0
    
    # 1. Synthesize signal vectors
    time_axis, sweep_matrix = generate_log_sweep(
        filename="chirp_sweep.wav",
        sample_rate=fs,
        duration=duration_secs,
        f_start=20.0,
        f_end=20000.0,
        amplitude=0.7
    )
    
    # 2. Render vertically aligned plots and save to PNG
    plot_and_save_analysis(time_axis, sweep_matrix, sample_rate=fs, output_image="chirp_sweep_analysis.png")