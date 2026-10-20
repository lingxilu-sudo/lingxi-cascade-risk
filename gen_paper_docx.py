"""
Generate the Cascade Risk Framework paper as an editable Word document (.docx).
Uses python-docx to produce a properly formatted document matching the PDF version.

Usage:
    python gen_paper_docx.py
    # Output: framework_paper.docx (project root)
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re


# ---------------------------------------------------------------------------
# OMML (Office Math Markup Language) helpers for native Word equations
# ---------------------------------------------------------------------------

def _omml_run(text, italic=True):
    """Create an OMML run (m:r). Math-italic by default, upright for operators."""
    r = OxmlElement('m:r')
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Cambria Math')
    rFonts.set(qn('w:hAnsi'), 'Cambria Math')
    rPr.append(rFonts)
    if not italic:
        sty = OxmlElement('m:sty')
        sty.set(qn('m:val'), 'p')  # plain (upright)
        rPr.append(sty)
    r.append(rPr)
    t = OxmlElement('m:t')
    t.text = text
    t.set(qn('xml:space'), 'preserve')
    r.append(t)
    return r


def _omml_sub(base, subscript, base_italic=True):
    """Create an OMML subscript element (m:sSub) — e.g. R_ds, CVaR_95."""
    sSub = OxmlElement('m:sSub')
    e = OxmlElement('m:e')
    e.append(_omml_run(base, italic=base_italic))
    sub = OxmlElement('m:sub')
    sub.append(_omml_run(subscript))
    sSub.append(e)
    sSub.append(sub)
    return sSub


def _build_omml(tokens):
    """Build an m:oMath element from token specifications.

    Token formats:
      ('sub', base, subscript)          — subscripted variable (italic base)
      ('sub', base, subscript, italic)  — subscripted with explicit base style
      ('op', text)                      — upright operator (=, +, ⋅, /, …)
      ('txt', text)                     — math-italic run
      ('txt', text, False)              — upright run (e.g. CVaR, E)
    """
    oMath = OxmlElement('m:oMath')
    for tok in tokens:
        if tok[0] == 'sub':
            if len(tok) == 4:
                oMath.append(_omml_sub(tok[1], tok[2], base_italic=tok[3]))
            else:
                oMath.append(_omml_sub(tok[1], tok[2]))
        elif tok[0] == 'op':
            oMath.append(_omml_run(tok[1], italic=False))
        elif len(tok) == 3:
            oMath.append(_omml_run(tok[1], italic=tok[2]))
        else:
            oMath.append(_omml_run(tok[1], italic=True))
    return oMath


def add_omml_equation(doc, tokens, font_size=10.5):
    """Add a centered display equation as a native Word math object (OMML)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)

    oMathPara = OxmlElement('m:oMathPara')
    oMathPara.append(_build_omml(tokens))
    p._p.append(oMathPara)
    return p

def set_cell_shading(cell, color):
    """Set cell background color."""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)

def add_formatted_text(paragraph, text):
    """Parse <b>, <i>, <sub>, <super> tags and add formatted runs."""
    # Simple regex-based parser for HTML-like tags
    pattern = r'<(b|i|sub|super)>(.*?)</\1>|([^<]+)'
    matches = re.findall(pattern, text)
    
    for bold_text, tag_content, plain_text in matches:
        if bold_text:
            run = paragraph.add_run(bold_text)
            run.bold = True
        elif tag_content:
            # Determine which tag it was
            if '<b>' in text[text.index(tag_content)-3:text.index(tag_content)]:
                run = paragraph.add_run(tag_content)
                run.bold = True
            elif '<i>' in text[text.index(tag_content)-3:text.index(tag_content)]:
                run = paragraph.add_run(tag_content)
                run.italic = True
            else:
                run = paragraph.add_run(tag_content)
        elif plain_text:
            paragraph.add_run(plain_text)

