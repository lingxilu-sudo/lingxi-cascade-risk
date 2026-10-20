"""Audit probe: quantify suspected bugs / rigor gaps in cascade_risk.

Run: python study/audit_probe.py
Reports numbers only; no files are modified.
"""

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cascade_risk.config import Config
from cascade_risk.physics import (
    OrbitalShell,
    CollisionModel,
    DebrisGrowthModel,
    CascadeSimulator,
)
from cascade_risk.actuarial import LossModel, RiskMetricsCalculator

p = Config.from_yaml().physics
e = Config.from_yaml().economics

shell = OrbitalShell(p.altitude_km, p.shell_thickness_km)
cm = CollisionModel(
    shell, p.cross_section_large_m2, p.relative_velocity_km_s,
    p.k_debris_mu, p.k_debris_sigma,
)
gm = DebrisGrowthModel(shell, cm, p.n_satellites, p.decay_rate_per_year)
sim = CascadeSimulator(shell, cm, gm)

print("=" * 72)
print("A. BASELINE RUN (used by several probes)")
print("=" * 72)
res = sim.run(
    p.n_debris_large, n_paths=1000, t_max_years=p.t_max_years,
    dt_years=p.dt_years, decay_uncertainty=p.decay_rate_uncertainty,
    seed=p.random_seed,
)
lm = LossModel(e.v_satellite_usd, e.n_policies, e.correlation_coefficient, e.discount_rate)
ld = lm.compute_loss_distribution(
    res.all_n_debris, p.n_debris_large, p.cross_section_large_m2,
    p.relative_velocity_km_s, shell.volume_km3,
)
rm = RiskMetricsCalculator(evt_threshold_percentile=e.evt_threshold_percentile)
m = rm.compute(ld.max_annual_losses, 0.005 * e.v_satellite_usd * e.n_policies)
print(f"N50 mean={res.all_n_debris[:, -1].mean():,.0f}  EL=${m.expected_loss/1e6:.1f}M")
print(f"VaR95=${m.var_95/1e6:.1f}M  CVaR95=${m.cvar_95/1e6:.1f}M")
print(f"EVT VaR95=${m.evt_var_95/1e6:.1f}M  xi={m.evt_shape_parameter:.4f}")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("B. EVT: code formula vs standard POT formula (exceedance ratio zeta)")
print("=" * 72)
losses = ld.max_annual_losses
u = np.percentile(losses, 90)
exc = losses[losses > u] - u
xi, loc, beta = stats.genpareto.fit(exc, floc=0)
zeta = len(exc) / len(losses)
print(f"threshold u=${u/1e6:.1f}M  n_exc={len(exc)}  zeta={zeta:.4f}")
print(f"GPD fit: xi={xi:.4f}  beta=${beta/1e6:.1f}M")


def evt_var_std(conf):
    if abs(xi) < 1e-10:
        return u + beta * np.log((1 - conf) / zeta) * -1
    return u + beta / xi * (((1 - conf) / zeta) ** (-xi) - 1)


for conf in (0.95, 0.99):
    fixed = rm._evt_var(xi, beta, u, conf, zeta)
    omitting_zeta = rm._evt_var(xi, beta, u, conf)  # old behaviour: zeta=1
    std = evt_var_std(conf)
    emp = np.percentile(losses, conf * 100)
    print(f"p={conf}: corrected=${fixed/1e6:.1f}M  omitting zeta=${omitting_zeta/1e6:.1f}M  "
          f"standard=${std/1e6:.1f}M  empirical=${emp/1e6:.1f}M")
print(f"EVT CVaR95 corrected=${rm._evt_cvar(xi, beta, u, 0.95, zeta)/1e6:.1f}M  "
      f"empirical=${np.mean(losses[losses >= np.percentile(losses, 95)])/1e6:.1f}M")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("C. Paper Eq. (portfolio aggregation) evaluated with baseline numbers")
print("=" * 72)
p_hit_50 = res.all_n_debris[:, -1].mean() * p.cross_section_large_m2 * 1e-6 \
    * p.relative_velocity_km_s * 31557600.0 / shell.volume_km3
