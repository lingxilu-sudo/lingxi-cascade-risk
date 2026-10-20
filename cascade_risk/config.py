# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Configuration management for the Cascade Risk Framework.

Loads parameters from YAML configuration files and provides
a unified Config object with validated, typed access.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_CONFIG_DIR = Path(__file__).parent.parent / "configs"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML config file from the configs/ directory."""
    filepath = _CONFIG_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Dataclasses for typed config access
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PhysicsConfig:
    altitude_km: float = 800.0
    shell_thickness_km: float = 200.0
    inclination_deg: float = 51.6
    n_debris_large: int = 36500
    n_satellites: int = 8000
    cross_section_large_m2: float = 10.0
    cross_section_dd_m2: float = 10.0  # Upper bound; real DD cross-section may be 0.01-1 m²
    relative_velocity_km_s: float = 10.0
    k_debris_mu: float = 5.5
    k_debris_sigma: float = 0.8
    dd_fragment_mu: float = 1.1       # DD yield ln-mean (median ~3); see constants.py
    dd_fragment_sigma: float = 0.5    # DD yield ln-sigma
    decay_rate_per_year: float = 0.005  # Effective removal rate (drag + grinding + dropout)
    decay_rate_uncertainty: float = 0.1
    t_max_years: float = 50.0
    dt_years: float = 0.1
    n_monte_carlo_paths: int = 1000
    random_seed: int = 42


@dataclass(frozen=True)
class EconomicsConfig:
    v_satellite_usd: float = 50_000_000
    v_satellite_uncertainty: float = 0.3
    historical_failure_rate: float = 0.005  # 0.5% in-orbit (not launch failure rate)
    expense_loading: float = 0.15
    risk_loading_multiplier: float = 1.5
    discount_rate: float = 0.04
    n_policies: int = 500
    correlation_coefficient: float = 0.3
    evt_threshold_percentile: float = 90.0


@dataclass(frozen=True)
class Config:
    """Master configuration container."""
    physics: PhysicsConfig = field(default_factory=PhysicsConfig)
    economics: EconomicsConfig = field(default_factory=EconomicsConfig)

    @classmethod
    def from_yaml(cls, baseline: str = "baseline.yaml") -> "Config":
        """Create Config from YAML files.

        Unknown keys raise instead of being silently ignored: a typo such as
        ``shell_thicknes_km`` would otherwise fall back to the dataclass
        default and change the simulation without any warning.

        If ``baseline.yaml`` itself is missing — the normal case for a
        pip-installed package that does not ship the repository's ``configs/``
        directory — the built-in dataclass defaults are used with a warning.
        Those defaults are identical to ``baseline.yaml`` (pinned by a test),
        so the published numbers stay reproducible.
        """
        try:
            data = _load_yaml(baseline) or {}
        except FileNotFoundError:
            if baseline != "baseline.yaml":
                raise
            warnings.warn(
                "configs/baseline.yaml not found (installed package without "
                "the repository's configs/ directory); using the built-in "
                "defaults, which are identical to that file.",
                RuntimeWarning,
                stacklevel=2,
            )
            return cls()

        # Guard the top level as well: a misspelled section name
        # ("physic:" instead of "physics:") would otherwise be dropped and
        # every physics parameter would silently fall back to its default.
        unknown_sections = set(data) - {"physics", "economics"}
        if unknown_sections:
            raise ValueError(
                f"Unknown config sections in {baseline}: "
                f"{sorted(unknown_sections)}"
            )

        phys_data = data.get("physics", {})
        econ_data = data.get("economics", {})

        unknown_phys = set(phys_data) - set(PhysicsConfig.__dataclass_fields__)
        unknown_econ = set(econ_data) - set(EconomicsConfig.__dataclass_fields__)
        if unknown_phys or unknown_econ:
            raise ValueError(
                f"Unknown config keys in {baseline}: "
                f"physics={sorted(unknown_phys)}, economics={sorted(unknown_econ)}"
            )

        physics = PhysicsConfig(**phys_data)
        economics = EconomicsConfig(**econ_data)

        return cls(physics=physics, economics=economics)


# Module-level default config
_default_config: Config | None = None


def get_config() -> Config:
    """Return the global Config singleton, loading from YAML on first call."""
    global _default_config
    if _default_config is None:
        _default_config = Config.from_yaml()
    return _default_config


def set_config(cfg: Config) -> None:
    """Override the global config (useful for testing)."""
    global _default_config
    _default_config = cfg
