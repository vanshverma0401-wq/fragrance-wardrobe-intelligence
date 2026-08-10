# Data model

The MVP uses two CSV inputs joined by `fragrance_id`.

```text
collection (one row per fragrance)
    1
    |
    | fragrance_id
    |
    *
wear_log (one row per logged wear)
```

## Collection

| Field | Type | Rule | Purpose |
|---|---|---|---|
| `fragrance_id` | text | unique, lowercase letters/numbers/hyphens | stable join key |
| `house` | text | required | house or maker |
| `name` | text | required | fragrance display name |
| `family` | text | required | normalized broad scent family |
| `notes` | semicolon list | at least one | note-profile comparison |
| `seasons` | semicolon list | at least one | declared seasonal fit |
| `occasions` | semicolon list | at least one | declared occasion fit |
| `price_usd` | decimal | greater than zero | purchase-price ratio |
| `bottle_ml` | decimal | greater than zero | collection context |
| `personal_rating` | decimal | 0 through 10 | owner-supplied preference context |
| `longevity_hours` | decimal | zero or greater | owner-supplied performance estimate |
| `projection` | integer | 1 through 5 | owner-supplied projection scale |

Multi-value fields are lowercased, trimmed, de-duplicated, and represented as
sets inside the application.

## Wear log

| Field | Type | Rule | Purpose |
|---|---|---|---|
| `wear_id` | text | unique | event key |
| `worn_on` | date | ISO `YYYY-MM-DD` | rotation and recency |
| `fragrance_id` | text | must exist in collection | collection relationship |
| `season` | text | required | actual logged context |
| `occasion` | text | required | actual logged context |
| `sprays` | integer | greater than zero | descriptive usage input |
| `performance_rating` | decimal | 0 through 10 | owner observation |
| `satisfaction_rating` | decimal | 0 through 10 | owner observation |

The MVP validates the relationship in Python. A later DuckDB/dbt version can
materialize dimensions, facts, tests, and marts from the same logical model.
