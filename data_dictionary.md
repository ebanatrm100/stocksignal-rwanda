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

## Snapshot comparison fields and interpretation

The separate snapshot comparison matches records using the three-part identity key `facility_code` + `product_code` + `batch_number`. It compares product name, quantity on hand, average monthly consumption, lead time, expiry date and last stock-update date for matching identities.

- **Added in current snapshot:** a complete identity appears only in the newer file.
- **Not present in current snapshot:** a complete identity in the previous file is absent from the newer file. This does not explain why it is absent.
- **Record changed:** one or more compared fields differ for a unique matching identity.
- **Ambiguous duplicate key:** the same identity appears more than once in either file; the comparator does not guess which row corresponds to which.
- **Unmatchable row:** one or more identity fields are missing, so the row cannot be matched safely.

The comparison is read-only and runs in the current app session. Its downloadable receipt is not a persistent database, cryptographic proof or tamper-proof audit history.

## Competition intelligence helpers

### Field completeness profile

The profile reports, for each of the nine required columns, the number of present values, missing/blank values and percentage completeness. It intentionally does not combine these fields into an unexplained overall score. A complete field is not necessarily a correct or current value; use it alongside row-level validation flags.

### What-if scenario simulator

The simulator recalculates the arithmetic stock-cover estimate under user-selected changes to monthly consumption and lead time. It uses the same 30.4375-days-per-month convention and compares the resulting estimate with lead time + review buffer. It does not forecast actual demand, model supplier behaviour, or recommend procurement actions. Source records are not changed.

### GS1 barcode text capture

The prototype parser accepts GS1 human-readable text in parentheses form or a scanner's GS1 element string for these Application Identifiers:

| AI | Meaning | Parsed output |
|---|---|---|
| `01` | Global Trade Item Number (GTIN-14) | `gtin` |
| `10` | Batch/lot number (variable length, up to 20 characters) | `batch_number` |
| `17` | Expiry date (`YYMMDD`) | `expiry_date` as `YYYY-MM-DD` |
| `21` | Serial number (variable length, up to 20 characters) | `serial_number` |

For scanner element strings, a GS1 group separator (ASCII 29 / FNC1 separator) is required to delimit a variable-length AI when another element follows it. The parser validates the GTIN-14 check digit and parses only the listed AIs; it does not decode barcode images, resolve product catalogues, establish product identity in a local system, or verify a label's authenticity. Parsed values are a draft and require visual confirmation against the source packaging and local product master.

References: [GS1 Application Identifiers](https://ref.gs1.org/ai/) and [GS1 General Specifications](https://ref.gs1.org/standards/genspecs/).

### Snapshot file fingerprints

The comparison receipt includes SHA-256 digests of the uploaded file bytes. The digest helps distinguish exact file versions and detect byte-level changes when a file is checked again. It does not prove who created a file, when the source system exported it, or that the receipt itself has not been edited. It is not a signed or tamper-proof audit trail.
