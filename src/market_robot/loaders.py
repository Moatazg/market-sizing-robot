from __future__ import annotations
import csv
from typing import Dict, Any, List
import pandas as pd

def load_segments_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_inflation_table(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def align_value_to_year(config: Dict[str, Any], value: float, from_year: int, to_year: int) -> float:
    infl = config.get("inflation") or {}
    cpi_path = infl.get("cpi_path")
    if not cpi_path or from_year == to_year:
        return value
    df = load_inflation_table(cpi_path)
    s_from = df[df["year"]==int(from_year)]
    s_to = df[df["year"]==int(to_year)]
    if s_from.empty or s_to.empty:
        return value
    c_from = float(s_from.iloc[0]["cpi_index"])
    c_to = float(s_to.iloc[0]["cpi_index"])
    return value * (c_to / c_from) if c_from>0 else value
