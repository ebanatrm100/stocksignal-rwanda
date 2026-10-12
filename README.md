<div align="center">
  <img src="assets/stocksignal-banner.svg" alt="STOCKSIGNAL — Turn inventory rows into clearer review signals" width="100%" />

  <h1>STOCKSIGNAL</h1>
  <p><strong>Turn inventory rows into clearer review signals.</strong></p>
  <p>A Rwanda-focused, human-in-the-loop prototype for reviewing medicine and health-commodity inventory data.</p>

  ![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
  ![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
  ![Project status](https://img.shields.io/badge/status-prototype-orange)
  ![Data](https://img.shields.io/badge/demo%20data-synthetic-087F86)
</div>

---

## Why STOCKSIGNAL?

Inventory teams can only act on what the records reveal. Missing values, stale updates, expiry dates, duplicate batch identifiers, and uncertain stock-cover estimates can make an inventory file harder to review.

**STOCKSIGNAL is a small, transparent review workspace** that reads a structured CSV and surfaces rule-based findings for a person to investigate. It is an early prototype for learning, demonstrations, and structured feedback—not a replacement for an electronic logistics management information system (eLMIS).

## What the prototype does

| Capability | What you can review |
|---|---|
| **Data-quality checks** | Missing fields, invalid numbers/dates, negative quantities or lead times, stale or future-dated updates |
| **Expiry review** | Expired batches and batches inside a configurable warning window |
| **Duplicate detection** | Repeated facility + product + batch keys |
| **Stock-cover screening** | Simple estimated days of stock compared with lead time plus a configurable buffer |
| **Downloadable findings** | Export row-level and product-level review results as CSV |
| **Configurable review date** | Test how date-based findings change as the analysis date changes |

The rules are visible in [`stocksignal.py`](stocksignal.py); the interactive interface is in [`app.py`](app.py). The calculation is deliberately simple and explainable rather than presented as AI or a predictive model.

## Run it locally

### 1. Get the project

Download this repository as a ZIP from GitHub and extract it, or clone it from your terminal after creating the repository:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/stocksignal-rwanda.git
cd stocksignal-rwanda
```

Replace `YOUR-GITHUB-USERNAME` with your GitHub username.

### 2. Install dependencies

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

### 3. Start the application

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux**

```bash
.venv/bin/python -m streamlit run app.py
```

Streamlit normally opens a browser at `http://localhost:8501`. That address is local to your computer. To make the app accessible when your terminal is closed and by people on other computers, deploy it to a hosting service; see [Deploy online](#deploy-online).

## Deploy online with Streamlit Community Cloud

1. Sign in at [GitHub](https://github.com/) and create a **public** repository named `stocksignal-rwanda` (public means the source code is visible).
2. Upload the contents of this project folder to the repository root. Check that `app.py`, `stocksignal.py`, `requirements.txt`, and `sample_inventory.csv` are at the top level.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) using your GitHub account.
4. Create an app and select your repository, the `main` branch, and `app.py` as the main file.
5. Deploy, then test the generated HTTPS `.streamlit.app` URL from an incognito window or another device.

Official guide: [Deploy a Streamlit app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

**Hosting note:** free Community Cloud apps can sleep after periods without traffic and may need to wake when opened. This does not guarantee uninterrupted 24/7 availability. A real deployment should also consider uptime, access control, privacy, security, and data-governance needs.

For a longer checklist, see [`README_DEPLOY.md`](README_DEPLOY.md). To upload the complete folder structure from Windows, follow [`GITHUB_UPLOAD_GUIDE.md`](GITHUB_UPLOAD_GUIDE.md).

## CSV format

Upload a CSV with these exact column names:

```text
facility_code
product_code
product_name
batch_number
quantity_on_hand
average_monthly_consumption
lead_time_days
expiry_date
last_stock_update
```

- Dates should use `YYYY-MM-DD` where possible.
- Quantity and consumption must use compatible units.
- The bundled [`sample_inventory.csv`](sample_inventory.csv) is **synthetic demonstration data** and intentionally contains examples of conditions the prototype can flag.
- Read [`data_dictionary.md`](data_dictionary.md) for field definitions and assumptions.

## How stock-cover screening works

The prototype estimates:

\[
\text{Estimated days of stock} = \frac{\text{eligible stock quantity}}{\text{average monthly consumption} / 30.4375}
\]

It then compares this estimate with:

\[
\text{Recorded lead time in days} + \text{review buffer}
\]

A result at or below that threshold is labelled for **human review**. It is not a reorder recommendation.

For a more conservative estimate, the current code excludes expired batches, batches with missing expiry dates, duplicate batch keys, missing facility/product/batch identifiers, invalid quantities, and negative quantities from the eligible stock quantity. These rows remain visible in row-level findings. Near-expiry batches are flagged but can still contribute while their expiry date is on or after the selected analysis date. The estimate does not model pending orders, seasonality, stock reservations, allocation, loss adjustments, demand spikes, supplier uncertainty, clinical criticality, or local policy.

## Tests

Run the automated tests with:

```bash
python -m pytest -q
```

Install the development dependencies first with `python -m pip install -r requirements-dev.txt`, then run the tests. The test suite covers sample-data checks, schema validation, configurable thresholds, expired/missing-expiry stock exclusion, duplicate batch handling, non-finite values, zero consumption, negative quantities, and inconsistent consumption values. A GitHub Actions workflow runs these tests on pushes and pull requests.

The manual demo checklist is in [`test_cases.md`](test_cases.md).

## Roadmap

- [ ] Collect feedback from authorised pharmacy / supply-chain reviewers using synthetic or approved de-identified test cases.
- [ ] Validate rule behaviour against independently reviewed test examples.
- [ ] Improve the explanation of excluded and uncertain stock records.
- [ ] Evaluate whether the workflow adds value alongside existing eLMIS processes before proposing integration.
- [ ] Complete privacy, security, access-control, and governance review before any real-data pilot.

These are future tasks, not claims of completed validation or integration.

## Safety and responsible use

> **Prototype only. Human review is required.**

- Do not upload patient information, credentials, confidential facility records, or real inventory data to this public demonstration.
- Do not use the output as an instruction to order, transfer, quarantine, dispense, or discard stock.
- A qualified, authorised person must verify the source data and follow approved procedures.
- Do not treat the estimate as a validated forecast or as evidence of improved medicine availability.
- The project does not replace eLMIS or any official system, supply-chain policy, or professional judgment.

See [`SECURITY.md`](SECURITY.md) before reporting an issue.

## Contributing

Issues and careful feedback are welcome, especially reproducible examples using synthetic data. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) first and never include confidential health or facility information in public issues.

## License

The code in this repository is available under the [MIT License](LICENSE). Third-party dependencies retain their own licenses.

---

<div align="center">
  <strong>STOCKSIGNAL</strong><br />
  <sub>Clearer review signals. Human decisions stay with authorised people.</sub>
</div>
