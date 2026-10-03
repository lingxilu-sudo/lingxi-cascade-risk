# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Debris Growth Model
====================
Implements the debris population dynamics as a stochastic ODE driven
by collision physics (not a free parameter).

The governing equation is:
    dN/dt = R_collision(N) × k_debris - λ × N

where:
    R_collision(N) = debris-satellite + debris-debris collision rate
    k_debris = fragments per collision (log-normal distributed)
    λ = natural orbital decay rate

This replaces the ad-hoc `cascade_rate` parameter with physics-driven growth.

References:
    Kessler, D.J. & Cour-Palais, B.G. (1978). "Collision Frequency of
    Artificial Satellites: The Creation of a Debris Belt."
    J. Geophys. Res., 83(A7), 2637-2646.
    Liou, J.-C. & Johnson, N.L. (2008). "Instability of the present
    LEO satellite populations." Science, 319(5869), 1397-1399.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from cascade_risk.physics.orbital_shell import OrbitalShell
from cascade_risk.physics.collision_model import CollisionModel, CollisionEvent


@dataclass
class DebrisState:
    """Snapshot of debris population at a point in time."""
    time_years: float
    n_debris: float
    n_collisions_cumulative: int
    n_fragments_generated_cumulative: int
    collision_events: list[CollisionEvent] = field(default_factory=list)


