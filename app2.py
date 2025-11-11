from pathlib import Path
from tkinter import DoubleVar, StringVar
from tkinter.messagebox import YES
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

class DoublePendulumApp(ttk.Frame):
    def __init__(self, root, duration=10, fps=30):
        super().__init__(root)
        self.pack(fill=BOTH, expand=YES)
        
        # Parameters
        self.m1_bob1 = DoubleVar(value=1.0)
        self.m2_bob1 = DoubleVar(value=1.0)
        self.l1_bob1 = DoubleVar(value=1.0)
        self.l2_bob1 = DoubleVar(value=1.0)
        
        self.θ1_bob1 = DoubleVar(value=90.0)
        self.θ2_bob1 = DoubleVar(value=120.0)
        self.ω1_bob1 = DoubleVar(value=0.0)
        self.ω2_bob1 = DoubleVar(value=0.0)
        
        # Tkinter parameters
        self.style = ttk.Style()
        themes = self.style.theme_names()
        
        # Track buttons and their base colors
        self.active_button = None
        self.buttons = {}         # name -> widget
        self.button_color = {}    # name -> base color (string like "success")

        buttons_info = [
            ("Calculate", "info"),
            ("Start", "success"),
            ("Pause", "warning"),
            ("Reset", "danger"),
        ]
        
        # Creating main layout
        for i in range(3):
            self.columnconfigure(i, weight=1) # all 3 columns expand horizontally equally
        # self.rowconfigure(0, weight=0) ## Prevents row 0 from expanding
        self.rowconfigure(1, weight=1) # Prevents row 1 from expanding
        self.rowconfigure(2, weight=0)
    
            
        # Debug
        style = ttk.Style()
        style.configure("Blue.TFrame", background="#5ca2ff")
        style.configure("Red.TFrame", background="#f35e5e")
        style.configure("Green.TFrame", background="#5eff7e")
        style.configure("Yellow.TFrame", background="#fff45e")
        style.configure("Purple.TFrame", background="#c95eff")
        style.configure("Orange.TFrame", background="#ffb45e")
        style.configure("Cyan.TFrame", background="#5efff1")
        style.configure("Pink.TFrame", background="#ff5ed1")
        style.configure("Gray.TFrame", background="#a3a3a3")
        
        ##################
        # Row 1
        ##################

        # Column 1
        col1_row1 = ttk.Frame(self, padding=10, style="Blue.TFrame")
        col1_row1.grid(row=0, column=0, columnspan=2,sticky=EW)
        
        # Header
        header_label = ttk.Label(col1_row1, text="Double Pendulum Simulation (30s)", font=("Liberation Sans", 24, "bold"))
        header_label.pack(side=BOTTOM, fill=BOTH, expand=YES)
        
        # Column 3
        col3_row1 = ttk.Frame(self, padding=10, style="Red.TFrame")
        col3_row1.grid(row=0, column=2, sticky=EW)
        
        # Theme
        theme_frame = ttk.Frame(col3_row1)
        theme_frame.pack(side=BOTTOM, anchor=E, expand=YES)
        theme_label = ttk.Label(theme_frame, text="Select Theme : ", font=("Liberation Sans", 10))
        theme_label.pack(side=LEFT, expand=YES)
        self.theme_dropdown = ttk.Combobox(theme_frame, values=themes, state="readonly", bootstyle="info")
        self.theme_dropdown.pack(side=RIGHT, expand=YES)
        self.theme_dropdown.set(self.style.theme.name)  # set current theme
        self.theme_dropdown.bind("<<ComboboxSelected>>", self.change_theme)

        
        ##################
        # Row 2
        ##################
        
        # Matplotlib Parameters
        rcParams['text.usetex'] = False
        rcParams['font.family'] = ['Liberation Serif', 'serif']
        rcParams['mathtext.fontset'] = 'cm'
        rcParams['figure.dpi'] = 100
                
        # Column 1
        col1_row2 = ttk.Frame(self, padding=10)
        col1_row2.grid(row=1, column=0, sticky=NSEW)
        
        
        # Graph 1
        # Matplotlib figure
        self.fig1 = Figure(figsize=(6, 6))
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_title(r"Swinging Pendulum ($y$ against $x$)", fontsize=14)
        # self.ax1.set_xlim(-2.5, 2.5)
        # self.ax1.set_ylim(-2.5, 2.5)
        # self.ax1.set_aspect('equal')
        self.ax1.grid(linestyle=':', color='gray', alpha=0.7)
        # Initialize plot elements
        self.line1, = self.ax1.plot([], [], 'o-', lw=2, markersize=8)
        self.trace1, = self.ax1.plot([], [], ',-', alpha=0.6, lw=1, label='Trace 1')
        self.ax1.legend(loc='upper right')
        self.fig1.tight_layout()
        # self.time_text1 = self.ax1.text(0.02, 0.95, '', transform=self.ax1.transAxes)
        # self.progress_text1 = self.ax1.text(0.02, 0.90, '', transform=self.ax1.transAxes)
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=col1_row2)
        self.canvas1.get_tk_widget().pack(fill=BOTH, expand=YES)
        
        # Column 2
        col2_row2 = ttk.Frame(self, padding=10, style="Yellow.TFrame")
        col2_row2.grid(row=1, column=1, sticky=NSEW)
        
        # Graph 1
        # Matplotlib figure
        self.fig2 = Figure(figsize=(6, 6))
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_title("Phase Space $X$ ($v_x$ against $x$)", fontsize=14)
        # self.ax2.set_xlim(-2.5, 2.5)
        # self.ax2.set_ylim(-2.5, 2.5)
        # self.ax2.set_aspect('equal')
        self.ax2.grid(linestyle=':', color='gray', alpha=0.7)
        # Initialize plot elements
        self.line2, = self.ax2.plot([], [], '-', lw=2, color='red', alpha=0.2)
        self.fig2.tight_layout()
        # self.time_text2 = self.ax2.text(0.02, 0.95, '', transform=self.ax2.transAxes)
        # self.progress_text2 = self.ax2.text(0.02, 0.90, '', transform=self.ax2.transAxes)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=col2_row2)
        self.canvas2.get_tk_widget().pack(fill=BOTH, expand=YES)

        # Column 3
        col3_row2 = ttk.Frame(self, padding=10, style="Purple.TFrame")
        col3_row2.grid(row=1, column=2, sticky=NSEW)
        
        # Graph 1
        # Matplotlib figure
        self.fig3 = Figure(figsize=(6, 6))
        self.ax3 = self.fig3.add_subplot(111)
        self.ax3.set_title("Phase Space $Y$ ($v_y$ against $y$)", fontsize=14)
        # self.ax3.set_xlim(-2.5, 2.5)
        # self.ax3.set_ylim(-2.5, 2.5)
        # self.ax3.set_aspect('equal')
        self.ax3.grid(linestyle=':', color='gray', alpha=0.7)
        # Initialize plot elements
        self.line3, = self.ax3.plot([], [], '-', lw=2, color='red', alpha=0.2)
        self.fig3.tight_layout()
        # self.time_text2 = self.ax3.text(0.02, 0.95, '', transform=self.ax3.transAxes)
        # self.progress_text2 = self.ax3.text(0.02, 0.90, '', transform=self.ax3.transAxes)

        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=col3_row2)
        self.canvas3.get_tk_widget().pack(fill=BOTH, expand=YES)
        
        ##################
        # Row 3
        ##################
        
        # --- Column 1 ---
        col1_row3 = ttk.Frame(self, padding=5, style="Pink.TFrame")
        col1_row3.grid(row=2, column=0, sticky=NSEW)
        col1_row3.grid_configure(pady=10)
        
        # Start-Stop Frame
        start_stop_frame = ttk.Labelframe(col1_row3, bootstyle="success", text="Playback Controls")
        start_stop_frame.pack(fill=BOTH, expand=YES)
        start_stop_frame.columnconfigure(0, weight=1) # adaptive inner layout
        start_stop_frame.rowconfigure(0, weight=1)
        
        # Inner Frame
        inner_start_stop_frame = ttk.Frame(start_stop_frame)
        inner_start_stop_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        inner_start_stop_frame.columnconfigure(0, weight=1) # Column 0
        inner_start_stop_frame.columnconfigure(1, weight=1) # Column 1

        # Gravity Meter column
        gravity_meter = ttk.Meter(inner_start_stop_frame, bootstyle="primary", subtext="Gravity", subtextstyle="primary", textright="(m/s²)", metertype="semi", stripethickness=5, amountused=98.0, amounttotal=200, amountformat="{:.1f}", interactive=True)
        gravity_meter.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Playback Buttons
        playback_buttons_frame = ttk.Frame(inner_start_stop_frame)
        playback_buttons_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # --- Configure for a Single Column Layout ---
        # Only Column 0 is configured to expand horizontally (weight=1).
        playback_buttons_frame.columnconfigure(0, weight=1) 
        # Configure all four rows to expand vertically.
        playback_buttons_frame.rowconfigure(0, weight=1)
        playback_buttons_frame.rowconfigure(1, weight=1)
        playback_buttons_frame.rowconfigure(2, weight=1) # New row for the 3rd button
        playback_buttons_frame.rowconfigure(3, weight=1) # New row for the 4th button

        # --- Grid the 4 Buttons in Column 0 ---
        for i, (text, color) in enumerate(buttons_info):
            # save base color
            self.button_color[text] = color

            btn = ttk.Button(
                playback_buttons_frame,
                text=text,
                bootstyle=f"{color}-outline",  # faint outline when idle
                command=lambda name=text, col=color: self.on_button_click(name, col)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=5, pady=4)

            self.buttons[text] = btn

        # Make column expand if needed
        try:
            playback_buttons_frame.columnconfigure(0, weight=1)
        except Exception:
            pass

        playback_buttons_frame.columnconfigure(0, weight=1)

        # --- Column 2 and 3 ---
        col2_row3 = ttk.Frame(self, padding=5, style="Cyan.TFrame")
        col2_row3.grid(row=2, column=1, columnspan=2, sticky=NSEW)
        col2_row3.grid_configure(pady=10)
        
        # Control Frame
        control_frame = ttk.Labelframe(col2_row3, bootstyle="primary", text="Pendulum Parameters")
        control_frame.pack(fill=BOTH, expand=YES)
        control_frame.columnconfigure(0, weight=1) # adaptive innner layout
        control_frame.rowconfigure(0, weight=1)
        
        # Inner Frame
        inner_control_frame = ttk.Frame(control_frame)
        inner_control_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        inner_control_frame.columnconfigure(0, weight=1)
        inner_control_frame.columnconfigure(1, weight=1)
        inner_control_frame.rowconfigure(0, weight=1)

        # First parameter column
        param1_frame = ttk.Labelframe(inner_control_frame, bootstyle="danger", text="Characteristics")
        param1_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=0)

        # Configure rows for even vertical spacing
        param1_frame.rowconfigure(0, weight=1)
        param1_frame.rowconfigure(1, weight=1)
        param1_frame.rowconfigure(2, weight=1)
        param1_frame.rowconfigure(3, weight=1)

        # Configure columns for 2-column layout: Text (fixed) | Slider (adaptive)
        param1_frame.columnconfigure(0, weight=0) # Column 0 for Labels: Fixed width
        param1_frame.columnconfigure(1, weight=1) # Column 1 for Sliders: Adaptive width

        # Labels and Sliders (Dynamic)
        self.labels = {}  # store references to labels
        self.add_param1(
            frame=param1_frame,
            row=0,
            name="m1 (kg)",
            variable=self.m1_bob1
        )
        self.add_param1(
            frame=param1_frame,
            row=1,
            name="m2 (kg)",
            variable=self.m2_bob1
        )
        self.add_param1(
            frame=param1_frame,
            row=2,
            name="l1 (m)",
            variable=self.l1_bob1
        )
        self.add_param1(
            frame=param1_frame,
            row=3,
            name="l2 (m)",
            variable=self.l2_bob1
        )

        # Second parameter column
        param2_frame = ttk.Labelframe(inner_control_frame, bootstyle="danger", text="State Vectors")
        param2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=0)

        # Configure rows for even vertical spacing
        param2_frame.rowconfigure(0, weight=1)
        param2_frame.rowconfigure(1, weight=1)
        param2_frame.rowconfigure(2, weight=1)
        param2_frame.rowconfigure(3, weight=1)

        # Configure columns for 2-column layout: Text (fixed) | Slider (adaptive)
        param2_frame.columnconfigure(0, weight=0) # Column 0 for Labels: Fixed width
        param2_frame.columnconfigure(1, weight=1) # Column 1 for Sliders: Adaptive width
        
        self.add_param2(
            frame=param2_frame,
            row=0,
            name="θ1 (°)",
            variable=self.θ1_bob1
        )
        self.add_param2(
            frame=param2_frame,
            row=1,
            name="θ2 (°)",
            variable=self.θ2_bob1
        )
        self.add_param2(
            frame=param2_frame,
            row=2,
            name="ω1 (°/s)",
            variable=self.ω1_bob1
        )
        self.add_param2(
            frame=param2_frame,
            row=3,
            name="ω2 (°/s)",
            variable=self.ω2_bob1
        )

    def add_param1(self, frame, row, name, variable):
        """Creates a label + slider pair and links the slider to label updates."""
        # Create label
        label = ttk.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.labels[name] = label  # save reference

        # Create slider
        scale = ttk.Scale(
            frame,
            from_=0, to=20.0,
            variable=variable,
            command=lambda val, n=name, v=variable: self.update_label(n, v)
        )
        scale.grid(row=row, column=1, sticky="ew", padx=(10, 20), pady=2)
        
    def add_param2(self, frame, row, name, variable):
        """Creates a label + slider pair and links the slider to label updates."""
        # Create label
        label = ttk.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.labels[name] = label  # save reference

        # Create slider
        scale = ttk.Scale(
            frame,
            from_=0, to=360.0,
            variable=variable,
            command=lambda val, n=name, v=variable: self.update_label(n, v)
        )
        scale.grid(row=row, column=1, sticky="ew", padx=(10, 20), pady=2)

    def update_label(self, name, var):
        """Update the corresponding label text dynamically."""
        self.labels[name].config(text=f"{name}: {var.get():.2f}")
        
        
    ##################
    # Functions
    ##################

    def change_theme(self, event=None):
        """Update the entire UI theme dynamically."""
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)
    
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
        
        
if __name__ == "__main__":
    root = ttk.Window("Title", "morph", resizable=(True, True))
    DoublePendulumApp(root, duration=10, fps=30)  # 30 seconds at 60 FPS
    root.mainloop()