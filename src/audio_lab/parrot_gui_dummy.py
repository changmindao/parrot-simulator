import tkinter as tk
import threading
import time

class PollyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🦜 Polly Simulator")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Define Color Palette for different App States
        self.states = {
            "sleeping": {"bg": "#2C3E50", "text": "#ECF0F1", "status": "💤 Polly is resting..."},
            "listening": {"bg": "#E74C3C", "text": "#FFFFFF", "status": "🔴 Listening! Speak now..."},
            "thinking": {"bg": "#F39C12", "text": "#FFFFFF", "status": "🧠 Consulting local brain..."},
            "speaking": {"bg": "#2ECC71", "text": "#FFFFFF", "status": "💬 Polly is squawking..."}
        }
        
        # Build UI Elements
        self.main_frame = tk.Frame(self.root, bg=self.states["sleeping"]["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.avatar_label = tk.Label(
            self.main_frame, 
            text="🦜", 
            font=("Arial", 72), 
            bg=self.main_frame["bg"]
        )
        self.avatar_label.pack(pady=30)
        
        self.status_label = tk.Label(
            self.main_frame, 
            text=self.states["sleeping"]["status"], 
            font=("Arial", 14, "bold"), 
            fg=self.states["sleeping"]["text"], 
            bg=self.main_frame["bg"]
        )
        self.status_label.pack(pady=10)
        
        # Temporary simulation button to test UI state changes safely
        self.test_button = tk.Button(
            self.root, 
            text="Simulate Audio Cycle", 
            command=self.start_simulation_thread
        )
        self.test_button.pack(side=tk.BOTTOM, fill=tk.X)

    def set_state(self, state_name):
        """Updates the UI colors and text safely from the main thread configuration."""
        if state_name in self.states:
            config = self.states[state_name]
            self.main_frame.config(bg=config["bg"])
            self.avatar_label.config(bg=config["bg"])
            self.status_label.config(text=config["status"], fg=config["text"], bg=config["bg"])
            self.root.update_idletasks()

    def start_simulation_thread(self):
        """Spins up a background worker thread so the UI stays completely interactive."""
        self.test_button.config(state=tk.DISABLED)
        worker = threading.Thread(target=self._fake_audio_pipeline)
        worker.daemon = True  # Ensures thread closes instantly if the main window is closed
        worker.start()

    def _fake_audio_pipeline(self):
        """Simulates the lifecycle of our parrot_wake logic using timestamps."""
        # Step 1: Wake up triggered
        self.set_state("listening")
        time.sleep(2.5)  # Simulates mic listening duration
        
        # Step 2: Processing audio / Ollama inference
        self.set_state("thinking")
        time.sleep(2.0)  # Simulates local LLM calculations
        
        # Step 3: Speaking response
        self.set_state("speaking")
        time.sleep(3.0)  # Simulates Alex TTS output execution
        
        # Step 4: Return to deep sleep
        self.set_state("sleeping")
        self.root.after(0, lambda: self.test_button.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = PollyGUI(root)
    root.mainloop()