def add_rich_paragraph(doc, text, style='Normal', bold=False, italic=False, 
                       font_size=10.5, font_name='Times New Roman', 
                       alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       space_after=6, space_before=0, first_indent=0):
    """Add a paragraph with basic formatting (no HTML tag parsing)."""
    p = doc.add_paragraph()
    p.style = doc.styles[style] if style in [s.name for s in doc.styles] else doc.styles['Normal']
    p.alignment = alignment
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    if first_indent:
        p.paragraph_format.first_line_indent = Pt(first_indent)
    
    # Strip HTML tags for plain text
    clean_text = re.sub(r'<[^>]+>', '', text)
    run = p.add_run(clean_text)
    run.font.size = Pt(font_size)
    run.font.name = font_name
    run.bold = bold
    run.italic = italic
    return p

def add_heading_styled(doc, text, level=1, font_size=12, color=RGBColor(15, 26, 48)):
    """Add a styled heading."""
    p = doc.add_paragraph()
    if level == 1:
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        font_size = font_size or 12.5
    elif level == 2:
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        font_size = font_size or 11
    else:
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        font_size = font_size or 10.5
    
    run = p.add_run(text)
    run.font.size = Pt(font_size)
    run.font.name = 'Times New Roman'
    run.bold = True
    run.font.color.rgb = color
    return p

def add_body_text(doc, text, font_size=10.5):
    """Add body text paragraph."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
    
    # Strip HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    run = p.add_run(clean_text)
    run.font.size = Pt(font_size)
    run.font.name = 'Times New Roman'
    return p

def add_equation(doc, text, font_size=10.5):
    """Add centered equation text."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    
    clean_text = re.sub(r'<[^>]+>', '', text)
    run = p.add_run(clean_text)
    run.font.size = Pt(font_size)
    run.font.name = 'Times New Roman'
    run.italic = True
    return p

def add_table_note(doc, text, font_size=9):
    """Add italic table note."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    
    clean_text = re.sub(r'<[^>]+>', '', text)
    run = p.add_run(clean_text)
    run.font.size = Pt(font_size)
    run.font.name = 'Times New Roman'
    run.italic = True
    run.font.color.rgb = RGBColor(85, 85, 85)
    return p

def make_styled_table(doc, headers, rows, col_widths=None):
    """Create a professionally styled table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        set_cell_shading(cell, '1A2744')
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.bold = True
                run.font.size = Pt(9.5)
                run.font.name = 'Times New Roman'
    
    # Data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_text in enumerate(row_data):
            cell = table.rows[row_idx + 1].cells[col_idx]
            cell.text = cell_text
            if row_idx % 2 == 1:
                set_cell_shading(cell, 'F8F9FA')
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9.5)
                    run.font.name = 'Times New Roman'
    
    # Set borders
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
    borders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'CCCCCC')
        borders.append(border)
    tblPr.append(borders)
    
    return table

# ===== BUILD DOCUMENT ================================================

doc = Document()

# Set default font
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(10.5)

# Set margins
sections = doc.sections
for section in sections:
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# ===== TITLE PAGE CONTENT ============================================

# Title
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(40)
p.paragraph_format.space_after = Pt(4)
run = p.add_run("A Physics-Based Monte Carlo Framework for Space Debris Cascade Risk and Insurance Pricing")
run.font.size = Pt(15)
run.font.name = 'Times New Roman'
run.bold = True
run.font.color.rgb = RGBColor(15, 26, 48)

# Gold separator line
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(12)
run = p.add_run("─" * 40)
run.font.color.rgb = RGBColor(200, 168, 78)
run.font.size = Pt(10)

# Author
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(3)
run = p.add_run("Lingxi Lu")
run.font.size = Pt(11)
run.font.name = 'Times New Roman'

# Affiliation
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run = p.add_run("Independent Researcher")
run.font.size = Pt(9.5)
run.font.name = 'Times New Roman'
run.italic = True
run.font.color.rgb = RGBColor(85, 85, 85)

# Version info
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(20)
run = p.add_run("October 2026  |  Version 2.0  |  Working Paper")
run.font.size = Pt(9.5)
run.font.name = 'Times New Roman'
run.italic = True
run.font.color.rgb = RGBColor(85, 85, 85)

# Abstract heading
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.space_after = Pt(4)
run = p.add_run("Abstract")
run.font.size = Pt(10.5)
run.font.name = 'Times New Roman'
run.bold = True

