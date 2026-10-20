# -*- coding: utf-8 -*-
"""Baseline verification: reproduce every headline number without plotting.

Run:  python study/verify_baseline.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cascade_risk.config import Config  # noqa: E402
from cascade_risk.physics import (  # noqa: E402
    OrbitalShell, CollisionModel, DebrisGrowthModel, CascadeSimulator,
)
from cascade_risk.actuarial import (  # noqa: E402
    LossModel, RiskMetricsCalculator, PremiumCalculator,
)


def fmt(x: float) -> str:
    return f"${x / 1e6:.1f}M"


def main() -> None:
    cfg = Config.from_yaml()
    p, e = cfg.physics, cfg.economics

    shell = OrbitalShell(p.altitude_km, p.shell_thickness_km)
    cm = CollisionModel(
        shell, p.cross_section_large_m2, p.relative_velocity_km_s,
        p.k_debris_mu, p.k_debris_sigma,
    )
    gm = DebrisGrowthModel(
        shell, cm, p.n_satellites, p.decay_rate_per_year,
    )
    sim = CascadeSimulator(shell, cm, gm)

    print("=== GEOMETRY & RATES (hand-check anchors) ===")
    print(f"V_shell            = {shell.volume_km3:.4e} km3")
    print(f"v_circ(800 km)     = {shell.orbital_velocity_km_s:.3f} km/s")
    print(f"R_ds(N0)           = {cm.collision_rate(p.n_debris_large, p.n_satellites):.3f} /yr")
    print(f"R_dd(N0)           = {cm.debris_debris_collision_rate(p.n_debris_large):.3f} /yr")
    print(f"K (code criterion) = {shell.carrying_capacity(p.cross_section_large_m2, p.relative_velocity_km_s, p.decay_rate_per_year):.0f}")

    print("\n=== MONTE CARLO ===")
    t0 = time.time()
    res = sim.run(
        p.n_debris_large, p.n_monte_carlo_paths, p.t_max_years,
        p.dt_years, p.decay_rate_uncertainty, p.random_seed,
    )
    print(f"elapsed            = {time.time() - t0:.1f}s")
    st = res.final_debris_stats()
    for k, v in st.items():
        print(f"final {k:6s}     = {v:,.0f}")
    mean_growth = st["mean"] / p.n_debris_large
    print(f"growth vs N0       = {mean_growth:.2f}x")

    print("\n=== LOSS & METRICS ===")
    lm = LossModel(
        e.v_satellite_usd, e.n_policies,
        e.correlation_coefficient, e.discount_rate,
    )
    ld = lm.compute_loss_distribution(
        all_n_debris=res.all_n_debris,
        cross_section_m2=p.cross_section_large_m2,
        v_rel_km_s=p.relative_velocity_km_s,
        shell_volume_km3=shell.volume_km3,
        dt_years=p.dt_years,
    )
    hist = lm.historical_loss(e.historical_failure_rate)
    rc = RiskMetricsCalculator(evt_threshold_percentile=e.evt_threshold_percentile)
    m = rc.compute(ld.max_annual_losses, hist)

    print(f"p_hit(t=0)         = {ld.hit_probabilities[0, 0] * 100:.4f}%")
    print(f"p_hit(t=50) mean   = {ld.hit_probabilities[:, -1].mean() * 100:.3f}%")
    print(f"EL                 = {fmt(m.expected_loss)}")
    print(f"loss std           = {fmt(m.loss_std)}")
    print(f"VaR95              = {fmt(m.var_95)}")
    print(f"CVaR95             = {fmt(m.cvar_95)}")
    print(f"VaR99              = {fmt(m.var_99)}")
    print(f"CVaR99             = {fmt(m.cvar_99)}")
    if m.evt_var_95 is not None:
        print(f"EVT VaR95          = {fmt(m.evt_var_95)}")
        print(f"EVT VaR99          = {fmt(m.evt_var_99)}")
        print(f"EVT CVaR95         = {fmt(m.evt_cvar_95)}")
        print(f"EVT xi             = {m.evt_shape_parameter:.3f}")

    print("\n=== PREMIUM (Solvency-II-style decomposition) ===")
    pc = PremiumCalculator(
        e.expense_loading, e.risk_loading_multiplier,
        e.discount_rate, e.n_policies,
    )
    pb = pc.compute_premium(m)
    print(f"EL                 = {fmt(pb.expected_loss)}")
    print(f"risk loading       = {fmt(pb.risk_loading)}")
    print(f"capital charge     = {fmt(pb.capital_charge)}")
    print(f"expense loading    = {fmt(pb.expense_loading)}")
    print(f"TOTAL              = {fmt(pb.total_premium)}")
    print(f"per policy         = {fmt(pb.premium_per_policy)}")
    print(f"historical         = {fmt(pb.historical_premium)}")
    print(f"CASCADE FACTOR     = {pb.cascade_factor:.2f}x")
    print(f"gap                = {fmt(pb.total_premium - pb.historical_premium)}")


if __name__ == "__main__":
    main()
