import tkinter as tk
import threading
from parrot_engine import PollyEngine

class PollyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🦜 Polly Simulator")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # --- UI State Configuration (Added 'processing' state) ---
        self.states = {
            "sleeping": {"bg": "#2C3E50", "text": "#ECF0F1", "status": "💤 Polly is resting..."},
            "listening": {"bg": "#E74C3C", "text": "#FFFFFF", "status": "🔴 Listening! Speak now..."},
            "processing": {"bg": "#2980B9", "text": "#FFFFFF", "status": "⏳ Processing audio signal..."},
            "thinking": {"bg": "#F39C12", "text": "#FFFFFF", "status": "🧠 Polly is thinking..."},
            "speaking": {"bg": "#2ECC71", "text": "#FFFFFF", "status": "💬 Polly is squawking..."}
        }
        
        self.animation_counter = 0
        self.current_state = "sleeping"
        
        # --- Build UI Layout ---
        self.main_frame = tk.Frame(self.root, bg=self.states["sleeping"]["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.avatar_label = tk.Label(self.main_frame, text="🦜", font=("Arial", 72), bg=self.main_frame["bg"])
        self.avatar_label.pack(pady=40)
        
        self.status_label = tk.Label(
            self.main_frame, 
            text=self.states["sleeping"]["status"], 
            font=("Arial", 14, "bold"), 
            fg=self.states["sleeping"]["text"], 
            bg=self.main_frame["bg"]
        )
        self.status_label.pack(pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start text animation loop
        self.update_loading_animation()
        
        # --- Initialize Audio Engine ---
        try:
            self.engine = PollyEngine(state_callback=self.set_ui_state)
            
            print("🦜 Starting core audio runtime inside worker thread...")
            self.worker_thread = threading.Thread(
                target=self.engine.run_pipeline, 
                args=(self.safe_destroy,)
            )
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
        except Exception as e:
            print(f"❌ Initialization failure: {e}")
            self.root.destroy()

    def set_ui_state(self, state_name):
        """Receives state switches from background threads and schedules updates safely."""
        if state_name in self.states:
            self.current_state = state_name
            config = self.states[state_name]
            self.root.after(0, lambda: self._update_ui_elements(config))

    def _update_ui_elements(self, config):
        """Executes actual configuration rendering directly on the Main Tkinter loop."""
        self.main_frame.config(bg=config["bg"])
        self.avatar_label.config(bg=config["bg"])
        self.status_label.config(text=config["status"], fg=config["text"], bg=config["bg"])

    def update_loading_animation(self):
        """Animate the dots while processing or thinking to show the app is active."""
        if self.current_state in ["processing", "thinking"]:
            self.animation_counter = (self.animation_counter % 3) + 1
            dots = "." * self.animation_counter
            base_text = self.states[self.current_state]["status"].rstrip(".")
            self.status_label.config(text=f"{base_text}{dots}")
        
        # Check and loop every 400ms
        self.root.after(400, self.update_loading_animation)

    def safe_destroy(self):
        self.root.after(0, self.root.destroy)

    def on_closing(self):
        print("🛑 Close action flagged. Powering down background pipelines...")
        if hasattr(self, 'engine'):
            self.engine.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PollyGUI(root)
    root.mainloop()