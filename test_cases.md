# STOCKSIGNAL test plan

## Automated tests

Run from the repository root:

```bash
python -m pytest -q
```

The automated suite checks core rule behaviour and safety-minded eligibility for stock-cover calculations. GitHub Actions runs it on pushes and pull requests.

## Manual demo checks

| ID | Input or action | Expected behaviour | What it checks |
|---|---|---|---|
| T01 | Load the bundled sample CSV | App displays records, metrics, and review findings | Main workflow |
| T02 | Upload a CSV missing `expiry_date` | Clear required-column error | Schema validation |
| T03 | Use quantity `-6` | Negative quantity is flagged and excluded from cover | Numeric validation |
| T04 | Repeat a facility/product/batch key | Both rows are flagged and excluded from cover | Duplicate detection |
| T05 | Use a stock update older than the configured threshold | Stale update is flagged | Record freshness |
| T06 | Set expiry before analysis date | Expired batch is flagged and excluded from cover | Expiry handling |
| T07 | Set expiry inside warning window | Near-expiry batch is flagged | Configurable expiry warning |
| T08 | Set monthly consumption to zero | Cover is not calculated | Divide-by-zero protection |
| T09 | Use cover at/below lead time + buffer | Product is labelled for human review | Screening rule |
| T10 | Export row or product review | Downloaded CSV contains review fields | Export behaviour |
| T11 | Change the analysis date | Date-based findings update | Date control |
| T12 | Use malformed numeric/date values | Invalid values are flagged | Input validation |
| T13 | Use a non-finite numeric value such as `inf` | Value is flagged and excluded from cover | Numeric robustness |
| T14 | Leave expiry blank | Batch is flagged and excluded from cover | Unknown expiry handling |

## Suggested user validation (future work)

With approval, ask a small group of authorised supply-chain reviewers to test the interface using synthetic or approved de-identified examples. Measure whether they understand flags, can find the evidence behind each flag, and identify false positives or missed cases. Do not use this small exercise to claim improved medicine availability or reduced losses; those outcomes require appropriately designed evaluation.
