from __future__ import annotations
import json, csv
from pathlib import Path
from .profitability import ProfitResult

def save_json(path: str, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def save_audit_csv(path: str, rows: list):
    if not rows:
        Path(path).write_text("", encoding="utf-8"); return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        from csv import DictWriter
        w = DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for r in rows: w.writerow(r)

def save_markdown(path: str, res: dict):
    c = res.get("currency","USD")
    def fmt(x): return f"{x:,.2f}"
    lines = [f"# Market Sizing Report — {res.get('project')} ({res.get('year')})", "",
             f"**Scenario:** {res.get('scenario')}  \n**Currency:** {c}", "",
             "## Headline Numbers",
             f"- **TAM:** {fmt(res['TAM'])} {c}",
             f"- **SAM:** {fmt(res['SAM'])} {c}",
             f"- **SOM (units):** {fmt(res['SOM_units'])}",
             f"- **SOM (value):** {fmt(res['SOM'])} {c}", "",
             "## Segment Breakdown",
             "| Segment | Eligible | Coverage | Penetration | ARPU | TAM_i | SAM_i | SOM_units_i |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for d in res["details"]:
        lines.append(f"| {d['segment']} | {fmt(d['eligible_units'])} | {d['coverage']:.2f} | {d['penetration_adj']:.2f} | {fmt(d['arpu'])} | {fmt(d['TAM_i'])} | {fmt(d['SAM_i'])} | {fmt(d['SOM_units_i'])} |")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    
def render_profitability_section(res: ProfitResult) -> str:
    cm = res.contribution_margin_pct
    cm_label = ("infeasible" if cm <= 0 else
                "very thin" if cm < 0.05 else
                "thin" if cm < 0.15 else "healthy")

    lines = [
        "## Feasibility & Profitability",
        "",
        f"**Scenario:** `{res.scenario}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Revenue | {res.revenue:,.2f} |",
        f"| Net Profit | {res.net_profit:,.2f} |",
        f"| Net Margin | {res.net_margin_pct*100:.1f}% |",
        f"| Contribution Margin | {cm*100:.1f}% ({cm_label}) |",
        f"| Break-even Revenue | {'∞' if res.breakeven_revenue == float('inf') else f'{res.breakeven_revenue:,.2f}'} |",
        f"| Implied Break-even TAM | {'∞' if res.implied_breakeven_TAM == float('inf') else f'{res.implied_breakeven_TAM:,.2f}'} |",
        f"| Min SOM to Break-even | {'∞' if res.min_som_to_breakeven == float('inf') else f'{res.min_som_to_breakeven*100:.2f}%'} |",
        "",
        "### Interpretation",
        "- If contribution margin ≤ 0, the model cannot break even without changing splits or variable costs.",
        "- If contribution margin is 5–15%, margins are fragile; tighten CAC/listing spend or renegotiate splits.",
        "- ≥ 15% is generally healthy for scaling fixed costs.",
        ""
    ]
    return "\n".join(lines)
