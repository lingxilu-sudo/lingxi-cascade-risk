# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Risk Metrics Calculator
========================
Computes actuarial risk metrics from loss distributions:
- Value at Risk (VaR) at multiple confidence levels
- Conditional VaR / Expected Shortfall (CVaR/ES)
- Extreme Value Theory (EVT) tail estimation using Generalized Pareto

References:
    McNeil, A.J. (1997). "Estimating the tails of loss severity
    distributions using extreme value theory." ASTIN Bulletin, 27(1), 117-137.
    Embrechts, P., Klüppelberg, C. & Mikosch, T. (1997). "Modelling
    Extremal Events." Springer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import stats


@dataclass
class RiskMetrics:
    """Complete set of actuarial risk metrics."""
    expected_loss: float
    loss_std: float
    loss_median: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    # EVT tail estimates
    evt_var_95: Optional[float] = None
    evt_var_99: Optional[float] = None
    evt_cvar_95: Optional[float] = None
    evt_shape_parameter: Optional[float] = None
    evt_scale_parameter: Optional[float] = None
    # Historical comparison
    historical_premium: float = 0.0
    cascade_factor_mean: float = 1.0
    cascade_factor_var95: float = 1.0


class RiskMetricsCalculator:
    """
    Computes comprehensive risk metrics from Monte Carlo loss samples.

    Parameters
    ----------
    confidence_levels : list[float]
        Confidence levels for VaR/CVaR (e.g., [0.95, 0.99]).
    evt_threshold_percentile : float
        Percentile above which to fit EVT (default 90).
    """

    def __init__(
        self,
        confidence_levels: list[float] = None,
        evt_threshold_percentile: float = 90.0,
    ):
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.evt_threshold_percentile = evt_threshold_percentile

    def compute(
        self,
        losses: np.ndarray,
        historical_premium: float = 0.0,
    ) -> RiskMetrics:
        """
        Compute full set of risk metrics from loss samples.

        Parameters
        ----------
        losses : np.ndarray
            Loss samples from Monte Carlo simulation (1D array).
        historical_premium : float
            Historical (non-cascade) premium for comparison.

        Returns
        -------
        RiskMetrics
            Complete risk metrics object.
        """
        metrics = RiskMetrics(
            expected_loss=float(np.mean(losses)),
            loss_std=float(np.std(losses)),
            loss_median=float(np.median(losses)),
            var_95=float(np.percentile(losses, 95)),
            var_99=float(np.percentile(losses, 99)),
            cvar_95=self._cvar(losses, 0.95),
            cvar_99=self._cvar(losses, 0.99),
            historical_premium=historical_premium,
        )

        # EVT tail estimation
        evt_result = self._fit_evt(losses)
        if evt_result is not None:
            shape, scale, threshold = evt_result
            metrics.evt_shape_parameter = shape
            metrics.evt_scale_parameter = scale
            metrics.evt_var_95 = self._evt_var(shape, scale, threshold, 0.95)
            metrics.evt_var_99 = self._evt_var(shape, scale, threshold, 0.99)
            metrics.evt_cvar_95 = self._evt_cvar(shape, scale, threshold, 0.95)

        # Cascade factors
        if historical_premium > 0:
            metrics.cascade_factor_mean = metrics.expected_loss / historical_premium
            metrics.cascade_factor_var95 = metrics.var_95 / historical_premium

        return metrics

    @staticmethod
    def _cvar(losses: np.ndarray, confidence: float) -> float:
        """
        Conditional VaR (Expected Shortfall): E[Loss | Loss > VaR].
        """
        var = np.percentile(losses, confidence * 100)
        tail = losses[losses >= var]
        return float(np.mean(tail)) if len(tail) > 0 else float(var)

    def _fit_evt(
        self, losses: np.ndarray
    ) -> Optional[tuple[float, float, float]]:
        """
        Fit Generalized Pareto Distribution to tail losses.

        Returns (shape, scale, threshold) or None if fit fails.
        """
        threshold = float(np.percentile(losses, self.evt_threshold_percentile))
        excesses = losses[losses > threshold] - threshold

        if len(excesses) < 10:
            return None

        try:
            shape, loc, scale = stats.genpareto.fit(excesses, floc=0)
            return float(shape), float(scale), threshold
        except Exception:
            return None

    @staticmethod
    def _evt_var(
        shape: float, scale: float, threshold: float, confidence: float
    ) -> float:
        """VaR from GPD fit."""
        n_exceedances_ratio = 1.0 - confidence  # Simplified
        if abs(shape) < 1e-10:
            return threshold + scale * (-np.log(1 - confidence))
        return threshold + scale / shape * (
            (1 - confidence) ** (-shape) - 1
        )

    @staticmethod
    def _evt_cvar(
        shape: float, scale: float, threshold: float, confidence: float
    ) -> float:
        """CVaR from GPD fit."""
        var = RiskMetricsCalculator._evt_var(shape, scale, threshold, confidence)
        if shape >= 1:
            return float("inf")  # CVaR undefined for shape >= 1
        if abs(shape) < 1e-10:
            return var + scale
        return var / (1 - shape) + (scale - shape * threshold) / (1 - shape)
