# Upload this project to GitHub (Windows)

This folder is already arranged as a GitHub repository. Keep the folder structure intact so the app, tests, banner, and automated test workflow all work together.

## Option A — Recommended for beginners: GitHub Desktop

1. Create a new repository at [github.com/new](https://github.com/new) named `stocksignal-rwanda`. Choose **Public** if you want judges to inspect the code. Do not initialize it with another README, license, or `.gitignore`, because these are included in this project.
2. Install and open [GitHub Desktop](https://desktop.github.com/), then sign in to your GitHub account.
3. In GitHub Desktop, choose **File → Clone repository**, select the `stocksignal-rwanda` repository from your GitHub account, and choose a local folder.
4. Extract the STOCKSIGNAL repository ZIP you downloaded. Open the extracted `StockSignal_GitHub_Repository` folder, select **all** its contents (including hidden `.gitignore`, `.github`, and `.streamlit` items), and copy them into the cloned `stocksignal-rwanda` folder. Merge folders if Windows asks.
5. In GitHub Desktop, review the changed-file list. Enter a summary such as `Add STOCKSIGNAL prototype`, click **Commit to main**, and then click **Push origin**.
6. Open the repository on GitHub and confirm the README banner appears and `app.py`, `stocksignal.py`, and `requirements.txt` are visible at the top level.

## Option B — Use Git commands

If Git is installed, create an empty repository named `stocksignal-rwanda` on GitHub, open PowerShell in the extracted `StockSignal_GitHub_Repository` folder, then run:

```powershell
git init
git add .
git commit -m "Add STOCKSIGNAL prototype"
git branch -M main
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/stocksignal-rwanda.git
git push -u origin main
```

Replace `YOUR-GITHUB-USERNAME` with your GitHub username. Git may ask you to authenticate through a browser or credential manager.

## After upload

Follow [`README_DEPLOY.md`](README_DEPLOY.md) to deploy the app to Streamlit Community Cloud. A GitHub repository URL and a live `.streamlit.app` URL are different links; the live URL exists only after deployment succeeds.
