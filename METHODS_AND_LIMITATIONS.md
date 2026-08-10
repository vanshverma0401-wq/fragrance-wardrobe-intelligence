# Methods and limitations

## Metrics

### Rotation rate

`unique fragrances with at least one logged wear / collection size`

This measures representation in the supplied log window. It does not measure
consumption, enjoyment, or ideal collection size.

### Cost per logged wear

`purchase price / number of logged wears`

An unworn fragrance returns `null`, not zero or infinity. This is a simple
purchase-to-usage ratio. It is not accounting cost, resale value, remaining
inventory value, or the amount physically consumed.

### Neglected fragrance

An item is included when it has no logged wear or its latest wear is at least the
selected threshold before the analysis date. The threshold is a user choice,
not a universal definition of neglect.

### Collection coverage

Coverage counts how many collection items declare each family, season, and
occasion. It reflects entered tags, not measured performance.

## Similarity heuristic

The recommender ranks alternatives already present in the collection. Its
weighted score is:

| Component | Weight | Calculation |
|---|---:|---|
| notes | 0.30 | Jaccard overlap of declared note sets |
| family | 0.20 | exact broad-family match |
| season | 0.15 | Jaccard overlap of declared season sets |
| occasion | 0.15 | Jaccard overlap of declared occasion sets |
| longevity | 0.10 | normalized difference over a 12-hour range |
| projection | 0.10 | normalized difference over the 1–5 scale |

Ties are ordered by stable fragrance identifier. Each result returns every
component and plain-language reasons for the shared profile.

## Interpretation boundary

The score is an explainable heuristic for exploring an owned wardrobe. It is
not trained, experimentally validated, or calibrated to predict preference,
quality, compliments, purchase value, or real-world olfactory similarity.

The synthetic demo is useful for verifying software behavior only. It cannot
support consumer or market conclusions.

## Known limitations

- note, family, season, and occasion labels are subjective and owner-entered;
- no weather, location, batch, skin chemistry, or blind-testing controls exist;
- price does not include discounts, tax, decants, resale value, or bottle level;
- spray counts are recorded but are not converted to volume because atomizers
  vary and the MVP does not claim a reliable universal conversion;
- recency depends on complete wear logging;
- the CLI produces analytical JSON but no visual dashboard yet;
- the standard-library MVP does not yet include DuckDB, dbt, or cloud execution.

## Reproducibility

All calculations are deterministic for the same CSV inputs, analysis date, and
threshold. The unit suite checks validation failures, hand-calculated metrics,
stable ranking, CLI output, documentation links, data consistency, and public
safety patterns.
