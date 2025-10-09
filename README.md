# Market Robot – Feasibility & Profitability Toolkit

**Market Robot** is a command-line and REPL-based toolkit for estimating market size and testing the financial feasibility of new ventures.  
It calculates **TAM**, **SAM**, and **SOM**, then projects **brokerage profitability**, **break-even thresholds**, and generates **consulting-style reports** in Markdown or CSV.

---

##  Key Features

### Market Modeling
- Computes **TAM (Total Addressable Market)**, **SAM (Serviceable Available Market)**, and **SOM (Serviceable Obtainable Market)** from configurable segments.
- Adjustable coverage, penetration, and ARPU multipliers for each scenario.
- Supports constraints such as supply caps and year-based pricebook adjustments.

### Profitability Modeling
- Computes brokerage-level profitability and feasibility metrics:
  - **Net Profit**, **Net Margin**, **Contribution Margin**, **Break-even Revenue**, **Implied Break-even TAM**, and **Minimum SOM to Break-even**.
- Supports scenario-based comparisons via CSV or direct computation from the last run.
- Includes built-in range validation and warnings for unrealistic splits or margins.

### Reporting
- Generates professional Markdown reports summarizing profitability and scenario feasibility.
- Exports results to **CSV**, **JSON**, or **Markdown** for presentation.
- Can act as an automated reporting engine for financial feasibility studies.

---

## Installation

Install dependencies:

```bash
cd market-robot
pip install -e .
```

Then start the REPL:

```bash
python -m market_robot
```

---

## Basic Workflow

```bash
> load_config examples/config.yaml
> load_segments examples/segments.csv
> compute base
> save_report report.json report.md audit.csv
```

This computes TAM/SAM/SOM using your config and segments and saves the results.

---

## Profitability & Feasibility Commands

Once you’ve produced a market computation, you can estimate profitability either by **CSV scenarios** or directly from your last run.

### Profit from CSV

```bash
> profit from_csv scenarios.csv --tam 10000000000 --out results.csv
```

#### Input CSV schema
| Column | Description |
|---------|--------------|
| `scenario` | Scenario name |
| `som_share` | SOM as a share of TAM (0–1) |
| `agent_split_pct` | Fraction of revenue paid to agents (0–1) |
| `other_variable_pct` | Other variable costs as a fraction of revenue (0–1) |
| `fixed_costs` | Total fixed costs |
| `tam` | Optional (override or use `--tam`) |

#### Output CSV fields
| Field | Description |
|--------|-------------|
| `revenue` | SOM × TAM |
| `net_profit` | Gross profit minus fixed costs |
| `net_margin_pct` | Net profit / revenue |
| `contribution_margin_pct` | 1 − agent_split − variable_cost |
| `breakeven_revenue` | Fixed / CM |
| `implied_breakeven_TAM` | Break-even revenue / SOM_share |
| `min_som_to_breakeven` | Minimum SOM share needed to cover costs |

---

### Profit from Last Result

```bash
> compute base
> profit_last --agent-split 0.70 --other-var 0.05 --fixed 8000000 --out last_profit.csv
```

This uses the `TAM` and `SOM` from your last computed scenario and automatically derives `som_share = SOM / TAM`.

Output is written to `last_profit.csv` and printed to console:

```
Profitability for 'base':
  Revenue: 100,000,000.00  Net Profit: 17,000,000.00  Net Margin: 17.0%
  CM: 22.0%  Breakeven Revenue: 36,363,636.36
```

---

### Generate a Markdown Report

```bash
> report feasibility results.csv --out feasibility_report.md
```

This creates a consulting-style **Feasibility Report** summarizing all profitability scenarios.

Example output:

```markdown
# Brokerage Feasibility Report

## Feasibility & Profitability

**Scenario:** base

| Metric | Value |
|---|---:|
| Revenue | 100,000,000.00 |
| Net Profit | 17,000,000.00 |
| Net Margin | 17.0% |
| Contribution Margin | 22.0% (healthy) |
| Break-even Revenue | 36,363,636.36 |
| Implied Break-even TAM | 3,636,363,636.36 |
| Min SOM to Break-even | 0.36% |

### Interpretation
- Healthy margin with modest fixed-cost coverage.
- Model remains feasible at current splits (≤70%) and variable cost (≤5%).
```

---

## Input Ranges and Break-Even Logic

### Valid Ranges

| Parameter | Allowed Range | Description |
|------------|----------------|-------------|
| `som_share` | [0, 1] | Share of TAM captured |
| `agent_split_pct` | [0, 1] | Fraction of revenue paid to agents |
| `other_variable_pct` | [0, 1] | Fraction of revenue lost to variable costs |
| `fixed_costs` | ≥ 0 | Total overhead |
| `tam` | ≥ 0 | Market commission pool |

#### Soft warnings
- `agent_split_pct > 0.85` → unusually high payout.  
- `other_variable_pct > 0.15` → high variable costs.  
- `som_share > 0.20` → aggressive share assumption.

---

### Break-Even Formulas

\[
	ext{Contribution Margin (CM)} = 1 - 	ext{agent_split_pct} - 	ext{other_variable_pct}
\]

- If CM > 0 → feasible  
- If CM = 0 → break-even impossible (no margin)  
- If CM < 0 → negative margin, scaling worsens losses

\[
	ext{Break-even Revenue} = rac{	ext{Fixed Costs}}{	ext{CM}}
\]

\[
	ext{Break-even TAM} = rac{	ext{Break-even Revenue}}{	ext{SOM Share}}
\]

\[
	ext{Min SOM Share to Break-even} = rac{	ext{Fixed Costs}}{	ext{CM} 	imes 	ext{TAM}}
\]

---

## Example Folder Layout

```
market_robot/
├── __init__.py
├── engine.py
├── loaders.py
├── pricing.py
├── profitability.py
├── reporting.py
├── repl.py
examples/
├── config.yaml
├── segments.csv
└── scenarios.csv
```

---

## Quick Start Example

```bash
> load_config examples/config.yaml
> load_segments examples/segments.csv
> compute base
> profit from_csv examples/scenarios.csv --tam 10000000000 --out results.csv
> report feasibility results.csv --out feasibility_report.md
```

---

