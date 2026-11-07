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
> **Could a Nigerian manufacturer cut emissions in line with science-based rates and save money doing it?**
>
> I built an end-to-end carbon accounting and decarbonisation model to find out. It uses a fictional manufacturer (EcoNaija, 3 sites) with synthetic activity data, but **real** 2026 emission factors and Nigerian energy prices.
>
> What the model shows:
> 🔹 **63% of the footprint is in the value chain (Scope 3)**. Steel and plastic resin alone are ~29%, so supplier data matters more than anything on site
> 🔹 **4 of 9 reduction levers save money**. A solar-battery hybrid replacing diesel generators pays back in ~2 years at today's diesel prices
> 🔹 The plan stays **cash-positive in every sensitivity case** I tested (FX, diesel, tariffs, capex, lever performance)
> 🔹 Physical measures cut ~18%. Keeping pace with SBTi's minimum reduction rates by 2030 also needs **quality-assured renewable electricity contracts**
>
> What I care about most is that the numbers hold up:
> ✅ DESNZ 2026 factors verified cell-by-cell against the official workbook
> ✅ A scope-correct Nigerian grid factor (estimated, with its uncertainty range shown)
> ✅ Spend mapped to 10 US EPA categories and inflation-adjusted
> ✅ Market-based Scope 2 claims screened against GHG Protocol quality criteria
> ✅ Every restatement documented, plus 37 automated tests on each change
>
> 📊 Live dashboard: https://carbon-footprint-esg-dashboard.streamlit.app/
> 💻 Code, methodology & 2-page executive summary: https://github.com/Engr-Daniel/carbon-footprint-esg-dashboard
>
> Built with Python, SQL, Streamlit and the GHG Protocol. Feedback from ESG and energy practitioners is very welcome, especially on Nigerian grid and supplier emissions data.
>
> *Illustrative case study. The pathway benchmarks against SBTi minimum rates and is not a validated target.*
>
> #ESG #Sustainability #CarbonAccounting #DataAnalytics #NetZero #Nigeria #ClimateAction
