# Changelog

Changes to STOCKSIGNAL are recorded here.

## 0.3.0 — Explainable inventory intelligence helpers

- Added per-field data completeness profiling.
- Added a user-defined what-if stock-cover sensitivity simulator.
- Added a limited GS1 text parser for GTIN-14, batch/lot, expiry and serial fields.
- Added SHA-256 fingerprints of uploaded snapshot files to comparison receipts.
- Restored the full required-field dictionary and manual checks T01–T14 while retaining snapshot checks T15–T20 and adding intelligence checks T21–T25.

These additions remain human-reviewed prototype features and do not provide demand forecasting, procurement instructions, barcode image decoding, catalogue lookup, or tamper-proof audit storage.

## 0.2.0 — Inventory comparison and competition-readiness documentation

- Added read-only comparison of previous and latest inventory CSV snapshots.
- Added row-level reporting for added, absent, changed, unchanged, ambiguous and unmatchable records.
- Added downloadable comparison reports and a per-run comparison receipt.
- Added automated snapshot-comparison tests.
- Documented the actual boundaries of voice, shelf mapping, coordination-board and field-kit prototypes.
- Added a competition demonstration guide and synthetic snapshot examples.
- Corrected the README banner path and documented the existing hosted app.
- Added a discoverable GitHub Actions test workflow under `.github/workflows/`.
- Added ignore rules for Python caches, local environments and secret files.

This remains an early prototype. No authorised field validation, eLMIS integration, real-time IoT, automatic speech recognition, persistent multi-user audit database or measured health impact is claimed.

## 0.1.0 — Initial public prototype package

- Added Streamlit review workspace for CSV inventory records.
- Added transparent row-level checks and product-level stock-cover screening.
- Added synthetic demo inventory, data dictionary, and manual test plan.
- Added automated tests and development dependencies.
- Added repository branding, contribution guidance, MIT license, and deployment checklist.

This version is an early prototype and has not been validated for operational healthcare use.
