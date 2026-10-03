# ============================================================================
# Physical and Mathematical Constants
# ============================================================================
"""
Reference values from standard orbital mechanics and space debris literature.
"""

import numpy as np

# --- Earth parameters ---
R_EARTH_KM = 6371.0              # Mean Earth radius (km)
MU_EARTH = 3.986004418e5         # Earth gravitational parameter (km³/s²)

# --- Time conversions ---
SECONDS_PER_YEAR = 31557600.0    # Julian year (s)
SECONDS_PER_DAY = 86400.0

# --- Orbital mechanics ---
# Circular orbital velocity at altitude h:
#   v_circ = sqrt(MU_EARTH / (R_EARTH + h))
# Typical LEO relative velocity for random inclinations:
#   v_rel ≈ sqrt(2) × v_circ ≈ 14 km/s at 800 km
# We use 10 km/s as a conservative mean (accounts for co-orbital debris)
V_REL_LEO_KM_S = 10.0

# --- NASA Standard Breakup Model (Johnson et al. 2001) ---
# Number of fragments > D_min (meters) from a collision with
# total mass M_total (kg) and collision energy E (J):
#   N(>D_min) = 0.1 × M_total^0.75 × E^0.5 × D_min^(-1.71)
# For characteristic fragment size D_min = 0.1 m (>10cm):
NASA_BREAKUP_EXPONENT_MASS = 0.75
NASA_BREAKUP_EXPONENT_ENERGY = 0.5
NASA_BREAKUP_EXPONENT_SIZE = -1.71
NASA_BREAKUP_COEFFICIENT = 0.1

# --- Fragment size distribution (power law) ---
# dN/dD ∝ D^(-alpha), alpha ≈ 1.71 for debris > 1cm
FRAGMENT_SIZE_POWER_LAW = 1.71

# --- Unit conversions ---
KM_TO_M = 1e3
M_TO_KM = 1e-3
KM2_TO_M2 = 1e6
M2_TO_KM2 = 1e-6

# --- Insurance / financial constants ---
CONFIDENCE_LEVELS = [0.95, 0.99]
EVT_THRESHOLD_PERCENTILE = 90
