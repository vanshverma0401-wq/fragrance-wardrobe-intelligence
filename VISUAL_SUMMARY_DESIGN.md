# Visual summary design

Date: 2026-08-10
Status: Selected recruiter-snapshot design

## Options considered

1. **Recruiter snapshot — selected.** One static image combining four KPIs, one
   ranked bar chart, one compact coverage comparison, and a synthetic-data note.
   Best for immediate GitHub scanning and grounded in the verified demo outputs.
2. **Consumer dashboard mockup.** More product-like, but it could imply a deployed
   interface or live personalization that the MVP does not provide.
3. **Technical pipeline infographic.** Useful for engineering depth, but less
   effective at showing the analytical result of the project.

## Chart contract

- **Analytical question:** What does the synthetic demonstration wardrobe reveal
  about rotation, purchase-cost-to-usage ratio, and seasonal coverage?
- **Takeaway:** Seven of eight fictional bottles appear in the wear log, but cost
  per logged wear varies substantially and one bottle has no logged wears.
- **Surface:** standalone static PNG for the repository README.
- **Size:** 1600 by 1000 pixels.
- **Primary comparison:** horizontal ranked bars for purchase price divided by
  logged wears across the seven worn items.
- **Secondary comparison:** four horizontal bars for declared collection coverage
  across spring, summer, fall, and winter.
- **Context:** eight fictional collection items, eighteen fictional wear events,
  analysis date 2026-08-10.
- **Fallback:** if the source data is insufficient, display KPIs and a table. The
  current seven comparable worn items and four seasons are sufficient for bars.

## Visual system

- near-white background, white cards, charcoal text, quiet grey guides;
- deep blue as the primary chart color and restrained gold as the focal accent;
- direct labels and exact values so color is not required to interpret the chart;
- no legend because the category labels already identify every bar;
- no gradients, decorative chart borders, or unsupported insight headline.

## Claim boundary

The image must visibly state that the data is synthetic and that cost per logged
wear is a simple purchase-price-to-logged-wears ratio. It must not imply a real
consumer collection, financial return, preference-prediction accuracy, market
finding, or deployed application.

## Reproducibility and QA

The rendering script reads the same public demo CSVs through the tested project
modules. Final QA requires checking exact dimensions, labels, value agreement
with CLI output, no clipping, and visual inspection of the exported PNG.
