# Cascade Risk Framework v2.0

## A Physics-Based Monte Carlo Model for Space Debris Insurance Pricing

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DOI](https://zenodo.org/badge/10.5281/zenodo.23095041.svg)](https://doi.org/10.5281/zenodo.23095041)

---

## Overview

The **Cascade Risk Framework** is an integrated model that couples **orbital-mechanics-driven debris cascade simulation** with **actuarial insurance pricing** for satellite operations.

**The problem:** The space insurance market prices risk using historical launch and in-orbit failure experience. No actuary models the probability that a single debris event triggers chain collisions (Kessler Syndrome), creating correlated losses across an entire portfolio.

**The solution:** This framework computes collision rates from first principles (orbital geometry, cross-sections, relative velocities), simulates debris cascade dynamics via Monte Carlo methods, and translates the resulting loss distributions into risk-adjusted premiums using VaR, CVaR, and Extreme Value Theory (the last as a diagnostic cross-check on the empirical tail).

## Key Results

| Metric | Value |
|--------|-------|
| Debris growth (50 years) | 36,500 → 1.51M objects (41×, baseline path) |
| Benchmark premium (0.5% of hull value, assumption) | $125M/year |
| Cascade-adjusted premium | $2,058M/year |
| **Cascade factor** | **16.5×** (7.4× on expected loss alone) |
| Expected loss (mean worst year) | $921.4M/year |
| VaR₉₅ / VaR₉₉ | $1,365M / $1,721M |
| CVaR₉₅ | $1,565M |
| EVT VaR₉₅ / VaR₉₉ (with exceedance ratio ζ = 0.10) | $1,375M / $1,677M |

**Read the headline as conditional.** The 16.5× is the year-50 fair premium, not today's: the same model gives $22.3M of expected loss at year 0, which is 0.18× the benchmark, and $111.0M at year 25 (0.89×). In 100% of paths the worst year is the final step, so the ratio measures how a static benchmark falls behind a growing cascade over 50 years. The 16.5× also assigns the entire global >10 cm catalogue (36,500 objects) to the 700–900 km shell, uses expected claim counts, and compares against a 0.5%-of-hull benchmark that is a modelling assumption rather than an observed premium. The benchmark is all-peril while the model prices debris collisions only, so the ratio is conservative on coverage. The mean-field backbone has a finite-time singularity at \(t^* \approx 61\) years, 11 years beyond the 50-year horizon. Sensitivity: \(N_0 = 8{,}000\) → EL $114M; 0.3% benchmark → 27.5×; 1.0% benchmark → 8.2×; binomial claim counts → EL +35%. The debris–debris term is deliberately generous: if its ~3 fragments per event were treated as 1–10 cm debris instead of catalogue objects, EL falls to $463M; if the DD cross-section were 1 m² instead of the shared 10 m² satellite section, EL falls to $484M. Both are upper bounds on the headline. See `study/AUDIT.md` for the full audit trail.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full simulation pipeline
python main.py

# With custom parameters
python main.py --paths 1000 --years 100

# Run tests
python -m pytest tests/ -v
```

Output figures are saved to `output/`.

## Project Structure

```
model/
├── cascade_risk/              # Main Python package
│   ├── physics/               # Orbital mechanics & debris simulation
│   │   ├── orbital_shell.py   # Shell geometry, volume, density
│   │   ├── collision_model.py # Collision rates (Kessler-Flournoy)
│   │   ├── debris_growth.py   # Debris population ODE
│   │   └── cascade_simulator.py # Monte Carlo orchestrator
│   ├── actuarial/             # Insurance pricing
│   │   ├── loss_model.py      # Loss distributions
│   │   ├── risk_metrics.py    # VaR, CVaR, EVT
│   │   ├── premium_calculator.py # Solvency-II-style pricing
│   │   └── portfolio_risk.py  # Correlated portfolio losses
│   ├── calibration/           # Historical event anchors
│   │   └── historical_events.py # Iridium-Cosmos, Fengyun-1C
│   ├── analysis/              # Sensitivity & visualization
│   │   ├── sensitivity.py     # OAT & Sobol analysis
│   │   └── visualization.py   # Publication-quality plots
│   ├── utils/                 # Constants & utilities
│   └── config.py              # YAML-based configuration
├── configs/                   # Parameter files
│   ├── baseline.yaml          # Default parameters
│   ├── sensitivity.yaml       # Sensitivity ranges
│   └── calibration.yaml       # Historical event data
├── tests/                     # Unit tests
├── paper/                     # Academic paper
├── output/                    # Generated results
├── main.py                    # Entry point
├── requirements.txt
└── README.md
```

## Model Architecture

### Physics Layer
- **Orbital Shell Geometry**: Spherical shell volume, number density, spatial density
- **Collision Rate**: Kessler-Flournoy kinetic theory formula for debris-satellite and debris-debris collisions
- **Fragment Generation**: event-anchored log-normal yield; the NASA Standard Breakup Model is retained only as an order-of-magnitude anchor
- **Poisson Process**: Stochastic collision events (not continuous flow)
- **Orbital Decay**: Atmospheric drag with stochastic noise

### Actuarial Layer
- **Loss Distribution**: Per-satellite hit probability from collision physics → portfolio losses
- **Risk Metrics**: VaR, CVaR (Expected Shortfall), EVT (Generalized Pareto, with peaks-over-threshold exceedance ratio) as a diagnostic
- **Premium Pricing**: Solvency-II-style decomposition (EL + Risk Loading + Capital Charge + Expense Loading)
- **Portfolio Correlation**: Gaussian Copula for variance and tail analysis only; expected loss is correlation-invariant, and the copula does not enter the headline premium

### Event Anchors
- Iridium 33 × Cosmos 2251 (2009): ~2,300 trackable fragments
- Fengyun-1C ASAT (2007): ~3,500 trackable fragments
- Kosmos 1408 ASAT (2021): ~1,500 trackable fragments

## Configuration

All parameters are in `configs/baseline.yaml`. Key tunable parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `altitude_km` | 800 | Orbital altitude |
| `n_debris_large` | 36,500 | Initial debris >10cm |
| `n_satellites` | 8,000 | Active satellites |
| `k_debris_mu` | 5.5 | Fragment yield (ln-mean) |
| `decay_rate_per_year` | 0.005 | Orbital decay rate |
| `v_satellite_usd` | 50M | Satellite value |
| `n_policies` | 500 | Insured satellites |
| `correlation_coefficient` | 0.3 | Portfolio correlation |

## Academic Paper

See `paper/framework_paper.md` for the full academic paper.

## Citation

```bibtex
@misc{lu2026cascade,
  title={The Cascade Risk Framework: A Physics-Based Monte Carlo Model for Space Debris Insurance Pricing},
  author={Lu, Lingxi},
  year={2026},
  publisher={Zenodo},
  doi={10.5281/zenodo.23095041},
  url={https://doi.org/10.5281/zenodo.23095041},
  note={Version 2.0}
}
```

## License

Framework methodology paper: CC BY 4.0
Simulation source code: Apache License 2.0

© 2026 Lingxi Lu. All rights reserved.

## Contact

Lingxi Lu — ling.xi.lu@gmail.com
