"""Public debt dynamics: projection, decomposition, deterministic shocks and a joint-shock fan chart.

Notation (all annual, as fractions): d = gross public debt / GDP; r = effective NOMINAL interest rate on debt
(interest paid / debt at the end of the previous year); g = REAL GDP growth; pi = GDP deflator growth;
alpha = share of debt in foreign currency at the end of the previous year; eps = nominal depreciation of the
local currency (rise in the local-currency price of one unit of foreign currency); pb = primary balance / GDP
(surplus positive); sfa = other identified flows / stock-flow adjustment, % of GDP (adds to debt).

    d_t = d_(t-1) * (1 + r_t + alpha_(t-1) eps_t (1 + r_t)) / ((1 + g_t)(1 + pi_t)) - pb_t + sfa_t

Decomposition of the change in d (the split used in the IMF's market-access-country DSA template; see
docs/model_spec.md), with D = 1 + g + pi + g pi:
    primary deficit         -pb
    real interest rate      d_(t-1) (r - pi (1 + g)) / D
    real GDP growth         d_(t-1) (-g) / D
    exchange rate           d_(t-1) alpha eps (1 + r) / D
    other flows             sfa
The three automatic-dynamics terms sum to d_(t-1)(r + alpha eps (1 + r) - g - pi - g pi) / D exactly.
Inputs in examples/ are hypothetical. Not any rating agency's or the IMF's model.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

VARS = ("g", "pi", "r", "pb", "eps")          # variables that can be shocked


@dataclass(frozen=True)
class Path:
    """Projection inputs, one entry per projection year t = 1..H."""
    years: tuple[int, ...]
    g: tuple[float, ...]
    pi: tuple[float, ...]
    r: tuple[float, ...]
    pb: tuple[float, ...]
    alpha: tuple[float, ...]       # FX share of debt at the end of the PREVIOUS year
    eps: tuple[float, ...]
    sfa: tuple[float, ...]

    def __post_init__(self):
        n = len(self.years)
        for name in ("g", "pi", "r", "pb", "alpha", "eps", "sfa"):
            if len(getattr(self, name)) != n:
                raise ValueError(f"{name} must have {n} entries")
        if any(not 0 <= a <= 1 for a in self.alpha):
            raise ValueError("alpha must be in [0, 1]")
        if any((1 + g) * (1 + p) <= 0 for g, p in zip(self.g, self.pi)):
            raise ValueError("nominal GDP must stay positive")

    @classmethod
    def from_dict(cls, d: dict) -> "Path":
        return cls(**{k: tuple(v) for k, v in d.items()})


def project(d0: float, p: Path) -> list[float]:
    """Debt ratio path d_1..d_H from d_0 (ratio form)."""
    out, d = [], d0
    for t in range(len(p.years)):
        d = d * (1 + p.r[t] + p.alpha[t] * p.eps[t] * (1 + p.r[t])) / ((1 + p.g[t]) * (1 + p.pi[t])) - p.pb[t] + p.sfa[t]
        out.append(d)
    return out


def project_levels(d0: float, p: Path, gdp0: float = 100.0) -> list[float]:
    """Second, independent implementation in levels: domestic and foreign-currency debt stocks carried separately,
    nominal GDP compounded, ratio taken at the end. Must agree with project() to rounding."""
    y = gdp0
    dom, fx = d0 * gdp0, 0.0                          # fx stock kept in local currency
    out = []
    for t in range(len(p.years)):
        total = dom + fx
        dom, fx = total * (1 - p.alpha[t]), total * p.alpha[t]            # currency mix at end of previous year
        y_new = y * (1 + p.g[t]) * (1 + p.pi[t])
        dom = dom * (1 + p.r[t])
        fx = fx * (1 + p.r[t]) * (1 + p.eps[t])
        dom += (-p.pb[t] + p.sfa[t]) * y_new
        y = y_new
        out.append((dom + fx) / y)
    return out


def decompose(d0: float, p: Path) -> list[dict]:
    rows, prev = [], d0
    for t, d in enumerate(project(d0, p)):
        g, pi, r, a, e = p.g[t], p.pi[t], p.r[t], p.alpha[t], p.eps[t]
        den = 1 + g + pi + g * pi
        real_r = prev * (r - pi * (1 + g)) / den
        real_g = prev * (-g) / den
        fx = prev * a * e * (1 + r) / den
        rows.append({"year": p.years[t], "debt": d, "change": d - prev, "primary_deficit": -p.pb[t],
                     "real_interest": real_r, "real_growth": real_g, "exchange_rate": fx,
                     "automatic_dynamics": real_r + real_g + fx, "other_flows": p.sfa[t],
                     "residual": (d - prev) - (-p.pb[t] + real_r + real_g + fx + p.sfa[t])})
        prev = d
    return rows


# ------------------------------------------------------------------ deterministic scenarios
def shock(p: Path, var: str, size: float, years: int = 2) -> Path:
    """Add `size` to `var` in the first `years` projection years (a temporary shock)."""
    vals = list(getattr(p, var))
    for t in range(min(years, len(vals))):
        vals[t] += size
    return replace(p, **{var: tuple(vals)})


def scenarios(d0: float, p: Path, sd: dict[str, float]) -> dict[str, list[float]]:
    """Baseline and one-standard-deviation, two-year shocks (growth down, interest up, primary balance down,
    depreciation up), plus all four together. sd: historical standard deviations by variable."""
    shocks = {"growth": ("g", -sd["g"]), "interest_rate": ("r", sd["r"]), "primary_balance": ("pb", -sd["pb"]),
              "exchange_rate": ("eps", sd["eps"])}
    out = {"baseline": project(d0, p)}
    combined = p
    for name, (var, size) in shocks.items():
        out[name] = project(d0, shock(p, var, size))
        combined = shock(combined, var, size)
    out["combined"] = project(d0, combined)
    return out


# ------------------------------------------------------------------ stochastic fan chart
def deviations(history: dict[str, list[float]]) -> list[dict[str, float]]:
    """Historical deviations from each variable's mean, kept year by year so co-movement is preserved."""
    n = len(history[VARS[0]])
    means = {v: sum(history[v]) / n for v in VARS}
    return [{v: history[v][i] - means[v] for v in VARS} for i in range(n)]


