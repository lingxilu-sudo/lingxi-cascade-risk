# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.
# The Lingxi Cascade Risk Framework.

"""
Main Entry Point: Cascade Risk Framework
=================================================
Runs the full simulation pipeline:
1. Build physics model (orbital shell + collision + debris growth)
2. Run Monte Carlo simulation
3. Compute loss distributions
4. Calculate actuarial risk metrics (VaR, CVaR, EVT)
5. Price insurance premiums
6. Generate publication-quality figures
7. Print results summary

Usage:
    python main.py
    python main.py --paths 2000 --years 100
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from cascade_risk.config import Config
from cascade_risk.physics import (
    OrbitalShell,
    CollisionModel,
    DebrisGrowthModel,
    CascadeSimulator,
)
from cascade_risk.actuarial import (
    LossModel,
    RiskMetricsCalculator,
    PremiumCalculator,
    PortfolioRiskModel,
)
from cascade_risk.analysis import SensitivityAnalyzer


def build_models(config: Config):
    """Initialize all model components from config."""
    p = config.physics
    e = config.economics

    shell = OrbitalShell(
        altitude_km=p.altitude_km,
        thickness_km=p.shell_thickness_km,
    )

    collision_model = CollisionModel(
        shell=shell,
        cross_section_m2=p.cross_section_large_m2,
        v_rel_km_s=p.relative_velocity_km_s,
        k_debris_mu=p.k_debris_mu,
        k_debris_sigma=p.k_debris_sigma,
    )

    growth_model = DebrisGrowthModel(
        shell=shell,
        collision_model=collision_model,
        n_satellites=p.n_satellites,
        decay_rate_per_year=p.decay_rate_per_year,
    )

    simulator = CascadeSimulator(shell, collision_model, growth_model)

    loss_model = LossModel(
        v_satellite_usd=e.v_satellite_usd,
        n_policies=e.n_policies,
        correlation_coefficient=e.correlation_coefficient,
        discount_rate=e.discount_rate,
    )

    risk_calc = RiskMetricsCalculator(
        evt_threshold_percentile=e.evt_threshold_percentile,
    )

    premium_calc = PremiumCalculator(
        expense_loading=e.expense_loading,
        risk_loading_multiplier=e.risk_loading_multiplier,
        discount_rate=e.discount_rate,
        n_policies=e.n_policies,
    )

    portfolio_model = PortfolioRiskModel(
        n_policies=e.n_policies,
        correlation_coefficient=e.correlation_coefficient,
        v_satellite_usd=e.v_satellite_usd,
    )

    return {
        "shell": shell,
        "collision_model": collision_model,
        "growth_model": growth_model,
        "simulator": simulator,
        "loss_model": loss_model,
        "risk_calc": risk_calc,
        "premium_calc": premium_calc,
        "portfolio_model": portfolio_model,
    }


def run_pipeline(config: Config, output_dir: Path, n_paths_override: int = None):
    """Execute the full simulation and analysis pipeline."""
    models = build_models(config)
    p = config.physics
    e = config.economics

    n_paths = n_paths_override or p.n_monte_carlo_paths

    # --- Model Parameters ---
    print("[1/6] Loading model parameters...")
    print(f"  k_debris: mu={config.physics.k_debris_mu:.2f}, sigma={config.physics.k_debris_sigma:.2f} (NASA Standard Breakup Model)")
    print(f"  Shell: {models['shell']}")
    print(f"  K (carrying capacity): {models['shell'].carrying_capacity(p.cross_section_large_m2, p.relative_velocity_km_s):.0f}")

    # --- Monte Carlo Simulation ---
    print(f"\n[2/6] Running Monte Carlo simulation ({n_paths} paths, {p.t_max_years} years)...")
    t0 = time.time()

    def progress(completed, total):
        print(f"  Progress: {completed}/{total} paths ({100*completed/total:.0f}%)")

    result = models["simulator"].run(
        n_debris_0=p.n_debris_large,
        n_paths=n_paths,
        t_max_years=p.t_max_years,
        dt_years=p.dt_years,
        decay_uncertainty=p.decay_rate_uncertainty,
        seed=p.random_seed,
        progress_callback=progress,
    )

    elapsed = time.time() - t0
    print(f"  Completed in {elapsed:.1f}s")

    # Final debris stats
    stats = result.final_debris_stats()
    print(f"  Final debris: mean={stats['mean']:.0f}, median={stats['median']:.0f}, "
          f"p95={stats['p95']:.0f}")

    # --- Loss Distribution ---
    print("\n[3/6] Computing loss distribution...")
    loss_dist = models["loss_model"].compute_loss_distribution(
        all_n_debris=result.all_n_debris,
        n_debris_0=p.n_debris_large,
        cross_section_m2=p.cross_section_large_m2,
        v_rel_km_s=p.relative_velocity_km_s,
        shell_volume_km3=models["shell"].volume_km3,
    )

    # --- Risk Metrics ---
    print("\n[4/6] Computing actuarial risk metrics...")
    historical_prem = models["loss_model"].historical_loss(e.historical_failure_rate)
    metrics = models["risk_calc"].compute(
        losses=loss_dist.max_annual_losses,
        historical_premium=historical_prem,
    )

    # --- Premium Pricing ---
    print("\n[5/6] Computing insurance premiums...")
    premium = models["premium_calc"].compute_premium(metrics)

    # --- Results ---
    print("\n" + "=" * 70)
    print("RESULTS: Cascade Risk Framework v2.0")
    print("=" * 70)
    print()
    print("SIMULATION:")
    print(f"  Monte Carlo paths:     {n_paths}")
    print(f"  Time horizon:          {p.t_max_years} years")
    print(f"  Time step:             {p.dt_years} years ({p.dt_years * 365:.1f} days)")
    print(f"  Altitude:              {p.altitude_km} km")
    print(f"  Initial debris (>10cm): {p.n_debris_large:,}")
    print(f"  Active satellites:     {p.n_satellites:,}")
    print()
    print("DEBRIS PROJECTION (Year 50):")
    print(f"  Mean:                  {stats['mean']:,.0f}")
    print(f"  Median:                {stats['median']:,.0f}")
    print(f"  95th percentile:       {stats['p95']:,.0f}")
    print()
    print("RISK METRICS:")
    print(f"  Expected Loss:         ${metrics.expected_loss / 1e6:.2f}M")
    print(f"  Loss Std Dev:          ${metrics.loss_std / 1e6:.2f}M")
    print(f"  VaR 95%:               ${metrics.var_95 / 1e6:.2f}M")
    print(f"  CVaR 95% (ES):         ${metrics.cvar_95 / 1e6:.2f}M")
    print(f"  VaR 99%:               ${metrics.var_99 / 1e6:.2f}M")
    print(f"  CVaR 99% (ES):         ${metrics.cvar_99 / 1e6:.2f}M")
    if metrics.evt_var_95 is not None:
        print(f"  EVT VaR 95%:           ${metrics.evt_var_95 / 1e6:.2f}M")
        print(f"  EVT VaR 99%:           ${metrics.evt_var_99 / 1e6:.2f}M")
        print(f"  EVT shape (xi):        {metrics.evt_shape_parameter:.3f}")
    print()
    print("INSURANCE PREMIUM (Solvency II Framework):")
    print(f"  Expected Loss (EL):    ${premium.expected_loss / 1e6:.2f}M")
    print(f"  Risk Loading:          ${premium.risk_loading / 1e6:.2f}M")
    print(f"  Capital Charge:        ${premium.capital_charge / 1e6:.2f}M")
    print(f"  Expense Loading:       ${premium.expense_loading / 1e6:.2f}M")
    print(f"  TOTAL PREMIUM:         ${premium.total_premium / 1e6:.2f}M/year")
    print(f"  Per-satellite:         ${premium.premium_per_policy:,.0f}/year")
    print()
    print("COMPARISON:")
    print(f"  Historical premium:    ${premium.historical_premium / 1e6:.2f}M/year")
    print(f"  CASCADE FACTOR:        {premium.cascade_factor:.1f}x")
    print()
    print("GENERATING FIGURES...")

    # --- Visualization ---
    from cascade_risk.analysis.visualization import PlotGenerator
    plotter = PlotGenerator(output_dir)
    plotter.plot_debris_cascade(result)
    plotter.plot_loss_distribution(loss_dist, metrics)
    plotter.plot_premium_comparison(result, models["loss_model"], models["premium_calc"], models["shell"], p, historical_prem)
    plotter.plot_premium_breakdown(premium)
    plotter.plot_sensitivity_tornado(models, config)

    print(f"\nAll outputs saved to: {output_dir}")
    print("=" * 70)
    print("Framework complete.")

    return result, metrics, premium


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cascade Risk Framework - Space Debris Insurance Pricing"
    )
    parser.add_argument(
        "--paths", type=int, default=None,
        help="Number of Monte Carlo paths (overrides config)"
    )
    parser.add_argument(
        "--years", type=float, default=None,
        help="Simulation time horizon in years"
    )
    parser.add_argument(
        "--config", type=str, default="baseline.yaml",
        help="Configuration file name"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: ./output)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load config
    config = Config.from_yaml(args.config)

    # Override if specified
    if args.years is not None:
        from dataclasses import replace
        config = replace(config, physics=replace(config.physics, t_max_years=args.years))

    # Output directory
    output_dir = Path(args.output) if args.output else Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    run_pipeline(config, output_dir, n_paths_override=args.paths)


if __name__ == "__main__":
    main()
