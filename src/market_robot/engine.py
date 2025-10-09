from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .pricing import derive_arpu_for_segment
from .loaders import align_value_to_year
from .profitability import compute_profit, ProfitResult

@dataclass
class Segment:
    name: str
    eligible_units: float
    coverage: float
    penetration: float
    arpu: Optional[float] = None
    currency: Optional[str] = None
    fx_to_config: Optional[float] = None
    pricebook_key: Optional[str] = None
    discount: Optional[float] = None
    attach_rate: Optional[float] = None

    @staticmethod
    def from_row(row: dict) -> "Segment":
        def fget(k, default=None, cast=float):
            v = row.get(k, None)
            if v is None or v == "":
                return default
            return cast(v)
        def sget(k, default=None):
            v = row.get(k, None)
            return v if v not in (None, "") else default
        return Segment(
            name=row.get("name","segment"),
            eligible_units=fget("eligible_units",0.0,float),
            coverage=fget("coverage",1.0,float),
            penetration=fget("penetration",0.0,float),
            arpu=fget("arpu",None,float),
            currency=sget("currency"),
            fx_to_config=fget("fx_to_config",None,float),
            pricebook_key=sget("pricebook_key"),
            discount=fget("discount",None,float),
            attach_rate=fget("attach_rate",None,float),
        )

class Engine:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.segments: List[Segment] = []
        self.audit_rows: List[Dict[str, Any]] = []
        self.last_result: Dict[str, Any] = {}

    def _resolve_arpu(self, seg: Segment, scenario: Dict[str, float]) -> float:
        if seg.arpu is not None:
            arpu = seg.arpu
        else:
            arpu = derive_arpu_for_segment(self.config, seg)
        arpu *= scenario.get("arpu_multiplier", 1.0)
        if seg.fx_to_config:
            arpu *= seg.fx_to_config
        return arpu

    def _penetration_adj(self, seg: Segment, scenario: Dict[str,float]) -> float:
        p = seg.penetration * scenario.get("penetration_multiplier", 1.0)
        return max(0.0, min(1.0, p))

    def compute(self, scenario_name: str = "base") -> Dict[str, Any]:
        scen = (self.config.get("scenarios") or {}).get(scenario_name, {"penetration_multiplier":1.0, "arpu_multiplier":1.0})
        supply_cap = (self.config.get("constraints") or {}).get("supply_cap", None)
        target_year = self.config.get("year", None)
        pb_year = self.config.get("pricebook",{}).get("year", target_year)

        tam = 0.0; sam = 0.0; details = []
        for seg in self.segments:
            arpu = self._resolve_arpu(seg, scen)
            if target_year is not None:
                arpu = align_value_to_year(self.config, arpu, from_year=pb_year, to_year=target_year)
            pen = self._penetration_adj(seg, scen)
            tam_i = seg.eligible_units * arpu
            sam_i = seg.eligible_units * seg.coverage * arpu
            som_units_i = seg.eligible_units * seg.coverage * pen
            tam += tam_i; sam += sam_i
            details.append({"segment":seg.name,"eligible_units":seg.eligible_units,"coverage":seg.coverage,
                            "penetration_adj":pen,"arpu":arpu,"TAM_i":tam_i,"SAM_i":sam_i,"SOM_units_i":som_units_i})

        total_uncapped = sum(d["SOM_units_i"] for d in details)
        if supply_cap is not None and total_uncapped>0:
            scale = min(total_uncapped, float(supply_cap))/total_uncapped
        else:
            scale = 1.0
        som_units = total_uncapped * scale
        som = sum((d["SOM_units_i"]*scale)*d["arpu"] for d in details)

        res = {"project": self.config.get("project","(unnamed)"),
               "currency": self.config.get("currency","USD"),
               "year": self.config.get("year", None),
               "scenario": scenario_name,
               "TAM": tam, "SAM": sam, "SOM_units": som_units, "SOM": som,
               "details": details}
        self.last_result = res
        self.audit_rows = [{"scenario":scenario_name, **d} for d in details]
        return res
    def compute_profitability(self, *, tam: float, som_share: float,
                              agent_split_pct: float, other_variable_pct: float,
                              fixed_costs: float, scenario_name: str = "scenario") -> ProfitResult:
        # light validation (reuse your existing config validation if you have it)
        for k, v in [("som_share", som_share), ("agent_split_pct", agent_split_pct), ("other_variable_pct", other_variable_pct)]:
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"{k} must be in [0,1], got {v}")
        if tam < 0 or fixed_costs < 0:
            raise ValueError("tam and fixed_costs must be ≥ 0")

        return compute_profit(
            tam=tam, som_share=som_share, agent_split=agent_split_pct,
            variable_cost_pct=other_variable_pct, fixed_costs=fixed_costs,
            name=scenario_name
        )
