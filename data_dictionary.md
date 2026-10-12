# STOCKSIGNAL CSV data dictionary

The prototype expects a CSV with the exact column names below. `sample_inventory.csv` contains fabricated demonstration records only.

| Column | Expected type | Meaning | Notes and validation |
|---|---|---|---|
| `facility_code` | Text | Pseudonymous facility/location identifier | Required. Missing identifiers prevent a row from contributing to product stock cover. |
| `product_code` | Text | Commodity/product identifier | Required. Treat as a local identifier; the app does not infer clinical equivalence. |
| `product_name` | Text | Display name for an inventory item | Required for record quality, but not used to group products. |
| `batch_number` | Text | Batch/lot identifier | Required. Duplicate facility + product + batch keys are flagged and excluded from stock-cover quantity. |
| `quantity_on_hand` | Number | Recorded quantity on hand | Must use consistent units. Missing, invalid, non-finite, and negative quantities are excluded from stock-cover quantity. |
| `average_monthly_consumption` | Number | Reported average amount used per month | Must be comparable with the quantity unit. Negative/invalid values are flagged; zero prevents a cover calculation. Different values for the same facility/product are flagged. |
| `lead_time_days` | Number | Expected replenishment lead time in days | Negative/invalid values are flagged. The maximum non-negative value across a facility/product group is used as a simple screening assumption. |
| `expiry_date` | Date (`YYYY-MM-DD`) | Expiry date for the batch | Missing/invalid/expired rows are excluded from stock-cover quantity. Expiry warnings do not determine whether an item is safe to dispense. |
| `last_stock_update` | Date (`YYYY-MM-DD`) | Date stock record was last updated | Dates after the analysis date or older than the configured freshness threshold are flagged. |

## Interpretation and assumptions

- Product grouping uses `facility_code` + `product_code`.
- A batch contributes to eligible stock quantity only when the facility/product/batch identity is present and unique, quantity is valid and non-negative, and a valid expiry date is on or after the selected analysis date.
- Duplicate rows, expired batches, missing-expiry batches, missing identities, and invalid/negative quantities remain visible for review but do not contribute to estimated stock cover.
- Average monthly consumption is summarized using the median of valid non-negative values in the facility/product group. Conflicting values are flagged because they reduce confidence in the estimate.
- Lead time is summarized using the maximum valid non-negative value in the group. Validate this rule with intended users before relying on it.
- Estimated days of stock = eligible stock quantity / (average monthly consumption / 30.4375).
- A review flag is produced when estimated cover is at or below lead time + the configurable buffer.

This does not include pending orders, seasonality, reservations, allocation, losses, demand spikes, service criticality, supplier uncertainty, or local policy. It is a transparent rule-based screening estimate, not a validated forecast or an official procurement threshold.

**Responsible use:** never treat demo results as an instruction to order, transfer, quarantine, dispense, or discard stock. An authorised person must verify all records and follow approved procedures. Do not put confidential health-facility or patient information into the public demo.
