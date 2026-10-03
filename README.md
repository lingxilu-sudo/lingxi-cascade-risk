# Cascade Risk Framework v2.0

## A Physics-Based Monte Carlo Model for Space Debris Insurance Pricing

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## Overview

The **Cascade Risk Framework** is the first model to couple **orbital mechanics-driven debris cascade simulation** with **actuarial insurance pricing** for satellite operations.

**The problem:** The space insurance market prices risk using historical launch failure rates. No actuary models the probability that a single debris event triggers chain collisions (Kessler Syndrome), creating correlated losses across an entire portfolio.

**The solution:** This framework computes collision rates from first principles (orbital geometry, cross-sections, relative velocities), simulates debris cascade dynamics via Monte Carlo methods, and translates the resulting loss distributions into risk-adjusted premiums using VaR, CVaR, and Extreme Value Theory.

## Key Results

| Metric | Value |
|--------|-------|
| Debris growth (50 years) | 36,500 → 1.5M objects (41×) |
| Historical premium | $125M/year |
| Cascade-adjusted premium | $580M/year |
| **Cascade factor** | **4.6×** |
| VaR₉₅ | $405M/year |
| CVaR₅ | $446M/year |

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
│   │   ├── premium_calculator.py # Solvency II pricing
│   │   └── portfolio_risk.py  # Correlated portfolio losses
│   ├── calibration/           # Historical event calibration
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
- **Fragment Generation**: NASA Standard Breakup Model (log-normal distribution, calibrated to real events)
- **Poisson Process**: Stochastic collision events (not continuous flow)
- **Orbital Decay**: Atmospheric drag with stochastic noise

### Actuarial Layer
- **Loss Distribution**: Per-satellite hit probability from collision physics → portfolio losses
- **Risk Metrics**: VaR, CVaR (Expected Shortfall), EVT (Generalized Pareto)
- **Premium Pricing**: Solvency II decomposition (EL + Risk Loading + Capital Charge + Expense Loading)
- **Portfolio Correlation**: Gaussian Copula for correlated multi-satellite losses

### Calibration
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
  title={A Physics-Based Monte Carlo Framework for Space Debris Cascade Risk and Insurance Pricing},
  author={Lu, Lingxi},
  year={2026},
  note={Version 2.0}
}
```

## License

Framework methodology paper: CC BY 4.0
Simulation source code: Apache License 2.0

© 2026 Lingxi Lu. All rights reserved.

## Contact

Lingxi Lu — ling.xi.lu@gmail.com
