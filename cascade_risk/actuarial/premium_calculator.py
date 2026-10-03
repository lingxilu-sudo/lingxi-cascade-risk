# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Premium Calculator
===================
Computes risk-adjusted insurance premiums using the Solvency II framework:

    Premium = EL + Risk Loading + Capital Charge + Expense Loading

where:
    EL = Expected Loss (pure premium)
    Risk Loading = multiplier × (CVaR - EL)
    Capital Charge = cost of holding regulatory capital
    Expense Loading = fixed percentage for admin/profit

References:
    European Commission (2009). "Solvency II Directive." 2009/138/EC.
    Swiss Re (2019). "sigma: Insurance and space."
    International Actuarial Association (2022). "Risk Classification
    for Insurance Products."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from cascade_risk.actuarial.risk_metrics import RiskMetrics


@dataclass
class PremiumBreakdown:
    """Detailed breakdown of insurance premium components."""
    expected_loss: float            # Pure premium (EL)
    risk_loading: float             # CVaR-based risk loading
    capital_charge: float           # Cost of regulatory capital
    expense_loading: float          # Admin + profit loading
    total_premium: float            # Sum of all components
    premium_per_policy: float       # Per-satellite premium
    # Comparison
    historical_premium: float
    cascade_factor: float
    # Time-varying
    premium_trajectory: Optional[np.ndarray] = None


class PremiumCalculator:
    """
    Computes risk-adjusted insurance premiums.

    Parameters
    ----------
    expense_loading : float
        Expense/profit loading as fraction of EL (e.g., 0.15 = 15%).
    risk_loading_multiplier : float
        Multiplier on (CVaR - EL) for risk loading.
    discount_rate : float
        Annual discount rate for NPV calculations.
    n_policies : int
        Number of insured satellites.
    """

    def __init__(
        self,
        expense_loading: float = 0.15,
        risk_loading_multiplier: float = 1.5,
        discount_rate: float = 0.04,
        n_policies: int = 500,
    ):
        self.expense_loading = expense_loading
        self.risk_loading_multiplier = risk_loading_multiplier
        self.discount_rate = discount_rate
        self.n_policies = n_policies

    def compute_premium(
        self,
        metrics: RiskMetrics,
    ) -> PremiumBreakdown:
        """
        Compute full premium breakdown from risk metrics.

        Premium = EL + RiskLoading + CapitalCharge + ExpenseLoading

        Parameters
        ----------
        metrics : RiskMetrics
            Computed risk metrics from Monte Carlo simulation.

        Returns
        -------
        PremiumBreakdown
            Detailed premium decomposition.
        """
        el = metrics.expected_loss

        # Risk loading: based on CVaR (tail risk surcharge)
        risk_loading = self.risk_loading_multiplier * (metrics.cvar_95 - el)
        risk_loading = max(risk_loading, 0.0)

        # Capital charge: cost of holding capital at VaR99 level
        # Assuming cost of capital = discount_rate
        capital_required = metrics.var_99 - el
        capital_charge = self.discount_rate * max(capital_required, 0.0)

        # Expense loading
        expense = self.expense_loading * el

        total = el + risk_loading + capital_charge + expense

        cascade_factor = total / metrics.historical_premium if metrics.historical_premium > 0 else 1.0

        return PremiumBreakdown(
            expected_loss=el,
            risk_loading=risk_loading,
            capital_charge=capital_charge,
            expense_loading=expense,
            total_premium=total,
            premium_per_policy=total / self.n_policies if self.n_policies > 0 else total,
            historical_premium=metrics.historical_premium,
            cascade_factor=cascade_factor,
        )

    def compute_time_varying_premium(
        self,
        annual_losses: np.ndarray,
        historical_premium: float,
    ) -> np.ndarray:
        """
        Compute time-varying premium trajectory.

        For each time step, compute the premium based on the median
        loss across all Monte Carlo paths at that time.

        Parameters
        ----------
        annual_losses : np.ndarray
            (n_paths, n_steps) annual loss array.
        historical_premium : float
            Historical baseline premium.

        Returns
        -------
        np.ndarray
            Premium at each time step.
        """
        n_paths, n_steps = annual_losses.shape
        median_losses = np.median(annual_losses, axis=0)

        premiums = np.zeros(n_steps)
        for t in range(n_steps):
            el = median_losses[t]
            risk_loading = self.risk_loading_multiplier * max(el * 0.1, 0)
            expense = self.expense_loading * el
            premiums[t] = el + risk_loading + expense

        return premiums

    def npv_of_premiums(
        self,
        premium_trajectory: np.ndarray,
        dt_years: float = 0.01,
    ) -> float:
        """
        Net Present Value of the premium trajectory.
        """
        discount_factors = np.array([
            1.0 / (1.0 + self.discount_rate) ** (t * dt_years)
            for t in range(len(premium_trajectory))
        ])
        return float(np.sum(premium_trajectory * discount_factors * dt_years))
