# sovereign-dsa-lab

![CI](https://github.com/narasimhamungi/sovereign-dsa-lab/actions/workflows/ci.yml/badge.svg)

Public debt dynamics for a sovereign: the debt-ratio projection with a foreign-currency share, the standard
decomposition of each year's change, deterministic shocks, and a fan chart that keeps the historical co-movement of
the shocks. Built to be reconciled line by line against a published debt-decomposition table.

> The shipped example, "Country H", is **hypothetical**: synthetic history and projections, not a real country.
> Not the IMF's or any rating agency's model, and not a rating.

## Status

- [x] Model specification, limitations, test plan and changelog: [`docs/`](docs/)
- [x] Projection with domestic and foreign-currency debt, exchange-rate term and other flows; decomposition into
      primary deficit, real interest rate, real growth, exchange rate and other flows
- [x] Second, independent implementation in levels (separate currency stocks, nominal GDP), agreeing with the ratio
      form to 1e-12 across random inputs (Hypothesis)
- [x] Deterministic one-standard-deviation shocks (growth, interest rate, primary balance, exchange rate, combined)
- [x] Fan chart from historical shocks drawn **jointly** (bootstrap of whole years, or multivariate normal with the
      historical covariance), with the independent-draw version alongside for comparison
- [x] Reconciliation tool for a transcribed published table: transcription check, automatic dynamics rebuilt from the
      memo items, and the path with the report's residual carried rather than fitted. Tested on synthetic tables
- [x] 20 pytest tests and CI
- [ ] **Validation against a real published table: not done.** Needs one staff-report table transcribed into
      `benchmarks/` ([`docs/validation.md`](docs/validation.md)). Until then this repo shows a working engine, not
      a validated one

## What the example shows (and does not)

On Country H, the final-year p10-p90 range is 25.2 pp of GDP with shocks drawn jointly and 14.4 pp with each
variable drawn independently. The synthetic history was **built** with strong co-movement (growth and the primary
balance correlate at 0.91), so this demonstrates the mechanism, not a fact about any country: when recessions bring
weaker primary balances and depreciation at the same time, independent draws understate the tail.

Full output: [`outputs/summary.md`](outputs/summary.md).

## Run

```bash
pip install -e ".[test]"
python -m pytest
sovereign-dsa-lab run --config examples/country_h_hypothetical.json --out outputs
sovereign-dsa-lab reconcile --benchmark benchmarks/<country>_<report>.csv --out outputs/reconciliation.md
```
