# Validation: what is left to do

The engine is validated against itself (hand calculation, identities, a second implementation). It is **not yet**
validated against a published analysis. That needs one table transcribed by hand.

1. Choose a country whose latest IMF Article IV staff report (imf.org, Publications > Country Reports) has a public
   debt sustainability annex with a table of contributions to the change in public debt, and a material foreign-
   currency share (otherwise the exchange-rate term is never exercised).
2. Copy `benchmarks/TEMPLATE.csv` to `benchmarks/<country>_<year>.csv`. Transcribe the last actual year and each
   projection year: debt, change, primary deficit, automatic dynamics, exchange-rate line if shown, other flows,
   residual, and the memo items r, g, π (α and ε only if the report gives them). Put the report title, date and page in
   `source` on the first row.
3. Run `sovereign-dsa-lab reconcile --benchmark benchmarks/<file>.csv --out outputs/reconciliation.md`. The
   transcription check runs first, so a typing error shows up as that, not as a model difference.
4. Write up in `docs/validation.md`: where the model matches, where it does not, and why (rounding, definitions of r,
   exchange-rate treatment, stock-flow items). Commit the CSV and the report. Only then tick the README line.
