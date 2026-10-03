# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Sensitivity Analysis
=====================
Implements both One-at-a-Time (OAT) and Sobol global sensitivity analysis.

Sobol indices decompose the output variance into contributions from
individual parameters and their interactions:
    S_i = V_i / V_total          (first-order / main effect)
    ST_i = 1 - V_~i / V_total    (total effect, including interactions)

References:
    Sobol, I.M. (2001). "Global sensitivity indices for nonlinear
    mathematical models." Mathematics and Computers in Simulation, 55(1-3), 271-280.
    Saltelli, A. et al. (2010). "Variance based sensitivity analysis
    of model output. Design and estimator for the total sensitivity index."
    Computer Physics Communications, 181(2), 259-270.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

import numpy as np


@dataclass
class SensitivityResult:
    """Results from sensitivity analysis."""
    parameter_name: str
    oat_impact: float                    # OAT premium range
    sobol_first_order: Optional[float] = None
    sobol_total_order: Optional[float] = None


@dataclass
class GlobalSensitivityResult:
    """Sobol sensitivity indices for all parameters."""
    parameter_names: list[str]
    first_order_indices: np.ndarray      # S_i
    total_order_indices: np.ndarray      # ST_i
    confidence_intervals: Optional[np.ndarray] = None


class SensitivityAnalyzer:
    """
    Performs sensitivity analysis on the cascade risk model.
    """

    # ------------------------------------------------------------------
    # One-at-a-Time (OAT)
    # ------------------------------------------------------------------

    @staticmethod
    def oat_analysis(
        param_name: str,
        param_values: np.ndarray,
        base_value: float,
        model_function: Callable[[str, float], float],
    ) -> np.ndarray:
        """
        One-at-a-time sensitivity: vary one parameter, measure output change.

        Parameters
        ----------
        param_name : str
            Name of the parameter to vary.
        param_values : np.ndarray
            Values to test.
        base_value : float
            Baseline value.
        model_function : callable
            Function that takes (param_name, value) and returns the metric.

        Returns
        -------
        np.ndarray
            Model output for each parameter value.
        """
        results = np.zeros(len(param_values))
        for i, val in enumerate(param_values):
            results[i] = model_function(param_name, val)
        return results

    # ------------------------------------------------------------------
    # Sobol Global Sensitivity (Saltelli sampling)
    # ------------------------------------------------------------------

    @staticmethod
    def sobol_analysis(
        model_function: Callable[[np.ndarray], np.ndarray],
        param_bounds: list[tuple[float, float]],
        param_names: list[str],
        n_samples: int = 1024,
        rng: Optional[np.random.Generator] = None,
    ) -> GlobalSensitivityResult:
        """
        Sobol sensitivity analysis using Saltelli sampling scheme.

        Parameters
        ----------
        model_function : callable
            Takes (n_samples × n_params) array, returns (n_samples,) outputs.
        param_bounds : list of (low, high) tuples
            Parameter ranges.
        param_names : list[str]
            Parameter names.
        n_samples : int
            Base sample size (must be power of 2 for best results).
        rng : np.random.Generator, optional

        Returns
        -------
        GlobalSensitivityResult
        """
        if rng is None:
            rng = np.random.default_rng()

        k = len(param_names)
        N = n_samples

        # Generate base samples (Sobol sequences would be ideal, use uniform here)
        A = np.zeros((N, k))
        B = np.zeros((N, k))
        for j, (low, high) in enumerate(param_bounds):
            A[:, j] = rng.uniform(low, high, N)
            B[:, j] = rng.uniform(low, high, N)

        # Evaluate model on A and B
        f_A = model_function(A)
        f_B = model_function(B)

        # Total variance
        f_all = np.concatenate([f_A, f_B])
        total_var = np.var(f_all)

        first_order = np.zeros(k)
        total_order = np.zeros(k)

        for j in range(k):
            # AB_j matrix: B with j-th column replaced by A's j-th column
            AB_j = B.copy()
            AB_j[:, j] = A[:, j]
            f_AB_j = model_function(AB_j)

            # First-order index: S_j = V[E[Y|X_j]] / V[Y]
            first_order[j] = np.mean(f_B * (f_AB_j - f_A)) / total_var if total_var > 0 else 0.0

            # Total-order index: ST_j = 1 - V[E[Y|X_~j]] / V[Y]
            total_order[j] = 1.0 - np.mean(f_A * (f_AB_j - f_B)) / total_var if total_var > 0 else 0.0

        # Clip to [0, 1]
        first_order = np.clip(first_order, 0.0, 1.0)
        total_order = np.clip(total_order, 0.0, 1.0)

        return GlobalSensitivityResult(
            parameter_names=param_names,
            first_order_indices=first_order,
            total_order_indices=total_order,
        )
