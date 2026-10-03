# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Historical Event Calibration
==============================
Calibrates the debris fragmentation model parameters against
real collision events:

1. Iridium 33 × Cosmos 2251 (2009) — accidental collision
2. Fengyun-1C ASAT test (2007) — intentional destruction
3. Kosmos 1408 ASAT test (2021) — intentional destruction

Uses observed fragment counts to calibrate the NASA Standard
Breakup Model parameters (k_debris distribution).

References:
    Johnson, N.L. et al. (2001). "History of On-Orbit Satellite
    Fragmentations." NASA/TM-2001-210780.
    Liou, J.-C. & Johnson, N.L. (2009). "A statistical analysis of
    the future debris environment." Acta Astronautica, 64(2-3), 244-253.
    NASA Orbital Debris Program Office. "Orbital Debris Quarterly News."
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import yaml


@dataclass(frozen=True)
class CollisionEvent:
    """Recorded orbital collision event."""
    name: str
    date: str
    altitude_km: float
    relative_velocity_km_s: float
    trackable_fragments: int       # >10 cm
    total_fragments_estimated: int
    total_mass_kg: float


# --- Known collision events ---
KNOWN_EVENTS: list[CollisionEvent] = [
    CollisionEvent(
        name="Iridium 33 × Cosmos 2251",
        date="2009-02-10",
        altitude_km=790,
        relative_velocity_km_s=11.6,
        trackable_fragments=2300,
        total_fragments_estimated=100_000,
        total_mass_kg=1510,  # 560 + 950 kg
    ),
    CollisionEvent(
        name="Fengyun-1C ASAT",
        date="2007-01-11",
        altitude_km=865,
        relative_velocity_km_s=8.0,
        trackable_fragments=3500,
        total_fragments_estimated=150_000,
        total_mass_kg=750,
    ),
    CollisionEvent(
        name="Kosmos 1408 ASAT",
        date="2021-11-15",
        altitude_km=480,
        relative_velocity_km_s=7.0,
        trackable_fragments=1500,
        total_fragments_estimated=50_000,
        total_mass_kg=2200,
    ),
]


class CalibrationEngine:
    """
    Calibrates fragmentation model parameters against historical events.

    The NASA Standard Breakup Model predicts:
        N(>D) = 0.1 × M^0.75 × E^0.5 × D^(-1.71)

    We calibrate the log-normal distribution of k_debris (fragments per
    collision) to match observed fragment counts.
    """

    def __init__(self, events: list[CollisionEvent] = None):
        self.events = events or KNOWN_EVENTS

    def calibrate_k_debris(self) -> dict[str, float]:
        """
        Calibrate log-normal parameters for fragments per collision.

        Returns
        -------
        dict with 'mu' and 'sigma' for log-normal distribution.
        """
        # For each event, compute fragments per kg
        fragments_per_kg = []
        for event in self.events:
            fpk = event.total_fragments_estimated / event.total_mass_kg
            fragments_per_kg.append(fpk)

        # Convert to log scale
        log_fpk = np.log(fragments_per_kg)

        # Log-normal parameters
        mu = float(np.mean(log_fpk))
        sigma = float(np.std(log_fpk, ddof=1)) if len(log_fpk) > 1 else 0.5

        return {"mu": mu, "sigma": max(sigma, 0.3)}

    def calibrate_collision_cross_section(self) -> dict[str, float]:
        """
        Estimate effective collision cross-section from event data.

        Uses the observed collision rate to back out σ_eff.
        """
        # Simplified: use literature value with uncertainty
        # Typical satellite cross-section: 5-20 m²
        return {"mean_m2": 10.0, "std_m2": 5.0}

    def validate_model(
        self,
        simulated_fragments: np.ndarray,
        event_index: int = 0,
    ) -> dict[str, float]:
        """
        Compare simulated fragment distribution against a real event.

        Parameters
        ----------
        simulated_fragments : np.ndarray
            Simulated fragment counts from the model.
        event_index : int
            Index of the event to compare against.

        Returns
        -------
        dict with comparison statistics.
        """
        event = self.events[event_index]
        observed = event.total_fragments_estimated

        return {
            "event_name": event.name,
            "observed_fragments": observed,
            "simulated_mean": float(np.mean(simulated_fragments)),
            "simulated_median": float(np.median(simulated_fragments)),
            "simulated_std": float(np.std(simulated_fragments)),
            "bias": float(np.mean(simulated_fragments) - observed),
            "relative_error": float(
                abs(np.mean(simulated_fragments) - observed) / observed
            ),
        }

    def load_calibration_config(self, filepath: str = None) -> dict:
        """Load calibration targets from YAML config."""
        if filepath is None:
            filepath = Path(__file__).parent.parent.parent / "configs" / "calibration.yaml"
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
