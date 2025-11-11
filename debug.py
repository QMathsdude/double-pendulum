import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import DoubleVar

class DoublePendulumApp(tb.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.pack(fill=BOTH, expand=YES, padx=20, pady=10)

        # Tkinter style
        self.style = tb.Style()

        # Pendulum parameters
        self.m1_bob1 = DoubleVar(value=1.0)
        self.m2_bob1 = DoubleVar(value=1.0)
        self.l1_bob1 = DoubleVar(value=1.0)
        self.l2_bob1 = DoubleVar(value=1.0)
        self.θ1_bob1 = DoubleVar(value=90.0)
        self.θ2_bob1 = DoubleVar(value=120.0)
        self.ω1_bob1 = DoubleVar(value=0.0)
        self.ω2_bob1 = DoubleVar(value=0.0)

        # --- Layout setup ---
        self.create_header()
        self.create_main_area()
        self.create_controls()

    # -------------------------------------------------------
    def create_header(self):
        header_frame = tb.Frame(self)
        header_frame.pack(fill=X, pady=(0, 10))  # stays at top, independent of grid

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

    # -------------------------------------------------------
    def create_main_area(self):
        """Main grid area for graphs and other content"""
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)

        # Configure a 3x3 grid inside this frame
        for i in range(3):
            self.main_frame.columnconfigure(i, weight=1)
        for j in range(3):
            self.main_frame.rowconfigure(j, weight=1)

        # Example placeholder widget
        tb.Label(
            self.main_frame,
            text="Graph area (placeholder)",
            bootstyle="secondary",
            anchor="center"
        ).grid(row=1, column=1, sticky=NSEW, padx=10, pady=10)

    # -------------------------------------------------------
    def create_controls(self):
        """Playback controls at the bottom"""
        playback_frame = tb.Labelframe(self, text="Playback Controls", bootstyle="info")
        playback_frame.pack(fill=X, pady=(10, 0))

        for text, style in [("Play", "success"), ("Pause", "warning"), ("Stop", "danger")]:
            btn = tb.Button(playback_frame, text=text, bootstyle=style)
            btn.pack(side=LEFT, padx=5, pady=5)

    # -------------------------------------------------------
    def change_theme(self, event=None):
        new_theme = self.theme_dropdown.get()
        self.style.theme_use(new_theme)


if __name__ == "__main__":
    root = tb.Window("Double Pendulum Simulation (30s)", "morph", resizable=(True, True))
    DoublePendulumApp(root)
    root.mainloop()
