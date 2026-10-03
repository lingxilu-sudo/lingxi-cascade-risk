"""Tests for the physics layer."""

import numpy as np
import pytest

from cascade_risk.physics.orbital_shell import OrbitalShell
from cascade_risk.physics.collision_model import CollisionModel
from cascade_risk.physics.debris_growth import DebrisGrowthModel


class TestOrbitalShell:
    def test_volume_positive(self):
        shell = OrbitalShell(altitude_km=800, thickness_km=200)
        assert shell.volume_km3 > 0

    def test_volume_reasonable(self):
        shell = OrbitalShell(altitude_km=800, thickness_km=200)
        # Volume should be on order of 10^10 km³
        assert 1e9 < shell.volume_km3 < 1e12

    def test_orbital_velocity(self):
        shell = OrbitalShell(altitude_km=800)
        v = shell.orbital_velocity_km_s
        # LEO velocity should be ~7.5 km/s
        assert 7.0 < v < 8.0

    def test_number_density(self):
        shell = OrbitalShell(altitude_km=800, thickness_km=200)
        density = shell.number_density(36500)
        assert density > 0
        assert density < 1  # Very sparse

    def test_carrying_capacity(self):
        shell = OrbitalShell(altitude_km=800, thickness_km=200)
        K = shell.carrying_capacity(cross_section_m2=10.0, v_rel_km_s=10.0)
        assert K > 0


class TestCollisionModel:
    def setup_method(self):
        self.shell = OrbitalShell(altitude_km=800, thickness_km=200)
        self.model = CollisionModel(
            shell=self.shell,
            cross_section_m2=10.0,
            v_rel_km_s=10.0,
            k_debris_mu=5.5,
            k_debris_sigma=0.8,
        )

    def test_collision_rate_positive(self):
        rate = self.model.collision_rate(n_debris=36500, n_satellites=8000)
        assert rate > 0

    def test_collision_rate_scales_with_debris(self):
        r1 = self.model.collision_rate(10000, 8000)
        r2 = self.model.collision_rate(20000, 8000)
        assert r2 > r1  # More debris → more collisions

    def test_debris_debris_rate(self):
        rate = self.model.debris_debris_collision_rate(n_debris=36500)
        assert rate >= 0

    def test_debris_debris_rate_zero_for_small_n(self):
        rate = self.model.debris_debris_collision_rate(n_debris=1)
        assert rate == 0.0

    def test_poisson_events(self):
        rng = np.random.default_rng(42)
        n_events = self.model.poisson_collision_events(
            n_debris=36500, n_satellites=8000, dt_years=0.01, rng=rng
        )
        assert n_events >= 0

    def test_hit_probability_bounded(self):
        p = self.model.hit_probability_per_year(n_debris=36500, n_satellites=8000)
        assert 0 <= p <= 1.0

    def test_generate_fragments_positive(self):
        rng = np.random.default_rng(42)
        n = self.model.generate_fragments(rng)
        assert n >= 1


class TestDebrisGrowth:
    def setup_method(self):
        self.shell = OrbitalShell(altitude_km=800, thickness_km=200)
        self.collision_model = CollisionModel(
            shell=self.shell, cross_section_m2=10.0, v_rel_km_s=10.0,
        )
        self.growth_model = DebrisGrowthModel(
            shell=self.shell,
            collision_model=self.collision_model,
            n_satellites=8000,
            decay_rate_per_year=0.005,
        )

    def test_trajectory_shape(self):
        rng = np.random.default_rng(42)
        times, debris, collisions = self.growth_model.simulate_trajectory(
            n_debris_0=36500, t_max_years=1.0, dt_years=0.1, rng=rng
        )
        assert len(times) == len(debris) == len(collisions)
        assert times[0] == 0.0
        assert times[-1] == pytest.approx(1.0, abs=0.1)

    def test_debris_non_negative(self):
        rng = np.random.default_rng(42)
        _, debris, _ = self.growth_model.simulate_trajectory(
            n_debris_0=36500, t_max_years=10.0, dt_years=0.1, rng=rng
        )
        assert np.all(debris >= 0)

    def test_debris_grows_with_collisions(self):
        rng = np.random.default_rng(42)
        _, debris, collisions = self.growth_model.simulate_trajectory(
            n_debris_0=36500, t_max_years=50.0, dt_years=0.1, rng=rng
        )
        # With collisions, debris should generally increase
        assert debris[-1] >= debris[0] * 0.5  # At least not much less
