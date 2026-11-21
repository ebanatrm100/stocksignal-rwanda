
## Inventory snapshot comparison checks

| ID | Input or action | Expected behaviour | What it checks |
|---|---|---|---|
| T15 | Compare the bundled previous and latest synthetic snapshots | 1 added, 1 absent, 3 changed, 6 unchanged, 1 ambiguous key and 0 unmatchable rows | End-to-end snapshot example |
| T16 | Change quantity for a matching facility/product/batch key | One changed record with before and after values | Field-level comparison |
| T17 | Add a new unique batch key to the latest export | One added record | Added-key detection |
| T18 | Remove a unique batch key from the latest export | One not-present record, without inferring the reason | Missing-key semantics |
| T19 | Duplicate a key in either export | Key is marked ambiguous and not automatically matched | Duplicate safety |
| T20 | Remove a facility, product or batch identifier | Row is reported as unmatchable | Incomplete-identity handling |
