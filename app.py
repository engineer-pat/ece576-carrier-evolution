import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.integrate import solve_ivp

# Set page configuration
st.set_page_config(page_title="Wow this deserves an A+", layout="wide")

st.title("Evolution of Charge Carriers Through Space and Time")
st.subheader("or: plotting n(x,t) and p(x,t)")

# Sidebar for parameters
st.sidebar.header("Parameters")

# actual stuff we'll use -----
# ----------------------

# Add semiconductor physics parameters
st.sidebar.header("Semiconductor Parameters")

# Material selector for diffusion coefficients
material = st.sidebar.selectbox(
    "Select Semiconductor Material",
    [
        "Silicon",
        "Gallium Arsenide",
        "Germanium",
        "Gallium Nitride",
        "Silicon Carbide",
        "Custom",
    ],
    help="Choose a semiconductor material to use predefined diffusion coefficients",
)

# Define diffusion coefficients based on material
material_params = {
    "Silicon": {"D_n": 36.0, "D_p": 12.0, "μ_n": 1450, "μ_p": 500},
    "Gallium Arsenide": {"D_n": 200.0, "D_p": 10.0, "μ_n": 8000, "μ_p": 400},
    "Germanium": {"D_n": 100.0, "D_p": 50.0, "μ_n": 3900, "μ_p": 1900},
    "Gallium Nitride": {"D_n": 25.0, "D_p": 5.0, "μ_n": 1000, "μ_p": 200},
    "Silicon Carbide": {"D_n": 20.0, "D_p": 3.0, "μ_n": 800, "μ_p": 120},
    "Custom": {"D_n": 25.0, "D_p": 10.0, "μ_n": 1000, "μ_p": 400},
}

# Set diffusion coefficients based on material selection
if material == "Custom":
    D_n = st.sidebar.number_input(
        "Electron diffusion coefficient (D_n)",
        value=25.0,
        min_value=0.1,
        step=0.1,
        help="Typical units: cm²/s",
    )

    D_p = st.sidebar.number_input(
        "Hole diffusion coefficient (D_p)",
        value=10.0,
        min_value=0.1,
        step=0.1,
        help="Typical units: cm²/s",
    )

    μ_n = st.sidebar.number_input(
        "Electron mobility (μ_n)",
        value=1000.0,
        min_value=1.0,
        step=10.0,
        help="Typical units: cm²/Vs",
    )

    μ_p = st.sidebar.number_input(
        "Hole mobility (μ_p)",
        value=400.0,
        min_value=1.0,
        step=10.0,
        help="Typical units: cm²/Vs",
    )
else:
    D_n = material_params[material]["D_n"]
    D_p = material_params[material]["D_p"]
    μ_n = material_params[material]["μ_n"]
    μ_p = material_params[material]["μ_p"]
    st.sidebar.info(
        f"Using D_n = {D_n} cm²/s, D_p = {D_p} cm²/s, μ_n = {μ_n} cm²/Vs, and μ_p = {μ_p} cm²/Vs for {material}"
    )

# Add light/potential parameters
st.sidebar.header("Light and Device Parameters")

# Power Po
P_0 = st.sidebar.slider(
    "Power (P₀)",
    min_value=0.0,
    max_value=11.0,
    value=3.0,
    step=1.0,
    help="Units in this app: mW",
)

n = st.sidebar.slider(
    "Efficiency (n)",
    min_value=0.0,
    max_value=1.0,
    value=1.0,
    step=0.05,
    help="For this app, we'll use 1.0 as default. This is the efficiency of the light source.",
)

hv = st.sidebar.slider(
    "Photon energy (hv)",
    min_value=0.0,
    max_value=3.0,
    value=2.0,
    step=0.1,
    help="Units in this app: eV",
)

V = st.sidebar.slider(
    "Voltage (V)",
    min_value=0.0,
    max_value=10.0,
    value=2.5,
    step=0.1,
    help="Units in this app: V",
)

L = st.sidebar.slider(
    "Length (L)",
    min_value=0.0,
    max_value=100.0,
    value=10.0,
    step=1.0,
    help="Units in this app: μm",
)


# Add other parameters
st.sidebar.header("Other Parameters")

# Initial x_o
x_0 = st.sidebar.slider(
    "Initial position (x₀)", min_value=-10.0, max_value=10.0, value=0.0, step=0.1
)

t_0 = st.sidebar.slider(
    "Initial time (t₀)", min_value=0.0, max_value=20.0, value=0.0, step=0.1
)


# crap to demonstrate how this app can work -----
# ---------------------

# Initial condition
y0 = st.sidebar.number_input("Initial value (y₀)", value=10.0, step=0.1)

# Decay constant
k = st.sidebar.number_input(
    "Decay constant (k)", value=0.5, min_value=0.01, max_value=10.0, step=0.1
)

# Time range
t_max = st.sidebar.slider(
    "Maximum time", min_value=1.0, max_value=20.0, value=10.0, step=0.5
)

# Number of points
num_points = st.sidebar.slider(
    "Number of points", min_value=50, max_value=1000, value=200, step=50
)

# Carrier lifetimes
tau_n = st.sidebar.number_input(
    "Electron lifetime (τ_n)",
    value=1.0,
    min_value=0.01,
    step=0.01,
    help="Typical units: μs",
)

