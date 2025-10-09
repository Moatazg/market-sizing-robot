from __future__ import annotations
from typing import Dict, Any

def derive_arpu_for_segment(config: Dict[str, Any], seg) -> float:
    pb = config.get("pricebook") or {}
    tiers = pb.get("tiers") or []
    key = seg.pricebook_key or (tiers[0]["key"] if tiers else None)
    if key is None:
        return 0.0
    t = next((t for t in tiers if t.get("key")==key), None)
    if t is None:
        return 0.0

    base = float(t.get("base_price", 0.0))
    model = t.get("pricing_model","flat")
    unit_scale = float(t.get("unit_scale",1.0))
    min_price = float(t.get("min_price",0.0))

    if model == "per_unit":
        list_price = max(min_price, base * unit_scale)
    else:
        list_price = max(min_price, base)

    disc = seg.discount if (seg.discount is not None) else float(pb.get("default_discount", 0.0))
    disc = max(0.0, min(1.0, disc))
    attach = seg.attach_rate if (seg.attach_rate is not None) else float(pb.get("default_attach_rate", 1.0))
    attach = max(0.0, min(1.0, attach))

    return list_price * (1.0 - disc) * attach
