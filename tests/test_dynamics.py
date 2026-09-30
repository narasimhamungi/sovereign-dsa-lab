import pytest
from hypothesis import given, settings, strategies as st

from conftest import flat
from sovereigndsalab import dynamics as dy


def test_one_step_by_hand():
    d = dy.project(0.60, flat(1, g=0.02, pi=0.03, r=0.05, pb=0.01, alpha=0.25, eps=0.10))
    assert d[0] == pytest.approx(0.60 * (1.05 + 0.25 * 0.10 * 1.05) / (1.02 * 1.03) - 0.01, abs=1e-15)


def test_debt_ratio_is_constant_when_interest_equals_nominal_growth():
    nominal = 1.02 * 1.03 - 1
    assert dy.project(0.8, flat(10, pi=0.03, r=nominal)) == pytest.approx([0.8] * 10, abs=1e-12)


def test_no_fx_share_means_no_exchange_rate_effect():
    rows = dy.decompose(0.6, flat(3, eps=0.2))
    assert all(r["exchange_rate"] == 0 for r in rows)


def test_shock_is_temporary():
    p = dy.shock(flat(5), "g", -0.03, years=2)
    assert p.g == pytest.approx((-0.01, -0.01, 0.02, 0.02, 0.02))


def test_scenarios_raise_debt(cfg, path):
    import statistics
    sd = {v: statistics.stdev(cfg["history"][v]) for v in dy.VARS}
    sc = dy.scenarios(cfg["d0"], path, sd)
    for k in ("growth", "interest_rate", "primary_balance", "exchange_rate", "combined"):
        assert sc[k][-1] > sc["baseline"][-1], k
    assert sc["combined"][-1] == max(v[-1] for v in sc.values())


def test_invalid_path_rejected():
    with pytest.raises(ValueError):
        dy.Path((2026,), (0.0,), (0.0,), (0.0,), (0.0,), (1.5,), (0.0,), (0.0,))


rates = st.floats(-0.05, 0.10)


@settings(max_examples=300, deadline=None)
@given(st.floats(0.0, 2.0), st.lists(st.tuples(rates, st.floats(-0.02, 0.15), st.floats(0.0, 0.15), st.floats(-0.05, 0.05),
                                             st.floats(0, 1), st.floats(-0.3, 0.5), st.floats(-0.03, 0.03)),
                                   min_size=1, max_size=12))
def test_decomposition_adds_up_and_levels_agree(d0, rows):
    g, pi, r, pb, a, e, s = zip(*rows)
    p = dy.Path(tuple(range(len(rows))), g, pi, r, pb, a, e, s)
    dec = dy.decompose(d0, p)
    for x in dec:
        assert x["residual"] == pytest.approx(0.0, abs=1e-12)
        assert x["automatic_dynamics"] == pytest.approx(x["real_interest"] + x["real_growth"] + x["exchange_rate"], abs=1e-15)
    # second implementation, in levels with separate currency stocks
    assert dy.project_levels(d0, p) == pytest.approx(dy.project(d0, p), rel=1e-12, abs=1e-12)


def test_fan_collapses_to_baseline_without_shocks(path):
    hist = {v: [0.01] * 10 for v in dy.VARS}
    f = dy.fan(0.62, path, hist, n=200)
    base = dy.project(0.62, path)
    for r, b in zip(f["percentiles"], base):
        assert r["p10"] == pytest.approx(b) and r["p90"] == pytest.approx(b)


def test_fan_is_ordered_and_reproducible(cfg, path):
    a = dy.fan(cfg["d0"], path, cfg["history"], n=500, seed=1)
    b = dy.fan(cfg["d0"], path, cfg["history"], n=500, seed=1)
    assert a == b
    for r in a["percentiles"]:
        assert r["p10"] <= r["p25"] <= r["p50"] <= r["p75"] <= r["p90"]


@pytest.mark.parametrize("method", ["bootstrap", "normal"])
def test_co_movement_widens_the_fan(cfg, path, method):
    """Synthetic history is built so that low growth, weak primary balances and depreciation arrive together.
    Drawing the variables independently discards that and understates the spread."""
    joint = dy.fan(cfg["d0"], path, cfg["history"], n=3000, method=method, joint=True)
    indep = dy.fan(cfg["d0"], path, cfg["history"], n=3000, method=method, joint=False)
    assert joint["width_final_p90_p10"] > 1.3 * indep["width_final_p90_p10"]


def test_normal_draws_reproduce_the_historical_covariance(cfg):
    devs = dy.deviations(cfg["history"])
    cov = dy._cov(devs)
    low = dy._cholesky(cov)
    rebuilt = [[sum(low[i][k] * low[j][k] for k in range(5)) for j in range(5)] for i in range(5)]
    assert sum(rebuilt, []) == pytest.approx(sum(cov, []), abs=1e-15)
