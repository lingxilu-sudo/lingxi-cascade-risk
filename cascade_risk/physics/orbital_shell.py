# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Orbital Shell Geometry
======================
Computes the geometric properties of a LEO altitude shell:
volume, debris number density, orbital velocity, and shell capacity.

References:
    Kessler, D.J. (1981). "Derivation of the collision probability between
    orbiting objects: The lifetimes of Jupiter's outer moons."
    Icarus, 48(1), 39-48.
"""

from __future__ import annotations

import numpy as np

from cascade_risk.utils.constants import R_EARTH_KM, MU_EARTH


class OrbitalShell:
    """
    Represents a spherical shell at a given altitude band in LEO.

    Parameters
    ----------
    altitude_km : float
        Center altitude of the shell (km).
    thickness_km : float
        Shell thickness (km). Default 200 km.
    """

    def __init__(self, altitude_km: float = 800.0, thickness_km: float = 200.0):
        self.altitude_km = altitude_km
        self.thickness_km = thickness_km
        self.r_inner_km = R_EARTH_KM + altitude_km - thickness_km / 2
        self.r_outer_km = R_EARTH_KM + altitude_km + thickness_km / 2

    # ------------------------------------------------------------------
    # Geometric properties
    # ------------------------------------------------------------------

    @property
    def volume_km3(self) -> float:
        """Volume of the spherical shell (km³)."""
        return (4.0 / 3.0) * np.pi * (
            self.r_outer_km**3 - self.r_inner_km**3
        )

    @property
    def volume_m3(self) -> float:
        """Volume in m³."""
        return self.volume_km3 * 1e9

    @property
    def mean_radius_km(self) -> float:
        """Mean orbital radius (km)."""
        return R_EARTH_KM + self.altitude_km

    @property
    def surface_area_km2(self) -> float:
        """Surface area at mean radius (km²)."""
        return 4.0 * np.pi * self.mean_radius_km**2

    # ------------------------------------------------------------------
    # Orbital mechanics
    # ------------------------------------------------------------------

    @property
    def orbital_velocity_km_s(self) -> float:
        """Circular orbital velocity at mean altitude (km/s)."""
        return np.sqrt(MU_EARTH / self.mean_radius_km)

    @property
    def orbital_period_s(self) -> float:
        """Orbital period (seconds)."""
        return 2.0 * np.pi * np.sqrt(
            self.mean_radius_km**3 / MU_EARTH
        )

    @property
    def orbital_period_hours(self) -> float:
        """Orbital period (hours)."""
        return self.orbital_period_s / 3600.0

    # ------------------------------------------------------------------
    # Density calculations
    # ------------------------------------------------------------------

    def number_density(self, n_objects: int) -> float:
        """
        Number density of objects in the shell (objects/km³).

        Parameters
        ----------
        n_objects : int
            Total number of objects in the shell.
        """
        return n_objects / self.volume_km3

    def spatial_density(self, n_objects: int, cross_section_m2: float) -> float:
        """
        Spatial density (flux-relevant): n × σ / V  (1/km).

        This is the key quantity for collision rate calculations.
        """
        sigma_km2 = cross_section_m2 * 1e-6  # m² → km²
        return n_objects * sigma_km2 / self.volume_km3

    # ------------------------------------------------------------------
    # Carrying capacity (Kessler threshold)
    # ------------------------------------------------------------------

    def carrying_capacity(
        self,
        cross_section_m2: float,
        v_rel_km_s: float,
        decay_rate_per_year: float = 0.005,
    ) -> float:
        """
        Characteristic debris scale at which the debris-debris collision
        rate equals the decay rate, K = V_shell / (σ × v_rel × τ_decay).

        This is **not** a tipping point: it ignores the fragment yield and
        the debris-satellite production term.  With the baseline b > λ the
        full mean field dN/dt = (b-λ)N + aN² has no positive equilibrium,
        so K (and the DD-only threshold λ/a) are diagnostics only.

        Parameters
        ----------
        cross_section_m2 : float
            Characteristic collision cross-section (m²).
        v_rel_km_s : float
            Mean relative velocity (km/s).
        decay_rate_per_year : float
            Orbital decay rate (1/year). Must match the value used by the
            growth model; hard-coding it silently disconnects K from the
            simulated decay.
        """
        if decay_rate_per_year <= 0:
            raise ValueError("decay_rate_per_year must be positive")
        sigma_km2 = cross_section_m2 * 1e-6
        tau_decay_years = 1.0 / decay_rate_per_year
        tau_decay_s = tau_decay_years * 31557600.0

        # K = V / (σ × v_rel × τ)
        # Units: km³ / (km² × km/s × s) = dimensionless count
        return self.volume_km3 / (sigma_km2 * v_rel_km_s * tau_decay_s)

    def __repr__(self) -> str:
        # Keep this ASCII: it is printed by main.py and a superscript
        # character raises UnicodeEncodeError on a stock Windows (GBK)
        # console.
        return (
            f"OrbitalShell(altitude={self.altitude_km} km, "
            f"thickness={self.thickness_km} km, "
            f"V={self.volume_km3:.2e} km^3)"
        )
