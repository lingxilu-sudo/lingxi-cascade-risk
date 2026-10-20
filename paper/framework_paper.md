# A Physics-Based Monte Carlo Framework for Space Debris Cascade Risk and Insurance Pricing

**Author:** Lingxi Lu
**Affiliation:** Independent Researcher
**Date:** October 2026
**Version:** 2.0

---

## Abstract

The commercial space insurance market, estimated at roughly $1.2 billion in 2025 (industry estimates vary), prices satellite risk using historical launch and in-orbit failure experience. No existing actuarial model accounts for **cascade risk** — the chain-reaction scenario in which one collision generates debris that triggers further collisions, creating correlated losses across an insurance portfolio. I present a coupled physics-actuarial model that simulates debris cascade dynamics in Low Earth Orbit (LEO) using Monte Carlo methods driven by first-principles collision physics, and translates the resulting loss distributions into risk-adjusted insurance premiums via Value at Risk (VaR), Conditional VaR (CVaR), and Extreme Value Theory (EVT). My baseline simulation at 800 km altitude demonstrates that debris populations grow from 36,500 to ~1.51 million objects over 50 years under business-as-usual conditions, with cascade-adjusted premiums **16.5× higher** than a 0.5%-of-hull-value in-orbit failure benchmark ($2,058M vs. $125M per year for a 500-satellite portfolio; 7.4× on an expected-loss-only basis). The framework is anchored to three documented collision events (Iridium 33 × Cosmos 2251, Fengyun-1C, Kosmos 1408) and the NASA Standard Breakup Model, and uses a Solvency-II-style premium decomposition (Expected Loss + Risk Loading + Capital Charge + Expense Loading). The 16.5× is conditional on assigning the entire >10 cm catalogue to the 700–900 km shell; it is a lower bound with respect to claim-count noise but an upper bound with respect to the debris–debris term's yield and cross-section (§4.4), and the mean-field backbone reaches a finite-time singularity at \(t^*\approx61\) years, only 11 years beyond the simulation horizon.

---

## 1. Introduction

### 1.1 The Unpriced Risk

The space debris environment in Low Earth Orbit (LEO) has transitioned from a background condition to an active operating cost. As of 2025, approximately 36,500 objects larger than 10 cm are tracked in Earth orbit, with an estimated 1 million objects between 1–10 cm and 130 million smaller fragments (ESA Space Environment Report, 2025). The World Economic Forum and Centre for Space Futures (January 2026) projected debris-related costs for LEO assets at $25.8–$42.3 billion between 2025 and 2035 under a business-as-usual scenario.

Despite this, the space insurance market continues to price risk using historical loss data — primarily launch and in-orbit failure experience plus single-asset collision probabilities. The critical gap: **no actuary formally models the probability that a single debris event could trigger a cascade of collisions**, generating correlated claims across an entire insurance portfolio simultaneously.

### 1.2 Prior Work

Freeman et al. (2021) proposed an actuarial modifier for underwriting On-Orbit Servicing (OOS) satellite insurance, incorporating space debris mitigation into premium calculations. Their model addresses direct collision risk but does not account for cascade dynamics — the chain-reaction scenario first described by Kessler (1978). Liou & Johnson (2008) demonstrated the instability of the present LEO satellite population through numerical simulation, but did not connect their results to insurance pricing.

### 1.3 Contribution

I present an integrated framework that:
1. **Couples collision physics with actuarial science**: Debris growth is driven by actual collision rates (no separately tuned cascade-rate parameter), computed from orbital mechanics.
2. **Implements Poisson-distributed collision events**: Each collision produces a random number of fragments drawn from an event-anchored log-normal yield, with the NASA Standard Breakup Model used as an order-of-magnitude anchor.
3. **Distinguishes collision types**: Debris-satellite and debris-debris collisions produce different fragment yields. This delays, but does not remove, the finite-time singularity; the baseline mean-field singularity is at \(t^*\approx61\) years.
4. **Quantifies portfolio-level correlated risk**: A separate Gaussian-copula module models simultaneous multi-satellite losses. Expected loss is correlation-invariant; the copula affects variance and tail metrics and is not used in the headline premium.
5. **Applies Extreme Value Theory (EVT)**: GPD fitting with the peaks-over-threshold exceedance ratio, used as a diagnostic cross-check on the empirical tail.
6. **Anchors parameters to real events**: Prior yield scales are checked against catalogued fragment counts from Iridium-Cosmos (2009), Fengyun-1C (2007), and Kosmos 1408 (2021); this is an external consistency check, not a formal calibration.
7. **Reports its own limits**: The headline is conditional on the global >10 cm catalogue residing in one shell, ignores binomial claim-count noise, treats debris-debris fragments as catalogue objects, and sits close to a finite-time singularity; each is quantified in §4.4.

