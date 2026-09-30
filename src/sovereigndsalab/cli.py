"""sovereign-dsa-lab run --config FILE.json --out DIR
   sovereign-dsa-lab reconcile --benchmark FILE.csv [--out FILE.md]

Inputs are the user's; the shipped example is hypothetical. Not the IMF's or any rating agency's model.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

from . import dynamics as dy
from . import reconcile as rc

DISCLAIMER = ("*Hypothetical example: synthetic history and projections, not a real country. Not the IMF's or any "
              "rating agency's model, and not a rating.*")


def _csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def run(cfg: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    p = dy.Path.from_dict(cfg["path"])
    d0 = cfg["d0"]
    dec = dy.decompose(d0, p)
    sd = {v: statistics.stdev(cfg["history"][v]) for v in dy.VARS}
    sc = dy.scenarios(d0, p, sd)
    f = cfg["fan"]
    joint = dy.fan(d0, p, cfg["history"], f["n"], f["method"], True, f["seed"])
    indep = dy.fan(d0, p, cfg["history"], f["n"], f["method"], False, f["seed"])
    _csv(out / "decomposition.csv", dec)
    _csv(out / "scenarios.csv", [{"year": y, **{k: v[i] for k, v in sc.items()}} for i, y in enumerate(p.years)])
    _csv(out / "fan_joint.csv", joint["percentiles"])
    _csv(out / "fan_independent.csv", indep["percentiles"])
    pc = lambda x: f"{round(100 * x, 1) + 0.0:.1f}"  # noqa: E731  (no "-0.0")
    lines = [f"# {cfg['label']}", "", DISCLAIMER, "", f"Debt/GDP {cfg['last_actual_year']}: {pc(d0)}%.", "",
             "## Baseline and decomposition (% of GDP)", "",
             "| Year | Debt | Change | Primary deficit | Real interest | Real growth | Exchange rate | Other |",
             "|---|---|---|---|---|---|---|---|"]
    for r in dec:
        lines.append(f"| {r['year']} | {pc(r['debt'])} | {pc(r['change'])} | {pc(r['primary_deficit'])} | "
                     f"{pc(r['real_interest'])} | {pc(r['real_growth'])} | {pc(r['exchange_rate'])} | {pc(r['other_flows'])} |")
    lines += ["", "## Deterministic shocks (one historical standard deviation, first two years)", "",
              "| Scenario | " + " | ".join(str(y) for y in p.years) + " | Peak |", "|---" * (len(p.years) + 2) + "|"]
    for k, v in sc.items():
        lines.append(f"| {k} | " + " | ".join(pc(x) for x in v) + f" | {pc(max(v))} |")
    lines += ["", f"## Fan chart ({f['n']:,} paths, {f['method']}, seed {f['seed']})", "",
              "| Year | p10 | p25 | p50 | p75 | p90 |", "|---|---|---|---|---|---|"]
    for r in joint["percentiles"]:
        lines.append(f"| {r['year']} | " + " | ".join(pc(r[k]) for k in ("p10", "p25", "p50", "p75", "p90")) + " |")
    lines += ["", f"- Final-year p10-p90 width: {pc(joint['width_final_p90_p10'])} pp with shocks drawn jointly, "
                  f"{pc(indep['width_final_p90_p10'])} pp with each variable drawn independently.",
              f"- Share of paths ending above the baseline: {joint['share_above_baseline_final']:.0%}.", ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return {"decomposition": dec, "scenarios": sc, "fan_joint": joint, "fan_independent": indep}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sovereign-dsa-lab")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("run")
    s.add_argument("--config", required=True)
    s.add_argument("--out", default="outputs")
    s = sub.add_parser("reconcile")
    s.add_argument("--benchmark", required=True)
    s.add_argument("--out")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        run(json.loads(Path(args.config).read_text(encoding="utf-8")), Path(args.out))
        print(f"wrote {args.out}/summary.md and CSVs")
        return 0
    res = rc.reconcile(rc.load(Path(args.benchmark)))
    text = rc.report_text(res, Path(args.benchmark).name)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
