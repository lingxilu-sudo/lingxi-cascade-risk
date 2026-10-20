# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Collision Probability Model
============================
Implements collision rate calculation using the kinetic theory approach
(Kessler 1981, Flournoy 1987) with Poisson-distributed collision events.

The collision rate between two populations is:
    R = n₁ × n₂ × σ × v_rel / V_shell

where n₁, n₂ are population counts, σ is the combined cross-section,
v_rel is the mean relative velocity, and V_shell is the shell volume.

Collision events follow a Poisson process, and each collision produces a
random number of fragments from an event-anchored log-normal yield.  The
NASA Standard Breakup Model is retained only as an order-of-magnitude
anchor; it is not evaluated by the sampler.

References:
    Kessler, D.J. (1981). Icarus, 48(1), 39-48.
    Johnson, N.L. et al. (2008). "History of On-Orbit Satellite
    Fragmentations, 14th Edition." NASA Orbital Debris Program Office.
    Liou, J.-C. & Johnson, N.L. (2006). "Risks in Space from
    Orbiting Debris." Science, 311(5759), 340-341.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from cascade_risk.physics.orbital_shell import OrbitalShell
from cascade_risk.utils.constants import (
    SECONDS_PER_YEAR,
    NASA_BREAKUP_COEFFICIENT,
    NASA_BREAKUP_EXPONENT_MASS,
    NASA_BREAKUP_EXPONENT_ENERGY,
    NASA_BREAKUP_EXPONENT_SIZE,
)


@dataclass(frozen=True)
class CollisionEvent:
    """Represents a single collision event."""
    time_years: float
    n_fragments_generated: int
    debris_before: float
    debris_after: float


class CollisionModel:
    """
    Computes collision rates and generates stochastic collision events.

    Parameters
    ----------
    shell : OrbitalShell
        The orbital shell geometry.
    cross_section_m2 : float
        Characteristic collision cross-section (m²).
    v_rel_km_s : float
        Mean relative velocity (km/s).
    k_debris_mu : float
        Log-normal mean for fragments per collision (ln-scale).
    k_debris_sigma : float
        Log-normal std dev for fragments per collision.
    """

    def __init__(
        self,
        shell: OrbitalShell,
        cross_section_m2: float = 10.0,
        v_rel_km_s: float = 10.0,
        k_debris_mu: float = 5.5,
        k_debris_sigma: float = 0.8,
    ):
        self.shell = shell
        self.cross_section_m2 = cross_section_m2
        self.v_rel_km_s = v_rel_km_s
        self.k_debris_mu = k_debris_mu
        self.k_debris_sigma = k_debris_sigma

        # Precompute constant factor for collision rate
        self._sigma_km2 = cross_section_m2 * 1e-6  # m² → km²
        self._v_rel_km_per_year = v_rel_km_s * SECONDS_PER_YEAR

    # ------------------------------------------------------------------
    # Collision rate
    # ------------------------------------------------------------------

    def collision_rate(
        self,
        n_debris: float,
        n_satellites: int,
    ) -> float:
        """
        Expected collision rate (collisions/year) between debris and satellites.

        R = n_debris × n_satellites × σ × v_rel / V_shell

        Parameters
        ----------
        n_debris : float
            Current debris population count.
        n_satellites : int
            Active satellite count.
        """
        return (
            n_debris
            * n_satellites
            * self._sigma_km2
            * self._v_rel_km_per_year
            / self.shell.volume_km3
        )

    def debris_debris_collision_rate(
        self,
        n_debris: float,
    ) -> float:
        """
        Expected debris-debris collision rate (collisions/year).

        R_dd = 0.5 × n_debris × (n_debris - 1) × σ × v_rel / V_shell

        The factor 0.5 avoids double-counting pairs.
        """
        if n_debris < 2:
            return 0.0
        return (
            0.5
            * n_debris
            * (n_debris - 1)
            * self._sigma_km2
            * self._v_rel_km_per_year
            / self.shell.volume_km3
        )

    # ------------------------------------------------------------------
    # Fragment generation (NASA Standard Breakup Model)
    # ------------------------------------------------------------------

    def generate_fragments(
        self,
        rng: np.random.Generator,
        total_mass_kg: float = 1500.0,
        collision_energy_j: Optional[float] = None,
    ) -> int:
        """
        Sample the number of trackable fragments from one collision.

        The operative yield is the event-anchored log-normal distribution
        specified by ``k_debris_mu`` / ``k_debris_sigma``.  The NASA
        Standard Breakup Model in ``constants.py`` is retained as an
        order-of-magnitude anchor but is **not** evaluated here.

        Parameters
        ----------
        rng : np.random.Generator
            Random number generator.
        total_mass_kg : float
            Accepted for API compatibility; not used by the log-normal
            sampler.
        collision_energy_j : float, optional
            Accepted for API compatibility; not used by the log-normal
            sampler.
        """
        # Use log-normal distribution for stochastic fragment count
        n_fragments = int(rng.lognormal(self.k_debris_mu, self.k_debris_sigma))
        return max(n_fragments, 1)  # At least 1 fragment

    # ------------------------------------------------------------------
    # Poisson collision events
    # ------------------------------------------------------------------

    def poisson_collision_events(
        self,
        n_debris: float,
        n_satellites: int,
        dt_years: float,
        rng: np.random.Generator,
    ) -> int:
        """
        Sample number of collision events in a time step from Poisson distribution.

        Parameters
        ----------
        n_debris : float
            Current debris population.
        n_satellites : int
            Active satellite count.
        dt_years : float
            Time step (years).
        rng : np.random.Generator
            Random number generator.
        """
        rate = self.collision_rate(n_debris, n_satellites)
        expected_events = rate * dt_years
        return rng.poisson(expected_events)

    def debris_debris_poisson_events(
        self,
        n_debris: float,
        dt_years: float,
        rng: np.random.Generator,
    ) -> int:
        """
        Sample debris-debris collision events from Poisson distribution.
        """
        rate = self.debris_debris_collision_rate(n_debris)
        expected_events = rate * dt_years
        return rng.poisson(expected_events)

    # ------------------------------------------------------------------
    # Hit probability (for insurance layer)
    # ------------------------------------------------------------------

    def hit_probability_per_year(
        self,
        n_debris: float,
        n_satellites: int,
    ) -> float:
        """
        Annual probability that a single satellite is hit by debris.

        p_hit = R / n_satellites = n_debris × σ × v_rel / V_shell

        This is the per-satellite annual collision probability.
        """
        rate = self.collision_rate(n_debris, n_satellites)
        return min(rate / n_satellites, 1.0) if n_satellites > 0 else 0.0

    @property
    def saturation_population(self) -> float:
        """Population at which each satellite is hit once per year on average.

        N_sat = V_shell / (σ v_rel T_year) = 1/q.  Beyond this density the
        dilute-gas rate formula is no longer physically meaningful and the
        loss layer already clips the hit probability at 1.
        """
        q = (self._sigma_km2 * self._v_rel_km_per_year
             / self.shell.volume_km3)
        return 1.0 / q