---

## 2. Methodology

### 2.1 Physical Layer: Collision-Driven Debris Dynamics

#### 2.1.1 Orbital Shell Geometry

I model a representative LEO shell at altitude $h = 800$ km with thickness $\Delta h = 200$ km (700–900 km). The shell volume is:

$$V_{\text{shell}} = \frac{4\pi}{3}\left[(R_\oplus + h + \Delta h/2)^3 - (R_\oplus + h - \Delta h/2)^3\right] \approx 1.29 \times 10^{11} \text{ km}^3$$

This altitude is selected because it hosts the highest concentration of defunct satellites and is a primary operating region for mega-constellations. Atmospheric drag at 800 km is weak, allowing debris to persist for decades to centuries.

#### 2.1.2 Collision Rate (Kessler-Flournoy Formula)

The collision rate between debris and satellites follows the kinetic theory approach (Kessler 1981):

$$R_{ds} = \frac{N_d \cdot N_s \cdot \sigma \cdot v_{\text{rel}} \cdot T_{\text{year}}}{V_{\text{shell}}}$$

where $N_d$ is the debris population, $N_s$ is the satellite count, $\sigma$ is the collision cross-section, $v_{\text{rel}}$ is the mean relative velocity, and $T_{\text{year}}$ is seconds per year.

Debris-debris collisions (the cascade driver) follow:

$$R_{dd} = \frac{N_d(N_d - 1) \cdot \sigma \cdot v_{\text{rel}} \cdot T_{\text{year}}}{2 \cdot V_{\text{shell}}}$$

**Critical observation:** $R_{dd} \propto N_d^2$. Doubling the debris population quadruples the debris-debris collision rate. This quadratic feedback is the mathematical root of the cascade.

At current population levels ($N_d = 36{,}500$, $N_s = 8{,}000$), the computed rates are approximately 7 debris-satellite and 16 debris-debris collisions per year.

#### 2.1.3 Fragment Generation (NASA Standard Breakup Model)

Each collision produces a random number of fragments drawn from a log-normal distribution. A critical innovation of this framework is the **asymmetric fragment yield** between collision types:

| Collision Type | Distribution | Median Fragments | Physical Rationale |
|---------------|-------------|-----------------|-------------------|
| Debris → Satellite (DS) | LogNormal(5.5, 0.8) | ~245 | Large satellite breakup; high collision energy |
| Debris → Debris (DD) | LogNormal(1.1, 0.5) | ~3 | Small fragment impact; low collision energy |

This asymmetry is physically motivated: a fragment striking an intact satellite releases far more energy (and creates more debris) than two small fragments colliding. Without it, the $N^2$ scaling of DD collision rates combined with high fragment yields (~245) would produce a much earlier finite-time singularity. The asymmetry delays the singularity but does not remove it: with baseline parameters the mean-field backbone diverges at \(t^*\approx61\) years, and the 50-year horizon sits at 82% of \(t^*\) (§4.4).

The operative sampler is the event-anchored log-normal yield above. The NASA Standard Breakup Model formula \(N(>D)=0.1M^{0.75}E^{0.5}D^{-1.71}\) is retained in `constants.py` only as an order-of-magnitude anchor; it is not called by the simulator, and collision mass and energy are not used to set the sampled yield.

#### 2.1.4 Stochastic Simulation

