"""
Generate the Cascade Risk Framework paper as a professional PDF.
Formatted for submission to international organizations (UNOOSA, SGAC, IADC).
A4 layout, Times Roman, with page numbers, headers, and keywords.

Usage:
    python gen_paper_pdf.py
    # Output: framework_paper.pdf (project root)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus import NextPageTemplate
from reportlab.lib.units import inch

# -- Page number callback ---------------------------------------------
def add_page_number(canvas, doc):
    """Add page number and header line to each page."""
    canvas.saveState()
    page_num = canvas.getPageNumber()
    # Footer: page number
    canvas.setFont('Times-Roman', 8)
    canvas.setFillColor(colors.HexColor('#666666'))
    canvas.drawCentredString(A4[0]/2, 1.2*cm, f"- {page_num} -")
    # Header line (after first page)
    if page_num > 1:
        canvas.setFont('Times-Italic', 7.5)
        canvas.setFillColor(colors.HexColor('#999999'))
        canvas.drawString(2.5*cm, A4[1] - 1.5*cm,
            "Cascade Risk Framework  |  Space Debris Insurance Pricing")
        canvas.drawRightString(A4[0] - 2.5*cm, A4[1] - 1.5*cm,
            "Working Paper  |  October 2026")
        # Thin rule
        canvas.setStrokeColor(colors.HexColor('#cccccc'))
        canvas.setLineWidth(0.5)
        canvas.line(2.5*cm, A4[1] - 1.65*cm, A4[0] - 2.5*cm, A4[1] - 1.65*cm)
    canvas.restoreState()

# -- Document Setup ---------------------------------------------------
doc = SimpleDocTemplate(
    'framework_paper.pdf',
    pagesize=A4,
    leftMargin=2.5*cm, rightMargin=2.5*cm,
    topMargin=2.2*cm, bottomMargin=2.2*cm
)

styles = getSampleStyleSheet()

# -- Custom Styles ----------------------------------------------------
title_style = ParagraphStyle(
    'PaperTitle', parent=styles['Title'],
    fontSize=15, leading=19, alignment=TA_CENTER,
    spaceAfter=4, fontName='Times-Bold',
    textColor=colors.HexColor('#0f1a30')
)
subtitle_style = ParagraphStyle(
    'Subtitle', parent=styles['Normal'],
    fontSize=10.5, leading=14, alignment=TA_CENTER,
    fontName='Times-Italic', textColor=colors.HexColor('#444444'),
    spaceAfter=8
)
author_style = ParagraphStyle(
    'Author', parent=styles['Normal'],
    fontSize=11, alignment=TA_CENTER, spaceAfter=3,
    fontName='Times-Roman'
)
affil_style = ParagraphStyle(
    'Affiliation', parent=styles['Normal'],
    fontSize=9.5, alignment=TA_CENTER, spaceAfter=2,
    fontName='Times-Italic', textColor=colors.HexColor('#555555')
)
h1_style = ParagraphStyle(
    'H1', parent=styles['Heading1'],
    fontSize=12.5, leading=16, spaceBefore=18, spaceAfter=8,
    fontName='Times-Bold', textColor=colors.HexColor('#0f1a30')
)
h2_style = ParagraphStyle(
    'H2', parent=styles['Heading2'],
    fontSize=11, leading=14, spaceBefore=12, spaceAfter=6,
    fontName='Times-Bold', textColor=colors.HexColor('#1a2744')
)
h3_style = ParagraphStyle(
    'H3', parent=styles['Heading3'],
    fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=4,
    fontName='Times-BoldItalic', textColor=colors.HexColor('#2a3f6a')
)
body_style = ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontSize=10.5, leading=15, alignment=TA_JUSTIFY,
    fontName='Times-Roman', spaceAfter=6,
    firstLineIndent=0
)
eq_style = ParagraphStyle(
    'Equation', parent=body_style,
    alignment=TA_CENTER, fontName='Times-Italic',
    spaceBefore=8, spaceAfter=8
)
table_note = ParagraphStyle(
    'TableNote', parent=body_style,
    fontSize=9, fontName='Times-Italic', spaceAfter=4,
    textColor=colors.HexColor('#555555')
)
keyword_style = ParagraphStyle(
    'Keywords', parent=body_style,
    fontSize=9.5, fontName='Times-Italic',
    spaceBefore=6, spaceAfter=12,
    textColor=colors.HexColor('#444444')
)

# -- Helper: styled table ---------------------------------------------
def make_table(data, col_widths=None):
    w = col_widths or [10*cm, 6*cm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a2744')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    return t

# -- Build Story ------------------------------------------------------
story = []

# ===== TITLE PAGE CONTENT ============================================
story.append(Spacer(1, 1.5*cm))
story.append(Paragraph(
    "A Physics-Based Monte Carlo Framework for Space Debris Cascade Risk and Insurance Pricing",
    title_style
))
story.append(Spacer(1, 0.6*cm))

# Horizontal rule
story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor('#c8a84e'),
                         spaceBefore=4, spaceAfter=12))

story.append(Paragraph("Lingxi Lu", author_style))
story.append(Paragraph("Independent Researcher", affil_style))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("October 2026  |  Version 2.0  |  Working Paper", affil_style))
story.append(Spacer(1, 0.8*cm))

# Abstract
story.append(Paragraph("<b>Abstract</b>", ParagraphStyle(
    'AbstractHead', parent=body_style, fontSize=10.5, fontName='Times-Bold',
    spaceBefore=4, spaceAfter=4
)))
story.append(Paragraph(
    "The commercial space insurance market was worth about $1.2 billion in 2025 (industry estimates vary). It prices satellite risk using launch and in-orbit failure experience. But no actuarial model accounts for cascade risk, where one collision generates debris that triggers more collisions, producing correlated losses across a portfolio. I build a coupled physics-actuarial framework to address this. For the physics piece, I wrote Monte Carlo code that tracks debris cascades in Low Earth Orbit (LEO). Collision rates come straight from orbital mechanics, not a separately tuned cascade-rate parameter. On the pricing side, I used Value at Risk (VaR), Conditional VaR (CVaR), and Extreme Value Theory (EVT) to convert loss distributions into premiums. I set the simulation at 800 km and ran it for 50 years. Debris went from 36,500 to roughly 1.51 million objects. The premiums I get are <i>16.5 times higher</i> than a 0.5%-of-hull-value in-orbit failure benchmark, $2,058 million against $125 million per year for 500 satellites; on expected loss alone the gap is 7.4 times. The $1,933 million gap is a systemic solvency concern for a portfolio concentrated in one shell, and it undermines long-term sustainability of outer space activities. I check the model against three real collision events and break down premiums following the Solvency II framework. I also discuss what this means for the UN Space 2030 Agenda and argue that risk-adjusted pricing could serve as an economic instrument for orbital sustainability. The 16.5x is conditional: it assigns the entire >10 cm catalogue to the 700-900 km shell, uses expected claim counts, and the mean-field backbone reaches a finite-time singularity at t* = 61 years, only 11 years beyond the horizon.",
    body_style
))

# Keywords
story.append(Paragraph(
    "<b>Keywords:</b> space debris, Kessler Syndrome, satellite insurance, Monte Carlo simulation, "
    "cascade risk, Solvency II, Extreme Value Theory, orbital sustainability, "
    "space traffic management, UN Space 2030 Agenda",
    keyword_style
))

story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'),
                         spaceBefore=8, spaceAfter=12))

# ===== 1. INTRODUCTION ===============================================
story.append(Paragraph("1. Introduction", h1_style))

story.append(Paragraph("1.1 The Unpriced Risk to Orbital Sustainability", h2_style))
story.append(Paragraph(
    "The space debris environment in Low Earth Orbit (LEO) has changed. It is no longer a background condition. It is an active operating cost. Tracking networks currently count approximately 36,500 objects larger than 10 cm in Earth orbit. On top of that, there are roughly 1 million objects between 1-10 cm and 130 million smaller fragments, according to the ESA Space Environment Report (2025). The World Economic Forum put a price tag on this: $25.8-$42.3 billion in debris-related costs for LEO assets between 2025 and 2035, assuming nothing changes. That kind of trajectory does not square with the long-term sustainability goals in the UN Space 2030 Agenda or the IADC Space Debris Mitigation Guidelines.",
    body_style
))
story.append(Paragraph(
    "And yet the $1.2 billion space insurance market still prices risk the old way, using historical loss data. Mostly launch and in-orbit failure experience plus single-asset collision probabilities. <i>Nobody is modeling the chance that one debris event sets off a cascade</i>, generating correlated claims across a whole portfolio at once. That gap creates a moral hazard. Operators flying in congested shells pay premiums that have nothing to do with the systemic risk they impose on everyone else in orbit.",
    body_style
))

story.append(Paragraph("1.2 Prior Work and Gap", h2_style))
story.append(Paragraph(
    "Freeman et al. (2021) came closest. They built an actuarial modifier for On-Orbit Servicing (OOS) satellite insurance, folding debris mitigation into premiums, but only for direct collision risk. Cascade dynamics, the chain-reaction scenario Kessler (1978) laid out, were not part of their model. Liou and Johnson (2008) ran numerical simulations that showed LEO satellite populations are unstable. They did not take the step of linking those results to insurance pricing. To my knowledge, nobody has coupled first-principles collision physics with actuarial risk metrics to produce regulatory-compliant insurance premiums.",
    body_style
))

story.append(Paragraph("1.3 Contribution", h2_style))
story.append(Paragraph(
    "My framework does six things. It couples collision physics with actuarial science so debris growth is driven by actual collision rates, with no separately tuned cascade-rate parameter. Collision events are drawn from a Poisson distribution, with event-anchored log-normal fragment yields; the NASA Standard Breakup Model serves as an order-of-magnitude anchor. DS and DD collision yields are kept separate, which delays but does not remove the finite-time singularity; the baseline mean-field singularity is at t* = 61 years. Portfolio-level correlated risk is handled by a separate Gaussian-copula module for variance and tail analysis; expected loss itself is correlation-invariant. Extreme Value Theory handles tail risk estimation with a peaks-over-threshold exceedance ratio. The yield scale is checked against three documented collision events, not formally calibrated to them. I also discuss the framework's relevance to international space governance and propose risk-adjusted pricing as an economic instrument for orbital sustainability.",
    body_style
))

# ===== 2. METHODOLOGY =================================================
story.append(Paragraph("2. Methodology", h1_style))

story.append(Paragraph("2.1 Physical Layer: Collision-Driven Debris Dynamics", h2_style))
story.append(Paragraph(
    "I model a representative LEO shell at altitude h = 800 km with thickness dh = 200 km (700-900 km). The shell volume works out to V = 1.29 x 10<super>11</super> km<super>3</super>. I picked this altitude because it has the most defunct satellites and is where most mega-constellations operate. Drag at 800 km is weak enough that debris can stick around for decades, sometimes centuries.",
    body_style
))

story.append(Paragraph("2.1.1 Collision Rate", h3_style))
story.append(Paragraph(
    "For collision rates between debris and satellites, I use the Kessler-Flournoy formula:",
    body_style
))
story.append(Paragraph(
    "<i>R</i><sub>ds</sub> = <i>N</i><sub>d</sub> ⋅ <i>N</i><sub>s</sub> ⋅ <i>σ</i> ⋅ <i>v</i><sub>rel</sub> ⋅ <i>T</i> / <i>V</i>                                                                                         (1)",
    eq_style
))
story.append(Paragraph(
    "Debris-debris collisions drive the cascade. The rate <i>R</i><sub>dd</sub> is proportional to <i>N</i><sub>d</sub>(<i>N</i><sub>d</sub>−1), which means it scales with <i>N</i><sub>d</sub><super>2</super>. Double the debris, you quadruple the collision rate. This quadratic feedback is the mathematical root of the cascade. At current population levels (<i>N</i><sub>d</sub> = 36,500, <i>N</i><sub>s</sub> = 8,000), I compute about 7 debris-satellite and 16 debris-debris collisions per year.",
    body_style
))

story.append(Paragraph("2.1.2 Fragment Generation", h3_style))
story.append(Paragraph(
    "The <i>asymmetric fragment yield</i> between collision types is an event-anchored prior; the NASA Standard Breakup Model is used only as an order-of-magnitude anchor:",
    body_style
))
frag_data = [
    ['Collision Type', 'Distribution', 'Median', 'Physical Rationale'],
    ['Debris-Satellite (DS)', 'LogNormal(5.5, 0.8)', '~245', 'Large satellite breakup'],
    ['Debris-Debris (DD)', 'LogNormal(1.1, 0.5)', '~3', 'Small fragment impact'],
]
story.append(make_table(frag_data, [4.5*cm, 4*cm, 2*cm, 5.5*cm]))
story.append(Paragraph(
    "Without this distinction, the N<super>2</super> scaling of DD rates combined with high yields (~245) would produce a much earlier finite-time singularity. With it, the baseline mean-field backbone diverges at t* = 61 years, only 11 years beyond the 50-year horizon. The asymmetry reflects the energy differential: a fragment striking an intact satellite releases orders of magnitude more energy than two small fragments colliding.",
    table_note
))

story.append(Paragraph("2.1.3 Stochastic Time-Stepping", h3_style))
story.append(Paragraph(
    "I model collisions as a Poisson process. I broke time into 0.1-year steps, about 36.5 days each. Within each step, I draw DS and DD collision counts, generate fragments from log-normal distributions, apply orbital decay (<i>λ</i> = 0.005/year with multiplicative Gaussian noise, standard deviation 10%, clipped below at 0.1), and update the population. <i>There is no separately tuned cascade-rate parameter</i>; the collision terms are fixed by orbital mechanics. That is not the same as \"no free parameters\": initial debris count, yield parameters, the 0.5% benchmark, satellite value, and portfolio size are modelling choices, and their influence is quantified in the limitations. Each Monte Carlo path uses a distinct random seed for reproducibility.",
    body_style
))

story.append(Paragraph("2.2 Economic Layer: From Debris to Insurance Premiums", h2_style))
story.append(Paragraph(
    "Getting from debris population to financial loss takes four steps. First, I compute per-satellite annual hit probability <i>p</i><sub>hit</sub> = <i>N</i><sub>d</sub> ⋅ <i>σ</i> ⋅ <i>v</i> ⋅ <i>T</i> / <i>V</i>. Second, I calculate per-policy expected loss = <i>p</i><sub>hit</sub> ⋅ <i>V</i><sub>sat</sub> ($50M average). Third, I aggregate the portfolio: expected loss is <i>p</i><sub>hit</sub> ⋅ <i>V</i><sub>sat</sub> ⋅ 500 and is invariant to correlation. A separate Gaussian-copula module (<i>ρ</i> = 0.3) is used for variance and tail analysis, but it does not enter the headline premium. Fourth, I pull out VaR, CVaR, and EVT risk metrics from 1,000 Monte Carlo paths.",
    body_style
))

story.append(Paragraph("2.2.1 Solvency-II-style Premium Decomposition", h3_style))
story.append(Paragraph(
    "<i>P</i> = E[<i>L</i>] + <i>λ</i><sub>R</sub> ⋅ (CVaR<sub>95</sub> − E[<i>L</i>]) + <i>r</i> ⋅ (VaR<sub>99</sub> − E[<i>L</i>]) + <i>λ</i><sub>E</sub> ⋅ E[<i>L</i>]                                                                                         (2)",
    eq_style
))
story.append(Paragraph(
    "where <i>λ</i><sub>R</sub> = 1.5 (risk loading multiplier), <i>r</i> = 0.04 (discount rate), <i>λ</i><sub>E</sub> = 0.15 (expense loading). This is a Solvency-II-style decomposition, not the calculation prescribed by Directive 2009/138/EC: the Directive applies a 6% cost of capital to the SCR, whereas the risk loading here is a multiple of the CVaR excess and the capital charge uses a 4% cost of capital. The three loadings are pricing assumptions, not regulatory parameters.",
    body_style
))

story.append(Paragraph("2.3 Consistency Check Against Observed Events", h2_style))
cal_data = [
    ['Event', 'Date', 'Fragments (>10cm)', 'Mass'],
    ['Fengyun-1C (ASAT test)', '2007-01-11', '~3,500', '880 kg'],
    ['Iridium 33 x Cosmos 2251', '2009-02-10', '~2,300', '1,510 kg'],
    ['Kosmos 1408 (ASAT test)', '2021-11-15', '~1,500', '2,200 kg'],
]
story.append(make_table(cal_data, [5.5*cm, 3*cm, 3.5*cm, 4*cm]))
story.append(Paragraph(
    "These three events collectively created about 7,300 catalogued fragments. The counts are catalogue totals rather than per-collision yields, so they are used as an order-of-magnitude consistency check, not to fit the operative log-normal parameters. Both ASAT tests (Fengyun-1C, Kosmos 1408) and the accidental collision (Iridium-Cosmos) are represented, ensuring the model captures both intentional and unintentional debris generation mechanisms.",
    table_note
))

story.append(Paragraph("2.4 Validation Against Current Observations", h2_style))
val_data = [
    ['Metric', 'Model Value', 'Observed/Market Data', 'Source'],
    ['Tracked debris (>10cm), 2025', '36,500', '36,500', '[11]'],
    ['Global insurance market, 2025', '-', '$1.2B', '[10]'],
    ['In-orbit failure benchmark', '0.5%', 'Assumption, not observed premium', 'Model assumption'],
    ['Fengyun-1C fragments', '~3,500', '~3,500', '[4]'],
    ['Iridium-Cosmos fragments', '~2,300', '~2,300', '[4]'],
    ['Kosmos 1408 fragments', '~1,500', '~1,500', '[4]'],
    ['Cascade-adjusted premium', '$2,058M/year', 'Not yet priced', 'Model prediction'],
]
story.append(make_table(val_data, [5*cm, 3.5*cm, 3.5*cm, 4*cm]))
story.append(Paragraph(
    "The model's initial conditions align with current observational data from the ESA Space Environment "
    "Report 2025 [11]. The event counts are order-of-magnitude consistency checks against IADC records and "
    "NASA fragmentation data [4], not a formal calibration. The cascade-adjusted premium of $2,058M/year "
    "represents what insurance pricing should reflect if cascade risk were properly accounted for, compared "
    "with a $125M/year benchmark built from a 0.5% in-orbit failure assumption, not an observed market premium.",
    table_note
))

# ===== 3. RESULTS =====================================================
story.append(Paragraph("3. Results", h1_style))

story.append(Paragraph("3.1 Debris Projection", h2_style))
sim_data = [
    ['Parameter', 'Value'],
    ['Monte Carlo paths', '1,000'],
    ['Time horizon', '50 years (2025-2075)'],
    ['Time step', '0.1 year (36.5 days)'],
    ['Initial debris (>10 cm)', '36,500'],
    ['Active satellites in shell', '8,000'],
    ['Insured portfolio', '500 satellites at $50M each'],
    ['Final debris (mean)', '1,509,425'],
    ['Final debris (median)', '1,429,504'],
    ['Final debris (95th pctile)', '2,236,440'],
]
story.append(make_table(sim_data, [7*cm, 9*cm]))
story.append(Paragraph(
    "Debris grows 41x over 50 years under business-as-usual conditions. The 95th percentile path "
    "reaches 2.24 million objects, representing a 61x increase. This is a horizon-specific projection: "
    "the deterministic mean-field backbone has a finite-time singularity at 61 years, so the 50-year "
    "point sits at 82% of t*.",
    table_note
))
story.append(Spacer(1, 6))

story.append(Paragraph("3.2 Actuarial Risk Metrics", h2_style))
risk_data = [
    ['Metric', 'Definition', 'Value'],
    ['Expected Loss (EL)', 'Mean worst-year portfolio loss', '$921.4M'],
    ['VaR (95%)', '95th pctile worst-year loss', '$1,365M'],
    ['CVaR (95%) / ES', 'Avg loss beyond VaR(95%)', '$1,565M'],
    ['VaR (99%)', '99th pctile worst-year loss', '$1,721M'],
    ['CVaR (99%) / ES', 'Avg loss beyond VaR(99%)', '$1,854M'],
    ['EVT VaR (95%)', 'GPD/POT estimate (zeta=0.10)', '$1,375M'],
    ['EVT VaR (99%)', 'GPD/POT estimate', '$1,677M'],
    ['EVT shape (xi)', 'GPD shape (xi<0: bounded)', '-0.032'],
]
story.append(make_table(risk_data, [4*cm, 6*cm, 6*cm]))
story.append(Spacer(1, 6))

story.append(Paragraph("3.3 Premium Decomposition", h2_style))
prem_data = [
    ['Component', 'Formula', 'Amount'],
    ['Expected Loss (EL)', 'Mean worst-year loss', '$921.4M'],
    ['Risk Loading', '1.5 x (CVaR95 - EL)', '$966.0M'],
    ['Capital Charge', '4% x (VaR99 - EL)', '$32.0M'],
    ['Expense Loading', '15% x EL', '$138.2M'],
    ['TOTAL PREMIUM', '', '$2,058M / year'],
    ['Per-policy premium', 'Total / 500 policies', '$4,115,098 / year'],
    ['Historical benchmark', '0.5% x $50M x 500', '$125.0M / year'],
    ['CASCADE FACTOR', 'Cascade / Benchmark', '16.5x'],
]
story.append(make_table(prem_data, [4.5*cm, 5.5*cm, 6*cm]))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "<b>Time alignment.</b> The premium is computed on the worst-year sample, and in 100% of the 1,000 paths "
    "the worst year is the final step, so the headline is the fair annual premium at the end of the horizon, "
    "not today's. The same model gives expected losses of $22.3M at t = 0 (0.18x the static benchmark) and "
    "$111.0M at t = 25 (0.89x). The 16.5x therefore measures how far a static benchmark falls behind a growing "
    "cascade by year 50; it is not a claim that current premiums are 16.5x too low today.",
    table_note
))
story.append(Spacer(1, 8))

story.append(Paragraph("3.4 Key Findings", h2_style))
story.append(Paragraph(
    "<b>1. Debris grows 41x over 50 years</b> (36,500 to 1.51M). The growth is faster than exponential: the mean-field backbone has a finite-time singularity at t* = 61 years, so the 50-year horizon sits at 82% of t*. The qualitative conclusion that LEO is unstable at current population levels is consistent with Liou and Johnson (2008), but no quantitative 41x alignment with their scenario is claimed.",
    body_style
))
story.append(Paragraph(
    "<b>2. The premium gap grows to 16.5x over the horizon.</b> At year 50 the cascade-adjusted premium ($2,058M) exceeds the 0.5% in-orbit failure benchmark ($125M) by $1,933M per year. That gap combines physics with Solvency-II-style loading; on expected loss alone it is 7.4x. The benchmark is all-peril while the model prices debris collisions only, so the ratio is conservative on coverage. The same model gives $22.3M of expected loss at year 0, which is 0.18x the benchmark, so the gap measures how a static premium falls behind a growing cascade rather than how mispriced today's market is. For a 500-satellite portfolio concentrated in one shell, the year-50 gap exceeds the estimated $1.2B global market, which is a solvency signal rather than a market-wide premium forecast. It is a lower bound on the fair premium because the model uses expected claim counts.",
    body_style
))
story.append(Paragraph(
    "<b>3. Tail risk is substantial but bounded.</b> CVaR(95%) ($1,565M) exceeds expected loss ($921M) by 70%. When I fit a generalized Pareto distribution with the peaks-over-threshold exceedance ratio (zeta = 0.10), EVT VaR(95%) comes in at $1,375M, within 0.7% of the empirical VaR(95%) of $1,365M. EVT VaR(99%) is $1,677M versus an empirical $1,721M. The earlier 32% gap was an artifact of omitting zeta; it is not evidence of an underestimated tail.",
    body_style
))
story.append(Paragraph(
    "<b>4. Risk loading dominates the premium.</b> The CVaR-based risk loading ($966M) exceeds the expected loss ($921M). This reflects the right-skewed loss distribution and the choice of worst-year loss, not a power-law tail; the fitted GPD shape is negative.",
    body_style
))
story.append(Paragraph(
    "<b>5. EVT indicates a bounded tail.</b> The GPD shape parameter xi = -0.032 indicates a Type III (bounded) tail. Empirical and EVT estimates agree within 3%, so EVT does not show that the Monte Carlo sample underestimates the tail; at 1,000 paths the 99% quantile remains noisy, which is why both estimates are reported.",
    body_style
))

# ===== 4. DISCUSSION ==================================================
story.append(Paragraph("4. Discussion", h1_style))

story.append(Paragraph("4.1 Systemic Risk to the Insurance Market", h2_style))
story.append(Paragraph(
    "The $1,933M annual gap between the benchmark and cascade-adjusted pricing is a <i>solvency concern for concentrated books</i>. When debris density is high, all satellites face elevated risk at the same time. Claims would be correlated across the entire portfolio; the separate copula module shows that correlation widens the tail rather than raising expected loss. A cascade event at static benchmark levels could exceed insurer reserves on a concentrated book and propagate losses to reinsurers. The historical record gives three reference points: Fengyun-1C in 2007, Iridium-Cosmos in 2009, Kosmos 1408 in 2021 - three events, each creating thousands of trackable fragments, all within a 14-year span.",
    body_style
))

story.append(Paragraph("4.2 Implications for International Space Governance", h2_style))
story.append(Paragraph(
    "Right now, the UN Space 2030 Agenda and IADC guidelines set norms for sustainable space operations. But there is no enforcement behind them. This framework proposes an <i>economic instrument</i> to go along with regulatory approaches: risk-adjusted insurance pricing that internalizes the externality of debris generation.",
    body_style
))
story.append(Paragraph(
    "Under cascade-aware pricing, operators who place satellites in less congested shells or invest in end-of-life deorbiting would get lower premiums. This gives operators a market-based incentive for sustainability without requiring direct regulation. Operators who contribute to orbital congestion would face premiums that reflect the systemic risk they impose on all space users.",
    body_style
))

story.append(Paragraph("4.3 Policy Recommendations", h2_style))
story.append(Paragraph(
    "<b>1.</b> Insurance regulators (e.g., EIOPA, NAIC) should require space insurers to disclose "
    "whether cascade risk is incorporated into pricing models.",
    body_style
))
story.append(Paragraph(
    "<b>2.</b> The IADC and UNCOPUOS should commission independent studies on the macroeconomic "
    "implications of underpriced cascade risk.",
    body_style
))
story.append(Paragraph(
    "<b>3.</b> Space agencies should explore premium differentiation as a condition for launch "
    "licensing -- satellites in congested shells pay higher insurance, which in funds debris mitigation.",
    body_style
))
story.append(Paragraph(
    "<b>4.</b> Reinsurance markets should develop cascade-risk-specific instruments (e.g., catastrophe "
    "bonds tied to debris density thresholds) to transfer systemic risk off insurer balance sheets.",
    body_style
))

story.append(Paragraph("4.4 Limitations", h2_style))
story.append(Paragraph(
    "Several limitations warrant discussion. First, the single-shell approximation (800 km only) does "
    "not capture the full 3D orbital environment with inclination and eccentricity distributions. Second, "
    "the model counts only catalogue-scale objects (>10 cm), yet each debris-debris event adds its ~3 "
    "fragments to that count and both channels share a 10 m2 satellite cross-section. Both choices raise "
    "the loss: excluding the DD fragments gives EL $462.6M, and a 1 m2 DD section gives $484.1M, so the "
    "$921.4M headline is an upper bound in this dimension. Third, fragment physics are "
    "simplified: the log-normal yield is an event-anchored prior, not a formal calibration, and collision "
    "mass and energy do not enter the sampler. Fourth, the initial condition assigns the entire global "
    ">10 cm catalogue to the 700-900 km shell; a sensitivity run gives cascade factors of 2.2x at N0 = 8,000 "
    "and 15.5x at 36,500, so the headline is conditional on that assumption. Fifth, the mean-field backbone "
    "has a finite-time singularity at t* = 61 years, so the 50-year horizon sits at 82% of t*; one-at-a-time "
    "parameter changes move t* between 27 and 136 years. Sixth, the loss model uses expected claim counts; "
    "adding Binomial(500, p_hit) noise raises worst-year EL to $1,242.5M (+35%) and VaR95 to $1,752.5M (+28%), "
    "so 16.5x is a lower bound in that dimension. Seventh, the 0.5% benchmark is an in-orbit failure "
    "assumption, not an observed market premium: 0.3% gives 27.5x and 1% gives 8.2x. Eighth, EL is the mean "
    "worst-year loss, and the model does not include active debris removal, dynamic satellite populations, "
    "or cross-altitude migration.",
    body_style
))

story.append(Paragraph("4.5 Future Work", h2_style))
story.append(Paragraph(
    "Future research directions include: (1) multi-shell model with cross-altitude migration; "
    "(2) NORAD TLE data integration for empirical debris tracking; (3) dynamic constellation deployment "
    "modeling; (4) ADR scenario analysis and premium reduction quantification; (5) reinsurance layer "
    "pricing (excess-of-loss, stop-loss, catastrophe bonds); (6) variance-based global sensitivity analysis "
    "with a low-discrepancy Saltelli design, since the current tornado chart is one-at-a-time.",
    body_style
))

# ===== 5. CONCLUSION ==================================================
story.append(Paragraph("5. Conclusion", h1_style))
story.append(Paragraph(
    "This framework shows that incorporating physics-based cascade dynamics into insurance pricing produces a <i>16.5x gap</i> relative to a 0.5% in-orbit failure benchmark (7.4x on expected loss alone). The main innovation is replacing ad-hoc cascade parameters with first-principles collision physics. Debris growth is driven by actual collision rates, with event-anchored fragment yields and asymmetric treatment of debris-satellite versus debris-debris collisions.",
    body_style
))
story.append(Paragraph(
    "The $1,933M annual pricing gap is a systemic risk to the global space insurance market, but it is also an opportunity. Risk-adjusted pricing can work as an economic instrument for orbital sustainability, going along with the regulatory framework of the UN Space 2030 Agenda. By aligning private insurance costs with systemic debris risk, this framework gives us a market-based pathway toward long-term sustainability of outer space activities. These numbers are conditional: the entire >10 cm catalogue is assigned to the 700-900 km shell, claim counts are treated as expected values, and the mean-field backbone is 11 years from a finite-time singularity. The 16.5x should be read with those boundaries, which are quantified in the limitations.",
    body_style
))

# ===== REFERENCES =====================================================
story.append(Paragraph("References", h1_style))
refs = [
    'Kessler, D.J. and Cour-Palais, B.G. (1978). "Collision Frequency of Artificial Satellites: The Creation of a Debris Belt." <i>J. Geophys. Res.</i>, 83(A6), 2637-2646.',
    'Kessler, D.J. (1981). "Derivation of the collision probability between orbiting objects." <i>Icarus</i>, 48(1), 39-48.',
    'Liou, J.-C. and Johnson, N.L. (2008). "Instability of the present LEO satellite populations." <i>Advances in Space Research</i>, 41(7), 1046-1053.',
    'Johnson, N.L. et al. (2008). "History of On-Orbit Satellite Fragmentations, 14th Edition." NASA Orbital Debris Program Office.',
    'Freeman, R. et al. (2021). "An actuarial modifier for underwriting OOS satellite insurance." <i>J. Space Operations</i>.',
    'McNeil, A.J., Frey, R. and Embrechts, P. (2015). <i>Quantitative Risk Management.</i> 2nd ed. Princeton University Press.',
    'European Commission (2009). "Solvency II Directive." 2009/138/EC.',
    'IADC (2007). "Space Debris Mitigation Guidelines." Inter-Agency Space Debris Coordination Committee.',
    'UNCOPUOS (2019). "Space 2030 Agenda." United Nations Committee on the Peaceful Uses of Outer Space.',
    'World Economic Forum / Centre for Space Futures (2026). "Clear Orbit, Secure Future: A Call to Action on Space Debris."',
    'ESA Space Environment Report (2025). European Space Agency.',
    'Saltelli, A. et al. (2010). "Variance based sensitivity analysis." <i>Comput. Phys. Commun.</i>, 181(2), 259-270.',
]
ref_style = ParagraphStyle('Ref', parent=body_style, fontSize=9, leading=13,
                           leftIndent=20, firstLineIndent=-20)
for i, ref in enumerate(refs, 1):
    story.append(Paragraph(f"[{i}] {ref}", ref_style))

# ===== DATA AVAILABILITY & CONTACT ====================================
story.append(Spacer(1, 14))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'),
                         spaceBefore=4, spaceAfter=8))
story.append(Paragraph(
    "<b>Data and Code Availability:</b> The simulation code is released under the Apache License 2.0 "
    "(see LICENSE); the manuscript text is distributed under CC BY 4.0. "
    "Source code (Python package <i>cascade_risk/</i>), configuration files, and simulation "
    "output data are available from the author upon request.",
    ParagraphStyle('DataAvail', parent=body_style, fontSize=9)
))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "<i>Correspondence: ling.xi.lu@gmail.com</i>",
    ParagraphStyle('Contact', parent=body_style, fontSize=9.5,
                   alignment=TA_CENTER, spaceBefore=6)
))

# -- Build with page numbers ------------------------------------------
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print("PDF generated: framework_paper.pdf")