# Abstract text
add_body_text(doc, 
    "The commercial space insurance market was worth about $1.2 billion in 2025 (industry estimates vary). It prices satellite risk using launch and in-orbit failure experience. But no actuarial model accounts for cascade risk, where one collision generates debris that triggers more collisions, producing correlated losses across a portfolio. I build a coupled physics-actuarial framework to address this. For the physics piece, I wrote Monte Carlo code that tracks debris cascades in Low Earth Orbit (LEO). Collision rates come straight from orbital mechanics, not a separately tuned cascade-rate parameter. On the pricing side, I used Value at Risk (VaR), Conditional VaR (CVaR), and Extreme Value Theory (EVT) to convert loss distributions into premiums. I set the simulation at 800 km and ran it for 50 years. Debris went from 36,500 to roughly 1.51 million objects. The premiums I get are 16.5 times higher than a 0.5%-of-hull in-orbit failure benchmark, $2,058 million against $125 million per year for 500 satellites; on expected loss alone the gap is 7.4 times. That comparison is a year-50 comparison: at t = 0 the same model's expected loss is $22.3 million, only 0.18 times the benchmark, so the result measures how a static premium falls behind a growing cascade rather than how mispriced today's market is. The $1,933 million gap is a solvency signal for a concentrated 500-satellite portfolio, and it undermines long-term sustainability of outer space activities. I check the model against three real collision events and break down premiums following the Solvency II framework. I also talk about what this means for the UN Space 2030 Agenda and argue that risk-adjusted pricing could serve as an economic instrument for orbital sustainability."
)

# Keywords
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(12)
run = p.add_run("Keywords: ")
run.font.size = Pt(9.5)
run.font.name = 'Times New Roman'
run.italic = True
run.bold = True
run = p.add_run("space debris, Kessler Syndrome, satellite insurance, Monte Carlo simulation, cascade risk, Solvency II, Extreme Value Theory, orbital sustainability, space traffic management, UN Space 2030 Agenda")
run.font.size = Pt(9.5)
run.font.name = 'Times New Roman'
run.italic = True

# Separator
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(12)
run = p.add_run("─" * 80)
run.font.color.rgb = RGBColor(204, 204, 204)
run.font.size = Pt(6)

# ===== 1. INTRODUCTION ===============================================

add_heading_styled(doc, "1. Introduction", level=1)
add_heading_styled(doc, "1.1 The Unpriced Risk to Orbital Sustainability", level=2)

add_body_text(doc, 
    "The space debris environment in Low Earth Orbit (LEO) has changed. It is no longer a background condition. It is an active operating cost. Tracking networks currently count over 36,500 objects larger than 10 cm in Earth orbit. On top of that, there are roughly 1 million objects between 1-10 cm and 130 million smaller fragments, according to the ESA Space Environment Report (2025). The World Economic Forum put a price tag on this: $25.8-$42.3 billion in debris-related costs for LEO assets between 2025 and 2035, assuming nothing changes. That kind of trajectory does not square with the long-term sustainability goals in the UN Space 2030 Agenda or the IADC Space Debris Mitigation Guidelines."
)

add_body_text(doc, 
    "And yet the $1.2 billion space insurance market still prices risk the old way, using historical loss data. Mostly launch and in-orbit failure experience plus single-asset collision probabilities. Nobody is modeling the chance that one debris event sets off a cascade, generating correlated claims across a whole portfolio at once. That gap creates a moral hazard. Operators flying in congested shells pay premiums that have nothing to do with the systemic risk they impose on everyone else in orbit."
)

add_heading_styled(doc, "1.2 Prior Work and Gap", level=2)

add_body_text(doc, 
    "Freeman et al. (2021) came closest. They built an actuarial modifier for On-Orbit Servicing (OOS) satellite insurance, folding debris mitigation into premiums, but only for direct collision risk. Cascade dynamics, the chain-reaction scenario Kessler (1978) laid out, were not part of their model. Liou and Johnson (2008) ran numerical simulations that showed LEO satellite populations are unstable. They did not take the step of linking those results to insurance pricing. To my knowledge, nobody has coupled first-principles collision physics with actuarial risk metrics to produce regulatory-compliant insurance premiums."
)

