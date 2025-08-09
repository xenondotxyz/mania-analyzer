import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from osrparse import Replay, GameMode
import numpy as np
import os

class HoldTimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xenon's osu!mania Hold Time Analyzer")
        self.root.geometry("800x600")

        self.replay_path = tk.StringVar()
        self.replay = None

        self.file_frame = tk.Frame(self.root)
        self.file_frame.pack(pady=10)

        self.label = tk.Label(self.file_frame, text="Select an osu!mania replay file (.osr):")
        self.label.pack(side=tk.LEFT)

        self.path_label = tk.Label(self.file_frame, textvariable=self.replay_path, width=40, anchor="w")
        self.path_label.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT)

        self.generate_button = tk.Button(self.root, text="Generate Hold-Time Graph", command=self.generate_graph)
        self.generate_button.pack(pady=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        """Open a file dialog to select a replay file."""
        file_path = filedialog.askopenfilename(
            title="Select osu!mania Replay File",
            filetypes=[("osu! Replay Files", "*.osr")]
        )
        if file_path:
            self.replay_path.set(file_path)
            try:
                self.replay = Replay.from_path(file_path)
                print(f"Detected replay mode: {self.replay.mode} (type: {type(self.replay.mode)})")
                print(f"GameMode.MANIA: {GameMode.MANIA} (type: {type(GameMode.MANIA)})")

                if self.replay.mode != GameMode.MANIA:
                    messagebox.showerror("Error", f"This replay is not for osu!mania! Detected mode: {self.replay.mode}")
                    self.replay = None
                    self.replay_path.set("")
                else:
                    messagebox.showinfo("Success", f"Loaded replay for {self.replay.username}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load replay: {e}")
                self.replay_path.set("")
                self.replay = None

    def calculate_hold_times(self, replay):
        """Calculate hold times from the replay data."""

        hold_times = {f"Key {i+1}": [] for i in range(4)} 
        key_mapping = {
            1: "Key 1",  
            2: "Key 2",  
            4: "Key 3",  
            8: "Key 4",  
        
        }

        press_start = {key: None for key in key_mapping.values()}
        current_time = 0

        for event in replay.replay_data:
            current_time += event.time_delta  
            keys = event.keys  

            for key_flag, key_name in key_mapping.items():
                if keys & key_flag:  
                    if press_start[key_name] is None:
                        press_start[key_name] = current_time
                else:  
                    if press_start[key_name] is not None:
                        hold_time = current_time - press_start[key_name]
                        if hold_time > 0:
                            hold_times[key_name].append(hold_time)
                        press_start[key_name] = None

        return hold_times

    def generate_graph(self):
        """Generate and display the hold-time histogram."""
        if not self.replay:
            messagebox.showwarning("Warning", "Please select a valid osu!mania replay file first!")
            return

        self.ax.clear()

        hold_times = self.calculate_hold_times(self.replay)

        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
        labels = []
        avg_hold_times = []

        for i, (key, times) in enumerate(hold_times.items()):
            if times:
                self.ax.hist(times, bins=50, alpha=0.5, color=colors[i % len(colors)], label=key, density=True)
                avg = np.mean(times) if times else 0
                avg_hold_times.append(avg)
                labels.append(f"{key} ({len(times)} holds, {avg:.2f}ms avg.)")

        self.ax.set_title(
            f"({self.replay.beatmap_hash}) {self.replay.username} at "
            f"{self.replay.timestamp.strftime('%d/%m/%Y %H:%M:%S')} + ({self.replay.score}ms)"
        )
        self.ax.set_xlabel("Milliseconds")
        self.ax.set_ylabel("Amount of Occurrences")
        self.ax.legend(labels)
        self.ax.grid(True, linestyle="--", alpha=0.7)

        self.canvas.draw()


def main():
    root = tk.Tk()
    app = HoldTimeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()