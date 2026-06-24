import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

INPUT_FILE = "chirp_sweep.wav"
OUTPUT_FILE = "record_sweep.wav"
PLOT_FILE = "chirp_thd.png"

def calculate_band_thd_average(freqs, thd_db, f_min=20.0, f_max=20000.0):
    """Calculates the energy-weighted (RMS) average THD over a specified band."""
    band_mask = (freqs >= f_min) & (freqs <= f_max)
    if not np.any(band_mask):
        return 0.0, -np.inf
    thd_band_db = thd_db[band_mask]
    linear_ratios = 10 ** (thd_band_db / 20)
    rms_linear_ratio = np.sqrt(np.mean(linear_ratios ** 2))
    return rms_linear_ratio * 100, 20 * np.log10(rms_linear_ratio + 1e-10)


def analyze_audio_system_true_thd(stimulus_path, recorded_path, output_img=PLOT_FILE):
    # 1. Load original stimulus and recorded response
    s_data, fs = sf.read(stimulus_path)
    r_data, fs_r = sf.read(recorded_path)
    
    if fs != fs_r:
        raise ValueError("Sample rates do not match!")
        
    N = len(s_data)
    
    # 2. Generate Farina Inverse Filter
    t = np.linspace(0, N/fs, N, endpoint=False)
    inv_filter = s_data[::-1] # Time-reverse
    
    # -3dB/octave amplitude modulation compensation envelope
    f_start, f_end = 20.0, 20000.0
    w1 = 2 * np.pi * f_start
    w2 = 2 * np.pi * f_end
    envelope = w1 / (w1 + (w2 - w1) * (t / (N/fs)))
    inv_filter = inv_filter * envelope

    # 3. Deconvolution via FFT
    S_inv = np.fft.fft(inv_filter, n=N*2)
    R = np.fft.fft(r_data, n=N*2)
    
    # Extract linear system impulse response (IR)
    ir = np.real(np.fft.ifft(R * S_inv))
    ir_max = np.max(np.abs(ir))
    if ir_max > 0:
        ir = ir / ir_max

    # 4. Locate Fundamental Impulse Peak
    main_peak_idx = np.argmax(np.abs(ir))
    
    # Compute Frequency Spectrum of the Fundamental
    fft_window_size = 4096
    start_win = max(0, main_peak_idx - 512)
    end_win = min(len(ir), main_peak_idx + (fft_window_size - 512))
    fundamental_signal = ir[start_win:end_win]
    fundamental_spec = np.abs(np.fft.rfft(fundamental_signal, n=fft_window_size))
    freqs = np.fft.rfftfreq(fft_window_size, d=1/fs)
    
    # Smooth fundamental spectrum magnitude
    magnitude_db = 20 * np.log10(fundamental_spec + 1e-10)
    magnitude_db -= np.max(magnitude_db)

    # 5. Math Time-Gating for Harmonic Extractions (2nd & 3rd Order)
    duration = 5.0
    factor = duration / np.log(f_end / f_start)
    
    total_harmonic_energy = np.zeros_like(fundamental_spec)
    harmonic_specs = {2: None, 3: None}
    
    for n in [2, 3]:
        # Calculate samples backward where the harmonic impulse arrives
        time_shift_seconds = factor * np.log(n)
        sample_shift = int(time_shift_seconds * fs)
        harmonic_peak_idx = main_peak_idx - sample_shift
        
        # Apply a precise time-gate around the isolated harmonic arrival window
        h_start = max(0, harmonic_peak_idx - 128)
        h_end = min(len(ir), harmonic_peak_idx + 128)
        harmonic_gate = ir[h_start:h_end]
        
        # Pull harmonic content to frequency domain
        h_spec = np.abs(np.fft.rfft(harmonic_gate, n=fft_window_size))
        harmonic_specs[n] = h_spec
        
        # Sum power arrays (squares)
        total_harmonic_energy += h_spec ** 2

    # 6. Calculate True Total Harmonic Distortion Ratio
    thd_ratio = np.sqrt(total_harmonic_energy) / (fundamental_spec + 1e-10)
    thd_db = 20 * np.log10(thd_ratio + 1e-10)
    
    # Format discrete harmonic curves relative to fundamental carrier wave
    h2_db = 20 * np.log10(harmonic_specs[2] / (fundamental_spec + 1e-10) + 1e-10)
    h3_db = 20 * np.log10(harmonic_specs[3] / (fundamental_spec + 1e-10) + 1e-10)

    # 7. Render Plot Stacking
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    
    thd_avg_pct, thd_avg_db = calculate_band_thd_average(freqs, thd_db, f_min=20, f_max=20000)
    title_block = (
        f"Audio System Characterization\n"
        f"Acoustic Band Summary (20Hz - 20kHz) | Integrated THD Avg: {thd_avg_pct:.2f}% ({thd_avg_db:.1f} dBc)"
    )
    fig.suptitle(title_block, fontsize=13, fontweight='bold', color='black', bbox=dict(facecolor='none', edgecolor='gray', pad=6.0))

    # Top Plot: Transfer Function
    ax1.plot(freqs, magnitude_db, color='crimson', linewidth=2, label="Fundamental Transfer Function")
    ax1.set_title("System Transfer Function (Frequency Response)")
    ax1.set_ylabel("Magnitude (dBr)")
    ax1.set_xscale('log')
    ax1.set_xlim(20, 20000)
    ax1.set_ylim(-45, 5)
    ax1.grid(True, which="both", linestyle='--', alpha=0.5)
    ax1.legend(loc="lower left")

    # Bottom Plot: True Time-Gated Harmonic Distortion Components
    ax2.plot(freqs, thd_db, color='darkorange', linewidth=2, label="Calculated THD")
    ax2.plot(freqs, h2_db, color='blue', linewidth=1, linestyle=':', label="2nd Harmonic (H2)")
    ax2.plot(freqs, h3_db, color='purple', linewidth=1, linestyle=':', label="3rd Harmonic (H3)")
    
    ax2.set_title("True Total Harmonic Distortion (Time-Gated Isolation)")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Distortion Level (dBc)")
    ax2.set_xscale('log')
    ax2.set_xlim(20, 20000)
    ax2.set_ylim(-90, -10)
    ax2.grid(True, which="both", linestyle='--', alpha=0.5)
    ax2.legend(loc="lower left")

    plt.tight_layout()
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"\nSuccess: True THD verification processing complete.")
    print(f"Plot saved with mathematical components to: '{output_img}'")
    plt.show()

if __name__ == "__main__":
    analyze_audio_system_true_thd(
        stimulus_path=INPUT_FILE,
        recorded_path=OUTPUT_FILE
    )