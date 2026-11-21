# STOCKSIGNAL — existing hosted deployment

The current public demonstration is:

**https://stocksignal-rwanda-regis.streamlit.app**

It is connected to the GitHub repository `ebanatrm100/stocksignal-rwanda`, branch `main`, with `app.py` as the application entry point.

## Publishing an update

1. Make and test changes on a separate Git branch.
2. Push the branch to `ebanatrm100/stocksignal-rwanda`.
3. Open a pull request targeting `main` and review the file changes.
4. Merge only after local tests pass and any applicable GitHub checks are successful.
5. Open the app's deployment page in Streamlit Community Cloud and confirm that the latest `main` commit has finished deploying.
6. Open the official URL in a private/incognito window or on another device and test the changed feature.

A merge into `main` triggers deployment when the Streamlit app is correctly connected and automatic deployment is enabled. Do not assume the update is live until Streamlit reports a successful deployment and you have tested the public URL.

## Important distinctions

- `http://localhost:8501` is local to the computer running Streamlit.
- The `.streamlit.app` address is the hosted app and can be opened on another device with internet access.
- Free hosted apps may sleep when unused and may take time to wake. Do not promise uninterrupted availability.
- The repository and demo are public. Use fabricated examples only; never upload patient details, credentials or confidential facility inventory.
- Deployment does not validate the business rules for operational healthcare use or authorise integration with eLMIS.

## Troubleshooting

- **App still shows an older version:** check the Streamlit deployment logs and confirm the deployed commit matches the latest `main` commit.
- **Missing Python package:** confirm the dependency is listed in root `requirements.txt` and inspect the first deployment error.
- **Missing sample file:** confirm the CSV is tracked in the repository root beside `app.py`.
- **Works locally but not in the cloud:** inspect the Streamlit logs; local success alone does not prove the hosted build succeeded.