n = e.n_policies
rho = e.correlation_coefficient
paper_loss = p_hit_50 * e.v_satellite_usd * n * (1 + (n - 1) * rho) / n
print(f"p_hit(50)={p_hit_50:.5f}  factor=(1+(n-1)rho)/n={(1+(n-1)*rho)/n:.4f}")
print(f"paper formula => ${paper_loss/1e6:.1f}M   code => ${p_hit_50*e.v_satellite_usd*n/1e6:.1f}M")
print("ratio =", round(paper_loss / (p_hit_50 * e.v_satellite_usd * n), 4))

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("D. Deterministic backbone: finite-time singularity and N0 sensitivity")
print("=" * 72)
k_ds = np.exp(p.k_debris_mu + p.k_debris_sigma**2 / 2)
k_dd = np.exp(1.1 + 0.5**2 / 2)
q = p.cross_section_large_m2 * 1e-6 * p.relative_velocity_km_s * 31557600.0 / shell.volume_km3
b = k_ds * p.n_satellites * q
a = 0.5 * k_dd * q
alpha = b - p.decay_rate_per_year


def ode_n(n0, t):
    e_at = np.exp(alpha * t)
    return n0 * e_at / (1 - (a * n0 / alpha) * (e_at - 1))


t_star = np.log(1 + alpha / (a * p.n_debris_large)) / alpha
print(f"k_ds={k_ds:.2f}  k_dd={k_dd:.2f}  q={q:.4e}  b={b:.5f}  a={a:.4e}")
print(f"t* (blow-up) = {t_star:.1f} years")
for t in (50, 55, 60):
    print(f"ODE N({t}) = {ode_n(p.n_debris_large, t):,.0f}  ({ode_n(p.n_debris_large, t)/p.n_debris_large:.1f}x)")
for n0 in (10_000, 20_000, 36_500):
    print(f"N0={n0:>6,}: N(50)={ode_n(n0,50):,.0f} ({ode_n(n0,50)/n0:.1f}x)  t*={np.log(1+alpha/(a*n0))/alpha:.1f} yr")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("E. Portfolio claim-frequency noise: deterministic expected count vs Binomial")
print("=" * 72)
rng = np.random.default_rng(7)
p_hit_paths = ld.hit_probabilities  # (paths, steps)
hits = rng.binomial(e.n_policies, np.clip(p_hit_paths, 0, 1))
binom_losses = hits.max(axis=1) * e.v_satellite_usd
print(f"deterministic: EL=${ld.max_annual_losses.mean()/1e6:.1f}M  "
      f"VaR95=${np.percentile(ld.max_annual_losses,95)/1e6:.1f}M  "
      f"sd=${ld.max_annual_losses.std()/1e6:.1f}M")
print(f"binomial     : EL=${binom_losses.mean()/1e6:.1f}M  "
      f"VaR95=${np.percentile(binom_losses,95)/1e6:.1f}M  "
      f"sd=${binom_losses.std()/1e6:.1f}M")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("F. aggregate_losses discounting: step index vs calendar time")
print("=" * 72)
wrong = ld.aggregate_losses.mean()  # ld was built with default dt_years=1.0
ld_correct = lm.compute_loss_distribution(
    res.all_n_debris, p.n_debris_large, p.cross_section_large_m2,
    p.relative_velocity_km_s, shell.volume_km3, p.dt_years,
)
right = ld_correct.aggregate_losses.mean()
print(f"step-as-year (old) = ${wrong/1e6:.1f}M   corrected (t*dt) = ${right/1e6:.1f}M   "
      f"ratio = {right/wrong:.1f}x")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("G. Config typo guard (unknown key must raise, not be dropped)")
print("=" * 72)
from unittest.mock import patch
bad = {"physics": {"shell_thicknes_km": 300.0}, "economics": {}}
with patch("cascade_risk.config._load_yaml", return_value=bad):
    try:
        Config.from_yaml("synthetic-typo.yaml")
    except ValueError as exc:
        print("typo rejected:", exc)
    else:
        print("ERROR: typo was silently accepted")

