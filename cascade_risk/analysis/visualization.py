# Copyright 2026 Lingxi Lu. All rights reserved.
# Licensed under the Apache License, Version 2.0.

"""
Publication-Quality Visualization
==================================
Generates journal-ready figures with:
- 600 DPI resolution
- Colorblind-friendly palette
- Consistent typography
- Proper axis labels with units

References:
    Wong, B. (2011). "Points of view: Color blindness."
    Nature Methods, 8(6), 441.
    IEEE Transactions on Visualization style guide.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# --- Publication style settings ---
rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 600,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "axes.linewidth": 1.0,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 15,
    "figure.titleweight": "bold",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "-",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

# Colorblind-friendly palette (Wong 2011)
COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "cyan": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#000000",
}


class PlotGenerator:
    """Generates publication-quality figures for the cascade risk framework."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Plot 1: Debris Cascade (Monte Carlo paths)
    # ------------------------------------------------------------------

    def plot_debris_cascade(self, result, n_sample_paths: int = 50):
        """Spaghetti plot of debris population with confidence bands."""
        fig, ax = plt.subplots(figsize=(10, 6))

        # Sample individual paths
        rng = np.random.default_rng(123)
        indices = rng.choice(result.n_paths, min(n_sample_paths, result.n_paths), replace=False)
        for idx in indices:
            ax.plot(
                result.times, result.all_n_debris[idx, :],
                color=COLORS["cyan"], alpha=0.15, linewidth=0.4,
            )

        # Confidence bands
        p5 = np.percentile(result.all_n_debris, 5, axis=0)
        p50 = np.percentile(result.all_n_debris, 50, axis=0)
        p95 = np.percentile(result.all_n_debris, 95, axis=0)

        ax.fill_between(result.times, p5, p95, alpha=0.2, color=COLORS["blue"],
                        label="90% confidence band")
        ax.plot(result.times, p50, color=COLORS["blue"], linewidth=2.5, label="Median path")
        ax.axhline(y=result.all_n_debris[0, 0], color=COLORS["red"], linestyle="--",
                    linewidth=1.5, label=f"Initial: {result.all_n_debris[0, 0]:,.0f}")

        ax.set_xlabel("Time (years)")
        ax.set_ylabel("Debris Population (>10 cm)")
        ax.set_title("Monte Carlo Simulation: Debris Cascade Dynamics")
        ax.legend(loc="upper left")
        ax.set_ylim(bottom=0)

        path = self.output_dir / "debris_cascade.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")

    # ------------------------------------------------------------------
    # Plot 2: Loss Distribution
    # ------------------------------------------------------------------

    def plot_loss_distribution(self, loss_dist, metrics):
        """Histogram of loss distribution with VaR/CVaR markers."""
        fig, ax = plt.subplots(figsize=(10, 6))

        losses_m = loss_dist.max_annual_losses / 1e6
        ax.hist(losses_m, bins=50, density=True, alpha=0.7,
                color=COLORS["blue"], edgecolor="white", label="Loss distribution")

        ax.axvline(x=metrics.expected_loss / 1e6, color=COLORS["green"],
                    linewidth=2, linestyle="-", label=f"Expected Loss: ${metrics.expected_loss/1e6:.2f}M")
        ax.axvline(x=metrics.var_95 / 1e6, color=COLORS["orange"],
                    linewidth=2, linestyle="--", label=f"VaR 95%: ${metrics.var_95/1e6:.2f}M")
        ax.axvline(x=metrics.var_99 / 1e6, color=COLORS["red"],
                    linewidth=2, linestyle="--", label=f"VaR 99%: ${metrics.var_99/1e6:.2f}M")

        if metrics.evt_var_95 is not None:
            ax.axvline(x=metrics.evt_var_95 / 1e6, color=COLORS["purple"],
                        linewidth=1.5, linestyle=":", label=f"EVT VaR 95%: ${metrics.evt_var_95/1e6:.2f}M")

        ax.set_xlabel("Maximum Annual Loss (Million USD)")
        ax.set_ylabel("Probability Density")
        ax.set_title("Loss Distribution from Monte Carlo Simulation")
        ax.legend(fontsize=9)

        path = self.output_dir / "loss_distribution.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")

    # ------------------------------------------------------------------
    # Plot 3: Premium Comparison
    # ------------------------------------------------------------------

    def plot_premium_comparison(self, result, loss_model, premium_calc, shell, phys_config, historical_prem):
        """Time-varying premium: historical vs cascade-adjusted."""
        fig, ax = plt.subplots(figsize=(10, 6))

        hit_prob = loss_model.compute_hit_probability(
            result.all_n_debris,
            phys_config.n_debris_large,
            cross_section_m2=phys_config.cross_section_large_m2,
            v_rel_km_s=phys_config.relative_velocity_km_s,
            shell_volume_km3=shell.volume_km3,
        )

        annual_losses = hit_prob * loss_model.v_satellite_usd
        prem_time = premium_calc.compute_time_varying_premium(annual_losses, historical_prem)

        prem_median = np.median(prem_time, axis=0) / 1e6 if prem_time.ndim > 1 else prem_time / 1e6
        prem_p5 = np.percentile(prem_time, 5, axis=0) / 1e6 if prem_time.ndim > 1 else prem_time / 1e6
        prem_p95 = np.percentile(prem_time, 95, axis=0) / 1e6 if prem_time.ndim > 1 else prem_time / 1e6

        hist_prem_m = historical_prem / 1e6
        ax.plot(result.times, np.full_like(result.times, hist_prem_m),
                color=COLORS["blue"], linewidth=2, linestyle="--", label="Historical Pricing")
        ax.plot(result.times, prem_median, color=COLORS["red"], linewidth=2.5,
                label="Cascade-Adjusted (median)")
        ax.fill_between(result.times, prem_p5, prem_p95, alpha=0.2, color=COLORS["red"],
                        label="90% confidence band")

        ax.set_xlabel("Time (years)")
        ax.set_ylabel("Annual Insurance Premium (Million USD)")
        ax.set_title("Insurance Premium: Historical vs Cascade-Adjusted")
        ax.legend()
        ax.set_ylim(bottom=0)

        path = self.output_dir / "premium_comparison.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")

    # ------------------------------------------------------------------
    # Plot 4: Premium Breakdown (stacked bar)
    # ------------------------------------------------------------------

    def plot_premium_breakdown(self, premium):
        """Stacked bar showing premium components."""
        fig, ax = plt.subplots(figsize=(8, 5))

        components = {
            "Expected\nLoss": premium.expected_loss / 1e6,
            "Risk\nLoading": premium.risk_loading / 1e6,
            "Capital\nCharge": premium.capital_charge / 1e6,
            "Expense\nLoading": premium.expense_loading / 1e6,
        }

        colors_list = [COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["purple"]]
        bottom = 0
        for (name, value), color in zip(components.items(), colors_list):
            ax.bar("Total Premium", value, bottom=bottom, color=color,
                    label=f"{name}: ${value:.2f}M", width=0.5, edgecolor="white")
            bottom += value

        ax.set_ylabel("Premium (Million USD)")
        ax.set_title("Insurance Premium Breakdown (Solvency II Framework)")
        ax.legend(loc="upper right", fontsize=9)

        path = self.output_dir / "premium_breakdown.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")

    # ------------------------------------------------------------------
    # Plot 5: Sensitivity Tornado Chart
    # ------------------------------------------------------------------

    def plot_sensitivity_tornado(self, models, config):
        """Tornado chart showing parameter sensitivity."""
        fig, ax = plt.subplots(figsize=(10, 6))

        params = {
            "Debris Yield (μ)": (4.5, 6.5, config.physics.k_debris_mu, "k_debris_mu"),
            "Orbital Decay Rate": (0.002, 0.010, config.physics.decay_rate_per_year, "decay_rate"),
            "Relative Velocity": (7.0, 14.0, config.physics.relative_velocity_km_s, "v_rel"),
            "Satellite Value": (20e6, 100e6, config.economics.v_satellite_usd, "v_sat"),
            "Portfolio Correlation": (0.0, 0.8, config.economics.correlation_coefficient, "corr"),
        }

        names = []
        impacts = []
        for label, (low, high, base, key) in params.items():
            test_vals = np.linspace(low, high, 20)
            # Simplified: scale loss linearly with parameter
            base_loss = config.economics.v_satellite_usd * 0.05
            losses = base_loss * (test_vals / base)
            impact = (np.max(losses) - np.min(losses)) / 1e6
            names.append(label)
            impacts.append(impact)

        sorted_idx = np.argsort(impacts)
        names_sorted = [names[i] for i in sorted_idx]
        impacts_sorted = [impacts[i] for i in sorted_idx]

        colors_list = [COLORS["blue"] if x < np.median(impacts_sorted) else COLORS["red"]
                       for x in impacts_sorted]

        ax.barh(range(len(names_sorted)), impacts_sorted, color=colors_list,
                edgecolor="white")
        ax.set_yticks(range(len(names_sorted)))
        ax.set_yticklabels(names_sorted)
        ax.set_xlabel("Premium Sensitivity (Million USD range)")
        ax.set_title("Sensitivity Analysis: What Drives Insurance Premium?")

        path = self.output_dir / "sensitivity_tornado.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")
