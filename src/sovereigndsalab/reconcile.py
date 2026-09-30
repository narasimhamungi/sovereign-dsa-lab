"""Reconcile the engine to a published debt-decomposition table (e.g. an IMF Article IV staff report).

The benchmark is a CSV transcribed by hand from the report, in percent, one row per year, first row = the last
actual year (only its debt is used). Columns (see benchmarks/TEMPLATE.csv):
    year, debt, change, primary_deficit, automatic_dynamics, other_flows, residual,     (contributions, % of GDP)
    r, g, pi                                                                              (memo items, %)
    optional: exchange_rate (contribution), alpha, eps (%); optional real_interest, real_growth
Three checks, in order:
1. Transcription: each row's contributions add to its change, and change = debt - previous debt, within rounding.
   Catches typing errors before they are mistaken for model differences.
2. Automatic dynamics rebuilt from the memo items and the previous year's debt vs the reported line.
3. Path: project from the first debt ratio with the reported primary deficits and other flows. The gap to the
   reported path should equal the cumulative reported residual, to rounding. A residual is never fitted.
"""
from __future__ import annotations

import csv
from pathlib import Path

REQUIRED = ("year", "debt", "change", "primary_deficit", "automatic_dynamics", "other_flows", "residual", "r", "g", "pi")


def load(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("year", "").strip() and not r["year"].startswith("#")]
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        raise ValueError(f"benchmark missing columns: {missing}")
    out = []
    for r in rows:
        out.append({k: (None if (v is None or v.strip() == "") else (int(v) if k == "year" else float(v)))
                    for k, v in r.items() if k != "source"})
    return out


def reconcile(rows: list[dict], tol_row: float = 0.25, tol_auto: float = 0.3, tol_path: float = 0.5) -> dict:
    """Tolerances in percentage points of GDP, reflecting tables rounded to 0.1."""
    base, proj = rows[0], rows[1:]
    report, ok = [], True
    prev_debt = base["debt"]
    for r in proj:
        # 1. transcription identity
        parts = r["primary_deficit"] + r["automatic_dynamics"] + r["other_flows"] + r["residual"]
        t_sum = abs(parts - r["change"])
        t_chg = abs((r["debt"] - prev_debt) - r["change"])
        # 2. automatic dynamics from memo items
        g, pi, rr = r["g"] / 100, r["pi"] / 100, r["r"] / 100
        den = 1 + g + pi + g * pi
        prev = prev_debt / 100
        auto = prev * (rr - pi * (1 + g) - g) / den
        if r.get("alpha") is not None and r.get("eps") is not None:
            auto += prev * (r["alpha"] / 100) * (r["eps"] / 100) * (1 + rr) / den
            fx_note = "computed"
        else:
            auto += (r.get("exchange_rate") or 0.0) / 100
            fx_note = "taken from report" if r.get("exchange_rate") else "none"
        auto_gap = auto * 100 - r["automatic_dynamics"]
        row_ok = t_sum <= tol_row and t_chg <= tol_row and abs(auto_gap) <= tol_auto
        report.append({"year": r["year"], "transcription_sum_gap": t_sum, "transcription_change_gap": t_chg,
                       "auto_reported": r["automatic_dynamics"], "auto_model": auto * 100, "auto_gap": auto_gap,
                       "fx_term": fx_note, "row_ok": row_ok})
        ok &= row_ok
        prev_debt = r["debt"]
    # 3. path without the report's residual, same exchange-rate treatment as check 2
    d = base["debt"] / 100
    path = []
    for r in proj:
        g, pi, rr = r["g"] / 100, r["pi"] / 100, r["r"] / 100
        growth = (1 + g) * (1 + pi)
        fx = 0.0
        if r.get("alpha") is not None and r.get("eps") is not None:
            fx = d * (r["alpha"] / 100) * (r["eps"] / 100) * (1 + rr) / growth
        elif r.get("exchange_rate"):
            fx = r["exchange_rate"] / 100
        d = d * (1 + rr) / growth + fx + r["primary_deficit"] / 100 + r["other_flows"] / 100
        path.append(d * 100)
    cum, gaps = 0.0, []
    for r, m in zip(proj, path):
        cum += r["residual"]
        gaps.append({"year": r["year"], "debt_reported": r["debt"], "debt_model_no_residual": m,
                     "gap": r["debt"] - m, "cumulative_reported_residual": cum,
                     "gap_minus_residual": r["debt"] - m - cum})
    path_ok = all(abs(x["gap_minus_residual"]) <= tol_path for x in gaps)
    return {"passed": ok and path_ok, "rows": report, "path": gaps, "tolerances_pp": (tol_row, tol_auto, tol_path)}


def report_text(res: dict, name: str) -> str:
    lines = [f"# Reconciliation to {name}: {'PASS' if res['passed'] else 'FAIL'}", "",
             "Percentage points of GDP. Tolerances (row identity, automatic dynamics, path): "
             + ", ".join(f"{t:g}" for t in res["tolerances_pp"]), "",
             "| Year | Transcription gap | Auto dynamics: report | model | gap | FX term |", "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        lines.append(f"| {r['year']} | {max(r['transcription_sum_gap'], r['transcription_change_gap']):.2f} | "
                     f"{r['auto_reported']:.2f} | {r['auto_model']:.2f} | {r['auto_gap']:+.2f} | {r['fx_term']} |")
    lines += ["", "| Year | Debt: report | model without residual | gap | cumulative reported residual | difference |",
              "|---|---|---|---|---|---|"]
    for g in res["path"]:
        lines.append(f"| {g['year']} | {g['debt_reported']:.1f} | {g['debt_model_no_residual']:.2f} | {g['gap']:+.2f} | "
                     f"{g['cumulative_reported_residual']:+.1f} | {g['gap_minus_residual']:+.2f} |")
    return "\n".join(lines) + "\n"
