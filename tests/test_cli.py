from conftest import ROOT
from sovereigndsalab.cli import main


def test_run_writes_outputs(tmp_path):
    assert main(["run", "--config", str(ROOT / "examples" / "country_h_hypothetical.json"), "--out", str(tmp_path)]) == 0
    for name in ("summary.md", "decomposition.csv", "scenarios.csv", "fan_joint.csv", "fan_independent.csv"):
        assert (tmp_path / name).exists()
    assert "not a real country" in (tmp_path / "summary.md").read_text(encoding="utf-8")
