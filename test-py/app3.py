from tkinter import DoubleVar, StringVar
from tkinter.messagebox import YES

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

class DoublePendulumApp(tb.Frame):
    def __init__(self, root):
        # GUI window
        super().__init__(root)
        self.pack(fill=BOTH, expand=YES, padx=20) # main window frame fills up completely during resizing
        
        # Parameters
        self.m1_bob1 = DoubleVar(value=1.0)
        self.m2_bob1 = DoubleVar(value=1.0)
        self.l1_bob1 = DoubleVar(value=1.0)
        self.l2_bob1 = DoubleVar(value=1.0)
        self.θ1_bob1 = DoubleVar(value=90.0)
        self.θ2_bob1 = DoubleVar(value=120.0)
        self.ω1_bob1 = DoubleVar(value=0.0)
        self.ω2_bob1 = DoubleVar(value=0.0)
        
        # Time tracking
        self.time = 0.0
        self.dt = 0.01
        
        # Tkinter Style object
        self.style = tb.Style()

        # Button tracking
        self.active_button = None # Track buttons and their base colors
        self.buttons = {}         # name -> widget
        self.button_color = {}    # name -> base color (string like "success")
        self.buttons_info = [
            ("Calculate", "info"),
            ("Start", "success"),
            ("Pause", "warning"),
            ("Reset", "danger"),
        ]
        
        # Slider tracking
        self.labels = {}  # store references to labels
        
        # Creation of GUI
        self.create_header()
        self.create_main()
        
        self.create_playback()
        self.create_controls()
    
    # ------------GUI Functions---------------
    
    def create_header(self):
        header_frame = tb.Frame(self)
        header_frame.pack(fill=X, pady=(10, 10))  # stays at top, independent of grid

        header_label = tb.Label(
            header_frame,
            text="Double Pendulum Simulation (30s)",
            font=("Liberation Sans", 24, "bold"),
            bootstyle="info"
        )
        header_label.pack(side=LEFT, padx=(5, 10))

        # Theme Dropdown
        themes = self.style.theme_names()
        self.theme_dropdown = tb.Combobox(
            header_frame,
            values=themes,
            state="readonly",
            bootstyle="info",
            font=("Liberation Sans", 10)
        )
        self.theme_dropdown.pack(side=RIGHT, padx=5)
        self.theme_dropdown.set(self.style.theme.name)
        self.theme_dropdown.bind("<<ComboboxSelected>>", self.change_theme)
    
    def create_main(self):
        """Main grid area for graphs and other content"""
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # Create a 3x3 grid inside this frame
        for i in range(3):
            self.main_frame.columnconfigure(i, weight=1) # all 3 columns expand horizontally equally
        for j in range(3):
            if j!=1: self.main_frame.columnconfigure(j, weight=0)
            else: self.main_frame.rowconfigure(j, weight=1)  # only row with graph expands vertically
            
        # Separator
        tb.Separator(self.main_frame, orient=HORIZONTAL, bootstyle="info").grid(row=0, column=0, columnspan=3, sticky=EW)
        
    def create_graphs(self):
        pass
    
    def create_playback(self):
        self.playback_frame = tb.Labelframe(
            self.main_frame, 
            text="Playback Controls", 
            bootstyle="info",
        )
        self.playback_frame.grid(row=2, column=0, pady=10, padx=5, sticky=NSEW)
        
        # Create a 3x3 grid inside playback_frame
        inner_playback_frame = tb.Frame(self.playback_frame)
        inner_playback_frame.pack(fill=BOTH, expand=YES)
        for i in range(3): inner_playback_frame.columnconfigure(i, weight=1)
        for j in range(3): inner_playback_frame.rowconfigure(j, weight=0)
        inner_playback_frame.rowconfigure(0, weight=0) # first row with graviioty meter expands

        # 1. Gravity Control Meter
        self.gravity_meter = tb.Meter(inner_playback_frame, bootstyle="primary", subtext="Gravity", subtextstyle="primary", textright="(m/s²)", metertype="semi", stripethickness=5, amountused=98.0, amounttotal=200, amountformat="{:.1f}", interactive=True)
        self.gravity_meter.grid(row=0, column=0, padx=10, pady=10, sticky=NSEW)
        
        # Separator
        tb.Separator(inner_playback_frame, orient=HORIZONTAL, bootstyle="info").grid(row=1, column=0, sticky=EW)
        
        # 2. Time Control Meter
        time_frame = tb.Frame(inner_playback_frame)
        time_frame.grid(row=2, column=0, padx=10, pady=10, sticky=EW)
        time_frame.columnconfigure(0, weight=1)
        time_frame.rowconfigure(0, weight=1) # for time label
        time_frame.rowconfigure(1, weight=1) # for progress bar
        self.time_label = tb.Label(time_frame, text="Time Elapsed: 0.0s", bootstyle="info")
        self.time_label.grid(row=0, column=0, padx=10, pady=5, sticky=EW)
        self.time_bar = tb.Progressbar(time_frame, bootstyle="success-striped", maximum=30, value=0)
        self.time_bar.grid(row=1, column=0, padx=10, pady=10, sticky=EW)
        
        # Separator
        tb.Separator(inner_playback_frame, orient=VERTICAL, bootstyle="info").grid(row=0, column=1 , rowspan=3, sticky=NS)
        
        # 3. Playback Controls
        playback_buttons_frame = tb.Frame(inner_playback_frame)
        playback_buttons_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=10, sticky=NSEW)
        playback_buttons_frame.columnconfigure(0, weight=1) 
        for i in range(len(self.buttons_info)): playback_buttons_frame.rowconfigure(i, weight=1)
        
        for i, (text, color) in enumerate(self.buttons_info):
            self.button_color[text] = color # save base color to use later in on_button_click
            btn = tb.Button( # each button initially styled with faint outline
                playback_buttons_frame,
                text=text,
                bootstyle=f"{color}-outline",
                command=lambda name=text, col=color: self.on_button_click(name, col) # calls self.on_button_click when button is pressed
            )
            btn.grid(row=i, column=0, sticky="ew", padx=5, pady=4)
            self.buttons[text] = btn # stores the created button widget in the self.buttons dictionary.
            
    def create_controls(self):
        """Additional controls at the bottom"""
        self.control_frame = tb.Labelframe(
            self.main_frame, 
            text="Parameter Controls", 
            bootstyle="danger",
        )
        self.control_frame.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky=NSEW)
        
        # Create a 1x2 grid inside playback_frame
        inner_control_frame = tb.Frame(self.control_frame)
        inner_control_frame.pack(fill=BOTH, expand=YES)
        for i in range(2): inner_control_frame.columnconfigure(i, weight=1)
        inner_control_frame.rowconfigure(0, weight=1)
        
        # 1. Pendulum 1 Controls
        bob1_frame = tb.Labelframe(inner_control_frame, bootstyle="primary", text="Characteristics")
        bob1_frame.grid(row=0, column=0, padx=5, pady=10, sticky=NSEW)
        for i in range(4): bob1_frame.rowconfigure(i, weight=1)
        bob1_frame.columnconfigure(0, weight=0) # for text labels (fixed width)
        bob1_frame.columnconfigure(1, weight=1) # for sliders (adaptive width)
        
        # Dynamic generation of sliders
        self.add_param1(
            frame=bob1_frame,
            row=0,
            name="m1 (kg)",
            variable=self.m1_bob1
        )
        self.add_param1(
            frame=bob1_frame,
            row=1,
            name="m2 (kg)",
            variable=self.m2_bob1
        )
        self.add_param1(
            frame=bob1_frame,
            row=2,
            name="l1 (m)",
            variable=self.l1_bob1
        )
        self.add_param1(
            frame=bob1_frame,
            row=3,
            name="l2 (m)",
            variable=self.l2_bob1
        )

        # 2. Pendulum 1 Controls
        bob2_frame = tb.Labelframe(inner_control_frame, bootstyle="primary", text="State Vectors")
        bob2_frame.grid(row=0, column=1, padx=5, pady=10, sticky=NSEW)
        for i in range(4): bob2_frame.rowconfigure(i, weight=1)
        bob2_frame.columnconfigure(0, weight=0) # for text labels (fixed width)
        bob2_frame.columnconfigure(1, weight=1) # for sliders (adaptive width)
        
        self.add_param2(
            frame=bob2_frame,
            row=0,
            name="θ1 (°)",
            variable=self.θ1_bob1
        )
        self.add_param2(
            frame=bob2_frame,
            row=1,
            name="θ2 (°)",
            variable=self.θ2_bob1
        )
        self.add_param2(
            frame=bob2_frame,
            row=2,
            name="ω1 (°/s)",
            variable=self.ω1_bob1
        )
        self.add_param2(
            frame=bob2_frame,
            row=3,
            name="ω2 (°/s)",
            variable=self.ω2_bob1
        )
        
        # Example additional control
        # tb.Button(self.control_frame, text="Reset All", bootstyle="danger", command=self.clear_active).pack(side=LEFT, padx=5, pady=5)
        

    # ------------Worker Functions---------------
    
    # Theme change
    def change_theme(self, event=None):
        """Update the entire UI theme dynamically."""
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)
    
    # Button tracking
    def on_button_click(self, name, color):
        """Highlight clicked button (solid color) and reset previous to outline."""
        # Reset previous active button (if any)
        if self.active_button and self.active_button in self.buttons:
            prev_name = self.active_button
            prev_color = self.button_color.get(prev_name, "secondary")
            self.buttons[prev_name].configure(bootstyle=f"{prev_color}-outline")
        # Set current button to solid color
        self.buttons[name].configure(bootstyle=f"{color}")
        self.active_button = name
        
    def clear_active(self):
        """Utility to reset any active button to outline state."""
        if self.active_button:
            name = self.active_button
            color = self.button_color.get(name, "secondary")
            self.buttons[name].configure(bootstyle=f"{color}-outline")
            self.active_button = None
            
    # Slider tracking
    def add_param1(self, frame, row, name, variable):
        """Creates a label + slider pair and links the slider to label updates."""
        # Create label
        label = tb.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.labels[name] = label  # save reference
        # Create slider
        scale = tb.Scale(
            frame,
            from_=0, to=20.0,
            variable=variable,
            command=lambda val, n=name, v=variable: self.update_label(n, v)
        )
        scale.grid(row=row, column=1, sticky="ew", padx=(10, 20), pady=2)
        
    def add_param2(self, frame, row, name, variable):
        """Creates a label + slider pair and links the slider to label updates."""
        # Create label
        label = tb.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.labels[name] = label  # save reference

        # Create slider
        scale = tb.Scale(
            frame,
            from_=0, to=360.0,
            variable=variable,
            command=lambda val, n=name, v=variable: self.update_label(n, v)
        )
        scale.grid(row=row, column=1, sticky="ew", padx=(10, 20), pady=2)
        
    def update_label(self, name, var):
        """Update the corresponding label text dynamically."""
        self.labels[name].config(text=f"{name}: {var.get():.2f}")
        

if __name__ == "__main__":
    root = tb.Window("Double Pendulum Simulation (30s)", "morph", resizable=(True, True))
    DoublePendulumApp(root)
    root.mainloop()
    
