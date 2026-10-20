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
            n_debris,
            cross_section_m2=10.0, v_rel_km_s=10.0, shell_volume_km3=1e10,
        )
        assert p[0] > 0

    def test_hit_probability_bounded(self):
        n_debris = np.array([1e12])  # Extreme case
        p = self.model.compute_hit_probability(
            n_debris,
            cross_section_m2=10.0, v_rel_km_s=10.0, shell_volume_km3=1e10,
        )
        assert p[0] <= 1.0

    def test_loss_distribution_shape(self):
        all_n_debris = np.random.default_rng(42).normal(40000, 5000, (100, 50))
        all_n_debris = np.abs(all_n_debris)
        loss_dist = self.model.compute_loss_distribution(
            all_n_debris,
            cross_section_m2=10.0, v_rel_km_s=10.0, shell_volume_km3=1e10,
        )
        assert loss_dist.max_annual_losses.shape == (100,)
        assert loss_dist.annual_losses.shape == (100, 50)

    def test_historical_loss(self):
        loss = self.model.historical_loss(failure_rate=0.005)
        assert loss == 0.005 * 50_000_000 * 500

    def test_aggregate_losses_use_calendar_time_and_dt(self):
        """Aggregate NPV must discount by t*dt and integrate with a dt factor.

        A regression test for two bugs: discounting the step index as if it
        were years, and summing 0.1-year rates as if each step were a year.
        """
        n_debris = np.full((1, 3), 36500.0)
        loss_dist = self.model.compute_loss_distribution(
            n_debris,
            cross_section_m2=10.0, v_rel_km_s=10.0,
            shell_volume_km3=1e10, dt_years=0.5,
        )
        annual = loss_dist.annual_losses[0, 0]
        expected = annual * (1 + 1.04 ** -0.5 + 1.04 ** -1.0) * 0.5
        assert loss_dist.aggregate_losses[0] == pytest.approx(expected, rel=1e-12)


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

    def test_evt_var_uses_exceedance_ratio(self):
        """EVT VaR must use zeta = N_u/n, not treat 1-p as a conditional tail.

        Omitting zeta overstates the tail probability by 1/zeta and inflates
        the quantile; this test pins the corrected POT formula to the
        empirical quantile.
        """
        rng = np.random.default_rng(0)
        losses = rng.lognormal(mean=14.0, sigma=1.0, size=20000)
        metrics = self.calc.compute(losses)
        assert metrics.evt_var_95 == pytest.approx(
            np.percentile(losses, 95), rel=0.08)
        assert metrics.evt_var_99 == pytest.approx(
            np.percentile(losses, 99), rel=0.10)

        # Direct check on the formula: with zeta=0.1 the tail probability is
        # divided by 0.1, so the quantile must be strictly lower.
        with_zeta = RiskMetricsCalculator._evt_var(0.1, 1.0, 10.0, 0.95, 0.1)
        without_zeta = RiskMetricsCalculator._evt_var(0.1, 1.0, 10.0, 0.95, 1.0)
        assert with_zeta < without_zeta


class TestPortfolioRisk:
    def test_diversification_ratio_is_defined(self):
        """A single-year Bernoulli VaR is 0 when p < 5%, so the old
        denominator was always zero and the ratio silently returned 1.0."""
        from cascade_risk.actuarial.portfolio_risk import PortfolioRiskModel

        model = PortfolioRiskModel(
            n_policies=500, correlation_coefficient=0.3,
            v_satellite_usd=50_000_000,
        )
        result = model.simulate_portfolio_losses(
            np.full((1, 10), 0.0366), n_simulations=4000,
            rng=np.random.default_rng(0),
        )
        assert result.sum_individual_var_95 > 0
        assert 0.0 < result.diversification_ratio < 1.0


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