# A misspelled *section* is the same failure mode one level up: without a
# top-level guard the whole physics block silently falls back to defaults.
bad_section = {"physic": {"altitude_km": 900.0}, "economics": {}}
with patch("cascade_risk.config._load_yaml", return_value=bad_section):
    try:
        Config.from_yaml("synthetic-section-typo.yaml")
    except ValueError as exc:
        print("section typo rejected:", exc)
    else:
        print("ERROR: section typo was silently accepted")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("H. Calibration helper output vs configured yield")
print("=" * 72)
from cascade_risk.calibration.historical_events import CalibrationEngine
cal = CalibrationEngine().calibrate_k_debris()
print(f"calibrate_k_debris() -> mu={cal['mu']:.3f}, sigma={cal['sigma']:.3f}")
print(f"config k_debris       -> mu={p.k_debris_mu}, sigma={p.k_debris_sigma}")
print(f"median yield: calibrated={np.exp(cal['mu']):.1f}  configured={np.exp(p.k_debris_mu):.1f}")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("I. carrying_capacity responds to the configured decay rate")
print("=" * 72)
K_base = shell.carrying_capacity(10.0, 10.0, 0.005)
K_fast = shell.carrying_capacity(10.0, 10.0, 0.05)
print(f"K(decay=0.005) = {K_base:,.0f}")
print(f"K(decay=0.05)  = {K_fast:,.0f}  (10x larger: faster decay raises the sustainable population)")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("J. dt / horizon consistency when t_max is not a multiple of dt")
print("=" * 72)
for dt, tmax in ((0.1, 50.0), (0.3, 50.0), (0.07, 1.0)):
    n_steps = int(tmax / dt) + 1
    times = np.linspace(0, tmax, n_steps)
    print(f"dt={dt}, tmax={tmax}: n_steps={n_steps}, effective spacing={times[1]-times[0]:.4f}")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("K. Hit-probability clipping: min(flux,1) vs 1-exp(-flux)")
print("=" * 72)
flux0 = p.n_debris_large * q
flux50 = res.all_n_debris[:, -1].mean() * q
for label, f in (("t=0", flux0), ("t=50", flux50)):
    print(f"{label}: flux={f:.5f}  min={min(f,1):.6f}  1-exp={1-np.exp(-f):.6f}  "
          f"reldiff={(min(f,1)-(1-np.exp(-f)))/f*100:.3f}%")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("L. PortfolioRiskModel cost estimate (single step)")
print("=" * 72)
import time
from cascade_risk.actuarial.portfolio_risk import PortfolioRiskModel
pr = PortfolioRiskModel(e.n_policies, e.correlation_coefficient, e.v_satellite_usd)
hit1 = np.full((1, 1), 0.01)
t0 = time.time()
pr.simulate_portfolio_losses(hit1, n_simulations=10000, rng=np.random.default_rng(0))
per_step = time.time() - t0
print(f"one time step, n_sim=10000, n=500: {per_step:.2f}s")
print(f"501 steps projected: {per_step*501/60:.1f} min")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("M. Time alignment: 'worst-year' sample vs a static annual benchmark")
print("=" * 72)
annual = ld.annual_losses  # (paths, steps), a rate per year
idx25 = int(25.0 / p.dt_years)
idx50 = annual.shape[1] - 1
el_t0 = annual[:, 0].mean()
el_t25 = annual[:, idx25].mean()
el_t50 = annual[:, idx50].mean()
el_max = ld.max_annual_losses.mean()
bench = 0.005 * e.v_satellite_usd * e.n_policies
print(f"E[L(t=0)]  = ${el_t0/1e6:,.1f}M   vs static benchmark ${bench/1e6:,.1f}M  "
      f"(model/bench = {el_t0/bench:.2f}x)")