Collision events follow a **Poisson process** with rate $R \cdot \Delta t$. At each time step ($\Delta t = 0.1$ year ≈ 36.5 days):
1. Sample debris-satellite events: $n_{ds} \sim \text{Poisson}(R_{ds} \cdot \Delta t)$
2. Sample debris-debris events: $n_{dd} \sim \text{Poisson}(R_{dd} \cdot \Delta t)$
3. Generate fragments: DS fragments $\sim$ LogNormal(5.5, 0.8); DD fragments $\sim$ LogNormal(1.1, 0.5)
4. Apply orbital decay: $N_{\text{decay}} = N_d \cdot \lambda \cdot \Delta t \cdot \eta$, where $\lambda = 0.005$/year and $\eta \sim \mathcal{N}(1, 0.1)$ is clipped below at 0.1 (a multiplicative Gaussian perturbation, not a uniform additive one)
5. Update: $N_d \leftarrow \max(N_d + N_{\text{new}} - N_{\text{decay}},\; 0)$

**No separately tuned cascade-rate parameter.** Unlike prior models that introduce a tunable "cascade rate" constant, the collision terms in this framework are fixed by orbital mechanics. This is not the same as "no free parameters": $N_0$, the yield parameters $(\mu,\sigma)$, the 0.5% benchmark, $V_{\text{sat}}$, and $N_{\text{policies}}$ are modelling choices, and their influence is quantified in §4.4.

### 2.2 Economic Layer: Actuarial Pricing

#### 2.2.1 From Debris to Loss

The conversion from debris population to financial loss proceeds in four steps:

**Step 1 — Hit probability.** The per-satellite annual hit probability is derived from collision physics:

$$p_{\text{hit}} = \frac{N_d \cdot \sigma \cdot v_{\text{rel}} \cdot T_{\text{year}}}{V_{\text{shell}}}$$

At current debris levels, $p_{\text{hit}} \approx 0.089\%$ per satellite per year.

**Step 2 — Per-policy expected loss.** Each insured satellite's expected annual loss is $p_{\text{hit}} \times V_{\text{sat}}$, where $V_{\text{sat}} = \$50\text{M}$.

**Step 3 — Portfolio aggregation and correlation.** Expected loss is linear in portfolio size and is invariant to correlation:

$$L_{\text{portfolio}} = \sum_{i=1}^{N_{\text{policies}}} L_i, \qquad \mathbb{E}[L_{\text{portfolio}}] = N_{\text{policies}} \cdot p_{\text{hit}} \cdot V_{\text{sat}}$$

Correlation changes the variance and the tail, not the mean. For equal marginal loss variance $\sigma_L^2$ and pairwise correlation $\rho$:

$$\operatorname{Var}(L_{\text{portfolio}}) = N_{\text{policies}}\,\sigma_L^2\left[1 + (N_{\text{policies}}-1)\rho\right]$$

A Gaussian copula with $\rho=0.3$ is implemented in `portfolio_risk.py` for the variance and tail analysis. It is a separate module and is not used in the headline premium. An earlier draft's factor $(1+(n-1)\rho)/n$ was a variance ratio mistakenly applied to the mean; it has been removed.

**Step 4 — Risk metrics.** From the loss distribution across 1,000 Monte Carlo paths, I extract VaR, CVaR, and EVT metrics.

#### 2.2.2 Risk Metrics

- **Loss sample:** each Monte Carlo path contributes its worst-year loss, $L = \max_t L(t)$; the sample is therefore a distribution of worst-year losses, not of annual losses averaged over time.
- **Value at Risk (VaR):** $\text{VaR}_\alpha = F^{-1}(\alpha)$ where $F$ is the loss CDF
- **Conditional VaR (CVaR/ES):** $\text{CVaR}_\alpha = \mathbb{E}[L \mid L \ge \text{VaR}_\alpha]$
- **EVT VaR:** Generalized Pareto Distribution fit to excesses above the 90th percentile. With threshold $u$, scale $\beta$, shape $\xi$, and exceedance ratio $\zeta = N_u/n$:

$$\widehat{\text{VaR}}_p = u + \frac{\beta}{\xi}\left[\left(\frac{1-p}{\zeta}\right)^{-\xi}-1\right]$$

Omitting $\zeta$ overstates the tail probability by $1/\zeta$ (here 10×). EVT is a diagnostic cross-check; the premium uses the empirical $\text{CVaR}_{95}$ and $\text{VaR}_{99}$.

#### 2.2.3 Premium Decomposition (Solvency II)

