# Deploy STOCKSIGNAL online

This checklist deploys the Streamlit prototype so it can be opened from other computers without leaving your personal terminal running.

## 1. Create the GitHub repository

1. Go to [GitHub](https://github.com/) and sign in.
2. Create a repository named `stocksignal-rwanda`.
3. Choose **Public** only if you are comfortable making the source code visible. Never commit passwords, API keys, or confidential/real health-facility data.
4. Upload the contents of this folder to the repository root. Ensure `app.py`, `stocksignal.py`, `requirements.txt`, and `sample_inventory.csv` are at the top level.

## 2. Deploy through Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app** / **Deploy an app**.
3. Select repository `stocksignal-rwanda`, branch `main`, and main file path `app.py`.
4. Deploy and wait for the build to finish.
5. Copy the HTTPS URL ending with `.streamlit.app`.
6. Test that URL in a private/incognito browser window and on another device, where possible.

Official guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## 3. Important distinctions

- `http://localhost:8501` is the local development address. It is not a public link.
- After a successful cloud deployment, the cloud host runs the app independently of your terminal.
- Free Community Cloud apps can sleep when unused; do not promise uninterrupted 24/7 availability.
- The code and sample records are a prototype. Do not upload confidential inventory, patient information, or real facility records to a public demo.
- Deployment does not validate the rules for operational use or establish approval to integrate with an eLMIS.

## Troubleshooting

- **`ModuleNotFoundError` during build:** check that `requirements.txt` is in the repository root and includes every dependency.
- **`FileNotFoundError` for sample data:** confirm `sample_inventory.csv` is at the same level as `app.py`.
- **App says it cannot find `app.py`:** set the Streamlit main file path to exactly `app.py`.
- **The app works locally but not after deployment:** open the deployment logs in Streamlit Community Cloud and resolve the first reported error.
