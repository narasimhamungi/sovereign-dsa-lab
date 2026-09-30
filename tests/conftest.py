import json
from pathlib import Path

import pytest

from sovereigndsalab.dynamics import Path as DPath

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cfg():
    return json.loads((ROOT / "examples" / "country_h_hypothetical.json").read_text(encoding="utf-8"))


@pytest.fixture
def path(cfg):
    return DPath.from_dict(cfg["path"])


def flat(n=5, g=0.02, pi=0.02, r=0.05, pb=0.0, alpha=0.0, eps=0.0, sfa=0.0):
    return DPath(tuple(range(2026, 2026 + n)), (g,) * n, (pi,) * n, (r,) * n, (pb,) * n, (alpha,) * n, (eps,) * n,
                 (sfa,) * n)
