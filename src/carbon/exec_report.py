"""Generate the 2-page executive summary PDF (reports/executive_summary.pdf).

All numbers are computed live from the model, so re-running after any data/factor change keeps
the report consistent with the code.  Run:  python src/carbon/exec_report.py
(run report_figures.py first so the embedded charts are current)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from carbon.emissions import ROOT, calculate_emissions, load_activity, load_factors, summarise  # noqa: E402
from carbon.scenarios import (apply_levers, baseline_activity, load_cost_assumptions, load_levers,  # noqa: E402
                              pathway_range, sensitivity_analysis)

FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "executive_summary.pdf"
TEAL, NAVY, CORAL, GREY = colors.HexColor("#2a9d8f"), colors.HexColor("#264653"), colors.HexColor("#e76f51"), colors.HexColor("#6b7280")


def compute() -> dict:
    act, f = load_activity(), load_factors()
    em = calculate_emissions(act, f)
    a, levers = load_cost_assumptions(), load_levers()
    base = baseline_activity(act, 2025)
    res, _ = apply_levers(base, levers, f, a, 2025)
    path = pathway_range(em, base, levers, f, a)
    sens = sensitivity_analysis(act, em, levers, f, a)
    yearly = summarise(em, ["year"]).set_index("year")["tco2e"]
    scope = summarise(em, ["scope"]).set_index("scope")["tco2e"]
    cat = summarise(em, ["category"]).sort_values("tco2e", ascending=False)
    p30 = path[path.year == 2030].iloc[0]
    phys = res[res.accounting == "location"]
    return dict(em=em, res=res, path=path, sens=sens, yearly=yearly, scope=scope, cat=cat, p30=p30, phys=phys,
                total=em.tco2e.sum(), y25=yearly.loc[2025], chg=yearly.loc[2025] / yearly.loc[2023] - 1,
                site=summarise(em, ["site"]).set_index("site")["tco2e"])


def build(out: Path = OUT) -> Path:
    d = compute()
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Title"], fontSize=17, leading=21, textColor=NAVY, alignment=TA_LEFT, spaceAfter=2)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5, leading=14, textColor=NAVY, spaceBefore=6, spaceAfter=3)
    B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=8.8, leading=11.6, spaceAfter=3)
    SM = ParagraphStyle("SM", parent=B, fontSize=7.2, leading=9, textColor=GREY)
    BUL = ParagraphStyle("BUL", parent=B, leftIndent=9, bulletIndent=0)

    res, p30, phys = d["res"], d["p30"], d["phys"]
    gap = p30.with_levers_market - p30.sbti_target
    gap_hi = p30.with_levers_market_upper - p30.sbti_target
    gap_loc = p30.with_levers_location - p30.sbti_target
    l2 = res.set_index("lever_id").loc["L2"]
    neg = res[res.cost_per_tco2e_usd < 0]
    sens = d["sens"].set_index("parameter")
    min_saving = d["sens"][["net_saving_low", "net_saving_high"]].min().min()
    s = d["scope"]
    top = d["cat"].iloc[0]

    story = [
        Paragraph("EcoNaija Manufacturing Ltd: Carbon Footprint &amp; Decarbonisation Strategy", H1),
        Paragraph(f"Executive summary · {date.today():%d %B %Y} · Prepared by Daniel Oyewale, Petgrave.io", SM),
        Paragraph("<b>Illustrative case study.</b> Activity data and company profile are synthetic; emission factors "
                  "(DESNZ 2026, verified) and 2026 Nigerian energy prices are real. Not a verified GHG inventory.", SM),
        Spacer(1, 4),
        Paragraph("Headline", H2),
    ]
    kpis = [
        ["2023-25 footprint", "2025 emissions", "Change vs 2023", "Modelled abatement", "Net saving", "2030 SBTi gap*"],
        [f"{d['total']:,.0f} t", f"{d['y25']:,.0f} t", f"{d['chg']:+.1%}", f"{phys.abatement_tco2e.sum():,.0f} t/yr",
         f"${-res.annualised_cost_usd.sum()/1000:,.0f}k/yr", f"{gap:+,.0f} t"],
    ]
    t = Table(kpis, colWidths=[30 * mm] * 6)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica", 7.2), ("TEXTCOLOR", (0, 0), (-1, 0), GREY),
        ("FONT", (0, 1), (-1, 1), "Helvetica-Bold", 12), ("TEXTCOLOR", (0, 1), (-1, 1), NAVY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
    ]))
    story += [t, Paragraph("tCO2e. *Market-based, central case, vs SBTi-aligned target (Scope 1+2 −4.2%/yr, Scope 3 −2.5%/yr from 2023); negative = on track.", SM)]

    story += [Paragraph("What the footprint shows", H2)]
    for txt in [
        f"<b>Scope 3 dominates ({s[3]/d['total']:.0%}).</b> {top.category} is the largest single source "
        f"({top.tco2e/d['total']:.0%}), so supplier data quality is the biggest driver of accuracy and of future reductions.",
        f"<b>Energy is the controllable core.</b> Grid electricity (Scope 2, {s[2]/d['total']:.0%}) and diesel generation "
        f"(Scope 1) concentrate at Port Harcourt Plant, which is {d['site']['Port Harcourt Plant']/d['total']:.0%} of the total.",
        f"<b>Emissions fell {abs(d['chg']):.1%} from 2023 to 2025</b>, slightly ahead of a straight-line path, but without "
        "new measures 2%/yr business growth would push them back up.",
    ]:
        story.append(Paragraph(txt, BUL, bulletText="•"))
    story.append(Table([[Image(str(FIG / "02_emission_hotspots.png"), width=88 * mm, height=55 * mm),
                         Image(str(FIG / "06_decarbonisation_pathway.png"), width=92 * mm, height=51 * mm)]],
                       colWidths=[90 * mm, 94 * mm]))

    story += [Paragraph("Recommended investment plan", H2)]
    plan = [["Priority", "Lever", "tCO2e/yr", "Capex", "USD/tCO2e", "Payback"]]
    for r in res.sort_values("cost_per_tco2e_usd").itertuples():
        pb = f"{r.simple_payback_years:.1f} yr" if r.simple_payback_years == r.simple_payback_years else "–"
        tier = "Fund now" if r.cost_per_tco2e_usd < 0 else ("Next" if r.cost_per_tco2e_usd <= 100 else "Strategic")
        plan.append([tier, Paragraph(r.lever, ParagraphStyle("c", parent=B, fontSize=7.4, leading=8.6)),
                     f"{r.abatement_tco2e:,.0f}", f"${r.capex_usd/1000:,.0f}k", f"{r.cost_per_tco2e_usd:,.0f}", pb])
    pt = Table(plan, colWidths=[18 * mm, 86 * mm, 17 * mm, 17 * mm, 20 * mm, 17 * mm], repeatRows=1)
    style = [("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7.6), ("FONT", (0, 1), (-1, -1), "Helvetica", 7.4),
             ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
             ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    for i, row in enumerate(plan[1:], start=1):
        c = TEAL if row[0] == "Fund now" else (colors.HexColor("#b08900") if row[0] == "Next" else CORAL)
        style.append(("TEXTCOLOR", (0, i), (0, i), c))
        style.append(("FONT", (0, i), (0, i), "Helvetica-Bold", 7.4))
    pt.setStyle(TableStyle(style))
    story += [pt, PageBreak()]

    story += [Paragraph("Decision points for the board", H2)]
    for txt in [
        f"<b>1. Approve the {len(neg)} cost-negative levers now.</b> They deliver {neg.abatement_tco2e.sum()/res.abatement_tco2e.sum():.0%} "
        f"of modelled abatement and pay for themselves. The flagship is the <b>Port Harcourt solar-battery hybrid</b>: "
        f"{l2.abatement_tco2e:,.0f} tCO2e/yr, ~${l2.capex_usd/1000:,.0f}k capex, ~{l2.simple_payback_years:.0f}-year payback, plus "
        "protection from diesel price shocks.",
        f"<b>2. Contract renewable electricity for the plant (PPA / I-RECs).</b> Without it, 2030 is missed on a "
        f"location basis ({gap_loc:+,.0f} t). With it, the central case is on track ({gap:+,.0f} t). Certificates must pass the GHG "
        "Protocol Scope 2 Quality Criteria (same-year vintage, Nigerian market, retired in a registry).",
        f"<b>3. Plan a second wave by ~2029.</b> If levers underperform, 2030 slips to {gap_hi:+,.0f} t, and growth erodes "
        "gains toward 2035. Candidates: deeper supplier engagement, fleet conversion (CNG/EV), expanded on-site solar.",
        "<b>4. Invest in data before targets are published.</b> Collect supplier-specific emissions data for the top "
        "spend categories and meter diesel use by generator. These are the largest sources of uncertainty.",
    ]:
        story.append(Paragraph(txt, B))
    story.append(Table([[Image(str(FIG / "05_macc_curve.png"), width=104 * mm, height=55 * mm),
                         Image(str(FIG / "07_sensitivity_tornado.png"), width=80 * mm, height=37 * mm)]],
                       colWidths=[106 * mm, 80 * mm], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(Paragraph(
        f"<b>Robustness:</b> the portfolio stays cash-positive in every sensitivity case tested (minimum "
        f"~${min_saving/1000:,.0f}k/yr). Lever effectiveness and the NGN/USD exchange rate move the business case most.",
        B))

    story += [Paragraph("Method, sources &amp; limitations", H2)]
    for txt in [
        "GHG Protocol Corporate &amp; Scope 3 Standards; operational control; 2023 base year; AR5 GWP100.",
        "Scope 1 &amp; travel/waste factors: <b>DESNZ 2026</b>, verified cell-by-cell against the official workbook. "
        "100% mineral fuel factors (no biofuel blend in Nigerian AGO/PMS).",
        "Nigeria grid: <b>Scope 2 combustion-only factor derived</b> from the NERC 2025 generation mix (67% gas), DESNZ "
        "gas combustion factor and a 33% fleet efficiency (range 28-38%). Upstream fuel supply and T&amp;D losses are reported "
        "separately in Scope 3 Category 3.",
        "Market-based Scope 2 only counts contractual instruments that pass the GHG Protocol Scope 2 Quality Criteria; Nigeria "
        "has no residual mix, so the grid average is the fallback.",
        "Scenario costs use Oct 2026 Nigerian prices (diesel NGN 1,900/L, Band A NGN 209.5/kWh, NGN 1,350/USD, 12% discount "
        "rate). Lever capex/opex are documented assumptions, phased in over 1-3 years with low/high effectiveness ranges.",
        "Limitations: synthetic activity data; spend-based Scope 3 is uncertain; UK-based proxies for landfill and car "
        "factors likely understate Nigerian conditions; no grid decarbonisation assumed.",
    ]:
        story.append(Paragraph(txt, ParagraphStyle("li", parent=SM, fontSize=7.6, leading=9.6), bulletText="•"))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Full model, code and data: github.com/Engr-Daniel/carbon-footprint-esg-dashboard", SM))

    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=13 * mm, rightMargin=13 * mm, topMargin=11 * mm,
                            bottomMargin=10 * mm, title="EcoNaija Carbon Footprint & Decarbonisation Strategy",
                            author="Daniel Oyewale (Petgrave.io)")
    doc.build(story)
    return out


if __name__ == "__main__":
    print("saved", build().relative_to(ROOT))
