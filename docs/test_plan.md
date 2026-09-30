# Test plan and results

| Area | Test |
|---|---|
| Hand calculation | One step with FX debt; debt ratio constant when r equals nominal growth and pb = 0 |
| Identities (Hypothesis, 300 random paths) | Decomposition adds to the change; automatic dynamics = sum of its parts; the levels implementation equals the ratio implementation to 1e-12 |
| Shocks | Temporary shocks last two years; every shock raises the final debt; combined is the worst |
| Fan | Collapses to the baseline with no shocks; percentiles ordered; reproducible by seed; the normal method reproduces the historical covariance; joint draws widen the fan on co-moving history (bootstrap and normal) |
| Reconciliation | Passes an engine-generated table rounded to 0.1, with and without a residual and with the exchange-rate line taken from the table; fails on a transcription typo and on a wrong memo item |

| Published benchmark | The Costa Rica (IMF CR 24/359) results documented in docs/validation.md stay as documented |

Results (30 Sep 2026): 21 passed on Python 3.10 to 3.14. Reconciliation to IMF CR 24/359: see docs/validation.md.
