import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

# --- Main Application Class ---
class App:
    def __init__(self, root):
        """
        Initialize the main application.
        """
        self.root = root
        self.root.title("Matplotlib Animation in Tkinter")
        self.root.geometry("800x600")

        # Create a frame for the plot
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # --- Matplotlib Setup ---
        # Create a Figure and an Axes
        self.fig, self.ax = plt.subplots()

        # Create the initial line object with empty data
        # We will update this line object in the animation
        self.line, = self.ax.plot([], [], 'r-') # 'r-' for a red line

        # Set up the plot limits
        self.ax.set_xlim(0, 4 * np.pi)
        self.ax.set_ylim(-1.2, 1.2)
        self.ax.set_title("Moving Sine Wave")
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")
        self.ax.grid(True)

        # --- Pre-calculate all data ---
        # Define animation parameters
        self.num_frames = 200
        self.num_points = 200
        self.x_data = np.linspace(0, 4 * np.pi, self.num_points)

        # Create the "completed array" (2D) to store all y-data
        self.all_y_data = np.zeros((self.num_frames, self.num_points))
        for i in range(self.num_frames): self.all_y_data[i, :] = np.sin(self.x_data + i * 0.1)
        
        # --- Tkinter-Matplotlib Bridge ---
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # --- Control Frame ---
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # Add a quit button
        quit_button = ttk.Button(master=control_frame, text="Quit", command=self.quit_app)
        quit_button.pack(side=tk.RIGHT, padx=10)
        
        # Start the animation
        self.start_animation()

    def init_animation(self):
        """
        Initialization function for the animation.
        Sets the line data to empty.
        """
        self.line.set_data([], [])
        return (self.line,)

    def update_animation(self, frame):
        """
        Update function for the animation.
        This is called for each new frame.
        """
        # Calculate new y-data based on the frame number (which acts as a time-step)
        # y_data = np.sin(self.x_data + frame * 0.1) # <-- We no longer calculate here

        # INSTEAD: We retrieve the pre-calculated data from our "completed array"
        # The 'frame' argument is used as the index
        y_data = self.all_y_data[frame, :]
        
        # Update the line's data
        self.line.set_data(self.x_data, y_data)
        
        # Return the artist that has been modified
        return (self.line,)

    def start_animation(self):
        """
        Create and start the FuncAnimation.
        """
        # We need to store the animation object as an instance variable
        # so it doesn't get garbage-collected.
        self.anim = FuncAnimation(
            self.fig,                # The figure to animate
            self.update_animation,   # The function to call for each frame
            init_func=self.init_animation, # The function to call at the start
            frames=self.num_frames,  # Use the number of frames we calculated
            interval=20,             # Milliseconds between frames
            blit=True                # Use blitting for performance
        )

    def quit_app(self):
        """
        Cleanly shut down the application.
        """
        # We can stop the animation if we want, but destroying root is enough
        # if self.anim:
        #     self.anim.event_source.stop()
        self.root.quit()
        self.root.destroy()

# --- Main execution ---
if __name__ == "__main__":
    # Set up the main Tkinter window
    root = tk.Tk()
    
    # Create the application instance
    app = App(root)
    
    # Start the Tkinter event loop
    tk.mainloop()