# Claims ledger

Generated 2026-11-04 from the repo's own README Status and validation table.

| Claim | Tag | Evidence |
|---|---|---|
| Debt-ratio projection with FX share, standard decomposition, deterministic shocks, fan chart with historical co-movement | Demonstrated | README Status checklist |
| Second independent implementation (levels form) agrees with ratio form to 1e-12 across random inputs (Hypothesis) | Demonstrated | property tests |
| Validated against IMF Costa Rica report (CR 24/359): within 0.28pp of GDP every year to 2033, nothing fitted | Demonstrated; one of three checks fails as designed and is reported, not hidden | `docs/validation.md`, validation table |
| 21 pytest tests, CI | Demonstrated | CI badge |
| "Country H" example is a real country / this is the IMF's or a rating agency's model | Unsupported — and README already states the opposite explicitly in its opening disclaimer | README header |

## Action
No overclaim found. This is the strongest-disclosed repo in the batch: it reports its own failing check (the residual-explains-the-gap test) as a finding rather than hiding it, which is exactly the fact discipline this ledger exists to enforce.