add_heading_styled(doc, "1.3 Contribution", level=2)

add_body_text(doc, 
    "My framework does seven things. It couples collision physics with actuarial science so debris growth is driven by actual collision rates, with no separately tuned cascade-rate parameter. Collision events are drawn from a Poisson distribution, with event-anchored log-normal fragment yields; the NASA Standard Breakup Model serves only as an order-of-magnitude anchor. DS and DD collision yields are kept separate, which delays but does not remove the finite-time singularity; the baseline mean-field singularity is at t* = 61 years. Portfolio-level correlated risk is handled by a separate Gaussian-copula module for variance and tail analysis; expected loss itself is correlation-invariant. Extreme Value Theory is used as a diagnostic cross-check on the empirical tail, with a peaks-over-threshold exceedance ratio. The yield scale is checked against three documented collision events, not formally calibrated to them. I also discuss the framework's relevance to international space governance and propose risk-adjusted pricing as an economic instrument for orbital sustainability."
)

# ===== 2. METHODOLOGY =================================================

add_heading_styled(doc, "2. Methodology", level=1)
add_heading_styled(doc, "2.1 Physical Layer: Collision-Driven Debris Dynamics", level=2)

add_body_text(doc, 
    "I model a representative LEO shell at altitude h = 800 km with thickness dh = 200 km (700-900 km). The shell volume works out to V = 1.29 x 10^11 km^3. I picked this altitude because it has the most defunct satellites and is where most mega-constellations operate. Drag at 800 km is weak enough that debris can stick around for decades, sometimes centuries."
)

add_heading_styled(doc, "2.1.1 Collision Rate", level=3)

add_body_text(doc, "For collision rates between debris and satellites, I use the Kessler-Flournoy formula:")

add_omml_equation(doc, [
    ('sub', 'R', 'ds'),
    ('op', '='),
    ('sub', 'N', 'd'),
    ('op', '⋅'),
    ('sub', 'N', 's'),
    ('op', '⋅'),
    ('txt', 'σ'),
    ('op', '⋅'),
    ('sub', 'v', 'rel'),
    ('op', '⋅'),
    ('txt', 'T'),
    ('op', '/'),
    ('txt', 'V'),
    ('op', ' '),
    ('txt', ' ', False),
    ('txt', '(1)', False),
])

add_body_text(doc, 
    "Debris-debris collisions drive the cascade. The rate R_dd is proportional to N_d(N_d-1), which means it scales with N_d^2. Double the debris, you quadruple the collision rate. This quadratic feedback is the mathematical root of the cascade. At current population levels (N_d = 36,500, N_s = 8,000), I compute about 7 debris-satellite and 16 debris-debris collisions per year."
)

add_heading_styled(doc, "2.1.2 Fragment Generation", level=3)

add_body_text(doc, "The asymmetric fragment yield between collision types is an event-anchored prior; the NASA Standard Breakup Model is used only as an order-of-magnitude anchor:")

make_styled_table(doc,
    ['Collision Type', 'Distribution', 'Median', 'Physical Rationale'],
    [
        ['Debris-Satellite (DS)', 'LogNormal(5.5, 0.8)', '~245', 'Large satellite breakup'],
        ['Debris-Debris (DD)', 'LogNormal(1.1, 0.5)', '~3', 'Small fragment impact'],
    ]
)

add_table_note(doc, 
    "Without this distinction, the N^2 scaling of DD rates combined with high yields (~245) would produce unphysical runaway growth. The asymmetry reflects the energy differential: a fragment striking an intact satellite releases orders of magnitude more energy than two small fragments colliding."
)

add_heading_styled(doc, "2.1.3 Stochastic Time-Stepping", level=3)

