"""Tests for the sensitivity analysis module."""

import numpy as np
import pytest

from cascade_risk.analysis.sensitivity import SensitivityAnalyzer


class TestSobol:
    def test_recovers_analytic_indices(self):
        """For f = x1 + 2*x2 the exact indices are S = ST = (0.2, 0.8)."""
        result = SensitivityAnalyzer.sobol_analysis(
            lambda X: X[:, 0] + 2.0 * X[:, 1],
            [(0.0, 1.0), (0.0, 1.0)],
            ["x1", "x2"],
            n_samples=20000,
            rng=np.random.default_rng(0),
        )
        assert result.first_order_indices[0] == pytest.approx(0.2, abs=0.04)
        assert result.first_order_indices[1] == pytest.approx(0.8, abs=0.04)
        assert result.total_order_indices[0] == pytest.approx(0.2, abs=0.04)
        assert result.total_order_indices[1] == pytest.approx(0.8, abs=0.04)

    def test_ignores_irrelevant_variable(self):
        """A variable absent from the model must get ~0, not ~1.

        The previous pairing assigned S ~ 1 to an irrelevant variable
        because f(AB_j) = f(B) for that column.
        """
        result = SensitivityAnalyzer.sobol_analysis(
            lambda X: X[:, 0] + X[:, 2],
            [(0.0, 1.0)] * 3,
            ["x1", "unused", "x3"],
            n_samples=20000,
            rng=np.random.default_rng(1),
        )
        assert abs(result.first_order_indices[1]) < 0.02
        assert abs(result.total_order_indices[1]) < 0.02

    def test_first_order_plus_interaction_below_total(self):
        """For a pure interaction f = x1*x2, S_i < ST_i."""
        result = SensitivityAnalyzer.sobol_analysis(
            lambda X: X[:, 0] * X[:, 1],
            [(0.0, 1.0), (0.0, 1.0)],
            ["x1", "x2"],
            n_samples=20000,
            rng=np.random.default_rng(2),
        )
        assert result.first_order_indices[0] < result.total_order_indices[0]
        assert result.first_order_indices[1] < result.total_order_indices[1]
