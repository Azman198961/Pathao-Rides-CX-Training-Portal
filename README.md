# Pathao Rides — CX Training Portal

A small Streamlit app for the CX Complaint Management Team, with two parts:

- **Induction Training** — calendar view; add a topic, assignment, task,
  trainee, score and an optional assignment file for any day.
- **Refresher Training** — agents enter their email + Employee ID, pick a
  topic, work through it, and mark it complete. Every completion is logged.

Both sections support **Excel export** and the admin side is protected by a
**password**. Data is stored in a local SQLite file (`training_portal.db`).

## Run locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml and set your real admin_password
streamlit run app.py
```

## Deploy for free — GitHub + Streamlit Community Cloud

1. Create a new **GitHub repository** and push this folder to it.
   Do **not** commit `.streamlit/secrets.toml` or `training_portal.db` —
   the included `.gitignore` already excludes both.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, and click **New app**.
3. Pick your repo, branch (`main`), and set the main file path to `app.py`.
4. Before/after deploying, open the app's **Settings → Secrets** and add:
   ```toml
   admin_password = "your-real-password-here"
   ```
5. Deploy. Share the resulting `*.streamlit.app` link with your team.

### A note on data persistence

Streamlit Community Cloud's filesystem is **ephemeral** — `training_portal.db`
survives while the app stays up, but a redeploy or a long idle-restart can
reset it. This is fine to start with for a small team. If you later need the
data to survive redeploys permanently, swap the functions in `db.py` for
calls to a free hosted database (e.g. Supabase Postgres, or a Google Sheet
via `gspread`) — `app.py` only calls the functions in `db.py`, so nothing
else needs to change.

## Editing

- Colors/theme: `.streamlit/config.toml`
- All data logic: `db.py`
- All screens/behavior: `app.py`
- Admin password: Streamlit Cloud → Settings → Secrets (or local
  `.streamlit/secrets.toml`)

Fully open source — MIT-license this repo however you'd like once it's on
GitHub.