add_body_text(doc, 
    "I model collisions as a Poisson process. I broke time into 0.1-year steps, about 36.5 days each. Within each step, I draw DS and DD collision counts, generate fragments from log-normal distributions, apply orbital decay (lambda = 0.005/year with multiplicative Gaussian noise, standard deviation 10%, clipped below at 0.1), and update the population. There is no separately tuned cascade-rate parameter; the collision terms are fixed by orbital mechanics. That is not the same as \\\"no free parameters\\\": initial debris count, yield parameters, the 0.5% benchmark, satellite value and portfolio size are modelling choices. Each Monte Carlo path uses a distinct random seed for reproducibility."
)

add_heading_styled(doc, "2.2 Economic Layer: From Debris to Insurance Premiums", level=2)

add_body_text(doc, 
    "Getting from debris population to financial loss takes four steps. First, I compute per-satellite annual hit probability p_hit = N_d * sigma * v * T / V. Second, I calculate per-policy expected loss = p_hit * V_sat ($50M average). Third, I aggregate across 500 insured satellites; an inter-policy loss correlation (rho = 0.3, driven by the shared debris environment) widens the tail but does not change the portfolio mean. Fourth, I pull out VaR and CVaR risk metrics from 1,000 Monte Carlo paths."
)

add_heading_styled(doc, "2.2.1 Solvency-II-style Premium Decomposition", level=3)

add_omml_equation(doc, [
    ('txt', 'P'),
    ('op', '='),
    ('txt', 'E', False),
    ('txt', '[L]'),
    ('op', '+'),
    ('sub', 'λ', 'R'),
    ('op', '⋅'),
    ('txt', '('),
    ('sub', 'CVaR', '95', False),
    ('op', '−'),
    ('txt', 'E', False),
    ('txt', '[L]'),
    ('txt', ')'),
    ('op', '+'),
    ('txt', 'r'),
    ('op', '⋅'),
    ('txt', '('),
    ('sub', 'VaR', '99', False),
    ('op', '−'),
    ('txt', 'E', False),
    ('txt', '[L]'),
    ('txt', ')'),
    ('op', '+'),
    ('sub', 'λ', 'E'),
    ('op', '⋅'),
    ('txt', 'E', False),
    ('txt', '[L]'),
    ('txt', ' ', False),
    ('txt', '(2)', False),
])

add_body_text(doc, 
    "where lambda_R = 1.5 (risk loading multiplier), r = 0.04 (discount rate), lambda_E = 0.15 (expense loading). This is a Solvency-II-style decomposition, not the calculation prescribed by Directive 2009/138/EC: the Directive applies a 6% cost of capital to the SCR, whereas the risk loading here is a multiple of the CVaR excess and the capital charge uses a 4% cost of capital. The three loadings are pricing assumptions, not regulatory parameters."
)

add_heading_styled(doc, "2.3 Consistency Check Against Observed Events", level=2)

make_styled_table(doc,
    ['Event', 'Date', 'Fragments (>10cm)', 'Mass'],
    [
        ['Fengyun-1C (ASAT test)', '2007-01-11', '~3,500', '880 kg'],
        ['Iridium 33 x Cosmos 2251', '2009-02-10', '~2,300', '1,510 kg'],
        ['Kosmos 1408 (ASAT test)', '2021-11-15', '~1,500', '2,200 kg'],
    ]
)

add_table_note(doc, 
    "These three events collectively created about 7,300 catalogued fragments. The counts are catalogue totals rather than per-collision yields, so they are used as an order-of-magnitude consistency check, not to fit the operative log-normal parameters. Both ASAT tests (Fengyun-1C, Kosmos 1408) and the accidental collision (Iridium-Cosmos) are represented, ensuring the model captures both intentional and unintentional debris generation mechanisms."
)

add_heading_styled(doc, "2.4 Validation Against Current Observations", level=2)

make_styled_table(doc,
    ['Metric', 'Model Value', 'Observed/Market Data', 'Source'],
    [
        ['Tracked debris (>10cm), 2025', '36,500', '36,500', '[9]'],
        ['Global insurance market, 2025', '-', '$1.2B', '[8]'],
        ['In-orbit failure benchmark', '0.5%', 'Assumption, not observed premium', 'Model assumption'],
        ['Fengyun-1C fragments', '~3,500', '~3,500', '[4]'],
        ['Iridium-Cosmos fragments', '~2,300', '~2,300', '[4]'],
        ['Kosmos 1408 fragments', '~1,500', '~1,500', '[4]'],
        ['Cascade-adjusted premium', '$2,058M/year', 'Not yet priced', 'Model prediction'],
    ]
)

