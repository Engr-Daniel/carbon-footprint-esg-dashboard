# AGENTS.md

Instructions for AI coding agents (Claude, Copilot, Codex, etc.) and human collaborators working in this repository.

## Project at a glance
A GHG Protocol-based carbon accounting pipeline plus a Streamlit ESG dashboard. It is a personal portfolio project by Daniel Oyewale, aimed at data analysis, data strategy and sustainability roles.

**Always read `MEMORY.md` (context & decisions) and `TASK.md` (current priorities) before starting work.**

## Setup & commands
```bash
pip install -r requirements-dev.txt   # dashboard only: requirements.txt
pytest -q                               # run tests (must pass before committing)
streamlit run app/streamlit_app.py      # run the dashboard
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
python src/carbon/report_figures.py     # regenerate README charts
python src/carbon/exec_report.py        # regenerate the executive summary PDF
```

## Code map
| Path | Purpose |
|---|---|
| `src/carbon/emissions.py` | Calculation engine. All emissions maths lives here. |
| `src/carbon/scenarios.py` | Levers, MACC costs, phased pathways + uncertainty, sensitivity, intensity, dual Scope 2 with instrument quality checks |
| `src/carbon/grid_factor.py` | Derivation of the scope-split Nigeria grid factor (CSV must match; a test enforces it) |
| `src/carbon/exec_report.py` | Builds `reports/executive_summary.pdf` from live model numbers |
| `tests/test_regression.py` | Pinned headline numbers. Update them deliberately, together with README/MEMORY/PDF |
| `data/reference/reduction_levers.csv`, `cost_assumptions.csv` | Scenario inputs. Every assumption needs a source or "Assumption" label |
| `src/carbon/report_figures.py` | Exports README/report charts to `reports/figures/` (re-run after changing data or factors) |
| `app/streamlit_app.py` | Dashboard UI only. It must not contain calculation logic. |
| `data/reference/emission_factors.csv` | Emission factor library (single source of truth) |
| `data/sample/` | Synthetic demo data (committed) |
| `data/raw/`, `data/processed/` | Real or large data (git-ignored, never commit) |
| `sql/schema.sql` | Relational model that mirrors the CSV structure |
| `docs/methodology.md` | Scopes, boundaries, assumptions |

## Rules
1. **Accuracy first.** Every emission factor needs a `source` and `unit`. Factors are keyed by `activity_type` + `component` (`primary` / `wtt` / `td_losses`), and each component must sit in the correct scope. Never invent factors. If you're unsure, mark it `VERIFY` in `notes`.
2. **Units must match** between activity data and factors. The engine raises an error otherwise, so don't bypass that check.
3. **Keep logic in `src/`.** Notebooks and the app import from `carbon` and never re-implement formulas.
4. **Test what you add.** New calculation functions need tests in `tests/`.
5. **Label synthetic data clearly** in charts, README and the app.
6. **No secrets or real client data** in the repo. Use `.env` and `.streamlit/secrets.toml`, which are git-ignored.
7. **Style:** Python 3.10+, type hints, small pure functions, descriptive names, docstrings on public functions.
8. **Docs:** If you change the scope, boundary or factors, update `docs/methodology.md` and the README findings.
9. **After each work session:** tick off items in `TASK.md` and add any key decision to `MEMORY.md`.

## Commit conventions
Use conventional commits: `feat:`, `fix:`, `docs:`, `data:`, `test:`, `refactor:`, `chore:`.

## Git attribution
Never add `Co-Authored-By`, `Claude-Session` or other AI attribution lines to commits or PRs (see CLAUDE.md).