$$P = \underbrace{\mathbb{E}[L_{\text{worst-year}}]}_{\text{Expected Loss}} + \underbrace{\lambda_R \cdot (\text{CVaR}_{95} - \mathbb{E}[L])}_{\text{Risk Loading}} + \underbrace{r \cdot (\text{VaR}_{99} - \mathbb{E}[L])}_{\text{Capital Charge}} + \underbrace{\lambda_E \cdot \mathbb{E}[L]}_{\text{Expense Loading}}$$

with $\lambda_R = 1.5$, $r = 0.04$, and $\lambda_E = 0.15$.

This is a **Solvency-II-style** decomposition, not the calculation prescribed by the Directive: Solvency II applies a 6% cost of capital to the SCR, whereas the risk loading here is a 1.5× multiple of the CVaR excess and the capital charge uses a 4% cost of capital. The three loadings are pricing assumptions, not regulatory parameters.

### 2.3 Consistency Check Against Observed Events

The three events below are used as an external consistency check and to anchor the order of magnitude of fragment yields; they are not a formal calibration of the operative log-normal parameters. The helper `calibrate_k_debris()` estimates a log-normal distribution for fragments per kilogram of catalogue mass, whereas the simulation samples fragments per collision; its output is therefore not wired into `k_debris_mu` or `k_debris_sigma`.

| Event | Date | Altitude | Trackable Fragments | Total Mass |
|-------|------|----------|-------------------|------------|
| Fengyun-1C ASAT | 2007-01-11 | 865 km | ~3,500 | 880 kg |
| Iridium 33 × Cosmos 2251 | 2009-02-10 | 790 km | ~2,300 | 1,510 kg |
| Kosmos 1408 ASAT | 2021-11-15 | 480 km | ~1,500 | 2,200 kg |

These events collectively created about 7,300 catalogued fragments. The counts are catalogue totals rather than per-collision yields, and catalog completeness and orbital decay differ by event, so they bound the yield only in order of magnitude.

---

## 3. Results

### 3.1 Baseline Simulation (1,000 Monte Carlo Paths)

| Metric | Value |
|--------|-------|
| Monte Carlo paths | 1,000 |
| Time horizon | 50 years |
| Time step | 0.1 year (36.5 days) |
| Initial debris (>10 cm) | 36,500 |
| Active satellites | 8,000 |
| Final debris (mean, year 50) | 1,509,425 |
| Final debris (median) | 1,429,504 |
| Final debris (95th percentile) | 2,236,440 |

### 3.2 Risk Metrics

| Metric | Definition | Value |
|--------|-----------|-------|
| Expected Loss | Mean worst-year portfolio loss | $921.4M |
| VaR₉₅ | 95th percentile of worst-year loss | $1,365M |
| CVaR₉₅ (ES) | Expected shortfall beyond VaR₉₅ | $1,565M |
| VaR₉₉ | 99th percentile of worst-year loss | $1,721M |
| CVaR₉₉ (ES) | Expected shortfall beyond VaR₉₉ | $1,854M |
| EVT VaR₉₅ | GPD/POT tail estimate ($\zeta=0.10$) | $1,375M |
| EVT VaR₉₉ | GPD/POT tail estimate | $1,677M |
| EVT shape (ξ) | GPD shape (ξ<0: bounded tail) | −0.032 |

EVT and the empirical quantiles agree within 3%: EVT VaR₉₅ $1,375M vs. empirical $1,365M (+0.7%); EVT VaR₉₉ $1,677M vs. empirical $1,721M (−2.5%); EVT CVaR₉₅ $1,562M vs. empirical $1,565M (−0.2%). The earlier 32% gap was an artifact of omitting the peaks-over-threshold exceedance ratio $\zeta$; it is not evidence of an underestimated tail. EVT is a diagnostic and is not used in the premium.

### 3.3 Insurance Premium (Solvency-II-Style Decomposition)

| Component | Formula | Amount |
|-----------|---------|--------|
| Expected Loss (EL) | Mean worst-year loss | $921.4M |
| Risk Loading | 1.5 × (CVaR₉₅ − EL) | $966.0M |
| Capital Charge | 4% × (VaR₉₉ − EL) | $32.0M |
| Expense Loading | 15% × EL | $138.2M |
| **Total Premium** | | **$2,058M/year** |
| Per-policy premium | Total / 500 policies | $4,115,098/year |
| Historical benchmark | 0.5% in-orbit failure × $50M × 500 | $125.0M/year |
| **Cascade Factor** | Cascade / Benchmark | **16.5×** |

