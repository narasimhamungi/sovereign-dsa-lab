"""The reconciliation must pass a table produced by the engine and rounded as reports round, and must fail on a
transcription error or a wrong memo item. It is tested on synthetic tables because no real one is committed yet."""
import csv

import pytest

from conftest import flat
from sovereigndsalab import dynamics as dy
from sovereigndsalab import reconcile as rc


def synthetic_table(tmp_path, residual=0.0, fx=True):
    p = flat(6, g=0.021, pi=0.027, r=0.052, pb=-0.012, alpha=0.3 if fx else 0.0, eps=0.04, sfa=0.004)
    d0 = 0.68
    dec = dy.decompose(d0, p)
    rows = [{"year": 2025, "debt": round(d0 * 100, 1)}]
    extra = 0.0
    for x in dec:
        extra += residual
        rows.append({"year": x["year"], "debt": round((x["debt"] + extra) * 100, 1),
                     "change": round((x["change"] + residual) * 100, 1),
                     "primary_deficit": round(x["primary_deficit"] * 100, 1),
                     "automatic_dynamics": round(x["automatic_dynamics"] * 100, 1),
                     "exchange_rate": round(x["exchange_rate"] * 100, 1),
                     "other_flows": round(x["other_flows"] * 100, 1), "residual": round(residual * 100, 1),
                     "r": 5.2, "g": 2.1, "pi": 2.7, "alpha": 30.0 if fx else "", "eps": 4.0 if fx else ""})
    path = tmp_path / "bench.csv"
    cols = ["year", "debt", "change", "primary_deficit", "automatic_dynamics", "exchange_rate", "other_flows",
            "residual", "r", "g", "pi", "alpha", "eps"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


def test_engine_table_rounded_to_one_decimal_reconciles(tmp_path):
    res = rc.reconcile(rc.load(synthetic_table(tmp_path)))
    assert res["passed"]


def test_a_reported_residual_is_carried_not_fitted(tmp_path):
    res = rc.reconcile(rc.load(synthetic_table(tmp_path, residual=0.003)))
    assert res["passed"]
    last = res["path"][-1]
    assert last["gap"] == pytest.approx(last["cumulative_reported_residual"], abs=0.5)


def test_exchange_rate_line_can_come_from_the_report(tmp_path):
    rows = rc.load(synthetic_table(tmp_path))
    for r in rows:
        r["alpha"] = r["eps"] = None
    res = rc.reconcile(rows)
    assert res["passed"] and res["rows"][0]["fx_term"] == "taken from report"


def test_transcription_error_is_caught(tmp_path):
    rows = rc.load(synthetic_table(tmp_path))
    rows[3]["primary_deficit"] += 1.0            # a typo
    res = rc.reconcile(rows)
    assert not res["passed"] and not res["rows"][2]["row_ok"]


def test_wrong_memo_item_is_caught(tmp_path):
    rows = rc.load(synthetic_table(tmp_path))
    for r in rows[1:]:
        r["r"] = 6.2                             # interest rate off by 1 pp
    assert not rc.reconcile(rows)["passed"]


def test_missing_column_rejected(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("year,debt\n2025,60\n", encoding="utf-8")
    with pytest.raises(ValueError):
        rc.load(p)


def test_template_parses_headers():
    from conftest import ROOT
    head = (ROOT / "benchmarks" / "TEMPLATE.csv").read_text(encoding="utf-8").splitlines()[0].split(",")
    assert set(rc.REQUIRED) <= set(head)
