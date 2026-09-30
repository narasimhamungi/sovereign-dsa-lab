# Validation against a published IMF table

**Benchmark:** IMF Country Report No. 24/359, *Costa Rica: Post-Financing Assessment* (December 2024), Annex II
(Sovereign Risk and Debt Sustainability Assessment), Table 4 "Baseline Scenario", page 32. Central government,
2023 actual and 2024-2033 projections. Transcribed by hand into `benchmarks/costa_rica_pfa_2024.csv`; output in
`outputs/reconciliation_costa_rica_pfa_2024.md`. Rerun with:

    sovereign-dsa-lab reconcile --benchmark benchmarks/costa_rica_pfa_2024.csv --out outputs/reconciliation_costa_rica_pfa_2024.md

**What is rebuilt and what is taken from the report.** The report publishes the effective interest rate, real growth
and the GDP deflator, so the real-interest and real-growth contributions are rebuilt from those. It does not publish
the foreign-currency share or the depreciation path, so the exchange-rate channel (its "relative inflation" line, plus
"real exchange rate" where shown) is taken from the report. Treating "relative inflation" as the exchange-rate channel
is my reading of the framework's presentation, not a published definition.

## Results

| Check | Result |
|---|---|
| 1. Transcription: contributions add to the change, and the change equals the debt difference | **Pass** every year (largest gap 0.10 pp, i.e. rounding) |
| 2. Automatic dynamics rebuilt from memo items vs the report's line (tolerance 0.3 pp) | **Pass** every year; gaps within ±0.05 pp in 2024-2029, widening to -0.24 pp by 2033 |
| 3. Model path without the report's residual: gap should equal the cumulative reported residual | **Fail** (difference reaches 0.97 pp by 2033) |
| Model path without any residual vs the reported debt path | Within **0.28 pp** of GDP in every year, 2024-2033 |

## Reading the results

- **The engine reproduces the published path.** From the report's own primary balances, interest rate, growth and
  deflator (and its exchange-rate line), the projected debt ratio stays within 0.3 pp of GDP of the IMF's path for ten
  years, with nothing fitted.
- **Check 3 was designed on an assumption the data rejects.** It assumed the rebuilt automatic dynamics would equal the
  report's line, so the report's residual (-0.1 pp a year) would explain the remaining gap. Instead the rebuilt
  dynamics come out slightly lower than the report's line in most years, by about the size of the residual, so adding
  the residual would move the model away from the reported path, not towards it. The check stays in the code as
  written; changing its criterion after seeing the result would make it meaningless.
- **Where the model and the report disagree.** The real-interest and real-growth terms match to rounding in the
  medium-term years (2024-2029, within ±0.06 pp). In the extended-projection years (2030-2033) the report's
  real-interest line is higher than the published effective rate implies, by up to 0.24 pp in 2033. Rounding of the
  memo items (each shown to one decimal) can explain at most about 0.07 pp, not this. The cause is not identifiable from the published table; a different
  interest-rate convention in the framework's extended projection is a possibility (inference, not verified).

## Limits

- One country, one report, one vintage; central government only.
- The exchange-rate channel is taken from the report, so it is not tested.
- Transcription is manual; check 1 guards against typing errors, not against misreading a row label.
