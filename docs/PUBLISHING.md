# Publishing checklist

Steps to take the project from private repo to public portfolio piece. Items marked **(you)** need the repo owner.

## 1. Final checks (done in CI)
- [x] `pytest -q` passes (unit and regression tests)
- [x] Dashboard smoke test and notebooks execute in GitHub Actions (`.github/workflows/tests.yml`)
- [x] Executive summary regenerated: `python src/carbon/report_figures.py && python src/carbon/exec_report.py`
- [x] Synthetic data is labelled in the README, dashboard, charts and PDF

## 2. Make the repo public (you)
1. GitHub → repo → **Settings** → scroll to **Danger Zone** → **Change repository visibility** → **Public**.
2. Repo home page → ⚙️ next to **About** → add the description, the topics, and (after step 3) the dashboard URL as the website.
3. Your profile → **Customize your pins** → pin this repo.

## 3. Deploy the dashboard on Streamlit Community Cloud (you, ~3 minutes)
1. Go to <https://share.streamlit.io> and **sign in with GitHub**.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Fill in:
   - Repository: `Engr-Daniel/carbon-footprint-esg-dashboard`
   - Branch: `master`
   - Main file path: `app/streamlit_app.py`
   - App URL (optional): e.g. `econaija-carbon`
   - **Advanced settings → Python version: 3.11 or newer**
4. Click **Deploy**. The first build takes a few minutes while it installs `requirements.txt`.
5. Copy the app URL and send it to Claude. It will be added to the README badge and the repo website field.

### If the app keeps loading ("in the oven" / spinning)
1. On the app page, open **Manage app** (bottom-right) to see the build log.
2. Check that `requirements.txt` contains only the 4 runtime packages (pandas, numpy, plotly, streamlit). Dev tools live in `requirements-dev.txt`.
3. **⋮ → Reboot app** after any requirements change. The first build takes a few minutes.
4. Free apps sleep after inactivity. Click **"Yes, get this app back up"** to wake one; it takes ~30 s.

> Private repos can also be deployed, but recruiters can't see the code then, so make the repo public first.

## 4. Share it (you)
- Attach `reports/executive_summary.pdf` to applications and proposals.
- Post on LinkedIn (draft below) with the dashboard link and 2–3 images: `05_macc_curve.png`, `06_decarbonisation_pathway.png`, `dashboard_scenarios.png`.

### LinkedIn post draft
> **What would it take for a Nigerian manufacturer to get on a science-based emissions pathway, and would it pay?**
>
> I built an end-to-end carbon accounting and decarbonisation model to find out, using a fictional company (EcoNaija Manufacturing Ltd, 3 sites) with real 2026 emission factors and Nigerian energy prices.
>
> What the model shows:
> 🔹 Scope 3 is over half the footprint, so supplier data is the biggest accuracy lever
> 🔹 4 of 9 reduction levers are *cost-negative*. A solar-battery hybrid replacing diesel generators pays back in ~2 years at today's diesel prices
> 🔹 Physical measures alone cut ~21%, which isn't enough for an SBTi-aligned 2030 target without quality-assured renewable electricity contracts
> 🔹 The portfolio stays cash-positive in every sensitivity case I tested (FX, diesel, tariffs, capex, effectiveness)
>
> Under the hood: Python carbon engine (GHG Protocol), DESNZ 2026 factors verified against the official workbook, a derived Scope 2 factor for the Nigerian grid, a marginal abatement cost curve, an SBTi pathway with uncertainty bands, and a Streamlit dashboard where you can change the assumptions yourself.
>
> 📊 Live dashboard: https://carbon-footprint-esg-dashboard.streamlit.app/
> 💻 Code & methodology: https://github.com/Engr-Daniel/carbon-footprint-esg-dashboard
>
> Feedback from ESG and energy practitioners very welcome, especially on Nigerian grid and Scope 3 data sources.
>
> #ESG #Sustainability #CarbonAccounting #DataAnalytics #NetZero #Nigeria #ClimateAction #Petgrave
