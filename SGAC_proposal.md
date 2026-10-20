# Space Debris Cascade Risk and Insurance Pricing

**To:** SGAC Space Safety & Sustainability Project Group
**From:** Lingxi Lu
**Date:** October 2026

---

## The Idea

Space insurance is priced off launch and in-orbit failure experience. Nobody models cascade risk — the possibility that one collision triggers a chain reaction, hitting an entire portfolio at once.

I built a model that does. It couples collision physics (Kessler-Flournoy rates, event-anchored fragment yields, N² feedback) with actuarial pricing (VaR, CVaR, EVT as a diagnostic, Solvency-II-style premium decomposition).

The result: by year 50 of the horizon, cascade-adjusted premiums are **16.5x** a static 0.5%-of-hull benchmark. $2,058M vs. $125M per year for a 500-satellite portfolio. Timing matters: at year 0 the same model's expected loss is $22.3M, only 0.18x the benchmark, and it catches up around year 25. The finding is that a premium which never updates falls behind a growing cascade; it is not a claim that today's market is 16.5x wrong. Because the test portfolio concentrates 500 satellites in one shell, the year-50 gap also exceeds the ~$1.2B global market — a solvency signal for a concentrated book, not a market-wide forecast. One caveat cuts the other way: the debris–debris term is deliberately generous (its ~3 fragments per event are counted as >10 cm objects and share the 10 m² satellite cross-section), so the headline is an upper bound in that dimension — removing those fragments or using a 1 m² debris–debris section roughly halves the year-50 expected loss.

---

## What the Model Does

- Simulates debris growth in a LEO shell (800 km) over 50 years
- 1,000 Monte Carlo paths, Poisson collision events, asymmetric fragment yields
- Debris grows from 36,500 to ~1.51 million objects (41x)
- Translates debris populations into loss distributions
- Extracts risk metrics and computes insurance premiums

Checked against three real events as order-of-magnitude anchors, not a formal calibration: Fengyun-1C (2007), Iridium-Cosmos (2009), Kosmos 1408 (2021).

---

## Why It Matters

If premiums don't reflect cascade risk:

- A concentrated book faces correlated claims it has not reserved for
- No market incentive for operators to choose less congested orbits
- The UN Space 2030 Agenda has no economic enforcement mechanism

Risk-adjusted pricing could fix this. Operators in congested shells pay more. Those who deorbit responsibly pay less. Market-based sustainability without new regulations.

---

## What I'm Asking

1. Feedback from people who know this field
2. Possible transmission to UNCOPUOS
3. Collaboration opportunities

I'm a high school student. The model has limitations (one shell with the entire global catalogue assigned to it, no ADR, no multi-altitude dynamics, a mean-field backbone that diverges about 11 years beyond the horizon); each is quantified in the paper. But the core insight — that physics-based cascade risk should inform insurance pricing — seems worth pursuing.

---

## Already Public

- Paper (full methodology, CC BY 4.0): https://doi.org/10.5281/zenodo.23095041
- Code (Python, Apache 2.0): https://github.com/lingxilu-sudo/lingxi-cascade-risk
- Interactive explainer: https://4physics.xyz/explainer/

**Email:** ling.xi.lu@gmail.com

---

## References

1. Kessler & Cour-Palais (1978). *J. Geophys. Res.*, 83(A6), 2637-2646.
2. Liou & Johnson (2008). *Advances in Space Research*, 41(7), 1046-1053.
3. Freeman et al. (2021). *The Journal of Space Operations*.
4. European Commission (2009). Solvency II Directive 2009/138/EC.
5. IADC (2007). Space Debris Mitigation Guidelines.
6. UNCOPUOS (2019). Space 2030 Agenda.
7. World Economic Forum (2026). Clear Orbit, Secure Future.
8. ESA (2025). Space Environment Report.