add_table_note(doc,
    "The model's initial conditions align with current observational data from the ESA Space Environment Report 2025 [9]. The event counts match IADC records and NASA fragmentation data [4] as an order-of-magnitude check. The cascade-adjusted premium of $2,058M/year is a conditional estimate of what cascade-aware pricing would be, compared with a $125M/year benchmark that applies a 0.5% of hull value rate to the same 500 satellites. The 0.5% rate is a modelling assumption, used here only as a reference point; it is not an observed market premium. The 16.5x ratio is conditional on the single-shell approximation, the DD cross-section upper bound, and the choice of benchmark."
)

# ===== 3. RESULTS =====================================================

add_heading_styled(doc, "3. Results", level=1)
add_heading_styled(doc, "3.1 Debris Projection", level=2)

make_styled_table(doc,
    ['Parameter', 'Value'],
    [
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
)

add_table_note(doc, 
    "Debris grows 41x over 50 years under business-as-usual conditions. The 95th percentile path reaches 2.24 million objects, representing a 61x increase."
)

add_heading_styled(doc, "3.2 Actuarial Risk Metrics", level=2)

make_styled_table(doc,
    ['Metric', 'Definition', 'Value'],
    [
        ['Expected Loss (EL)', 'Mean worst-year portfolio loss', '$921.4M'],
        ['VaR (95%)', '95th pctile worst-year loss', '$1,365M'],
        ['CVaR (95%) / ES', 'Avg loss beyond VaR(95%)', '$1,565M'],
        ['VaR (99%)', '99th pctile worst-year loss', '$1,721M'],
        ['CVaR (99%) / ES', 'Avg loss beyond VaR(99%)', '$1,854M'],
    ]
)

add_heading_styled(doc, "3.3 Premium Decomposition", level=2)

make_styled_table(doc,
    ['Component', 'Formula', 'Amount'],
    [
        ['Expected Loss (EL)', 'Mean worst-year loss', '$921.4M'],
        ['Risk Loading', '1.5 x (CVaR95 - EL)', '$966.0M'],
        ['Capital Charge', '4% x (VaR99 - EL)', '$32.0M'],
        ['Expense Loading', '15% x EL', '$138.2M'],
        ['TOTAL PREMIUM', '', '$2,058M / year'],
        ['Per-policy premium', 'Total / 500 policies', '$4,115,098 / year'],
        ['Benchmark premium', '0.5% x $50M x 500 (assumption)', '$125.0M / year'],
        ['CASCADE FACTOR', 'Cascade / Benchmark', '16.5x'],
    ]
)

add_table_note(doc,
    "Time alignment: the premium is computed on the worst-year sample, and in 100% of the 1,000 paths the worst year is the final step, so the headline is the fair annual premium at the end of the horizon, not today's. The same model gives expected losses of $22.3M at t = 0 (0.18x the static benchmark) and $111.0M at t = 25 (0.89x). The 16.5x therefore measures how far a static benchmark falls behind a growing cascade by year 50; it is not a claim that current premiums are 16.5x too low today."
)

add_heading_styled(doc, "3.4 Key Findings", level=2)

add_body_text(doc, 
    "1. Debris grows 41x over 50 years (36,500 to 1.51M) in the baseline path. The driver is the N^2 feedback in debris-debris collision rates, which produces accelerating growth: more debris means more collisions, which means more debris. Liou and Johnson (2008) reached a qualitatively similar conclusion about the instability of the present LEO population."
)

add_body_text(doc, 
    "2. The premium gap grows to 16.5x over the horizon. At year 50 the cascade-adjusted premium ($2,058M) is 16.5x a 0.5%-of-hull in-orbit failure benchmark ($125M), a gap of $1,933M per year; on expected loss alone the ratio is 7.4x. The benchmark is all-peril while the model prices debris collisions only, so the ratio is conservative on coverage. The same model gives $22.3M of expected loss at year 0 (0.18x the benchmark), so the gap measures how a static premium falls behind a growing cascade rather than how mispriced today's market is. Because the year-50 gap exceeds the roughly $1.2B annual global premium base, it should be read as a solvency signal for a concentrated 500-satellite book in one shell, not as a market-wide premium forecast."
)

add_body_text(doc, 
    "3. Tail risk is substantial. CVaR(95%) ($1,565M) exceeds expected loss ($921M) by 70%, indicating that extreme cascade scenarios produce losses well above the mean."
)

add_body_text(doc, 
    "4. Risk loading dominates the premium. The CVaR-based risk loading ($966M) exceeds the expected loss ($921M). This reflects the right-skewed loss distribution, a direct consequence of the quadratic feedback mechanism."
)

# ===== 4. DISCUSSION ==================================================

add_heading_styled(doc, "4. Discussion", level=1)
add_heading_styled(doc, "4.1 Systemic Risk to the Insurance Market", level=2)

add_body_text(doc, 
    "The $1,933M annual gap between the benchmark and cascade-adjusted pricing is a solvency signal. When debris density is high, all satellites face elevated risk at the same time, so claims would be correlated across a whole portfolio. A cascade event at benchmark premium levels could exceed insurer reserves on a concentrated book and propagate losses to reinsurers. The historical record gives three calibration points: Fengyun-1C in 2007, Iridium-Cosmos in 2009, and Kosmos 1408 in 2021 - three events spanning 14 years, each creating thousands of catalogued fragments."
)

add_heading_styled(doc, "4.2 Implications for International Space Governance", level=2)

add_body_text(doc, 
    "Right now, the UN Space 2030 Agenda and IADC guidelines set norms for sustainable space operations. But there is no enforcement behind them. This framework proposes an economic instrument to go along with regulatory approaches: risk-adjusted insurance pricing that internalizes the externality of debris generation."
)

add_body_text(doc, 
    "Under cascade-aware pricing, operators who place satellites in less congested shells or invest in end-of-life deorbiting would get lower premiums. This gives operators a market-based incentive for sustainability without requiring direct regulation. Operators who contribute to orbital congestion would face premiums that reflect the systemic risk they impose on all space users."
)

add_heading_styled(doc, "4.3 Policy Recommendations", level=2)

add_body_text(doc, 
    "1. Insurance regulators (e.g., EIOPA, NAIC) should require space insurers to disclose whether cascade risk is incorporated into pricing models."
)

add_body_text(doc, 
    "2. The IADC and UNCOPUOS should commission independent studies on the macroeconomic implications of underpriced cascade risk."
)

add_body_text(doc, 
    "3. Space agencies should explore premium differentiation as a condition for launch licensing -- satellites in congested shells pay higher insurance, which in funds debris mitigation."
)

add_body_text(doc, 
    "4. Reinsurance markets should develop cascade-risk-specific instruments (e.g., catastrophe bonds tied to debris density thresholds) to transfer systemic risk off insurer balance sheets."
)

add_heading_styled(doc, "4.4 Limitations", level=2)

add_body_text(doc, 
    "Several limitations warrant discussion. First, the single-shell approximation (800 km only) does not capture the full 3D orbital environment, and the framework covers only >10 cm catalogue objects; the roughly one million 1-10 cm objects are not modeled. Second, the debris-debris collision rate is an upper bound: both channels share a 10 m2 satellite cross-section, whereas the true DD cross-section for two >10 cm objects is ~0.01 m2, 2-3 orders of magnitude smaller. The 16.5x cascade factor is materially dependent on the DD term. Third, the orbital decay parameter is an effective removal rate lumping atmospheric drag, collisional grinding, and catalogue dropout, not pure drag lifetime. Fourth, the 0.5% benchmark is an in-orbit failure assumption, not an observed market premium: 0.3% gives 27.5x and 1% gives 8.2x. Fifth, the fragment yield is an event-anchored log-normal prior calibrated to observed fragment counts from three historical events, not a physics-based calibration using collision mass and energy."
)

add_heading_styled(doc, "4.5 Future Work", level=2)

add_body_text(doc, 
    "Future research directions include: (1) multi-shell model with cross-altitude migration; (2) NORAD TLE data integration for empirical debris tracking; (3) dynamic constellation deployment modeling; (4) ADR scenario analysis and premium reduction quantification; (5) reinsurance layer pricing (excess-of-loss, stop-loss, catastrophe bonds)."
)

# ===== 5. CONCLUSION ==================================================

add_heading_styled(doc, "5. Conclusion", level=1)

add_body_text(doc, 
    "This framework shows that incorporating physics-based cascade dynamics into insurance pricing produces premiums 16.5x a 0.5%-of-hull in-orbit failure benchmark for a 500-satellite portfolio in one shell. The main methodological point is that the cascade rate is not an adjustable knob: debris growth is driven by collision rates derived from orbital mechanics, with event-anchored fragment yields and an asymmetric treatment of debris-satellite versus debris-debris collisions. The magnitude is conditional on the single-shell approximation, the DD cross-section upper bound, and the choice of benchmark; these caveats are discussed in the limitations."
)

add_body_text(doc, 
    "The $1,933M annual pricing gap is a solvency concern for concentrated books, but it is also an opportunity. Risk-adjusted pricing can work as an economic instrument for orbital sustainability, complementing the regulatory framework of the UN Space 2030 Agenda. By aligning private insurance costs with systemic debris risk, this framework offers a market-based pathway toward long-term sustainability of outer space activities."
)

# ===== REFERENCES =====================================================

add_heading_styled(doc, "References", level=1)

refs = [
    'Kessler, D.J. and Cour-Palais, B.G. (1978). "Collision Frequency of Artificial Satellites: The Creation of a Debris Belt." J. Geophys. Res., 83(A6), 2637-2646.',
    'Kessler, D.J. (1981). "Derivation of the collision probability between orbiting objects." Icarus, 48(1), 39-48.',
    'Liou, J.-C. and Johnson, N.L. (2008). "Instability of the present LEO satellite populations." Advances in Space Research, 41(7), 1046-1053.',
    'Johnson, N.L. et al. (2008). "History of On-Orbit Satellite Fragmentations, 14th Edition." NASA Orbital Debris Program Office.',
    'Freeman, R. et al. (2021). "An actuarial modifier for underwriting OOS satellite insurance." J. Space Operations.',
    'European Commission (2009). "Solvency II Directive." 2009/138/EC.',
    'IADC (2007). "Space Debris Mitigation Guidelines." Inter-Agency Space Debris Coordination Committee.',
    'UNCOPUOS (2019). "Space 2030 Agenda." United Nations Committee on the Peaceful Uses of Outer Space.',
    'World Economic Forum / Centre for Space Futures (2026). "Clear Orbit, Secure Future: A Call to Action on Space Debris."',
    'ESA Space Environment Report (2025). European Space Agency.',
]

for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(20)
    p.paragraph_format.first_line_indent = Pt(-20)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(f"[{i}] {ref}")
    run.font.size = Pt(9)
    run.font.name = 'Times New Roman'

# ===== DATA AVAILABILITY & CONTACT ====================================

# Separator
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(14)
p.paragraph_format.space_after = Pt(8)
run = p.add_run("─" * 80)
run.font.color.rgb = RGBColor(204, 204, 204)
run.font.size = Pt(6)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
run = p.add_run("Data and Code Availability: ")
run.font.size = Pt(9)
run.font.name = 'Times New Roman'
run.bold = True
run = p.add_run("Code is released under the Apache License 2.0; the manuscript text and figures are released under CC BY 4.0. Source code (Python package cascade_risk/), configuration files, and simulation output data are available from the author upon request.")
run.font.size = Pt(9)
run.font.name = 'Times New Roman'

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
run = p.add_run("Correspondence: ling.xi.lu@gmail.com")
run.font.size = Pt(9.5)
run.font.name = 'Times New Roman'
run.italic = True

# ===== SAVE DOCUMENT ==================================================

doc.save('framework_paper_new.docx')
print("Word document generated: framework_paper_new.docx")
