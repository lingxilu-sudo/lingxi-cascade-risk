"""Audit probe 2: Monte Carlo convergence, dt bias, and tail spread."""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cascade_risk.config import Config
from cascade_risk.physics import (
    OrbitalShell, CollisionModel, DebrisGrowthModel, CascadeSimulator,
)
from cascade_risk.actuarial import LossModel, RiskMetricsCalculator

p = Config.from_yaml().physics
e = Config.from_yaml().economics
shell = OrbitalShell(p.altitude_km, p.shell_thickness_km)
cm = CollisionModel(shell, p.cross_section_large_m2, p.relative_velocity_km_s,
                    p.k_debris_mu, p.k_debris_sigma)


def run(n_paths, dt, seed=42):
    gm = DebrisGrowthModel(shell, cm, p.n_satellites, p.decay_rate_per_year)
    sim = CascadeSimulator(shell, cm, gm)
    t0 = time.time()
    r = sim.run(p.n_debris_large, n_paths, p.t_max_years, dt,
                p.decay_rate_uncertainty, seed)
    lm = LossModel(e.v_satellite_usd, e.n_policies,
                   e.correlation_coefficient, e.discount_rate)
    ld = lm.compute_loss_distribution(r.all_n_debris, p.n_debris_large,
                                      p.cross_section_large_m2,
                                      p.relative_velocity_km_s, shell.volume_km3)
    m = RiskMetricsCalculator().compute(ld.max_annual_losses,
                                        0.005 * e.v_satellite_usd * e.n_policies)
    return r, m, time.time() - t0


print("=" * 72)
print("M. Path-count convergence (seed=42, dt=0.1)")
print("=" * 72)
base = None
for n in (300, 1000, 2000):
    r, m, sec = run(n, 0.1)
    fin = r.all_n_debris[:, -1]
    if base is None:
        base = m.expected_loss
    print(f"paths={n:>4}: N50 mean={fin.mean():,.0f}  p5={np.percentile(fin,5):,.0f}  "
          f"p95={np.percentile(fin,95):,.0f}  max={fin.max():,.0f}")
    print(f"           EL=${m.expected_loss/1e6:.1f}M ({m.expected_loss/base:.3f}x of 300)  "
          f"VaR95=${m.var_95/1e6:.1f}M  CVaR95=${m.cvar_95/1e6:.1f}M  ({sec:.1f}s)")

print()
print("=" * 72)
print("N. Time-step bias (300 paths, seed=42)")
print("=" * 72)
for dt in (0.2, 0.1, 0.05):
    r, m, sec = run(300, dt)
    print(f"dt={dt}: N50={r.all_n_debris[:,-1].mean():,.0f}  EL=${m.expected_loss/1e6:.1f}M  "
          f"VaR95=${m.var_95/1e6:.1f}M  ({sec:.1f}s)")