The historical figure is a 0.5% in-orbit failure benchmark, not an observed market premium. At 1% the factor falls to 8.2×; at 0.3% it rises to 27.5×. The expected-loss-only gap is 7.4× ($921.4M / $125M); the remainder comes from the Solvency-II-style risk, capital, and expense loadings. The benchmark covers all in-orbit failures, whereas the model prices debris collisions only; a like-for-like debris-only benchmark would be smaller, so 16.5× is conservative with respect to coverage. For the same reason, the year-0 ratio (0.18×) is not a like-for-like comparison and is not read as evidence about current pricing.

**Time alignment.** The premium is computed on the worst-year sample, and in 100% of the 1,000 paths the worst year is the final step, so the headline is the fair annual premium at the end of the horizon, not today's. The same model gives expected losses of $22.3M at \(t=0\) (0.18× the static benchmark) and $111.0M at \(t=25\) (0.89×). The 16.5× therefore measures how far a static benchmark falls behind a growing cascade by year 50; it is not a claim that current premiums are 16.5× too low today.

### 3.4 Key Findings

1. **Debris grows 41× over 50 years** under business-as-usual conditions, from 36,500 to ~1.51 million objects. The growth is faster than exponential: the mean-field backbone has a finite-time singularity at \(t^*\approx61\) years, so the 50-year horizon sits at 82% of \(t^*\). The 41× is a horizon-specific projection, not a stable long-run rate.

2. **The premium gap grows to 16.5× over the horizon.** At year 50 the cascade-aware premium is $2,058M against $125M from a static benchmark, a $1,933M annual gap produced by physics and Solvency II loading combined; on an expected-loss-only basis the gap is 7.4×. The same model gives $22.3M of expected loss at year 0 (0.18× the benchmark), so the gap is a projection of how a static premium falls behind a growing cascade, not a statement about today's prices. For this 500-satellite portfolio the year-50 gap exceeds the estimated $1.2B global market, which is a solvency signal about a concentrated portfolio rather than a forecast of market-wide premiums.

3. **Tail risk is substantial but bounded.** CVaR₉₅ ($1,565M) exceeds the expected loss ($921M) by 70%, indicating that extreme cascade scenarios produce losses well above the mean. EVT VaR₉₅ ($1,375M) is within 0.7% of the empirical VaR₉₅ ($1,365M); the earlier 32% gap was an artifact of omitting the peaks-over-threshold exceedance ratio $\zeta$. The fitted tail is bounded ($\xi=-0.032$), not heavy.

4. **Risk loading dominates the premium.** The CVaR-based risk loading ($966M) exceeds the expected loss ($921M), reflecting the right-skewed loss distribution. This is a consequence of the quadratic feedback and of taking the worst year per path, not evidence of a power-law tail.

5. **EVT indicates a bounded tail.** The GPD shape parameter $\xi=-0.032$ is a Type III (bounded) tail. Empirical and EVT estimates agree within 3%, so EVT does not provide evidence that the Monte Carlo sample underestimates the tail; at 1,000 paths the 99% quantile remains noisy, which is why both estimates are reported.

---

## 4. Discussion

### 4.1 Model Validation

The qualitative conclusion — that the current LEO population is unstable under business-as-usual — is consistent with Liou & Johnson (2008). A quantitative alignment is not claimed: their scenario assumptions, fragment-yield model, and time horizon differ from mine, and no 41× factor is taken from their paper. The comparison is a directional consistency check, not a validation of the magnitude.

### 4.2 Systemic Risk Implications

The $1,933M annual gap between a static benchmark ($125M) and the year-50 cascade-adjusted premium ($2,058M) is a **solvency signal for concentrated books**, not a forecast of sector-wide insolvency. When debris density is high, all satellites face elevated risk simultaneously, so claims would be correlated across the entire portfolio. A cascade event at static premium levels could exceed reserves on a book like the 500-satellite test portfolio. The gap is larger than the roughly $1.2B annual global premium base precisely because that portfolio concentrates high-value satellites in one congested shell; scaling the benchmark to the whole market is not claimed.

