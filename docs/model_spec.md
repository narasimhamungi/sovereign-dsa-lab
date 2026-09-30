# Model specification

Implemented in `src/sovereigndsalab/dynamics.py`. All rates annual, as fractions.

## Projection

d_t = d_(t-1) (1 + r_t + α_(t-1) ε_t (1 + r_t)) / ((1 + g_t)(1 + π_t)) - pb_t + sfa_t

d: gross public debt / GDP. r: effective nominal interest rate (interest paid / previous year's debt). g: real GDP
growth. π: GDP deflator growth. α: foreign-currency share of debt at the end of the previous year. ε: nominal
depreciation (rise in the local-currency price of foreign currency). pb: primary balance / GDP, surplus positive.
sfa: other identified flows (privatisation receipts negative, bank support positive), % of GDP.

**Second implementation.** `project_levels` carries domestic and foreign-currency stocks in levels, compounds nominal
GDP, and takes the ratio at the end. It shares no formula with the ratio form beyond the definitions of the inputs;
the two agree to 1e-12 in property tests.

## Decomposition

With D = 1 + g + π + gπ:

| Contribution | Formula |
|---|---|
| Primary deficit | -pb |
| Real interest rate | d_(t-1) (r - π(1 + g)) / D |
| Real growth | d_(t-1) (-g) / D |
| Exchange rate | d_(t-1) α ε (1 + r) / D |
| Other flows | sfa |

This is the split used in the IMF's market-access-country DSA template. Reports prepared under the IMF's newer
framework for market-access countries (from 2022) may split the automatic dynamics differently, so the reconciliation
compares the **total** automatic dynamics, which does not depend on the split.

## Shocks

- Deterministic: one historical standard deviation, applied in the first two projection years, per variable and
  combined (growth down, interest rate up, primary balance down, depreciation up).
- Fan chart: historical deviations from each variable's mean, kept as whole-year vectors. Bootstrap draws a whole
  historical year per projection year; the normal method uses the historical covariance (Cholesky). `joint=False`
  breaks the co-movement (independent years per variable, or a diagonal covariance) for comparison.

## Reconciliation (`reconcile.py`)

1. Transcription: contributions add to the change and the change equals the debt difference, within rounding.
2. Automatic dynamics rebuilt from the memo items (r, g, π; α and ε if given, else the report's exchange-rate line)
   and the previous year's debt, against the reported line.
3. Path without the report's residual; its gap to the reported path must equal the cumulative reported residual.
   Tolerances default to 0.25, 0.3 and 0.5 pp of GDP, reflecting tables rounded to 0.1.
