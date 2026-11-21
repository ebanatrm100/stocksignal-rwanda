# STOCKSIGNAL — competition demo guide

## The 20-second explanation

“StockSignal is a read-only inventory review prototype. It helps a reviewer spot data-quality issues, expiry concerns and simple stock-cover signals in a CSV export. Its additional snapshot-comparison workflow shows which batch records were added, changed or are no longer present between two exports. It supports human review; it does not replace eLMIS or make procurement or clinical decisions.”

## Suggested 4-minute demonstration

### 1. Introduce the problem (30 seconds)

Explain that inventory exports can contain missing fields, stale updates, duplicate batch identifiers, expiry concerns and unclear stock-cover signals. These issues make it harder for a person to know which records need checking.

### 2. Show the dashboard (45 seconds)

Open the official hosted app. Keep the synthetic sample selected. Point to the summary cards and explain that the counts are rule-based review signals, not measured health outcomes. Open the priority review list and show how a data conflict can block an unreliable stock-cover calculation.

### 3. Explain a record-level finding (40 seconds)

Choose one row and explain the visible reason for its flag. Emphasise that StockSignal shows evidence for a person to verify; it does not direct anyone to order, move, dispense, quarantine or discard stock.

### 4. Demonstrate snapshot comparison (75 seconds)

Open **06 / Inventory change intelligence**.

- Previous inventory export: `sample_snapshot_previous.csv`
- Latest inventory export: `sample_snapshot_latest.csv`

Show the expected result: 1 added, 1 not present in latest, 3 changed, 6 unchanged, 1 ambiguous duplicate key and 0 unmatchable rows. Open the record-level report and show a before-and-after quantity change. Explain that an absent record is not proof of a transfer, consumption or deletion; it only means the key is absent in that file.

Download the change report and comparison receipt only if time permits.

### 5. Mention the other prototypes honestly (30 seconds)

The frontline workflow area includes a verified-text observation draft, manual shelf mapping, a non-binding session-only coordination board and a ZIP field work kit for offline spreadsheet review. These are prototypes, not shared multi-user services, automatic speech transcription, RFID/IoT tracking or a standalone offline app.

### 6. Close with the next step (20 seconds)

“The next responsible step is to validate the rules with authorised supply-chain reviewers using approved test data, then assess interoperability with existing eLMIS processes. We are not claiming operational impact before that evaluation.”

## Likely judge questions

**Does StockSignal replace eLMIS?**

No. It is a read-only CSV review prototype. Existing inventory systems remain the system of record. Any future integration would need an approved technical and governance process.

**Is the stock-cover result an AI prediction?**

No. It is a transparent arithmetic screening estimate: eligible quantity divided by average daily consumption, compared with recorded lead time plus a configurable review buffer. It does not model future demand or supplier uncertainty.

**Is the voice feature automatic transcription?**

No. A user may record an audio memo, but the prototype requires a person to enter or verify the text. The parser uses cautious text rules to prepare a draft.

**Are shelf locations connected to smart shelves or RFID?**

No. The prototype lets a user manually assign rows to cells on a demonstration grid. It has no sensor or RFID connection.

**Can multiple facilities see the swap board together?**

No. Offers and expressions of interest are temporary session data. The board does not approve transfers, check clinical equivalence, reserve stock or arrange transport.

**Is there an offline app?**

No. The ZIP is a portable work kit for spreadsheet review. The hosted app needs internet, and there is no automatic sync or conflict resolution.

**Has StockSignal reduced stockouts or medicine waste?**

That has not been measured. The prototype has not completed an authorised field evaluation, so no real-world impact claim should be made.

**How will real inventory data be protected?**

The public demonstration uses synthetic data only. A real pilot would require authorised access, privacy and security review, role controls, retention rules and local approval before any confidential data is processed.

## Presentation checklist

- [ ] Open the official `.streamlit.app` URL before the presentation and verify it loads.
- [ ] Confirm the snapshot-comparison section is visible.
- [ ] Keep the two synthetic snapshot CSV files available locally.
- [ ] Test the comparison once and confirm the expected counts.
- [ ] Keep the comparison report available as a backup demonstration artifact.
- [ ] Do not upload real facility records or patient information.
- [ ] Do not claim AI forecasting, eLMIS integration, RFID, automatic speech transcription, persistent audit history, multi-user sync or proven health impact.
- [ ] Have a short verbal explanation ready in case the internet connection fails.
