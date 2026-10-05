# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Loss Distribution Model
========================
Converts debris cascade simulation output into insurance loss distributions.

Implements:
- Per-satellite hit probability from collision physics
- Correlated multi-satellite losses (Copula-based)
- Annual and aggregate loss distributions

References:
    McNeil, A.J., Frey, R. & Embrechts, P. (2015). "Quantitative Risk
    Management: Concepts, Techniques and Tools." 2nd ed. Princeton.
    Nelsen, R.B. (2006). "An Introduction to Copulas." 2nd ed. Springer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats


@dataclass
class LossDistribution:
    """Container for computed loss distribution."""
    annual_losses: np.ndarray          # (n_paths, n_steps) - per-path per-time losses
    max_annual_losses: np.ndarray      # (n_paths,) - worst year per path
    aggregate_losses: np.ndarray       # (n_paths,) - total NPV losses
    hit_probabilities: np.ndarray      # (n_paths, n_steps)
    n_policies: int
    v_satellite_usd: float


class LossModel:
    """
    Converts debris population trajectories into insurance loss distributions.

    The key improvement over the baseline model: losses are derived from
    actual collision physics (hit probability from debris density) rather
    than an arbitrary base_hit_probability parameter.

    Parameters
    ----------
    v_satellite_usd : float
        Average insured satellite value (USD).
    n_policies : int
        Number of insured satellites in the portfolio.
    correlation_coefficient : float
        Inter-policy loss correlation (0=independent, 1=perfectly correlated).
    discount_rate : float
        Annual discount rate for NPV calculation.
    """

    def __init__(
        self,
        v_satellite_usd: float = 50_000_000,
        n_policies: int = 500,
        correlation_coefficient: float = 0.3,
        discount_rate: float = 0.04,
    ):
        self.v_satellite_usd = v_satellite_usd
        self.n_policies = n_policies
        self.correlation_coefficient = correlation_coefficient
        self.discount_rate = discount_rate

    def compute_hit_probability(
        self,
        n_debris: np.ndarray,
        n_debris_0: float,
        cross_section_m2: float = 10.0,
        v_rel_km_s: float = 10.0,
        shell_volume_km3: float = 1.0,
    ) -> np.ndarray:
        """
        Compute per-satellite annual hit probability from debris density.

        p_hit = n_debris × σ × v_rel × T_year / V_shell

        This replaces the ad-hoc base_hit_probability with physics-derived values.

        Parameters
        ----------
        n_debris : np.ndarray
            Debris population (scalar or array).
        n_debris_0 : float
            Reference debris population for scaling.
        cross_section_m2 : float
            Satellite collision cross-section (m²).
        v_rel_km_s : float
            Mean relative velocity (km/s).
        shell_volume_km3 : float
            Orbital shell volume (km³).

        Returns
        -------
        np.ndarray
            Annual hit probability (same shape as n_debris).
        """
        sigma_km2 = cross_section_m2 * 1e-6
        seconds_per_year = 31557600.0

        # Collision flux: n_debris × σ × v_rel / V
        # Units: (1/km³) × km² × km/s = 1/(km·s)
        # Multiply by seconds/year → 1/km × km = dimensionless probability
        # But we need per-satellite probability, so no n_satellites factor
        flux = n_debris * sigma_km2 * v_rel_km_s * seconds_per_year / shell_volume_km3

        return np.minimum(flux, 1.0)

    def compute_loss_distribution(
        self,
        all_n_debris: np.ndarray,
        n_debris_0: float,
        cross_section_m2: float = 10.0,
        v_rel_km_s: float = 10.0,
        shell_volume_km3: float = 1.0,
    ) -> LossDistribution:
        """
        Full loss distribution computation from Monte Carlo debris paths.

        Parameters
        ----------
        all_n_debris : np.ndarray
            (n_paths, n_steps) debris population array.
        n_debris_0 : float
            Initial/reference debris count.
        cross_section_m2 : float
            Satellite cross-section (m²).
        v_rel_km_s : float
            Relative velocity (km/s).
        shell_volume_km3 : float
            Shell volume (km³).

        Returns
        -------
        LossDistribution
            Complete loss distribution object.
        """
        n_paths, n_steps = all_n_debris.shape

        # Per-satellite hit probability
        hit_prob = self.compute_hit_probability(
            all_n_debris, n_debris_0,
            cross_section_m2, v_rel_km_s, shell_volume_km3
        )

        # Per-satellite annual loss
        per_sat_loss = hit_prob * self.v_satellite_usd

        # Portfolio loss (expected value)
        # Note: Correlation affects variance/risk metrics, not expected value.
        # Correlation is handled in portfolio_risk.py via Gaussian Copula.
        portfolio_annual_losses = per_sat_loss * self.n_policies

        # Maximum annual loss per path
        max_annual_losses = np.max(portfolio_annual_losses, axis=1)

        # Aggregate (NPV) loss per path
        discount_factors = np.array([
            1.0 / (1.0 + self.discount_rate) ** t
            for t in range(n_steps)
        ])
        aggregate_losses = np.sum(
            portfolio_annual_losses * discount_factors[np.newaxis, :],
            axis=1
        )

        return LossDistribution(
            annual_losses=portfolio_annual_losses,
            max_annual_losses=max_annual_losses,
            aggregate_losses=aggregate_losses,
            hit_probabilities=hit_prob,
            n_policies=self.n_policies,
            v_satellite_usd=self.v_satellite_usd,
        )

    def historical_loss(self, failure_rate: float = 0.005) -> float:
        """
        Historical expected annual loss based on in-orbit failure rate only.
        No cascade risk included. Uses 0.5% in-orbit rate (not launch failure).
        """
        return failure_rate * self.v_satellite_usd * self.n_policies
