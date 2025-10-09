# market_robot/profitability.py
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class ProfitResult:
    scenario: str
    TAM: float
    SOM_share: float
    revenue: float
    agent_split_pct: float
    agent_commissions: float
    other_variable_pct: float
    other_variable_costs: float
    fixed_costs: float
    gross_profit: float
    net_profit: float
    net_margin_pct: float
    contribution_margin_pct: float
    breakeven_revenue: float
    implied_breakeven_TAM: float
    min_som_to_breakeven: float | float

def compute_profit(
    tam: float,
    som_share: float,
    agent_split: float,
    variable_cost_pct: float = 0.0,
    fixed_costs: float = 0.0,
    name: str = "scenario",
) -> ProfitResult:
    revenue = tam * som_share
    agent_commissions = revenue * agent_split
    other_variable = revenue * variable_cost_pct
    gross_profit = revenue - agent_commissions - other_variable
    net_profit = gross_profit - fixed_costs
    net_margin_pct = (net_profit / revenue) if revenue > 0 else 0.0

    cm = 1.0 - agent_split - variable_cost_pct
    if cm <= 0:
        breakeven_revenue = float("inf")
        implied_breakeven_TAM = float("inf")
        min_som_to_breakeven = float("inf")
        cm_out = 0.0
    else:
        breakeven_revenue = fixed_costs / cm
        implied_breakeven_TAM = (breakeven_revenue / som_share) if som_share > 0 else float("inf")
        min_som_to_breakeven = (fixed_costs / (cm * tam)) if tam > 0 else float("inf")
        cm_out = cm

    return ProfitResult(
        scenario=name, TAM=tam, SOM_share=som_share, revenue=revenue,
        agent_split_pct=agent_split, agent_commissions=agent_commissions,
        other_variable_pct=variable_cost_pct, other_variable_costs=other_variable,
        fixed_costs=fixed_costs, gross_profit=gross_profit, net_profit=net_profit,
        net_margin_pct=net_margin_pct, contribution_margin_pct=cm_out,
        breakeven_revenue=breakeven_revenue, implied_breakeven_TAM=implied_breakeven_TAM,
        min_som_to_breakeven=min_som_to_breakeven,
    )
