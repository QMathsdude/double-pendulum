from tkinter import DoubleVar, StringVar
from tkinter.messagebox import YES

import ttkbootstrap as tb
from ttkbootstrap.constants import *

import numpy as np
from scipy.linalg import solve

from utils import position_bob1, velocity_bob1, position_bob2, velocity_bob2, simulate_double_pendulum

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

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
        
        # Arrays (start as None)
        self.θ1_arr = self.θ2_arr = None
        self.ω1_arr = self.ω2_arr = None
        self.x1_arr = self.y1_arr = None
        self.x2_arr = self.y2_arr = None
        self.vx1_arr = self.vy1_arr = None
        self.vx2_arr = self.vy2_arr = None
        self.t_values = None
        self.results = None

        # animation / playback state
        self.anim = None
        self.frame_index = 0
        self.total_frames = 0
        self.data_ready = False

        # time control
        self.time = 0.0
        self.dt = 0.01
        self.running = False
        self.after_id = None

        # store slider widgets so enable/disable is robust
        self.scales = []

        # ttkbootstrap style
        self.style = tb.Style()

        # buttons bookkeeping
        self.active_button = None
        self.buttons = {}
        self.button_color = {}
        self.buttons_info = [
            ("Calculate", "info"),
            ("Start", "success"),
            ("Pause", "warning"),
            ("Reset", "danger"),
            ("Default", "secondary")
        ]

        # labels
        self.labels = {}

        # build UI
        self.create_header()
        self.create_main()
        self.create_graphs()
        self.create_playback()
        self.create_controls()

    # ---------- GUI creation ----------
    def create_header(self):
        header_frame = tb.Frame(self)
        header_frame.pack(fill=X, pady=(10, 10))

        header_label = tb.Label(
            header_frame,
            text="Double Pendulum Simulation (30s)",
            font=("Liberation Sans", 24, "bold"),
            bootstyle="info"
        )
        header_label.pack(side=LEFT, padx=(5, 10))

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
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)

        for i in range(3):
            self.main_frame.columnconfigure(i, weight=1)
        for j in range(3):
            if j != 1:
                self.main_frame.rowconfigure(j, weight=0)
            else:
                self.main_frame.rowconfigure(j, weight=1)

        tb.Separator(self.main_frame, orient=HORIZONTAL, bootstyle="info").grid(row=0, column=0, columnspan=3, sticky=EW)

    def create_graphs(self):
        self.graph_frame = tb.Labelframe(self.main_frame, text="Visualization", bootstyle="success")
        self.graph_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=10, sticky=NSEW)

        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        limits = self.l1_bob1.get() + self.l2_bob1.get() + 0.5
        self.ax.set_xlim(-limits, limits)
        self.ax.set_ylim(-limits, limits)
        self.ax.set_aspect('equal')
        self.ax.grid(ls=':', color='gray', alpha=0.7)

        (self.bob1,) = self.ax.plot([], [], ms=5, mfc='crimson', mec='crimson', marker='o', ls='--', lw=0.5,color='black', zorder=2)
        (self.bob2,) = self.ax.plot([], [], ms=5, mfc='royalblue', mec='royalblue', marker='o', ls='--', lw=0.5, color='green', zorder=1)

        (self.trail1,) = self.ax.plot([], [], color='crimson', ls="--", lw=0.5, alpha=0.5, zorder=0)
        (self.trail2,) = self.ax.plot([], [], color='royalblue', ls="--", lw=0.5, alpha=0.5, zorder=0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=3, sticky=NSEW, pady=10)

    def create_playback(self):
        self.playback_frame = tb.Labelframe(self.main_frame, text="Playback Controls", bootstyle="info")
        self.playback_frame.grid(row=2, column=0, pady=10, padx=5, sticky=NSEW)

        inner = tb.Frame(self.playback_frame)
        inner.pack(fill=BOTH, expand=YES)
        for i in range(3):
            inner.columnconfigure(i, weight=1)
        for j in range(3):
            inner.rowconfigure(j, weight=0)
        inner.rowconfigure(0, weight=0)

        self.gravity_meter = tb.Meter(
            inner,
            bootstyle="primary",
            subtext="Gravity",
            subtextstyle="primary",
            textright="(m/s²)",
            metertype="semi",
            stripethickness=5,
            amounttotal=200.0,
            amountused=self.gravity.get(),
            amountformat="{:.2f}",
            interactive=True,
        )
        self.gravity_meter.amountusedvar.trace("w", self.on_gravity_change)
        # self.gravity_meter.bind("<B1-Motion>", self.on_gravity_change) # live changes when sliding
        # self.gravity_meter.bind("<ButtonRelease-1>", self.on_gravity_change) # final change on release
        self.gravity_meter.grid(row=0, column=0, padx=10, pady=10, sticky=NSEW)

        tb.Separator(inner, orient=HORIZONTAL, bootstyle="info").grid(row=1, column=0, sticky=EW)

        time_frame = tb.Frame(inner)
        time_frame.grid(row=2, column=0, padx=10, pady=10, sticky=EW)
        time_frame.columnconfigure(0, weight=1)
        time_frame.rowconfigure(0, weight=1)
        time_frame.rowconfigure(1, weight=1)
        self.time_label = tb.Label(time_frame, text="Time Elapsed: 0.0s", bootstyle="info")
        self.time_label.grid(row=0, column=0, padx=10, pady=5, sticky=EW)
        self.time_bar = tb.Progressbar(time_frame, bootstyle="success-striped", maximum=30, value=0)
        self.time_bar.grid(row=1, column=0, padx=10, pady=10, sticky=EW)

        tb.Separator(inner, orient=VERTICAL, bootstyle="info").grid(row=0, column=1, rowspan=3, sticky=NS)

        playback_buttons_frame = tb.Frame(inner)
        playback_buttons_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=10, sticky=NSEW)
        playback_buttons_frame.columnconfigure(0, weight=1)
        for i in range(len(self.buttons_info)):
            playback_buttons_frame.rowconfigure(i, weight=1)

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
        self.control_frame = tb.Labelframe(self.main_frame, text="Parameter Controls", bootstyle="danger")
        self.control_frame.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky=NSEW)

        inner_control_frame = tb.Frame(self.control_frame)
        inner_control_frame.pack(fill=BOTH, expand=YES)
        for i in range(2):
            inner_control_frame.columnconfigure(i, weight=1)
        inner_control_frame.rowconfigure(0, weight=1)

        bob1_frame = tb.Labelframe(inner_control_frame, bootstyle="primary", text="Characteristics")
        bob1_frame.grid(row=0, column=0, padx=5, pady=10, sticky=NSEW)
        for i in range(4):
            bob1_frame.rowconfigure(i, weight=1)
        bob1_frame.columnconfigure(0, weight=0)
        bob1_frame.columnconfigure(1, weight=1)

        self.add_param1(frame=bob1_frame, row=0, name="m1 (kg)", variable=self.m1_bob1)
        self.add_param1(frame=bob1_frame, row=1, name="m2 (kg)", variable=self.m2_bob1)
        self.add_param1(frame=bob1_frame, row=2, name="l1 (m)", variable=self.l1_bob1)
        self.add_param1(frame=bob1_frame, row=3, name="l2 (m)", variable=self.l2_bob1)

        bob2_frame = tb.Labelframe(inner_control_frame, bootstyle="primary", text="State Vectors")
        bob2_frame.grid(row=0, column=1, padx=5, pady=10, sticky=NSEW)
        for i in range(4):
            bob2_frame.rowconfigure(i, weight=1)
        bob2_frame.columnconfigure(0, weight=0)
        bob2_frame.columnconfigure(1, weight=1)

        self.add_param2(frame=bob2_frame, row=0, name="θ1 (°)", variable=self.θ1_bob1)
        self.add_param2(frame=bob2_frame, row=1, name="θ2 (°)", variable=self.θ2_bob1)
        self.add_param2(frame=bob2_frame, row=2, name="ω1 (°/s)", variable=self.ω1_bob1)
        self.add_param2(frame=bob2_frame, row=3, name="ω2 (°/s)", variable=self.ω2_bob1)

    # ---------- Helpers ----------
    
    def change_theme(self, event=None):
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)

    def on_gravity_change(self, event=None, *args):
        new_val = float(self.gravity_meter.amountusedvar.get())
        self.gravity.set(new_val)

    def on_button_click(self, name, color):
        if self.active_button and self.active_button in self.buttons:
            prev_name = self.active_button
            prev_color = self.button_color.get(prev_name, "secondary")
            self.buttons[prev_name].configure(bootstyle=f"{prev_color}-outline")
        self.buttons[name].configure(bootstyle=f"{color}")
        self.active_button = name

        if name == "Calculate":
            self.calculate_states()
        elif name == "Start":
            self.start_time()
        elif name == "Pause":
            self.stop_time()
        elif name == "Reset":
            self.reset_time()
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
            # Manually update some widgets
            self.gravity_meter.configure(amountused=98.1)
            for name, var in zip(
                        ["m1 (kg)", "m2 (kg)", "l1 (m)", "l2 (m)", "θ1 (°)", "θ2 (°)", "ω1 (°/s)", "ω2 (°/s)"],
                        [self.m1_bob1, self.m2_bob1, self.l1_bob1, self.l2_bob1, self.θ1_bob1, self.θ2_bob1, self.ω1_bob1, self.ω2_bob1]
                    ):
                        self.update_label(name, var)


    def clear_active(self):
        if self.active_button:
            name = self.active_button
            color = self.button_color.get(name, "secondary")
            self.buttons[name].configure(bootstyle=f"{color}-outline")
            self.active_button = None

    def add_param1(self, frame, row, name, variable):
        label = tb.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky=W, padx=5, pady=2)
        self.labels[name] = label
        scale = tb.Scale(
            frame,
            from_=0, to=10.0,
            variable=variable,
            command=lambda val, n=name, v=variable: self.update_label(n, v)
        )
        scale.grid(row=row, column=1, sticky=EW, padx=(10, 20), pady=2)
        self.scales.append(scale)

    def add_param2(self, frame, row, name, variable):
        label = tb.Label(frame, text=f"{name}: {variable.get():.2f}")
        label.grid(row=row, column=0, sticky=W, padx=5, pady=2)
        self.labels[name] = label
        scale = tb.Scale(
            frame,
            from_=-180.0, to=180.0,
            variable=variable,
            command=lambda val, n=name, v=variable: self.update_label(n, v)
        )
        scale.grid(row=row, column=1, sticky=EW, padx=(10, 20), pady=2)
        self.scales.append(scale)

    def update_label(self, name, var):
        self.labels[name].config(text=f"{name}: {var.get():.2f}")

    # ---------- Playback controls ----------
    def start_time(self):
        """Start or resume the animation"""
        if not self.data_ready:
            print("Please press Calculate first.")
            return

        # If we've already finished, restart from beginning
        if self.frame_index >= self.total_frames:
            self.frame_index = 0
            self.time = 0.0
            self.time_bar["value"] = 0
            self.time_label.configure(text=f"Time Elapsed: {self.time:.2f}s")

        if not self.running:
            self.running = True
            self.disable_sliders()
            self.set_calculate_state("disabled")
            self.set_default_state("disabled")
            self.set_gravity_state(False)
            self.animate_next_frame()

    def stop_time(self):
        """Pause the animation"""
        if self.running:
            self.running = False
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

        # reset UI
        self.time_bar["value"] = 0
        # set maximum back to default 30
        self.time_bar["maximum"] = 30
        self.time_label.configure(text="Time Elapsed: 0.0s")

        # clear arrays
        self.t_values = None
        self.results = None
        self.θ1_arr = self.θ2_arr = None
        self.ω1_arr = self.ω2_arr = None
        self.x1_arr = self.y1_arr = None
        self.x2_arr = self.y2_arr = None

        # clear plot
        self.bob1.set_data([], [])
        self.bob2.set_data([], [])
        self.trail1.set_data([], [])
        self.trail2.set_data([], [])
        self.canvas.draw_idle()

        self.enable_sliders()
        self.set_calculate_state("normal")
        self.set_default_state("normal") 
        self.set_gravity_state(True)

        print("Simulation reset.")

    def animate_next_frame(self):
        """Manual per-frame animation using Tk after()"""
        # Stops animation if not running
        if not self.running:
            return

        # Draws next frame
        i = self.frame_index # Trail index
        if self.frame_index < self.total_frames:
            x1, y1 = self.x1_arr[i], self.y1_arr[i]
            x2, y2 = self.x2_arr[i], self.y2_arr[i]

            # update rods
            self.bob1.set_data([0, x1], [0, y1])
            self.bob2.set_data([x1, x2], [y1, y2])

            # update trails directly from precomputed arrays
            self.trail1.set_data(self.x1_arr[:i],self.y1_arr[:i])
            self.trail2.set_data(self.x2_arr[:i],self.y2_arr[:i])

            self.canvas.draw_idle()

            # update time
            self.time = float(self.t_values[i])
            self.time_bar["value"] = self.time
            self.time_label.configure(text=f"Time Elapsed: {self.time:.2f}s")

            self.frame_index += 1
            self.after_id = self.after(int(self.dt * 1000), self.animate_next_frame)
        else:
            # finished
            self.running = False
            self.after_id = None
            self.enable_sliders()
            self.set_calculate_state("normal")
            self.set_default_state("normal") 
            self.set_gravity_state(True)
            print("Animation finished.")

    def disable_sliders(self):
        """Disable all sliders."""
        for s in self.scales:
            try:
                s.configure(state="disabled")
            except Exception:
                pass

    def enable_sliders(self):
        """Enable all sliders."""
        for s in self.scales:
            try:
                s.configure(state="normal")
            except Exception:
                pass

    def set_calculate_state(self, state):
        """Enable or disable the Calculate button."""
        calc_btn = self.buttons.get("Calculate")
        if calc_btn:
            calc_btn.configure(state=state)
            
    def set_default_state(self, state):
        """Enable or disable the Default button."""
        default_btn = self.buttons.get("Default")
        if default_btn:
            default_btn.configure(state=state)

    def set_gravity_state(self, state):
        """Enable or disable the Gravity Meter."""
        if self.gravity_meter:
            self.gravity_meter.configure(interactive=state)

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
            30, 0.01,
            0.1 * self.gravity.get()
        )

        # unpack
        self.θ1_arr, self.θ2_arr = self.results[:, 0], self.results[:, 1]
        self.ω1_arr, self.ω2_arr = self.results[:, 2], self.results[:, 3]
        self.x1_arr, self.y1_arr = position_bob1(self.θ1_arr, self.l1_bob1.get())
        self.x2_arr, self.y2_arr = position_bob2(self.x1_arr, self.y1_arr, self.θ2_arr, self.l2_bob1.get())
        self.vx1_arr, self.vy1_arr = velocity_bob1(self.θ1_arr, self.ω1_arr, self.l1_bob1.get())
        self.vx2_arr, self.vy2_arr = velocity_bob2(self.vx1_arr, self.vy1_arr, self.θ2_arr, self.ω2_arr, self.l2_bob1.get())

        # bookkeeping
        self.total_frames = len(self.t_values)
        self.frame_index = 0
        self.time = 0.0
        # set the progress bar maximum to final time
        try:
            self.time_bar["maximum"] = float(self.t_values[-1])
        except Exception:
            self.time_bar["maximum"] = 30
        self.time_bar["value"] = 0

        # mark ready and draw first frame so user sees result immediately
        self.data_ready = True
        if self.total_frames > 0:
            self.bob1.set_data([0, self.x1_arr[0]], [0, self.y1_arr[0]])
            self.bob2.set_data([self.x1_arr[0], self.x2_arr[0]], [self.y1_arr[0], self.y2_arr[0]])
            limits = self.l1_bob1.get() + self.l2_bob1.get() + 0.5
            self.ax.set_xlim(-limits, limits)
            self.ax.set_ylim(-limits, limits)
        else:
            self.bob1.set_data([], [])
            self.bob2.set_data([], [])
        self.canvas.draw_idle()

        print(f"Gravity {self.gravity.get():.2f} m/s²")
        print(f"Calculated {self.total_frames} frames. Ready to start.")

    # leftover (not used by this flow but harmless)
    def animate_frame(self, i):
        self.bob1.set_data([0, self.x1_arr[i]], [0, self.y1_arr[i]])
        self.bob2.set_data([self.x1_arr[i], self.x2_arr[i]], [self.y1_arr[i], self.y2_arr[i]])
        return self.bob1, self.bob2

if __name__ == "__main__":
    root = tb.Window("Double Pendulum Simulation (30s)", "morph", resizable=(True, True))
    DoublePendulumApp(root)
    root.mainloop()