tau_p = st.sidebar.number_input(
    "Hole lifetime (τ_p)",
    value=0.5,
    min_value=0.01,
    step=0.01,
    help="Typical units: μs",
)

# Carrier velocities
v_n = st.sidebar.number_input(
    "Electron velocity (v_n)",
    value=1e7,
    min_value=1e5,
    step=1e5,
    format="%.2e",
    help="Typical units: cm/s",
)

v_p = st.sidebar.number_input(
    "Hole velocity (v_p)",
    value=8e6,
    min_value=1e5,
    step=1e5,
    format="%.2e",
    help="Typical units: cm/s",
)

# Position and time references
st.sidebar.header("Reference Points")
x_0 = st.sidebar.number_input(
    "Reference position (x₀)", value=0.0, step=0.1, help="Typical units: μm"
)

t_0 = st.sidebar.number_input(
    "Reference time (t₀)", value=0.0, step=0.1, help="Typical units: ns"
)


# Define the differential equation
def exponential_decay(t, y, k=0.5):
    return -k * y


# Generate numerical solution using scipy
t_span = (0, t_max)
t_eval = np.linspace(0, t_max, num_points)
solution = solve_ivp(exponential_decay, t_span, [y0], args=(k,), t_eval=t_eval)

# Generate analytical solution for comparison
t_analytical = np.linspace(0, t_max, num_points)
y_analytical = y0 * np.exp(-k * t_analytical)

# Create plots
col1, col2 = st.columns(2)

with col1:
    st.subheader("Numerical Solution")
    fig_numerical = px.line(
        x=solution.t,
        y=solution.y[0],
        labels={"x": "Time", "y": "y(t)"},
        title="Numerical Solution of dy/dt = -k*y",
    )
    fig_numerical.update_traces(line=dict(color="blue", width=2))
    st.plotly_chart(fig_numerical, use_container_width=True)

with col2:
    st.subheader("Analytical Solution")
    fig_analytical = px.line(
        x=t_analytical,
        y=y_analytical,
        labels={"x": "Time", "y": "y(t)"},
        title="Analytical Solution: y(t) = y₀·e^(-k·t)",
    )
    fig_analytical.update_traces(line=dict(color="red", width=2))
    st.plotly_chart(fig_analytical, use_container_width=True)

# Combined plot
st.subheader("Comparison of Solutions")
fig_combined = go.Figure()
fig_combined.add_trace(
    go.Scatter(
        x=solution.t,
        y=solution.y[0],
        mode="lines",
        name="Numerical",
        line=dict(color="blue", width=2),
    )
)
fig_combined.add_trace(
    go.Scatter(
        x=t_analytical,
        y=y_analytical,
        mode="lines",
        name="Analytical",
        line=dict(color="red", width=2, dash="dash"),
    )
)
fig_combined.update_layout(
    title="Comparison of Numerical and Analytical Solutions",
    xaxis_title="Time",
    yaxis_title="y(t)",
    legend_title="Solution Type",
)
st.plotly_chart(fig_combined, use_container_width=True)

# Display equation. This part is manual and must be changed, does not follow above changes in code.
st.markdown(
    """
    # NOTE: CLAUDE ADDED THIS. But nice to see some latex before we go at it. 
    Suggest using o4-mini or 4-o to convert a pic and then copy pasta in here.
    
### Mathematical Details
The exponential decay equation is:
$$\\frac{dy}{dt} = -k \cdot y$$

With the analytical solution:
$$y(t) = y_0 \cdot e^{-k \cdot t}$$

Where:
- $y_0$ is the initial value
- $k$ is the decay constant
- $t$ is time

### Ambipolar Diffusion Equations
$$\\frac{\\delta p(x,t)}{\\delta t} = D \\frac{\\delta^2 p(x,t)}{\\delta x^2} - \\frac{p(x,t)}{\\tau_p}$$
$$c = \\frac{[(x-x_0)]^2 + [v_n t]^2}{4D_n t}$$
"""
)

# Display material properties table
st.subheader("Semiconductor Material Properties")
st.markdown(
    "The table below shows typical diffusion coefficient and mobility values for common semiconductor materials at room temperature:"
)

# Create a DataFrame for the table
material_data = {
    "Material": [
        "Silicon",
        "Gallium Arsenide",
        "Germanium",
        "Gallium Nitride",
        "Silicon Carbide",
    ],
    "Electron Diffusion Coefficient (D₍ₙ₎) [cm²/s]": [36.0, 200.0, 100.0, 25.0, 20.0],
    "Hole Diffusion Coefficient (D₍ₚ₎) [cm²/s]": [12.0, 10.0, 50.0, 5.0, 3.0],
    "Electron Mobility (μ₍ₙ₎) [cm²/Vs]": [1450, 8000, 3900, 1000, 800],
    "Hole Mobility (μ₍ₚ₎) [cm²/Vs]": [500, 400, 1900, 200, 120],
}

# Highlight the currently selected material
if material != "Custom":
    st.markdown(f"**Currently using: {material}**")

# Display the table
st.table(material_data)

st.markdown(
    """
*Note: Values shown are typical for room temperature. Actual values may vary based on doping concentration, temperature, and other factors.*
"""
)

st.markdown(
    """
    
    """
)
