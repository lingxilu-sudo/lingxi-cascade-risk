# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Monte Carlo Cascade Simulator
===============================
Orchestrates large-scale Monte Carlo simulation of debris cascade
paths and collects results into structured arrays for actuarial analysis.

References:
    Rubinstein, R.Y. & Kroese, D.P. (2016). "Simulation and the
    Monte Carlo Method." 3rd ed. Wiley.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from cascade_risk.physics.orbital_shell import OrbitalShell
from cascade_risk.physics.collision_model import CollisionModel
from cascade_risk.physics.debris_growth import DebrisGrowthModel


@dataclass
class SimulationResult:
    """Container for Monte Carlo simulation results."""
    times: np.ndarray                          # (n_steps,)
    all_n_debris: np.ndarray                   # (n_paths, n_steps)
    all_n_collisions: np.ndarray               # (n_paths, n_steps)
    n_paths: int
    t_max_years: float
    dt_years: float
    config_snapshot: dict = field(default_factory=dict)

    @property
    def n_steps(self) -> int:
        return len(self.times)

    def debris_percentile(self, p: float) -> np.ndarray:
        """Debris population at percentile p across all paths."""
        return np.percentile(self.all_n_debris, p, axis=0)

    def final_debris_stats(self) -> dict[str, float]:
        """Summary statistics of final debris population."""
        final = self.all_n_debris[:, -1]
        return {
            "mean": float(np.mean(final)),
            "median": float(np.median(final)),
            "std": float(np.std(final)),
            "p5": float(np.percentile(final, 5)),
            "p95": float(np.percentile(final, 95)),
            "min": float(np.min(final)),
            "max": float(np.max(final)),
        }


class CascadeSimulator:
    """
    Runs Monte Carlo simulation of debris cascade dynamics.

    Parameters
    ----------
    shell : OrbitalShell
        Orbital shell geometry.
    collision_model : CollisionModel
        Collision physics model.
    growth_model : DebrisGrowthModel
        Debris population dynamics model.
    """

    def __init__(
        self,
        shell: OrbitalShell,
        collision_model: CollisionModel,
        growth_model: DebrisGrowthModel,
    ):
        self.shell = shell
        self.collision_model = collision_model
        self.growth_model = growth_model

    def run(
        self,
        n_debris_0: float,
        n_paths: int = 1000,
        t_max_years: float = 50.0,
        dt_years: float = 0.01,
        decay_uncertainty: float = 0.1,
        seed: int = 42,
        progress_callback: Optional[callable] = None,
    ) -> SimulationResult:
        """
        Run full Monte Carlo simulation.

        Parameters
        ----------
        n_debris_0 : float
            Initial debris population.
        n_paths : int
            Number of independent Monte Carlo paths.
        t_max_years : float
            Simulation horizon (years).
        dt_years : float
            Time step (years).
        decay_uncertainty : float
            Std dev of Gaussian noise on decay rate.
        seed : int
            Random seed for reproducibility.
        progress_callback : callable, optional
            Called with (completed, total) for progress reporting.

        Returns
        -------
        SimulationResult
            Structured results with all path data.
        """
        base_rng = np.random.default_rng(seed)

        # Run first path to determine dimensions
        first_rng = np.random.default_rng(base_rng.integers(0, 2**63))
        times, _, _ = self.growth_model.simulate_trajectory(
            n_debris_0, t_max_years, dt_years, decay_uncertainty, first_rng
        )
        n_steps = len(times)

        # Allocate result arrays
        all_n_debris = np.zeros((n_paths, n_steps))
        all_n_collisions = np.zeros((n_paths, n_steps))

        for path_idx in range(n_paths):
            path_seed = base_rng.integers(0, 2**63)
            path_rng = np.random.default_rng(path_seed)

            _, debris, collisions = self.growth_model.simulate_trajectory(
                n_debris_0, t_max_years, dt_years, decay_uncertainty, path_rng
            )

            all_n_debris[path_idx, :] = debris
            all_n_collisions[path_idx, :] = collisions

            if progress_callback and (path_idx + 1) % 100 == 0:
                progress_callback(path_idx + 1, n_paths)

        return SimulationResult(
            times=times,
            all_n_debris=all_n_debris,
            all_n_collisions=all_n_collisions,
            n_paths=n_paths,
            t_max_years=t_max_years,
            dt_years=dt_years,
        )