### 4.3 Market Design

Conversely, cascade-aware pricing creates economic incentives for sustainability. Operators who place satellites in less congested shells or invest in end-of-life deorbiting would receive lower premiums — making debris mitigation profitable without regulatory mandates.

### 4.4 Limitations

1. **Single-shell approximation**: I model one altitude band (800 km) rather than the full 3D orbital environment with inclination and eccentricity distributions.
2. **Catalogue-scale count with a generous DD term**: the model tracks objects larger than 10 cm and omits the roughly one million 1–10 cm objects. Two choices in the debris–debris (DD) channel are optimistic for the headline. First, every DD event adds its ~3 fragments to the >10 cm count, although a few-fragment yield is more plausibly 1–10 cm debris; excluding those fragments lowers $N(50)$ from 1.51M to 758,000 and EL from \$921.4M to \$462.6M. Second, both channels share the 10 m² satellite cross-section, so the DD rate is an upper bound; a 1 m² DD section lowers $N(50)$ to 793,000 and EL to \$484.1M. The 16.5× therefore depends materially on the DD term and is an upper bound in this dimension.
3. **Simplified fragment physics**: the operative log-normal yield is an event-anchored prior, not a formal calibration. Collision mass and energy do not enter the sampler, and the NASA Standard Breakup Model is used only as an order-of-magnitude anchor.
4. **Initial condition**: $N_0 = 36{,}500$ is the global >10 cm catalogue, all assigned to the 700–900 km shell. This is an upper-bound assumption for the shell fraction. With 300 paths and seed 42, the cascade factor is 2.21× at $N_0=8{,}000$, 2.76× at 10,000, 3.37× at 12,000, 6.13× at 20,000, and 15.51× at 36,500 (the last differs from the 1,000-path 16.46× by 6%, a path-count effect).
5. **Finite-time singularity**: the deterministic backbone diverges at $t^*=61.1$ years; $N(55)=89.3N_0$ and $N(60)=581.5N_0$, so the 50-year horizon sits at 82% of $t^*$. One-at-a-time intervals over the six tornado parameters (including the DD yield) move $t^*$ between 27 and 136 years. The 41× growth is therefore a horizon-specific projection, not a stable long-run rate.
6. **Expected claim counts**: the loss model uses $p_{\text{hit}}N_{\text{policies}}$ as the annual claim count rather than drawing $\mathrm{Binomial}(N_{\text{policies}}, p_{\text{hit}})$. Adding that layer raises the worst-year EL from $921.4M to $1,242.5M (+35%) and VaR₉₅ from $1,365.1M to $1,752.5M (+28%). The 16.5× is a lower bound in this dimension.
7. **Benchmark sensitivity**: the 0.5% in-orbit failure rate is an assumption, not an observed market premium. At 1% the cascade factor falls to 8.2×; at 0.3% it rises to 27.5×.
8. **Expected-loss definition**: EL is the mean worst-year loss, not the mean annual loss. In the baseline, debris grows strongly in expectation, although individual paths step down in about 10% of steps (decay with no collision, measured on 300 paths); the maximum still falls on the final step in 100% of the 1,000 paths. This equivalence would break with ADR or a dynamic satellite population.
9. **Monte Carlo resolution**: 1,000 paths. At 300/1,000/2,000 paths, EL is $925.0M/$921.4M/$921.6M and VaR₉₅ is $1,354.9M/$1,365.1M/$1,364.9M; at $\Delta t=0.2/0.1/0.05$ year, EL is $896.5M/$925.0M/$913.0M. The 99% quantile and the GPD shape parameter remain uncertain at this sample size.
10. **Hit-probability linearization**: the model uses $\min(\lambda,1)$ for the annual hit probability rather than $1-e^{-\lambda}$. At year 50 the two differ by 1.8%; at year 0 by less than 0.05%.
11. **No active debris removal**: the model does not account for emerging ADR technologies that could reduce debris populations.
12. **Static satellite population**: the satellite count is held constant; in reality, mega-constellation deployments and end-of-life deorbiting affect the population dynamically.
13. **No cross-shell migration**: debris generated at one altitude may migrate to others due to atmospheric drag and collision-induced velocity changes.

