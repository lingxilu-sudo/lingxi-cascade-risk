# Space Debris Cascade Risk and Insurance Pricing

**To:** SGAC Space Safety & Sustainability Project Group
**From:** Lingxi Lu
**Date:** October 2026

---

## The Idea

Space insurance is priced off historical launch failure rates. Nobody models cascade risk — the possibility that one collision triggers a chain reaction, hitting an entire portfolio at once.

I built a model that does. It couples collision physics (Kessler-Flournoy rates, NASA breakup model, N² feedback) with actuarial pricing (VaR, CVaR, EVT, Solvency II decomposition).

The result: cascade-adjusted premiums are **5.0x higher** than current historical-loss pricing. $620M vs. $125M per year for a 500-satellite portfolio.

---

## What the Model Does

- Simulates debris growth in a LEO shell (800 km) over 50 years
- 1,000 Monte Carlo paths, Poisson collision events, asymmetric fragment yields
- Debris grows from 36,500 to ~1.51 million objects (41x)
- Translates debris populations into loss distributions
- Extracts risk metrics and computes insurance premiums

Calibrated against three real events: Fengyun-1C (2007), Iridium-Cosmos (2009), Kosmos 1408 (2021).

---

## Why It Matters

If premiums don't reflect cascade risk:

- Insurers face insolvency from correlated claims
- No market incentive for operators to choose less congested orbits
- The UN Space 2030 Agenda has no economic enforcement mechanism

Risk-adjusted pricing could fix this. Operators in congested shells pay more. Those who deorbit responsibly pay less. Market-based sustainability without new regulations.

---

## What I'm Asking

1. Feedback from people who know this field
2. Possible transmission to UNCOPUOS
3. Collaboration opportunities

I'm a high school student. The model has limitations (single-shell, no ADR, no multi-altitude dynamics). But the core insight — that physics-based cascade risk should inform insurance pricing — seems worth pursuing.

---

## Available On Request

- Technical paper (~15 pages, full methodology)
- Code (Python, CC BY 4.0)
- Interactive explainer (HTML)

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
