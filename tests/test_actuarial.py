"""Tests for the actuarial layer."""

import numpy as np
import pytest

from cascade_risk.actuarial.loss_model import LossModel
from cascade_risk.actuarial.risk_metrics import RiskMetricsCalculator
from cascade_risk.actuarial.premium_calculator import PremiumCalculator


class TestLossModel:
    def setup_method(self):
        self.model = LossModel(
            v_satellite_usd=50_000_000,
            n_policies=500,
            correlation_coefficient=0.3,
            discount_rate=0.04,
        )

    def test_hit_probability_positive(self):
        n_debris = np.array([36500.0])
        p = self.model.compute_hit_probability(
            n_debris, n_debris_0=36500,
            cross_section_m2=10.0, v_rel_km_s=10.0, shell_volume_km3=1e10,
        )
        assert p[0] > 0

    def test_hit_probability_bounded(self):
        n_debris = np.array([1e12])  # Extreme case
        p = self.model.compute_hit_probability(
            n_debris, n_debris_0=36500,
            cross_section_m2=10.0, v_rel_km_s=10.0, shell_volume_km3=1e10,
        )
        assert p[0] <= 1.0

    def test_loss_distribution_shape(self):
        all_n_debris = np.random.default_rng(42).normal(40000, 5000, (100, 50))
        all_n_debris = np.abs(all_n_debris)
        loss_dist = self.model.compute_loss_distribution(
            all_n_debris, n_debris_0=36500,
            cross_section_m2=10.0, v_rel_km_s=10.0, shell_volume_km3=1e10,
        )
        assert loss_dist.max_annual_losses.shape == (100,)
        assert loss_dist.annual_losses.shape == (100, 50)

    def test_historical_loss(self):
        loss = self.model.historical_loss(failure_rate=0.02)
        assert loss == 0.02 * 50_000_000 * 500


class TestRiskMetrics:
    def setup_method(self):
        self.calc = RiskMetricsCalculator()

    def test_basic_metrics(self):
        losses = np.random.default_rng(42).normal(1e6, 1e5, 10000)
        metrics = self.calc.compute(losses, historical_premium=5e5)
        assert metrics.expected_loss > 0
        assert metrics.var_95 > metrics.expected_loss
        assert metrics.cvar_95 >= metrics.var_95

    def test_cvar_geq_var(self):
        losses = np.random.default_rng(42).exponential(1e6, 10000)
        metrics = self.calc.compute(losses)
        assert metrics.cvar_95 >= metrics.var_95
        assert metrics.cvar_99 >= metrics.var_99

    def test_cascade_factor(self):
        losses = np.array([1e6] * 1000)
        metrics = self.calc.compute(losses, historical_premium=5e5)
        assert metrics.cascade_factor_mean == pytest.approx(2.0, rel=0.01)


class TestPremiumCalculator:
    def setup_method(self):
        from cascade_risk.actuarial.risk_metrics import RiskMetrics
        self.calc = PremiumCalculator(
            expense_loading=0.15,
            risk_loading_multiplier=1.5,
            discount_rate=0.04,
            n_policies=500,
        )
        self.metrics = RiskMetrics(
            expected_loss=1e6,
            loss_std=1e5,
            loss_median=1e6,
            var_95=1.2e6,
            var_99=1.3e6,
            cvar_95=1.25e6,
            cvar_99=1.3e6,
            historical_premium=5e5,
        )

    def test_premium_components_positive(self):
        premium = self.calc.compute_premium(self.metrics)
        assert premium.expected_loss > 0
        assert premium.risk_loading >= 0
        assert premium.capital_charge >= 0
        assert premium.expense_loading > 0
        assert premium.total_premium > 0

    def test_total_exceeds_el(self):
        premium = self.calc.compute_premium(self.metrics)
        assert premium.total_premium >= premium.expected_loss

    def test_cascade_factor(self):
        premium = self.calc.compute_premium(self.metrics)
        assert premium.cascade_factor > 1.0