def _cov(devs: list[dict[str, float]]) -> list[list[float]]:
    n = len(devs)
    return [[sum(x[a] * x[b] for x in devs) / (n - 1) for b in VARS] for a in VARS]


def _cholesky(m: list[list[float]]) -> list[list[float]]:
    k = len(m)
    low = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1):
            s = m[i][j] - sum(low[i][x] * low[j][x] for x in range(j))
            if i == j:
                low[i][j] = s ** 0.5 if s > 1e-18 else 0.0
            else:
                low[i][j] = s / low[j][j] if low[j][j] else 0.0
    return low


def fan(d0: float, p: Path, history: dict[str, list[float]], n: int = 5000, method: str = "bootstrap",
        joint: bool = True, seed: int = 20260930, pct: tuple[float, ...] = (0.1, 0.25, 0.5, 0.75, 0.9)) -> dict:
    """Simulate n debt paths by adding one shock vector per year to the baseline.

    method "bootstrap": each year draws a whole historical year's deviation vector, so shocks keep their observed
    co-movement (recessions hit growth and the primary balance together). method "normal": multivariate normal
    with the historical covariance. joint=False draws each variable independently (from a different historical year,
    or with the off-diagonal covariances set to zero), which is the comparison that shows why co-movement matters.
    Returns percentiles by year plus the share of paths above the baseline's final debt."""
    rng = random.Random(seed)
    devs = deviations(history)
    cov = _cov(devs)
    if not joint:
        cov = [[cov[i][j] if i == j else 0.0 for j in range(len(VARS))] for i in range(len(VARS))]
    low = _cholesky(cov)
    h = len(p.years)
    finals, paths = [], []
    for _ in range(n):
        vals = {v: list(getattr(p, v)) for v in VARS}
        for t in range(h):
            if method == "bootstrap":
                draw = rng.choice(devs) if joint else {v: rng.choice(devs)[v] for v in VARS}
            elif method == "normal":
                z = [rng.gauss(0, 1) for _ in VARS]
                draw = {v: sum(low[i][j] * z[j] for j in range(i + 1)) for i, v in enumerate(VARS)}
            else:
                raise ValueError("method must be 'bootstrap' or 'normal'")
            for v in VARS:
                vals[v][t] += draw[v]
        path = project(d0, replace(p, **{v: tuple(vals[v]) for v in VARS}))
        paths.append(path)
        finals.append(path[-1])
    by_year = []
    for t in range(h):
        col = sorted(x[t] for x in paths)
        by_year.append({"year": p.years[t], **{f"p{int(q * 100)}": col[min(n - 1, int(q * n))] for q in pct}})
    base_final = project(d0, p)[-1]
    return {"percentiles": by_year, "share_above_baseline_final": sum(f > base_final for f in finals) / n,
            "width_final_p90_p10": by_year[-1]["p90"] - by_year[-1]["p10"]}
