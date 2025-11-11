import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

class DoublePendulumApp(ttk.Frame):
    def __init__(self, root, duration=10, fps=30):
        super().__init__(root, padding=(20,10))
        self.pack(fill=tk.BOTH, expand=tk.YES)
        self.root = root
        # Parameters
        self.duration = duration
        self.fps = fps
        self.total_frames = duration * fps
        
        # Other setups
        self.setup_gui()
        
        
    def setup_gui(self):
        ##################################
        # Window App
        ##################################
        self.root.title(f"Amazing Double Pendulum Simulation ({self.duration}s)")
        # self.root.geometry("500x500")
        
        ##################################
        # Main frame
        ##################################
        style = ttk.Style()
        style.configure("Coloured.TFrame", background="#f0f0f0")
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ##################################
        # Header Frame
        ##################################
        header_frame = ttk.Frame(main_frame, padding=(0, 10))
        header_frame.pack(fill=tk.Y, pady=(0, 10))
        # Header Label
        header_label = ttk.Label(header_frame, text="Double Pendulum Simulation", width=50, font=("Liberation Sans", 24, "bold"))
        header_label.pack(pady=0, side=tk.LEFT, anchor=tk.S)
        # Header Theme Selector
        theme_label = ttk.Label(header_frame, text="Select Theme:", font=("Liberation Sans", 10))
        theme_label.pack(pady=0, side=tk.RIGHT, anchor=tk.S)
        # Header Theme Combobox
        pass
    
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=0)

        ##################################
        # 1. Simulation frame
        ##################################
        self.simulation_frame = ttk.Labelframe(main_frame, bootstyle="primary", text="Simulation")
        self.simulation_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        # Matplotlib figure
        self.fig = Figure(figsize=(6, 6))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(-2.5, 2.5)
        self.ax.set_ylim(-2.5, 2.5)
        self.ax.set_aspect('equal')
        self.ax.grid()
        
        # Initialize plot elements
        self.line, = self.ax.plot([], [], 'o-', lw=2, markersize=8)
        self.trace, = self.ax.plot([], [], ',-', alpha=0.6, lw=1)
        self.time_text = self.ax.text(0.02, 0.95, '', transform=self.ax.transAxes)
        self.progress_text = self.ax.text(0.02, 0.90, '', transform=self.ax.transAxes)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.simulation_frame)
        self.canvas.get_tk_widget().pack()  
        
        ##################################
        # 2. Controls frame
        ##################################
        control_frame = ttk.Labelframe(main_frame, bootstyle="primary", text="Controls")
        # control_frame.place(x=50, y=50, width=300, height=100)
        control_frame.pack(fill=tk.BOTH, expand=True)
        # A. Bob 1 Frame
        bob1_frame = ttk.Labelframe(control_frame, bootstyle="danger", text="Pendulum 1")
        bob1_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        button1 = ttk.Button(bob1_frame, bootstyle="info", text="Restart", command='helo')
        button1.pack(side=tk.TOP, anchor=tk.W, padx=10, pady=10)
        
        # tk.Button(bob1_frame, text="Pause/Resume", command='helo').pack(side=tk.TOP, anchor=tk.W, padx=10, pady=10)
        
        
if __name__ == "__main__":
    root = ttk.Window("Title", "morph", resizable=(True, True))
    DoublePendulumApp(root, duration=10, fps=30)  # 30 seconds at 60 FPS
    root.mainloop()