### 4.5 Future Work

1. **Multi-shell model**: Extend to multiple altitude bands (600, 800, 1000, 1200 km) with cross-shell debris migration.
2. **Real TLE data calibration**: Incorporate NORAD Two-Line Element catalogs for initial debris distribution.
3. **Dynamic satellite population**: Model constellation deployment and deorbiting schedules.
4. **Active debris removal scenarios**: Quantify the insurance premium reduction from ADR interventions.
5. **Reinsurance layer**: Model excess-of-loss and stop-loss reinsurance structures for cascade risk transfer.
6. **Global sensitivity analysis**: identify the most impactful parameters with a variance-based Saltelli design using a low-discrepancy sequence; the current tornado chart is a one-at-a-time diagnostic, not a Sobol decomposition.

---

## 5. Conclusion

This framework demonstrates that incorporating physics-based cascade dynamics into insurance pricing produces a **16.5× gap** relative to a 0.5% in-orbit failure benchmark (7.4× on expected loss alone). The model's key innovation is replacing ad-hoc cascade parameters with first-principles collision physics: debris growth is driven by actual collision rates computed from orbital mechanics, with event-anchored fragment yields and asymmetric treatment of debris-satellite versus debris-debris collisions. The framework provides insurers with a tool for quantifying cascade risk through VaR, CVaR, and EVT metrics, and decomposes premiums with a Solvency-II-style loading structure (the 6% cost-of-capital calculation of Directive 2009/138/EC is not reproduced). The $1,933M annual gap represents both a systemic risk to insurers and an opportunity for market-based debris mitigation incentives. The magnitude is conditional: it assumes the entire >10 cm catalogue sits in the 700–900 km shell, uses expected claim counts, treats debris–debris fragments as catalogue objects (a generous upper bound), and sits close to a finite-time singularity; these caveats are quantified in §4.4 and should accompany the headline in any policy use.

---

## References

1. Kessler, D.J. (1978). "Collision Frequency of Artificial Satellites: The Creation of a Debris Belt." *Journal of Geophysical Research*, 83(A7), 2637-2646.
2. Kessler, D.J. (1981). "Derivation of the collision probability between orbiting objects." *Icarus*, 48(1), 39-48.
3. Liou, J.-C. & Johnson, N.L. (2008). "Instability of the present LEO satellite populations." *Advances in Space Research*, 41(7), 1046-1053.
4. Johnson, N.L. et al. (2008). "History of On-Orbit Satellite Fragmentations, 14th Edition." NASA Orbital Debris Program Office.
5. Freeman, R. et al. (2021). "An actuarial modifier for underwriting OOS satellite insurance." *The Journal of Space Operations*.
6. McNeil, A.J., Frey, R. & Embrechts, P. (2015). *Quantitative Risk Management.* 2nd ed. Princeton University Press.
7. European Commission (2009). "Solvency II Directive." 2009/138/EC.
8. IADC (2007). "Space Debris Mitigation Guidelines." Inter-Agency Space Debris Coordination Committee.
9. UNCOPUOS (2019). "Space 2030 Agenda." United Nations Committee on the Peaceful Uses of Outer Space.
10. World Economic Forum / Centre for Space Futures (2026). "Clear Orbit, Secure Future: A Call to Action on Space Debris."
11. ESA Space Environment Report (2025). European Space Agency.
12. Saltelli, A. et al. (2010). "Variance based sensitivity analysis." *Computer Physics Communications*, 181(2), 259-270.

---

## Data & Code Availability

The simulation code is organized as a Python package (`cascade_risk/`) with modular architecture:
- `physics/`: Orbital mechanics, collision models, Monte Carlo simulator
- `actuarial/`: Loss distributions, risk metrics, premium pricing
- `calibration/`: Historical event data and parameter fitting
- `analysis/`: Sensitivity analysis and visualization

Configuration is managed via YAML files in `configs/`. The simulation code is released under the Apache License 2.0 (see `LICENSE`); the manuscript text is distributed under CC BY 4.0. Running `python -X utf8 main.py` reproduces the headline numbers, and `python -X utf8 study/verify_baseline.py` prints a step-by-step cross-check.

---

*Correspondence: ling.xi.lu@gmail.com*
