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

from cascade_risk.utils.constants import DD_FRAGMENT_MU, DD_FRAGMENT_SIGMA

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
        ax.set_title("Worst-Year Loss Across Debris Paths")
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
            cross_section_m2=phys_config.cross_section_large_m2,
            v_rel_km_s=phys_config.relative_velocity_km_s,
            shell_volume_km3=shell.volume_km3,
        )

        # Portfolio-level annual losses: per-satellite loss × number of
        # insured satellites.  Omitting n_policies would plot a per-satellite
        # premium against a portfolio historical premium (~500x too low).
        annual_losses = hit_prob * loss_model.v_satellite_usd * loss_model.n_policies
        prem_time = premium_calc.compute_time_varying_premium(annual_losses, historical_prem)

        # The trajectory is a pointwise composite of cross-path percentiles
        # (mean, CVaR95, VaR99), not a sample of premium paths, so it has no
        # sampling distribution and no confidence band can be drawn from it.
        prem_curve = prem_time / 1e6

        hist_prem_m = historical_prem / 1e6
        ax.plot(result.times, np.full_like(result.times, hist_prem_m),
                color=COLORS["blue"], linewidth=2, linestyle="--",
                label="Static 0.5% benchmark (assumption)")
        ax.plot(result.times, prem_curve, color=COLORS["red"], linewidth=2.5,
                label=f"Cascade-adjusted (year-50: ${prem_curve[-1]:,.0f}M)")

        ax.set_xlabel("Time (years)")
        ax.set_ylabel("Annual Insurance Premium (Million USD)")
        ax.set_title("Static Benchmark vs Cascade-Adjusted Premium")
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
        ax.set_title("Insurance Premium Breakdown (Solvency-II-style)")
        ax.legend(loc="upper right", fontsize=9)

        path = self.output_dir / "premium_breakdown.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")

    # ------------------------------------------------------------------
    # Plot 5: Sensitivity Tornado Chart
    # ------------------------------------------------------------------

    def plot_sensitivity_tornado(self, models, config):
        """Analytic one-at-a-time sensitivity of the time-to-singularity.

        This is deliberately *not* a re-run of the Monte Carlo model (that
        would cost minutes per parameter).  It solves the deterministic
        mean-field backbone

            dN/dt = (b - lambda) N + a N^2

        whose closed-form solution diverges at

            t* = ln(1 + alpha / (a N0)) / alpha,   alpha = b - lambda.

        Reporting N(50) instead would be uninformative: with the baseline
        parameters t* = 61 years, so many one-at-a-time intervals push the
        singularity inside the 50-year horizon and N(50) diverges.  The
        singularity time is finite in every case and shows directly which
        parameters can move the blow-up inside the horizon.  This is an
        analytic OAT, not a variance-based Sobol index.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        shell = models["shell"]
        p = config.physics

        n0 = p.n_debris_large

        def t_star(k_mu, decay, v_rel, n_sat, sigma_m2,
                   k_dd_mu=DD_FRAGMENT_MU):
            q = sigma_m2 * 1e-6 * v_rel * 31557600.0 / shell.volume_km3
            b = float(np.exp(k_mu + p.k_debris_sigma ** 2 / 2)) * n_sat * q
            k_dd = float(np.exp(k_dd_mu + DD_FRAGMENT_SIGMA ** 2 / 2))
            a = 0.5 * k_dd * q
            alpha = b - decay
            if alpha <= 0:
                return np.inf  # decay dominates: no finite-time blow-up
            ratio = alpha / (a * n0)
            return float(np.log1p(ratio) / alpha)

        base = dict(
            k_mu=p.k_debris_mu,
            decay=p.decay_rate_per_year,
            v_rel=p.relative_velocity_km_s,
            n_sat=p.n_satellites,
            sigma_m2=p.cross_section_large_m2,
            k_dd_mu=DD_FRAGMENT_MU,
        )
        params = {
            "Debris yield (ln-mean)": ("k_mu", 4.5, 6.5),
            "DD yield (ln-mean)": ("k_dd_mu", 0.6, 1.6),
            "Cross-section": ("sigma_m2", 5.0, 20.0),
            "Active satellites": ("n_sat", 4000, 12000),
            "Relative velocity": ("v_rel", 7.0, 14.0),
            "Orbital decay rate": ("decay", 0.002, 0.010),
        }

        rows = []
        for label, (key, low, high) in params.items():
            lo = dict(base); lo[key] = low
            hi = dict(base); hi[key] = high
            rows.append((label, t_star(**lo), t_star(**hi)))
        rows.sort(key=lambda row: min(row[1], row[2]))

        x_max = 160.0
        y_positions = np.arange(len(rows))
        for y, (label, t_lo, t_hi) in zip(y_positions, rows):
            finite = [t for t in (t_lo, t_hi) if np.isfinite(t)]
            crosses = bool(finite) and min(finite) < 50.0
            color = COLORS["red"] if crosses else COLORS["blue"]
            if finite:
                left, right = min(finite), min(max(finite), x_max)
                ax.plot([left, right], [y, y], color=color, linewidth=4, solid_capstyle="round")
                for t in (t_lo, t_hi):
                    if np.isfinite(t):
                        ax.plot(t, y, "o", color=color, markersize=7)
                        ax.annotate(f"{t:.0f}", (t, y), textcoords="offset points",
                                    xytext=(0, 9), ha="center", fontsize=8, color=color)
                    else:
                        ax.annotate("no blow-up", (x_max, y), textcoords="offset points",
                                    xytext=(-4, 9), ha="right", fontsize=8, color=color)
            else:
                ax.annotate("no finite-time blow-up in this range", (x_max, y),
                            textcoords="offset points", xytext=(-4, 0), ha="right",
                            fontsize=8, color=color)

        ax.axvline(50.0, color=COLORS["black"], linestyle="--", linewidth=1.5,
                   label="50-year simulation horizon")
        ax.axvline(61.1, color=COLORS["green"], linestyle=":", linewidth=1.5,
                   label="Baseline t* = 61.1 years")

        ax.set_yticks(y_positions)
        ax.set_yticklabels([row[0] for row in rows])
        ax.set_xlim(20.0, x_max)
        ax.set_xlabel("Time to finite-time singularity t* (years)")
        ax.set_title("Analytic OAT Sensitivity: Can One Parameter Move the\n"
                     "Singularity Inside the 50-Year Horizon?")
        ax.legend(loc="upper right", fontsize=9)

        path = self.output_dir / "sensitivity_tornado.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"  Saved: {path}")
