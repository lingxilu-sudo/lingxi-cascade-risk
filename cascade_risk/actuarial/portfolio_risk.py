# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Portfolio Risk Model
=====================
Models correlated losses across an insurance portfolio of satellites.

When a debris cascade event occurs, multiple satellites may be damaged
simultaneously, creating correlated claims that exceed the sum of
individual expected losses (systemic risk).

Implements:
- Gaussian Copula for correlated default/hit modeling
- Portfolio VaR vs. sum-of-individual VaR (diversification benefit/cost)
- Aggregate loss distribution with correlation

References:
    Embrechts, P., Lindskog, F. & McNeil, A.J. (2003). "Modelling
    dependence with Copulas and applications to risk management."
    In: Handbook of Heavy Tailed Distributions in Finance.
    Denuit, M. et al. (2005). "Actuarial Theory for Dependent Risks."
    Wiley.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats, linalg


@dataclass
class PortfolioRiskResult:
    """Portfolio-level risk assessment."""
    portfolio_var_95: float
    portfolio_var_99: float
    portfolio_cvar_95: float
    # n_policies × V_sat: the largest loss the portfolio can take in one year.
    # Despite the name this is a capped exposure, not a sum of per-satellite
    # 95% VaRs (a single satellite's 95% VaR is zero here; see below).
    sum_individual_var_95: float
    # Portfolio VaR95 divided by that exposure: the share of the maximum
    # possible loss at the 95% level.  A concentration measure, not a
    # diversification benefit.  NaN when a satellite's horizon hit
    # probability is below 5%.
    diversification_ratio: float
    expected_portfolio_loss: float
    loss_samples: np.ndarray


