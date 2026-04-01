import numpy as np

def temperature_stress_factor(temp):
    return np.exp((temp - 25.0) / 10.0)

def dod_stress_factor(dod):
    dod_clipped = np.maximum(1.0, dod)
    return np.power(dod_clipped / 80.0, 1.5)

def c_rate_stress_factor(c_rate):
    return np.exp((np.abs(c_rate) - 1.0) * 0.5)
