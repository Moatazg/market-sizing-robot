from __future__ import annotations
import cmd, yaml, pprint
from .engine import Engine, Segment
from .loaders import load_segments_csv
from .reporting import save_json, save_markdown, save_audit_csv
import csv, argparse, shlex
from .profitability import compute_profit

class REPL(cmd.Cmd):
    intro = "market_robot REPL — type 'help' for commands. Ctrl-D or 'quit' to exit."
    prompt = "> "
    def __init__(self):
        super().__init__(); self.engine = Engine()

    def do_load_config(self, arg):
        path = arg.strip()
        if not path: print("Usage: load_config <path>"); return
        with open(path, "r", encoding="utf-8") as f:
            self.engine.config = yaml.safe_load(f) or {}
        print(f"Loaded config from {path}.")

    def do_show_config(self, arg):
        pprint.pprint(self.engine.config)

    def do_set(self, arg):
        parts = arg.strip().split(" ", 1)
        if len(parts)!=2: print("Usage: set constraints.supply_cap 150"); return
        keypath, valraw = parts
        try: val = yaml.safe_load(valraw)
        except Exception: val = valraw
        d = self.engine.config; keys = keypath.split(".")
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict): d[k] = {}
            d = d[k]
        d[keys[-1]] = val; print(f"Set {keypath} = {val}")

    def do_load_segments(self, arg):
        path = arg.strip()
        if not path: print("Usage: load_segments <path>"); return
        rows = load_segments_csv(path)
        self.engine.segments = [Segment.from_row(r) for r in rows]
        print(f"Loaded {len(self.engine.segments)} segments.")

    def do_compute(self, arg):
        scen = arg.strip() or "base"
        if not self.engine.segments or not self.engine.config: print("Load config and segments first."); return
        res = self.engine.compute(scen); self._print_result(res)

    def do_save_report(self, arg):
        parts = arg.strip().split()
        if not parts: print("Usage: save_report report.json [report.md] [audit.csv]"); return
        if not self.engine.last_result: print("Run 'compute' first."); return
        save_json(parts[0], self.engine.last_result)
        if len(parts)>1: save_markdown(parts[1], self.engine.last_result)
        if len(parts)>2: save_audit_csv(parts[2], self.engine.audit_rows)
        print("Saved.")

    def do_quit(self, arg): print("Bye."); return True
    def do_EOF(self, arg): print(""); return self.do_quit(arg)

    def do_profit(self, arg):
        """
        profit from_csv <path> [--tam X] [--out results.csv]
        """
        argv = shlex.split(arg)
        if not argv or argv[0] != "from_csv":
            print(self.do_profit.__doc__)
            return
        parser = argparse.ArgumentParser(prog="profit from_csv", add_help=False)
        parser.add_argument("from_csv")
        parser.add_argument("--tam", type=float, default=None)
        parser.add_argument("--out", type=str, default="results.csv")
        ns, _ = parser.parse_known_args(argv[1:])

        rows_in = list(csv.DictReader(open(ns.from_csv, "r", encoding="utf-8")))
        out_rows = []
        for r in rows_in:
            # expected columns: scenario, som_share, agent_split_pct, other_variable_pct, fixed_costs, [tam]
            tam = ns.tam if ns.tam is not None else float(r.get("tam", "nan"))
            if tam != tam:  # NaN check
                raise ValueError("Provide --tam or include 'tam' column in CSV.")
            pr = compute_profit(
                tam=tam,
                som_share=float(r["som_share"]),
                agent_split=float(r["agent_split_pct"]),
                variable_cost_pct=float(r["other_variable_pct"]),
                fixed_costs=float(r["fixed_costs"]),
                name=r.get("scenario","scenario"),
            )
            out_rows.append({k: getattr(pr, k) for k in pr.__dataclass_fields__.keys()})

        with open(ns.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader(); w.writerows(out_rows)
        print(f"Saved → {ns.out}")

    def do_report(self, arg):
        """
        report feasibility <results.csv> [--out report.md]
        """
        argv = shlex.split(arg)
        if not argv or argv[0] != "feasibility":
            print(self.do_report.__doc__)
            return
        parser = argparse.ArgumentParser(prog="report feasibility", add_help=False)
        parser.add_argument("results_csv")
        parser.add_argument("--out", default="feasibility_report.md")
        ns, _ = parser.parse_known_args(argv[1:])

        rows = list(csv.DictReader(open(ns.results_csv, "r", encoding="utf-8")))
        from .reporting import render_profitability_section
        sections = ["# Brokerage Feasibility Report", ""]
        for r in rows:
            # build a ProfitResult-like object quickly:
            from .profitability import ProfitResult
            pr = ProfitResult(**{k: (float(r[k]) if k not in ("scenario",) else r[k]) for k in r.keys()})
            sections.append(render_profitability_section(pr))
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))
        print(f"Saved → {ns.out}")

    def _print_result(self, res):
        c = res.get("currency","USD"); fmt = lambda x: f"{x:,.2f}"
        print(f"\nProject: {res.get('project')}  Year: {res.get('year')}  Scenario: {res.get('scenario')}")
        print(f"TAM: {fmt(res['TAM'])} {c}"); print(f"SAM: {fmt(res['SAM'])} {c}")
        print(f"SOM_units: {fmt(res['SOM_units'])}"); print(f"SOM: {fmt(res['SOM'])} {c}")
        print("\nBreakdown:")
        for d in res["details"]:
            print(f"  - {d['segment']}: TAM_i={fmt(d['TAM_i'])} {c}, SAM_i={fmt(d['SAM_i'])} {c}, SOM_units_i={fmt(d['SOM_units_i'])} (ARPU={fmt(d['arpu'])})")

def main(): REPL().cmdloop()