"""
MIT License

Copyright (c) 2025 Errol Tay

See LICENSE for full license text.
"""

import numpy as np
from scipy.linalg import solve

# Convert Polar to Cartesian coordinates
def position_bob1(θ1, l1):
    x1 = l1 * np.sin(θ1)
    y1 = -l1 * np.cos(θ1)
    return x1, y1

def velocity_bob1(θ1, ω1, l1):
    vx1 = l1 * ω1 * np.cos(θ1)
    vy1 = l1 * ω1 * np.sin(θ1)
    return vx1, vy1

def position_bob2(x1, y1, θ2, l2):
    x2 = x1 + l2 * np.sin(θ2)
    y2 = y1 - l2 * np.cos(θ2)
    return x2, y2

def velocity_bob2(vx1, vy1, θ2, ω2, l2):
    vx2 = vx1 + l2 * ω2 * np.cos(θ2)
    vy2 = vy1 + l2 * ω2 * np.sin(θ2)
    return vx2, vy2

# Functions which simulate the double pendulum
def double_pendulum_derivatives(t, y, m1, m2, l1, l2, g):
    """
    Returns the derivatives of the double pendulum system.
    """
    # Parameters
    θ1, θ2, ω1, ω2 = y # unpack state vector
    delta = θ2 - θ1
    m12 = m1 + m2
    
    # Defining the vectors as matrix functions
    A = np.array([
        [m12 * l1, m2 * l2 * np.cos(delta)],
        [l1 * np.cos(delta), l2]
    ])
    
    b = np.array([
        m2 * l2 * abs(ω2**2) * np.sin(delta) - m12 * g * np.sin(θ1),
        -l1 * abs(ω1**2) * np.sin(delta) - g * np.sin(θ2)
    ])
    
    # Solve for acceleration
    α1, α2 = solve(A, b)
    
    return np.array([ω1, ω2, α1, α2]) # return derivatives

def rk4_step(f, t, y, dt, *args):
    """
    4th Order Runge-Kutta step
    """
    # Runge-Kutta returns state vectors from derivatives
    k1 = f(t, y, *args)
    k2 = f(t + dt/2, y + dt/2 * k1, *args)
    k3 = f(t + dt/2, y + dt/2 * k2, *args)
    k4 = f(t + dt, y + dt * k3, *args)

    return y + dt/6 * (k1 + 2*k2 + 2*k3 + k4)

def simulate_double_pendulum(θ1, θ2, ω1=0, ω2=0,  
                             m1=1, m2=1, 
                             l1=1, l2=1, 
                             t_max=10, dt=0.01,
                             g=9.81):
    """
    Simulate the double pendulum
    """
    # Initial state
    y = np.array([θ1, θ2, ω1, ω2])
    
    # Time array
    t_values = np.arange(0, t_max+dt, dt)
    
    # Store results
    results = np.zeros((len(t_values), 4))
    results[0] = y
    
    # Simulation loop
    for i in range(1, len(t_values)):
        results[i] = rk4_step(double_pendulum_derivatives, t_values[i-1], 
                             results[i-1], dt, m1, m2, l1, l2, g)
    
    return t_values, results