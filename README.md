# 🦜 Polly Simulator

Polly Simulator is a multi-threaded, fully local AI voice assistant that runs entirely on your machine without relying on external cloud APIs. It features a responsive graphical user interface (GUI) that dynamically shifts states as it processes your voice commands, delivering a seamless edge-computing conversational experience.

## 🌟 Key Features

* **Acoustic Wake-Word Trigger:** Operates a low-overhead passive listening background stage that continuously scans microphone frames for the activation keyword ("parrot").
* **Edge AI Inference:** Processes multi-turn conversations completely locally using the `phi3` Large Language Model via Ollama.
* **Dynamic GUI Dashboard:** Built with a native, multi-threaded Tkinter interface that handles computationally heavy audio tasks in a background thread to prevent window freezing. Features custom status messages and smooth loading animations (`⏳ Processing...`).
* **Persistent Memory:** Automatically writes and restores conversation history to a local `history.json` file to maintain multi-turn context across application restarts.
* **Phonetic Audio Tuning:** Optimizes speech output via native macOS system parameters (`rate 200` and `pitch 65`) to synthesize a distinct, rapid-fire robotic parrot cadence (~300 WPM).

---

## 🏗️ Architecture Layout

The repository follows a clean, decoupled design enforcing the **Single Responsibility Principle**:
