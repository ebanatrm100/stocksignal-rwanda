
## Snapshot comparison fields and interpretation

The separate snapshot comparison matches records using the three-part identity key `facility_code` + `product_code` + `batch_number`. It compares product name, quantity on hand, average monthly consumption, lead time, expiry date and last stock-update date for matching identities.

- **Added in current snapshot:** a complete identity appears only in the newer file.
- **Not present in current snapshot:** a complete identity in the previous file is absent from the newer file. This does not explain why it is absent.
- **Record changed:** one or more compared fields differ for a unique matching identity.
- **Ambiguous duplicate key:** the same identity appears more than once in either file; the comparator does not guess which row corresponds to which.
- **Unmatchable row:** one or more identity fields are missing, so the row cannot be matched safely.

The comparison is read-only and runs in the current app session. Its downloadable receipt is not a persistent database, cryptographic proof or tamper-proof audit history.