print(f"E[L(t=25)] = ${el_t25/1e6:,.1f}M  ({el_t25/bench:.2f}x benchmark)")
print(f"E[L(t=50)] = ${el_t50/1e6:,.1f}M  ({el_t50/bench:.2f}x benchmark)")
print(f"E[max_t L] = ${el_max/1e6:,.1f}M  ({el_max/bench:.2f}x benchmark)  <- headline EL")
frac_at_end = np.mean(np.argmax(annual, axis=1) == idx50)
print(f"share of paths whose worst year is the final step: {frac_at_end*100:.1f}%")
print("=> the headline is a peak-horizon annual premium, not a today premium;")
print("   at t=0 the model's fair expected loss is below the static benchmark.")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("N. Path monotonicity: is N(t) really monotone? (300 paths, seed=42)")
print("=" * 72)
gm2 = DebrisGrowthModel(shell, cm, p.n_satellites, p.decay_rate_per_year)
sim2 = CascadeSimulator(shell, cm, gm2)
r2 = sim2.run(p.n_debris_large, 300, p.t_max_years, p.dt_years,
              p.decay_rate_uncertainty, 42)
d2 = r2.all_n_debris
diffs = np.diff(d2, axis=1)
print(f"share of steps with a decrease: {np.mean(diffs < 0)*100:.2f}%")
print(f"paths with at least one decrease: {np.mean((diffs < 0).any(axis=1))*100:.1f}%")
print(f"mean decreases per path: {np.mean((diffs < 0).sum(axis=1)):.1f}")
print(f"share of paths whose maximum is the final step: "
      f"{np.mean(np.argmax(d2, axis=1) == d2.shape[1]-1)*100:.1f}%")
print("=> paths are NOT monotone (decay-only steps), but the path maximum")
print("   still lands on the final step, which is what the loss sample uses.")

# ----------------------------------------------------------------------
print()
print("=" * 72)
print("O. DD term: how much of the headline rests on the DD assumptions?")
print("=" * 72)
# Two optimistic choices in the DD channel: (a) the ~3 fragments per DD
# event are added to the >10 cm catalogue count; (b) DS and DD share the
# 10 m2 satellite cross-section.  Re-run the 1,000-path baseline with each
# assumption relaxed.
import cascade_risk.physics.debris_growth as dg


def _dd_variant(tag, dd_mu=None, dd_rate_scale=1.0):
    cm_v = CollisionModel(shell, p.cross_section_large_m2,
                          p.relative_velocity_km_s,
                          p.k_debris_mu, p.k_debris_sigma)
    if dd_rate_scale != 1.0:
        orig = cm_v.debris_debris_collision_rate
        cm_v.debris_debris_collision_rate = (
            lambda n, f=dd_rate_scale, o=orig: f * o(n))
    gm_v = DebrisGrowthModel(shell, cm_v, p.n_satellites, p.decay_rate_per_year)
    old_mu = dg.DD_FRAGMENT_MU
    if dd_mu is not None:
        dg.DD_FRAGMENT_MU = dd_mu
    try:
        r_v = CascadeSimulator(shell, cm_v, gm_v).run(
            p.n_debris_large, 1000, p.t_max_years, p.dt_years,
            p.decay_rate_uncertainty, 42)
    finally:
        dg.DD_FRAGMENT_MU = old_mu
    lm_v = LossModel(e.v_satellite_usd, e.n_policies,
                     e.correlation_coefficient, e.discount_rate)
    ld_v = lm_v.compute_loss_distribution(
        r_v.all_n_debris, p.n_debris_large, p.cross_section_large_m2,
        p.relative_velocity_km_s, shell.volume_km3, p.dt_years)
    print(f"{tag:30s} N50={r_v.all_n_debris[:, -1].mean():>10,.0f}  "
          f"EL=${ld_v.max_annual_losses.mean()/1e6:7.1f}M")


_dd_variant("baseline")
_dd_variant("DD fragments excluded (1-10cm)", dd_mu=-20.0)
_dd_variant("DD cross-section 1 m2", dd_rate_scale=0.1)
print("=> both DD assumptions inflate the headline; report it as an upper bound")
print("   in this dimension (limitations item 2 in the paper).")