class PortfolioRiskModel:
    """
    Models correlated satellite losses in an insurance portfolio.

    Uses a Gaussian Copula to generate correlated hit/miss outcomes
    across satellites, then aggregates into portfolio loss.

    Parameters
    ----------
    n_policies : int
        Number of insured satellites.
    correlation_coefficient : float
        Correlation of the *latent Gaussian* variables, not of the hit
        indicators.  A Gaussian copula with latent correlation ρ induces a
        weaker correlation between the resulting 0/1 hit events, so this is
        an upper bound on the event correlation.
    v_satellite_usd : float
        Average satellite value (USD).
    """

    def __init__(
        self,
        n_policies: int = 500,
        correlation_coefficient: float = 0.3,
        v_satellite_usd: float = 50_000_000,
    ):
        self.n_policies = n_policies
        self.correlation_coefficient = np.clip(correlation_coefficient, 0.0, 0.999)
        self.v_satellite_usd = v_satellite_usd

    def _build_correlation_matrix(self) -> np.ndarray:
        """
        Build equicorrelation matrix for the portfolio.

        Σ = (1-ρ)I + ρ·11'
        """
        rho = self.correlation_coefficient
        n = self.n_policies
        corr_matrix = np.full((n, n), rho)
        np.fill_diagonal(corr_matrix, 1.0)
        return corr_matrix

    def simulate_portfolio_losses(
        self,
        hit_probabilities: np.ndarray,
        n_simulations: int = 10000,
        rng: Optional[np.random.Generator] = None,
    ) -> PortfolioRiskResult:
        """
        Simulate correlated portfolio losses using Gaussian Copula.

        For each time step, generate correlated Bernoulli outcomes across
        all satellites.  The debris-population uncertainty is collapsed to
        the cross-path mean hit probability at each step; this module
        therefore measures portfolio aggregation at a fixed hazard, not the
        full Monte Carlo loss distribution used in the headline premium.

        Parameters
        ----------
        hit_probabilities : np.ndarray
            (n_paths, n_steps) per-satellite hit probabilities.
        n_simulations : int
            Number of portfolio simulations per time step.
        rng : np.random.Generator, optional
            Random number generator.

        Returns
        -------
        PortfolioRiskResult
            Portfolio-level risk metrics.
        """
        if rng is None:
            rng = np.random.default_rng()

        n_paths, n_steps = hit_probabilities.shape
        n = self.n_policies

        # Build correlation matrix
        corr_matrix = self._build_correlation_matrix()

        # Cholesky decomposition for correlated sampling
        try:
            L = linalg.cholesky(corr_matrix, lower=True)
        except linalg.LinAlgError:
            # Fallback: use nearest positive definite matrix
            corr_matrix = self._nearest_positive_definite(corr_matrix)
            L = linalg.cholesky(corr_matrix, lower=True)

        # Simulate correlated losses
        # For efficiency, use the mean hit probability across paths
        mean_hit_prob = np.mean(hit_probabilities, axis=0)  # (n_steps,)

        portfolio_losses = np.zeros((n_simulations, n_steps))

        for step in range(n_steps):
            p = mean_hit_prob[step]
            if p <= 0:
                continue

            # Generate correlated uniform variables via Gaussian Copula
            z = rng.standard_normal((n_simulations, n))
            correlated_z = z @ L.T
            uniform_vars = stats.norm.cdf(correlated_z)

            # Bernoulli hits
            hits = (uniform_vars < p).astype(float)

            # Portfolio loss = number of hits × satellite value
            portfolio_losses[:, step] = hits.sum(axis=1) * self.v_satellite_usd

        # Aggregate: use maximum annual loss
        max_losses = portfolio_losses.max(axis=1)

        # Portfolio VaR
        port_var_95 = float(np.percentile(max_losses, 95))
        port_var_99 = float(np.percentile(max_losses, 99))
        port_cvar_95 = float(np.mean(max_losses[max_losses >= port_var_95])) if len(max_losses[max_losses >= port_var_95]) > 0 else port_var_95

        # "Sum of individual VaRs" denominator.
        # A single satellite's 95% VaR over the horizon is 0 unless its hit
        # probability exceeds 95%, so the textbook denominator is identically
        # zero here and the ratio would divide by zero.  Instead we divide by
        # the capped exposure n × V_sat (every satellite lost in one year),
        # which turns the field into a concentration measure: the portfolio
        # VaR95 as a share of the maximum possible loss.  Below a 5% horizon
        # hit probability the ratio is not informative and is reported as NaN.
        p_any_hit = 1.0 - float(np.prod(1.0 - np.clip(mean_hit_prob, 0.0, 1.0)))
        if p_any_hit > 0.05:
            sum_individual_var_95 = self.v_satellite_usd * n
            div_ratio = port_var_95 / sum_individual_var_95
        else:
            sum_individual_var_95 = float("nan")
            div_ratio = float("nan")

        return PortfolioRiskResult(
            portfolio_var_95=port_var_95,
            portfolio_var_99=port_var_99,
            portfolio_cvar_95=port_cvar_95,
            sum_individual_var_95=sum_individual_var_95,
            diversification_ratio=div_ratio,
            expected_portfolio_loss=float(np.mean(max_losses)),
            loss_samples=max_losses,
        )

    @staticmethod
    def _nearest_positive_definite(matrix: np.ndarray) -> np.ndarray:
        """Force a symmetric matrix to be positive definite.

        For symmetric input the SVD of A is A = V S Vᵀ, so ``Vᵀ diag(s) V``
        reconstructs A and the symmetrization changes nothing: this is a
        diagonal-jitter fallback, not Higham's (2002) alternating projection,
        and the result is shifted rather than "nearest".
        """
        A = (matrix + matrix.T) / 2
        _, s, V = linalg.svd(A)
        H = V.T @ np.diag(s) @ V
        A2 = (A + H) / 2
        A3 = (A2 + A2.T) / 2
        if PortfolioRiskModel._is_positive_definite(A3):
            return A3
        # Simple fallback: add small diagonal
        k = 1
        while not PortfolioRiskModel._is_positive_definite(A3 + k * np.eye(matrix.shape[0]) * 1e-6):
            k += 1
            if k > 1000:
                break
        return A3 + k * np.eye(matrix.shape[0]) * 1e-6

    @staticmethod
    def _is_positive_definite(matrix: np.ndarray) -> bool:
        try:
            linalg.cholesky(matrix, lower=True)
            return True
        except linalg.LinAlgError:
            return False
