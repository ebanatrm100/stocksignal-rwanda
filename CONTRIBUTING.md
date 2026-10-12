# Contributing to STOCKSIGNAL

Thank you for helping improve this prototype. Small, evidence-backed contributions are welcome.

## Good first contributions

- Report a confusing message or reproducible rule issue using synthetic data.
- Improve documentation or accessibility.
- Add focused tests for edge cases.
- Suggest a workflow improvement that keeps human review central.

## Before opening a pull request

1. Create an issue or explain the specific problem your change solves.
2. Keep rule behaviour explicit and understandable; avoid presenting heuristics as validated predictions.
3. Add or update tests for changes to analysis logic.
4. Run `python -m pytest -q` from the project root.
5. Update `README.md`, `data_dictionary.md`, or `test_cases.md` when assumptions or behaviour change.

## Data and privacy rules

Use only synthetic or approved de-identified examples. Never commit patient records, real facility inventory, personal information, passwords, access tokens, or other confidential data. Public GitHub issues are visible to others; describe problems without disclosing sensitive details.

Contributions are reviewed on a best-effort basis. Opening a pull request does not guarantee acceptance or deployment.
