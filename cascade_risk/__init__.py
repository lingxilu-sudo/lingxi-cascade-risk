"""
Cascade Risk Framework
===============================
A physics-based Monte Carlo model for space debris insurance pricing.

This is the first framework that couples orbital mechanics-driven debris
cascade simulation with actuarial risk metrics (VaR, CVaR, EVT) to produce
risk-adjusted insurance premiums for satellite operations.

Modules:
    physics     - Orbital mechanics, collision models, debris cascade simulation
    actuarial   - Loss distributions, risk metrics, premium pricing
    calibration - Historical event calibration (Iridium-Cosmos, Fengyun-1C)
    analysis    - Sensitivity analysis (OAT, Sobol)
    utils       - Physical constants, unit conversions
"""

__version__ = "2.0.0"
__author__ = "Lingxi Lu"
__email__ = "ling.xi.lu@gmail.com"

from cascade_risk.config import Config, get_config, set_config
from cascade_risk.physics import (
    OrbitalShell,
    CollisionModel,
    DebrisGrowthModel,
    CascadeSimulator,
    SimulationResult,
)
from cascade_risk.actuarial import (
    LossModel,
    LossDistribution,
    RiskMetricsCalculator,
    RiskMetrics,
    PremiumCalculator,
    PremiumBreakdown,
    PortfolioRiskModel,
)
from cascade_risk.calibration import CalibrationEngine, KNOWN_EVENTS

__all__ = [
    # Config
    "Config", "get_config", "set_config",
    # Physics
    "OrbitalShell", "CollisionModel", "DebrisGrowthModel",
    "CascadeSimulator", "SimulationResult",
    # Actuarial
    "LossModel", "LossDistribution",
    "RiskMetricsCalculator", "RiskMetrics",
    "PremiumCalculator", "PremiumBreakdown",
    "PortfolioRiskModel",
    # Calibration
    "CalibrationEngine", "KNOWN_EVENTS",
]
