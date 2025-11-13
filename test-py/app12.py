from tkinter import VERTICAL, DoubleVar, StringVar
from tkinter.messagebox import YES

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

import numpy as np
from scipy.linalg import solve

from app.utils import position_bob1, velocity_bob1, position_bob2, velocity_bob2, simulate_double_pendulum

from matplotlib.pyplot import rcParams, style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation


class DoublePendulumApp(tb.Frame):
    def __init__(self, root):
        # GUI window
        super().__init__(root)
        self.pack(fill=BOTH, expand=YES, padx=20)
        
        # Parameters
        self.m1_bob1 = DoubleVar(value=1.0)
        self.m2_bob1 = DoubleVar(value=1.0)
        self.l1_bob1 = DoubleVar(value=1.0)
        self.l2_bob1 = DoubleVar(value=1.0)
        self.θ1_bob1 = DoubleVar(value=90.0)
        self.θ2_bob1 = DoubleVar(value=120.0)
        self.ω1_bob1 = DoubleVar(value=0.0)
        self.ω2_bob1 = DoubleVar(value=0.0)
        self.gravity = DoubleVar(value=98.1)
        
        # Arrays (initialise first)
        self.θ1_arr = self.θ2_arr = np.array([1]) # dummy arrays
        self.ω1_arr = self.ω2_arr = np.array([1])
        self.x1_arr = self.y1_arr = np.array([1])
        self.x2_arr = self.y2_arr = np.array([1])
        self.vx1_arr = self.vy1_arr = np.array([1])
        self.vx2_arr = self.vy2_arr = np.array([1])
        self.t_values = None
        self.results = None

        # Animation & playback state
        self.anim = None
        self.frame_index = 0
        self.total_frames = 0
        self.data_ready = False

        # Time control
        self.time = 0.0
        self.dt = 0.01
        self.time_max = 30.0
        # self.time_max = 30.0
        self.running = False
        self.anim_in_process = False
        self.after_id = None

        # Store slider widgets so enable/disable is robust
        self.scales = []

        # Ttkbootstrap style
        self.style = tb.Style()

        # Buttons bookkeeping
        self.active_button = None
        self.buttons = {}
        self.button_color = {}
        self.buttons_info = [ # for creating buttons
            ("Start", "success"),
            ("Pause", "warning"),
            ("Reset", "danger"),
            ("Default", "info")
        ]

        # Labels
        self.labels = {}

        # Build UI
        self.create_header()
        self.create_main()
        self.create_graphs()
        self.create_playback()
        self.create_controls()
        self.update_pendulum_preview()

    # ---------- GUI creation ----------
    
    def create_header(self):
        # 1. Header label
        header_frame = tb.Frame(self)
        header_frame.pack(fill=X, pady=(10, 10))

        header_label = tb.Label(
            header_frame,
            text=f"Double Pendulum Simulation ({self.time_max}s)",
            font=("Liberation Sans", 22, "bold"),
            bootstyle="info"
        )
        header_label.pack(side=LEFT, padx=(5, 10))

        # 2. Theme selector
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
        # Main frame
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # 3X3 grid main frame
        for i in range(3): self.main_frame.columnconfigure(i, weight=1)
        for j in range(3):
            if j != 1: self.main_frame.rowconfigure(j, weight=0)
            else: self.main_frame.rowconfigure(j, weight=1)

        tb.Separator(self.main_frame, orient=HORIZONTAL, bootstyle="info").grid(row=0, column=0, columnspan=3, sticky=EW)

    def create_graphs(self):
        # Creation of graph frame
        self.graph_frame = tb.Labelframe(self.main_frame, text="Visualization", bootstyle="success")
        self.graph_frame.grid(row=1, column=0, columnspan=3, pady=0, padx=0, sticky=NSEW)
        
        # MPL customization
        rcParams['text.usetex'] = False
        rcParams['font.family'] = ['Liberation Serif', 'serif']
        rcParams['mathtext.fontset'] = 'cm'
        rcParams['figure.dpi'] = 100
        style.use('seaborn-v0_8')
        
        self.fig = Figure(figsize=(15, 5))
        self.ax1 = self.fig.add_subplot(131)
        self.ax2 = self.fig.add_subplot(132)
        self.ax3 = self.fig.add_subplot(133)
        
        # 1. Double Pendulum Visualization
        limit1 = self.l1_bob1.get() + self.l2_bob1.get() + 0.5
        self.ax1.set_title(r"Double Pendulum, $y(m)$ against $x(m)$", fontsize=12)
        self.ax1.set_xlim(-limit1, limit1)
        self.ax1.set_ylim(-limit1, limit1)
        self.ax1.axhline(0, color='black', lw=0.5, ls='--', alpha=0.5)
        self.ax1.axvline(0, color='black', lw=0.5, ls='--', alpha=0.5)
        self.ax1.set_aspect('equal', adjustable='box')
        # self.ax1.grid(ls=':', color='gray', alpha=0.7)
        for spine in self.ax1.spines.values():
            spine.set_visible(True)
            spine.set_color('gray')
            spine.set_linewidth(1.5)

        (self.bob1,) = self.ax1.plot([], [], ms=5, mfc='crimson', mec='crimson', marker='o', ls='--', lw=0.5, color='maroon', zorder=2, label='Bob 1')
        (self.bob2,) = self.ax1.plot([], [], ms=5, mfc='royalblue', mec='royalblue', marker='o', ls='--', lw=0.5, color='green', zorder=1, label='Bob 2')
        (self.trail1,) = self.ax1.plot([], [], color='crimson', ls="--", lw=0.5, alpha=0.5, zorder=0)
        (self.trail2,) = self.ax1.plot([], [], color='royalblue', ls="--", lw=0.5, alpha=0.5, zorder=0)
        self.ax1.legend(loc='best', frameon=True, facecolor='white')
        
        # 2. Position (θ°) against time (t) plot
        self.ax2.set_title(r"Angles of Pendulum, $θ(\degree)$ against $t(s)$", fontsize=12)
        self.ax2.set_xlim(0, self.time_max+0.5)
        self.ax2.set_ylim(-360, 360)
        self.ax2.axhline(0, color='black', lw=0.5, ls='--', alpha=0.5)
        self.ax2.axvline(0, color='black', lw=0.5, ls='--', alpha=0.5)

        # Set aspect ratio to make plot area square
        data_ratio = 720 / (self.time_max + 0.5) # ratio of y against x data ranges
        self.ax2.set_aspect(1.0 / data_ratio) 
        # self.ax2.grid(ls=':', color='gray', alpha=0.7)
        for spine in self.ax2.spines.values():
            spine.set_visible(True)
            spine.set_color('gray')
            spine.set_linewidth(1.5)
        
        (self.angle1,) = self.ax2.plot([], [], ls='-', lw=1.5, color='crimson', label=r'$\theta_1$')
        (self.angle2,) = self.ax2.plot([], [], ls='-', lw=1.5, color='royalblue', label=r'$\theta_2$')
        self.ax2.legend(loc='best', frameon=True, facecolor='white')
        
        # 3. Phase Space X
        self.ax3.set_title(r"Phase Space, $v_x(\mathrm{ms}^{-1})$ against $x(m)$", fontsize=12)
        limit3_position = max(np.maximum(np.abs(self.x1_arr), np.abs(self.x2_arr)))
        limit3_velocity = max(np.maximum(np.abs(self.vx1_arr), np.abs(self.vx2_arr)))
        limit3 = max(limit3_position, limit3_velocity)
        self.ax3.set_xlim(-limit3*1.1, limit3*1.1)
        self.ax3.set_ylim(-limit3*1.1, limit3*1.1)
        self.ax3.axhline(0, color='black', lw=0.5, ls='--', alpha=0.5)
        self.ax3.axvline(0, color='black', lw=0.5, ls='--', alpha=0.5)
        self.ax3.set_aspect('equal', adjustable='box')
        # self.ax3.grid(ls=':', color='gray', alpha=0.7)
        for spine in self.ax3.spines.values():
            spine.set_visible(True)
            spine.set_color('gray')
            spine.set_linewidth(1.5)
        
        (self.phase1,) = self.ax3.plot([], [], ls='-', lw=1, color='crimson', label='Phase 1')
        (self.phase2,) = self.ax3.plot([], [], ls='-', lw=1, color='royalblue', label='Phase 2')
        self.ax3.legend(loc='best', frameon=True, facecolor='white')

        # Add canvas to tkinter
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def create_playback(self):
        # Playback frame
        self.playback_frame = tb.Labelframe(self.main_frame, text="Playback Controls", bootstyle="info")
        self.playback_frame.grid(row=2, column=0, pady=10, padx=5, sticky=NSEW)

        # Inner playback frame
        inner_playback_frame = tb.Frame(self.playback_frame)
        inner_playback_frame.pack(fill=BOTH, expand=YES)
        
        # 3X3 grid inside inner playback frame
        for i in range(3): inner_playback_frame.columnconfigure(i, weight=1)
        for j in range(3): inner_playback_frame.rowconfigure(j, weight=0)
        inner_playback_frame.rowconfigure(0, weight=0)

        # 1. Gravity Meter
        self.gravity_meter = tb.Meter(
            inner_playback_frame,
            bootstyle="primary",
            subtext="Gravity",
            subtextstyle="primary",
            textright="(m/s²)",
            metertype="semi",
            stripethickness=5,
            metersize=120,
            amounttotal=200.0,
            amountused=self.gravity.get(),
            amountformat="{:.2f}",
            interactive=True,
        )
        self.gravity_meter.grid(row=0, column=0, padx=10, pady=10, sticky=NSEW)
        self.gravity_meter.amountusedvar.trace("w", self.on_gravity_change) # Checks for change in the meter value

        tb.Separator(inner_playback_frame, orient=HORIZONTAL, bootstyle="info").grid(row=1, column=0, sticky=EW)

        # Time frame
        time_frame = tb.Frame(inner_playback_frame)
        time_frame.grid(row=2, column=0, padx=10, pady=10, sticky=EW)
        time_frame.columnconfigure(0, weight=1) # 2X1 grid
        time_frame.rowconfigure(0, weight=1)
        time_frame.rowconfigure(1, weight=1)
        
        # 2. Time Elapsed Progress Bar
        self.time_label = tb.Label(time_frame, text="Time Elapsed: 0.0s", bootstyle="info")
        self.time_label.grid(row=0, column=0, padx=10, pady=5, sticky=EW)
        self.time_bar = tb.Progressbar(time_frame, bootstyle="success-striped", maximum=self.time_max, value=0)
        self.time_bar.grid(row=1, column=0, padx=10, pady=10, sticky=EW)

        tb.Separator(inner_playback_frame, orient=VERTICAL, bootstyle="info").grid(row=0, column=1, rowspan=3, sticky=NS)
    
        # Playback buttons frame
        playback_buttons_frame = tb.Frame(inner_playback_frame)
        playback_buttons_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=10, sticky=NSEW)
        playback_buttons_frame.columnconfigure(0, weight=1)
        
        # Vertical frame for buttons
        for i in range(len(self.buttons_info)): playback_buttons_frame.rowconfigure(i, weight=1)
        
        # 3. Playback buttons
        for i, (text, color) in enumerate(self.buttons_info):
            self.button_color[text] = color
            btn = tb.Button(
                playback_buttons_frame,
                text=text,
                bootstyle=f"{color}-outline",
                command=lambda name=text, col=color: self.on_button_click(name, col)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=5, pady=4)
            self.buttons[text] = btn

    def create_controls(self):
        # Controls frame
        self.control_frame = tb.Labelframe(self.main_frame, text="Parameter Controls", bootstyle="danger")
        self.control_frame.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky=NSEW)

        # Inner controls frame
        inner_control_frame = tb.Frame(self.control_frame)
        inner_control_frame.pack(fill=BOTH, expand=YES)
        
        # 1X2 grid inside inner controls frame
        for i in range(2): inner_control_frame.columnconfigure(i, weight=1)
        inner_control_frame.rowconfigure(0, weight=1)

        # 1. Parameters for Bob
        param_frame_1 = tb.Labelframe(inner_control_frame, bootstyle="primary", text="Characteristics")
        param_frame_1.grid(row=0, column=0, padx=5, pady=10, sticky=NSEW)
        for i in range(4): param_frame_1.rowconfigure(i, weight=1)
        param_frame_1.columnconfigure(0, weight=0)
        param_frame_1.columnconfigure(1, weight=1)

        self.add_param_1(frame=param_frame_1, row=0, name="m1 (kg)", variable=self.m1_bob1)
        self.add_param_1(frame=param_frame_1, row=1, name="m2 (kg)", variable=self.m2_bob1)
        self.add_param_1(frame=param_frame_1, row=2, name="l1 (m)", variable=self.l1_bob1)
        self.add_param_1(frame=param_frame_1, row=3, name="l2 (m)", variable=self.l2_bob1)

        # 2. State Vectors for Bob 
        param_frame_2 = tb.Labelframe(inner_control_frame, bootstyle="primary", text="State Vectors")
        param_frame_2.grid(row=0, column=1, padx=5, pady=10, sticky=NSEW)
        for i in range(4): param_frame_2.rowconfigure(i, weight=1)
        param_frame_2.columnconfigure(0, weight=0)
        param_frame_2.columnconfigure(1, weight=1)

        self.add_param_2(frame=param_frame_2, row=0, name="θ1 (°)", variable=self.θ1_bob1)
        self.add_param_2(frame=param_frame_2, row=1, name="θ2 (°)", variable=self.θ2_bob1)
        self.add_param_2(frame=param_frame_2, row=2, name="ω1 (°/s)", variable=self.ω1_bob1)
        self.add_param_2(frame=param_frame_2, row=3, name="ω2 (°/s)", variable=self.ω2_bob1)

    # ---------- Helpers ----------
    
    def change_theme(self, event=None):
        """Change the theme of the application."""
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)

    def on_gravity_change(self, event=None, *args):
        """Updates self.gravity when meter changes."""
        new_val = float(self.gravity_meter.amountusedvar.get())
        self.gravity.set(new_val)

    def on_button_click(self, name, color):
        if self.active_button and self.active_button in self.buttons:
            prev_name = self.active_button
            prev_color = self.button_color.get(prev_name, "secondary")
            self.buttons[prev_name].configure(bootstyle=f"{prev_color}-outline")
        self.buttons[name].configure(bootstyle=f"{color}")
        self.active_button = name

        if name == "Start": self.start_time()
        elif name == "Pause": self.stop_time()
        elif name == "Reset": self.reset_time()
        elif name == "Default":
            self.m1_bob1.set(1.0)
            self.m2_bob1.set(1.0)
            self.l1_bob1.set(1.0)
            self.l2_bob1.set(1.0)
            self.θ1_bob1.set(90.0)
            self.θ2_bob1.set(120.0)
            self.ω1_bob1.set(0.0)
            self.ω2_bob1.set(0.0)
            self.gravity.set(98.1)
            self.gravity_meter.configure(amountused=98.1)
            for name, var in zip(
                ["m1 (kg)", "m2 (kg)", "l1 (m)", "l2 (m)", "θ1 (°)", "θ2 (°)", "ω1 (°/s)", "ω2 (°/s)"],
                [self.m1_bob1, self.m2_bob1, self.l1_bob1, self.l2_bob1, self.θ1_bob1, self.θ2_bob1, self.ω1_bob1, self.ω2_bob1]
            ):
                self.update_label(name, var)
            self.update_pendulum_preview()

    def clear_active(self):
        """Clear the active button highlight."""
        if self.active_button:
            name = self.active_button
            color = self.button_color.get(name, "secondary")
            self.buttons[name].configure(bootstyle=f"{color}-outline")
            self.active_button = None

    def add_param_1(self, frame, row, name, variable):
        """Add a parameter slider for physical characteristics like mass & length."""
        label = tb.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky=W, padx=5, pady=2)
        self.labels[name] = label
        scale = tb.Scale(
            frame,
            from_=0, to=10.0,
            variable=variable,
            command=lambda val, n=name, v=variable: (self.update_label(n, v), self.update_pendulum_preview())
        )
        scale.grid(row=row, column=1, sticky=EW, padx=(10, 20), pady=2)
        self.scales.append(scale)

    def add_param_2(self, frame, row, name, variable):
        """Add a parameter slider for state vectors, θ & ω."""
        label = tb.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky=W, padx=5, pady=2)
        self.labels[name] = label
        scale = tb.Scale(
            frame,
            from_=-180.0, to=180.0,
            variable=variable,
            command=lambda val, n=name, v=variable: (self.update_label(n, v), self.update_pendulum_preview())
        )
        scale.grid(row=row, column=1, sticky=EW, padx=(10, 20), pady=2)
        self.scales.append(scale)

    def update_label(self, name, var):
        """Update the label text for a given parameter."""
        self.labels[name].config(text=f"{name}: {var.get():.2f}")

    # ---------- Playback controls ----------
    
    def start_time(self):
        """Compute, then start the animation."""
        # If finished running, restart from beginning
        if self.frame_index >= self.total_frames or not self.data_ready:
            self.calculate_states()

        # Reset progress/time if needed
        if self.frame_index >= self.total_frames:
            self.frame_index = 0
            self.time = 0.0
            self.time_bar["value"] = 0
            self.time_label.configure(text=f"Time Elapsed: {self.time:.2f}s")
            self.anim_in_process = False

        # Start animation if not running
        if not self.running:
            self.running = True
            self.disable_sliders()
            self.set_default_state("disabled")
            self.set_gravity_state(False)
            self.start_animation()


    def stop_time(self):
        """Pause the animation"""
        if self.running:
            self.running = False
            self.anim.pause()
            # if self.anim_in_process: self.anim.pause()   
            
            if self.after_id:
                self.after_cancel(self.after_id)
                self.after_id = None

    def reset_time(self):
        """Reset everything"""
        self.stop_time()
        self.time = 0.0
        self.frame_index = 0
        self.total_frames = 0
        self.data_ready = False

        # Reset time bar
        self.time_bar["value"] = 0
        # Set maximum to default = 30.0s
        self.time_bar["maximum"] = self.time_max
        self.time_label.configure(text="Time Elapsed: 0.0s")

        # Clear arrays
        self.θ1_arr = self.θ2_arr = np.array([1])
        self.ω1_arr = self.ω2_arr = np.array([1])
        self.x1_arr = self.y1_arr = np.array([1])
        self.x2_arr = self.y2_arr = np.array([1])
        self.t_values = None
        self.results = None
        
        # Stop animation
        try: self.anim.event_source.stop()
        except Exception: pass
        self.anim_in_process = False

        # Clear plot
        self.bob1.set_data([], [])
        self.bob2.set_data([], [])
        self.trail1.set_data([], [])
        self.trail2.set_data([], [])
        self.angle1.set_data([], [])
        self.angle2.set_data([], [])
        self.phase1.set_data([], [])
        self.phase2.set_data([], [])
        self.canvas.draw_idle()
        
        # Draw preview
        self.update_pendulum_preview()
        
        # Re-enable buttons and sliders
        self.enable_sliders()
        self.set_calculate_state("normal")
        self.set_default_state("normal") 
        self.set_gravity_state(True)

        print("Simulation reset.")

    def disable_sliders(self):
        """Disable all sliders."""
        for s in self.scales:
            try: s.configure(state="disabled")
            except Exception: pass

    def enable_sliders(self):
        """Enable all sliders."""
        for s in self.scales:
            try: s.configure(state="normal")
            except Exception: pass

    def set_calculate_state(self, state):
        """Enable or disable the Calculate button."""
        calc_btn = self.buttons.get("Calculate")
        if calc_btn: calc_btn.configure(state=state)
            
    def set_default_state(self, state):
        """Enable or disable the Default button."""
        default_btn = self.buttons.get("Default")
        if default_btn: default_btn.configure(state=state)

    def set_gravity_state(self, state):
        """Enable or disable the Gravity Meter."""
        if self.gravity_meter: self.gravity_meter.configure(interactive=state)

    # ---------- Calculation ----------
    
    def calculate_states(self):
        """Compute full trajectories and store arrays — no animation starts here."""
        print("Calculate pressed. Computing states...")
        # call your simulation util (keeps your original signature)
        self.t_values, self.results = simulate_double_pendulum(
            self.θ1_bob1.get() * np.pi / 180,
            self.θ2_bob1.get() * np.pi / 180,
            self.ω1_bob1.get() * np.pi / 180,
            self.ω2_bob1.get() * np.pi / 180,
            self.m1_bob1.get(),
            self.m2_bob1.get(),
            self.l1_bob1.get(),
            self.l2_bob1.get(),
            self.time_max, self.dt,
            0.1 * self.gravity.get()
        )
        # Bookkeeping
        self.total_frames = len(self.t_values)
        self.frame_index = 0
        self.time = 0.0
        
        try: # set the progress bar maximum to final time
            self.time_bar["maximum"] = float(self.t_values[-1])
        except Exception:
            self.time_bar["maximum"] = self.time_max
        self.time_bar["value"] = 0

        # Unpack all values into arrays
        self.θ1_arr, self.θ2_arr = self.results[:, 0], self.results[:, 1]
        self.θ1_deg_arr, self.θ2_deg_arr = np.degrees(self.θ1_arr), np.degrees(self.θ2_arr)
        self.ω1_arr, self.ω2_arr = self.results[:, 2], self.results[:, 3]
        self.x1_arr, self.y1_arr = position_bob1(self.θ1_arr, self.l1_bob1.get())
        self.x2_arr, self.y2_arr = position_bob2(self.x1_arr, self.y1_arr, self.θ2_arr, self.l2_bob1.get())
        self.vx1_arr, self.vy1_arr = velocity_bob1(self.θ1_arr, self.ω1_arr, self.l1_bob1.get())
        self.vx2_arr, self.vy2_arr = velocity_bob2(self.vx1_arr, self.vy1_arr, self.θ2_arr, self.ω2_arr, self.l2_bob1.get())

        # Create large arrays for animation
        self.x1_arr_anim = []
        self.y1_arr_anim = []
        self.x2_arr_anim = []
        self.y2_arr_anim = []
        for i in range(self.total_frames):
            self.x1_arr_anim.append(self.x1_arr[:i+1])
            self.y1_arr_anim.append(self.y1_arr[:i+1])
            self.x2_arr_anim.append(self.x2_arr[:i+1])
            self.y2_arr_anim.append(self.y2_arr[:i+1])
        
        self.θ1_deg_arr_anim = []
        self.θ2_deg_arr_anim = []
        self.t_values_anim = []
        for i in range(self.total_frames):
            self.θ1_deg_arr_anim.append(self.θ1_deg_arr[:i+1])
            self.θ2_deg_arr_anim.append(self.θ2_deg_arr[:i+1])
            self.t_values_anim.append(self.t_values[:i+1])
            
        self.vx1_arr_anim = []
        self.vy1_arr_anim = []
        self.vx2_arr_anim = []
        self.vy2_arr_anim = []
        for i in range(self.total_frames):
            self.vx1_arr_anim.append(self.vx1_arr[:i+1])
            self.vy1_arr_anim.append(self.vy1_arr[:i+1])
            self.vx2_arr_anim.append(self.vx2_arr[:i+1])
            self.vy2_arr_anim.append(self.vy2_arr[:i+1])

        # Mark Ready (indication to user), by drawing only first frame
        self.data_ready = True
        
        # Draws the first frame
        if self.total_frames > 0:
            # Double pendulum
            self.bob1.set_data([0, self.x1_arr[0]], [0, self.y1_arr[0]])
            self.bob2.set_data([self.x1_arr[0], self.x2_arr[0]], [self.y1_arr[0], self.y2_arr[0]])
            limit1 = self.l1_bob1.get() + self.l2_bob1.get() + 0.5
            self.ax1.set_xlim(-limit1, limit1)
            self.ax1.set_ylim(-limit1, limit1)
            
            # Position (t is fixed)
            max_angle = np.max(np.abs(np.concatenate([self.θ1_deg_arr, self.θ2_deg_arr])))
            buffer = 90.0 # for y-spacing
            limit2_angle = np.ceil((max_angle + buffer) / 10.0) * 10.0 
            self.ax2.set_ylim(-limit2_angle, limit2_angle)
            self.ax2.set_aspect(abs(self.time_max / (2 * limit2_angle)))  # computed aspect ratio
            
            # Phase
            self.ax3.set_title(r"Phase Space, $v_x(\mathrm{ms}^{-1})$ against $x(m)$", fontsize=12)
            limit3_position = max(np.maximum(np.abs(self.x1_arr), np.abs(self.x2_arr)))
            limit3_velocity = max(np.maximum(np.abs(self.vx1_arr), np.abs(self.vx2_arr)))
            limit3 = max(limit3_position, limit3_velocity)
            self.ax3.set_xlim(-limit3*1.1, limit3*1.1)
            self.ax3.set_ylim(-limit3*1.1, limit3*1.1)
            self.ax3.set_aspect('equal', adjustable='box')

        else: # Clear plot if there are no data
            self.bob1.set_data([], [])
            self.bob2.set_data([], [])
            self.trail1.set_data([], [])
            self.trail2.set_data([], [])
            self.angle1.set_data([], [])
            self.angle2.set_data([], [])
            self.phase1.set_data([], [])
            self.phase2.set_data([], [])
            
        self.canvas.draw_idle()

        print(f"Gravity {self.gravity.get():.2f} m/s²")
        print(f"Calculated {self.total_frames} frames. Ready to start.")
        
    def update_pendulum_preview(self):
        """Instantly update the pendulum diagram when any slider (θ₁, θ₂, l₁, l₂) moves."""
        # Get current slider values
        θ1 = np.radians(self.θ1_bob1.get())
        θ2 = np.radians(self.θ2_bob1.get())
        l1 = self.l1_bob1.get()
        l2 = self.l2_bob1.get()

        # Compute coordinates of bobs
        x1 = l1 * np.sin(θ1)
        y1 = -l1 * np.cos(θ1)
        x2 = x1 + l2 * np.sin(θ2)
        y2 = y1 - l2 * np.cos(θ2)

        # Update the line objects
        self.bob1.set_data([0, x1], [0, y1])
        self.bob2.set_data([x1, x2], [y1, y2])

        # Auto-adjust axis limits to fit both rods
        limit = l1 + l2 + 0.5
        self.ax1.set_xlim(-limit, limit)
        self.ax1.set_ylim(-limit, limit)

        # Refresh canvas without lag
        self.canvas.draw_idle()

        
    # --- Animation ---
    
    def start_animation(self):
        """
        Create and start the FuncAnimation.
        """
        # Stops if not running
        if not self.running:
            return
        
        # Animation
        if self.frame_index < self.total_frames:
            # Resume paused (existing) animation
            if self.anim_in_process: self.anim.resume()
            # Starts new animation if there are no existing
            else: 
                self.anim_in_process = True
                self.anim = FuncAnimation(
                    self.fig,
                    self.update_animation, # Function to call for each frame
                    init_func=self.init_animation, # Function to call at the start
                    frames=self.total_frames, 
                    interval=self.dt * 1000, # Milliseconds between frames
                    blit=True
                )
        # Finished running animation
        else:
            self.running = False
            self.after_id = None
            self.enable_sliders()
            self.set_calculate_state("normal")
            self.set_default_state("normal") 
            self.set_gravity_state(True)
            self.update_pendulum_preview()
            self.anim_in_process = False
            print("Animation finished.")

    def update_animation(self, frame):
        """
        Update function for the animation.
        This is called for each new frame.
        """
        t_vals = self.t_values_anim[frame]
        
        x1 = self.x1_arr_anim[frame]
        y1 = self.y1_arr_anim[frame]
        x2 = self.x2_arr_anim[frame]
        y2 = self.y2_arr_anim[frame]
        ang1 = self.θ1_deg_arr_anim[frame]
        ang2 = self.θ2_deg_arr_anim[frame]
        vx1 = self.vx1_arr_anim[frame]
        vx2 = self.vx2_arr_anim[frame]
        
        # Update plots
        self.bob1.set_data([0, x1[-1]], [0, y1[-1]])
        self.bob2.set_data([x1[-1], x2[-1]], [y1[-1], y2[-1]])
        self.trail1.set_data(x1, y1)
        self.trail2.set_data(x2, y2)
        self.angle1.set_data(t_vals, ang1)
        self.angle2.set_data(t_vals, ang2)
        self.phase1.set_data(x1, vx1)
        self.phase2.set_data(x2, vx2)
        
        # --- update time display (new) ---
        current_time = self.t_values[frame]
        self.time_bar["value"] = current_time
        self.time_label.configure(text=f"Time Elapsed: {current_time:.2f}s")
        # self.time_label.update_idletasks()  # force redraw of UI
        
        # Return the artist that has been modified
        return (self.bob1, self.bob2, self.trail1, self.trail2, self.angle1, self.angle2, self.phase1, self.phase2)
    
    def init_animation(self):
        """
        Initialization function for the animation.
        Sets the line data to empty.
        """
        self.bob1.set_data([], [])
        self.bob2.set_data([], [])
        self.trail1.set_data([], [])
        self.trail2.set_data([], [])
        self.angle1.set_data([], [])
        self.angle2.set_data([], [])
        self.phase1.set_data([], [])
        self.phase2.set_data([], [])

        return (self.bob1, self.bob2, self.trail1, self.trail2, self.angle1, self.angle2, self.phase1, self.phase2)

if __name__ == "__main__":
    root = tb.Window("Double Pendulum Simulation (30s)", "morph", resizable=(True, True))
    DoublePendulumApp(root)
    root.mainloop()
