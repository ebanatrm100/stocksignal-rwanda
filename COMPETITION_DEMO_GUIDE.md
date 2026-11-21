# STOCKSIGNAL — competition demonstration guide

## The 20-second explanation

“StockSignal is a read-only inventory review prototype. It helps a reviewer spot data-quality issues, expiry concerns and simple stock-cover signals in a CSV export. Its snapshot-comparison workflow shows which batch records were added, changed or are no longer present between two exports. It also offers explainable what-if calculations and a limited GS1 barcode text parser. It supports human review; it does not replace eLMIS or make procurement or clinical decisions.”

## Suggested 5-minute demonstration

### 1. Introduce the problem (30 seconds)

Explain that inventory exports can contain missing fields, stale updates, duplicate batch identifiers, expiry concerns and unclear stock-cover signals. These issues make it harder for a person to know which records need checking.

### 2. Show the dashboard (45 seconds)

Open the official hosted app. Keep the synthetic sample selected. Point to the summary cards and explain that the counts are rule-based review signals, not measured health outcomes. Open the priority review list and show how a data conflict can block an unreliable stock-cover calculation.

### 3. Show a record-level finding (40 seconds)

Choose one row and explain the visible reason for its flag. Emphasise that StockSignal shows evidence for a person to verify; it does not direct anyone to order, move, dispense, quarantine or discard stock.

### 4. Demonstrate snapshot comparison (75 seconds)

Open **06 / Inventory change intelligence**.

- Previous inventory export: `sample_snapshot_previous.csv`
- Latest inventory export: `sample_snapshot_latest.csv`

Show the expected result: 1 added, 1 not present in latest, 3 changed, 6 unchanged, 1 ambiguous duplicate key and 0 unmatchable rows. Open the record-level report and show a before-and-after quantity change. Explain that an absent record is not proof of a transfer, consumption or deletion; it only means the key is absent in that file.

Download the change report and comparison receipt. Point out that the receipt includes file SHA-256 fingerprints. Explain accurately: a hash helps identify exact file bytes, but does not prove who created the file or create a signed audit trail.

### 5. Demonstrate the intelligence helpers (60 seconds)

Open **07 / Data intelligence**. Show the per-field completeness profile and explain why StockSignal reports missing values by field rather than inventing one overall quality score. Then open the what-if simulator, select a product with a calculated baseline, increase the assumed consumption and add a delivery delay. Explain that the display is arithmetic sensitivity analysis, not AI forecasting or a procurement instruction.

### 6. Demonstrate GS1 text capture (45 seconds)

Open **08 / GS1 traceability**. Paste this synthetic example:

```text
(01)09506000134352(17)270630(10)LOT-A123
```

Show the parsed GTIN, expiry date and batch/lot as a draft. Explain that the prototype parses only selected GS1 text fields and still requires a person to verify the original package. It does not decode camera images, query a product catalogue or verify package authenticity.

### 7. Mention the other prototypes and close (45 seconds)

The frontline workflow area includes a verified-text observation draft, manual shelf mapping, a non-binding session-only coordination board and a ZIP field work kit for offline spreadsheet review. These are prototypes, not shared multi-user services, automatic speech transcription, RFID/IoT tracking or a standalone offline app.

“The next responsible step is to validate these tools with authorised supply-chain reviewers using approved test data, then assess interoperability with existing eLMIS processes. We are not claiming operational impact before that evaluation.”

## Likely judge questions

**Does StockSignal replace eLMIS?**

No. It is a read-only CSV review prototype. Existing inventory systems remain the system of record. Any future integration would need an approved technical and governance process.

**Is the stock-cover result an AI prediction?**

No. It is a transparent arithmetic screening estimate: eligible quantity divided by average daily consumption, compared with recorded lead time plus a configurable review buffer. The scenario simulator changes only user-entered assumptions. It does not model future demand or supplier uncertainty.

**What does the GS1 function do?**

It parses selected GS1 Application Identifier text values: GTIN-14 (01), batch/lot (10), expiry date (17) and serial (21). It is not an image decoder, product master lookup or authenticity check. Every parsed field must be checked against the package and local master data.

**Is the file receipt a tamper-proof audit log?**

No. SHA-256 fingerprints identify exact file bytes. The receipt is downloadable and editable; it is not digitally signed, centrally stored or tamper-proof.

**Is the voice feature automatic transcription?**

No. A user may record an audio memo, but the prototype requires a person to enter or verify the text. The parser uses cautious text rules to prepare a draft.

**Are shelf locations connected to smart shelves or RFID?**

No. The prototype lets a user manually assign rows to cells on a demonstration grid. It has no sensor or RFID connection.

**Can multiple facilities see the coordination board together?**

No. Offers and expressions of interest are temporary session data. The board does not approve transfers, check clinical equivalence, reserve stock or arrange transport.

**Has StockSignal reduced stockouts or medicine waste?**

That has not been measured. The prototype has not completed an authorised field evaluation, so no real-world impact claim should be made.

## Presentation checklist

- [ ] Open the official `.streamlit.app` URL before the presentation and verify it loads.
- [ ] Confirm the snapshot-comparison section is visible.
- [ ] Keep the two synthetic snapshot CSV files available locally.
- [ ] Test the comparison once and confirm the expected counts.
- [ ] Test the scenario simulator with a synthetic product.
- [ ] Test the GS1 text example above.
- [ ] Keep downloaded reports available as backup demonstration artifacts.
- [ ] Do not upload real facility records or patient information.
- [ ] Do not claim AI forecasting, eLMIS integration, RFID, automatic speech transcription, persistent audit history, multi-user sync or proven health impact.
- [ ] Have a short verbal explanation ready in case the internet connection fails.
