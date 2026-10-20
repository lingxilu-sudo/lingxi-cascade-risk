"""Audit probe 3: sensitivity of the headline to the initial debris count.

The paper injects the global >10 cm catalogue (36,500) into a single
700-900 km shell.  This probe asks what happens if only a fraction of the
catalogue actually resides in that shell.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cascade_risk.config import Config
from cascade_risk.physics import (
    OrbitalShell, CollisionModel, DebrisGrowthModel, CascadeSimulator,
)
from cascade_risk.actuarial import LossModel, RiskMetricsCalculator, PremiumCalculator

p = Config.from_yaml().physics
e = Config.from_yaml().economics
shell = OrbitalShell(p.altitude_km, p.shell_thickness_km)
cm = CollisionModel(shell, p.cross_section_large_m2, p.relative_velocity_km_s,
                    p.k_debris_mu, p.k_debris_sigma)

print("N0 sensitivity (300 paths, seed=42)")
print(f"{'N0':>8} {'N50':>12} {'growth':>8} {'EL $M':>9} {'VaR95 $M':>10} {'factor':>8}")
for n0 in (8_000, 10_000, 12_000, 20_000, 36_500):
    gm = DebrisGrowthModel(shell, cm, p.n_satellites, p.decay_rate_per_year)
    r = CascadeSimulator(shell, cm, gm).run(
        n0, 300, p.t_max_years, p.dt_years, p.decay_rate_uncertainty, 42)
    lm = LossModel(e.v_satellite_usd, e.n_policies,
                   e.correlation_coefficient, e.discount_rate)
    ld = lm.compute_loss_distribution(r.all_n_debris, n0, p.cross_section_large_m2,
                                      p.relative_velocity_km_s, shell.volume_km3)
    m = RiskMetricsCalculator().compute(ld.max_annual_losses,
                                        0.005 * e.v_satellite_usd * e.n_policies)
    prem = PremiumCalculator(e.expense_loading, e.risk_loading_multiplier,
                             e.discount_rate, e.n_policies).compute_premium(m)
    print(f"{n0:>8,} {r.all_n_debris[:,-1].mean():>12,.0f} "
          f"{r.all_n_debris[:,-1].mean()/n0:>7.1f}x "
          f"{m.expected_loss/1e6:>9.1f} {m.var_95/1e6:>10.1f} "
          f"{prem.cascade_factor:>7.2f}x")