class DebrisGrowthModel:
    """
    Simulates debris population evolution with collision-driven growth.

    The key innovation: debris growth is NOT driven by a free parameter
    (`cascade_rate`) but by actual collision physics. Each collision
    event generates new fragments, which increase future collision rates.

    Parameters
    ----------
    shell : OrbitalShell
        Orbital shell geometry.
    collision_model : CollisionModel
        Collision rate calculator.
    n_satellites : int
        Active satellite population.
    decay_rate_per_year : float
        Natural orbital decay rate (1/year).
    """

    def __init__(
        self,
        shell: OrbitalShell,
        collision_model: CollisionModel,
        n_satellites: int = 8000,
        decay_rate_per_year: float = 0.005,
    ):
        self.shell = shell
        self.collision_model = collision_model
        self.n_satellites = n_satellites
        self.decay_rate_per_year = decay_rate_per_year

    def simulate_path(
        self,
        n_debris_0: float,
        t_max_years: float = 50.0,
        dt_years: float = 0.01,
        decay_uncertainty: float = 0.1,
        rng: Optional[np.random.Generator] = None,
    ) -> DebrisState:
        """
        Run a single Monte Carlo path of debris evolution.

        Parameters
        ----------
        n_debris_0 : float
            Initial debris population.
        t_max_years : float
            Simulation horizon (years).
        dt_years : float
            Time step (years).
        decay_uncertainty : float
            Std dev of Gaussian noise on decay rate (fraction).
        rng : np.random.Generator, optional
            Random number generator. Created if None.

        Returns
        -------
        DebrisState
            Final state with full trajectory recorded.
        """
        if rng is None:
            rng = np.random.default_rng()

        n_steps = int(t_max_years / dt_years) + 1
        times = np.linspace(0, t_max_years, n_steps)
        n_debris_arr = np.zeros(n_steps)
        n_collisions_arr = np.zeros(n_steps, dtype=int)

        n_debris = float(n_debris_0)
        n_collisions_total = 0
        n_fragments_total = 0
        collision_events: list[CollisionEvent] = []

        for i in range(n_steps):
            n_debris_arr[i] = n_debris
            n_collisions_arr[i] = n_collisions_total

            if i == n_steps - 1:
                break

            # --- Stochastic decay rate ---
            decay_noise = rng.normal(1.0, decay_uncertainty)
            effective_decay = self.decay_rate_per_year * max(decay_noise, 0.1)

            # --- Poisson collision events ---
            # 1. Debris-satellite collisions
            n_ds_events = self.collision_model.poisson_collision_events(
                n_debris, self.n_satellites, dt_years, rng
            )

            # 2. Debris-debris collisions (cascade driver)
            n_dd_events = self.collision_model.debris_debris_poisson_events(
                n_debris, dt_years, rng
            )

            total_events = n_ds_events + n_dd_events

            # Generate new fragments (vectorized, different yields per collision type)
            if n_dd_events > 0:
                n_dd_frag = int(np.sum(rng.lognormal(1.1, 0.5, size=n_dd_events)))
            else:
                n_dd_frag = 0

            if n_ds_events > 0:
                n_ds_frag = int(np.sum(rng.lognormal(
                    self.collision_model.k_debris_mu,
                    self.collision_model.k_debris_sigma,
                    size=n_ds_events,
                )))
            else:
                n_ds_frag = 0

            n_new_debris = n_dd_frag + n_ds_frag

            if total_events > 0:
                n_collisions_total += total_events
                n_fragments_total += n_new_debris

                collision_events.append(CollisionEvent(
                    time_years=times[i],
                    n_fragments_generated=n_new_debris,
                    debris_before=n_debris,
                    debris_after=n_debris,  # Updated after decay below
                ))

            # --- Update debris population ---
            # Decay
            n_decay = n_debris * effective_decay * dt_years
            n_debris = max(n_debris + n_new_debris - n_decay, 0.0)

            # Update last collision event with final debris count
            if collision_events and collision_events[-1].time_years == times[i]:
                collision_events[-1] = CollisionEvent(
                    time_years=times[i],
                    n_fragments_generated=collision_events[-1].n_fragments_generated,
                    debris_before=collision_events[-1].debris_before,
                    debris_after=n_debris,
                )

        return DebrisState(
            time_years=t_max_years,
            n_debris=n_debris,
            n_collisions_cumulative=n_collisions_total,
            n_fragments_generated_cumulative=n_fragments_total,
            collision_events=collision_events,
        )

    def simulate_trajectory(
        self,
        n_debris_0: float,
        t_max_years: float = 50.0,
        dt_years: float = 0.01,
        decay_uncertainty: float = 0.1,
        rng: Optional[np.random.Generator] = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Run a single path and return full time series arrays.

        Returns
        -------
        times : np.ndarray
            Time array (years).
        n_debris : np.ndarray
            Debris population at each time step.
        annual_collisions : np.ndarray
            Cumulative collisions at each time step.
        """
        if rng is None:
            rng = np.random.default_rng()

        n_steps = int(t_max_years / dt_years) + 1
        times = np.linspace(0, t_max_years, n_steps)
        n_debris_arr = np.zeros(n_steps)
        annual_collisions = np.zeros(n_steps)

        n_debris = float(n_debris_0)
        n_collisions_total = 0

        for i in range(n_steps):
            n_debris_arr[i] = n_debris
            annual_collisions[i] = n_collisions_total

            if i == n_steps - 1:
                break

            # Stochastic decay
            decay_noise = rng.normal(1.0, decay_uncertainty)
            effective_decay = self.decay_rate_per_year * max(decay_noise, 0.1)

            # Poisson collision events
            n_ds = self.collision_model.poisson_collision_events(
                n_debris, self.n_satellites, dt_years, rng
            )
            n_dd = self.collision_model.debris_debris_poisson_events(
                n_debris, dt_years, rng
            )
            total_events = n_ds + n_dd

            # Generate new fragments (vectorized)
            # Debris-debris collisions produce fewer fragments than satellite collisions
            # Small debris fragments (~1-10cm) colliding produce ~1-5 new fragments
            # Satellite collisions produce ~100-1000 fragments (NASA breakup model)
            if n_dd > 0:
                # Debris-debris: small fragment yield (log-normal, median ~3)
                n_dd_fragments = int(np.sum(rng.lognormal(
                    1.1, 0.5, size=n_dd,
                )))
            else:
                n_dd_fragments = 0

            if n_ds > 0:
                # Debris-satellite: larger fragment yield (log-normal, median ~245)
                n_ds_fragments = int(np.sum(rng.lognormal(
                    self.collision_model.k_debris_mu,
                    self.collision_model.k_debris_sigma,
                    size=n_ds,
                )))
            else:
                n_ds_fragments = 0

            n_new = n_dd_fragments + n_ds_fragments

            n_collisions_total += total_events

            # Update population
            n_decay = n_debris * effective_decay * dt_years
            n_debris = max(n_debris + n_new - n_decay, 0.0)

        return times, n_debris_arr, annual_collisions
