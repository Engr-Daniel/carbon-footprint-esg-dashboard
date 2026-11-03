# 🌍 Carbon Footprint & ESG Dashboard

End-to-end **Scope 1, 2 & 3 greenhouse gas (GHG) emissions analysis** and an **interactive ESG dashboard**, built on the [GHG Protocol Corporate Standard](https://ghgprotocol.org/corporate-standard). The case study is set in Nigeria.

> ⚠️ **Demo data:** The current dataset is **synthetic** and belongs to a fictional company, *EcoNaija Manufacturing Ltd* (3 sites, 2023–2025). The emission factors are **indicative** and must be checked against the latest official releases before any real-world use.

---

## 📌 Business Problem
Investors, regulators and buyers are asking more and more for credible emissions disclosures. Examples include IFRS S2 / ISSB, the Nigerian SEC sustainability disclosure roadmap and supply-chain requirements. Many organisations, especially SMEs in Africa, lack a transparent and repeatable way to:
1. **Measure** their carbon footprint across all three scopes
2. **Identify hotspots** where reductions matter most
3. **Track progress** against reduction targets

This project provides a lightweight, auditable carbon accounting pipeline and a dashboard that answers all three questions.

## 🎯 Objectives
- Build a reusable emissions calculation engine (activity data × emission factor)
- Model the data relationally (SQL) for scalability
- Find emission hotspots by scope, category and site
- Track performance against a science-aligned reduction target
- Turn the findings into actionable decarbonisation recommendations

## 🗂️ Project Structure
```
carbon-footprint-esg-dashboard/
├── app/
│   └── streamlit_app.py          # Interactive dashboard
├── data/
│   ├── raw/                      # Raw inputs (git-ignored)
│   ├── processed/                # Cleaned outputs (git-ignored)
│   ├── reference/
│   │   └── emission_factors.csv  # Emission factor library
│   └── sample/
│       └── activity_data_sample.csv  # Synthetic activity data
├── docs/
│   └── methodology.md            # Boundaries, scopes, assumptions
├── notebooks/
│   └── 01_exploratory_analysis.ipynb
├── reports/figures/              # Exported charts
├── sql/
│   └── schema.sql                # Relational data model + views
├── src/carbon/
│   └── emissions.py              # Calculation engine
├── tests/
│   └── test_emissions.py         # Unit tests (pytest)
├── AGENTS.md                     # Guide for AI coding agents / collaborators
├── MEMORY.md                     # Project decisions & context log
├── TASK.md                       # Roadmap & task tracker
└── requirements.txt
```

## 🧮 Methodology (summary)
| Scope | What it covers | Activities in this project |
|---|---|---|
| **Scope 1** | Direct emissions from owned or controlled sources | Diesel generators, fleet fuel, natural gas, LPG, refrigerant leaks |
| **Scope 2** | Indirect emissions from purchased energy | Grid electricity (Nigeria grid factor) |
| **Scope 3** | Other value-chain emissions | Purchased goods (spend-based), business travel, commuting, waste |

**Formula:** `tCO2e = activity quantity × emission factor (kgCO2e/unit) ÷ 1000`

The full method is in [`docs/methodology.md`](docs/methodology.md).

## 📊 Key Findings (synthetic data, 2023–2025)
- **Total footprint:** ~13,000 tCO2e over 3 years (~4,100 tCO2e in 2025)
- **Scope 3 is about 50%** of emissions. *Purchased goods & services* is the biggest single hotspot.
- **Grid electricity (Scope 2)** and **diesel generators (Scope 1)** come next. The Port Harcourt Plant is the highest-emitting site.
- Emissions fell **~9.8% between 2023 and 2025**, which is **off track** for a 30% reduction target.

## 💡 Recommendations
1. **Supplier engagement:** collect primary data from the top suppliers and move from spend-based to activity-based Scope 3.
2. **Solar + battery hybrid systems** at Port Harcourt Plant to cut diesel and grid dependence.
3. **Energy efficiency:** HVAC upgrades and refrigerant leak management.
4. **Travel policy:** virtual-first meetings and fewer long-haul flights.
5. **Set a formal target** aligned with SBTi, and report annually using this pipeline.

## 🚀 Getting Started
```bash
git clone https://github.com/Engr-Daniel/carbon-footprint-esg-dashboard.git
cd carbon-footprint-esg-dashboard
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the dashboard
streamlit run app/streamlit_app.py

# Run tests
pytest -q
```

## 🛠️ Tech Stack
Python (pandas, plotly, matplotlib) · Streamlit · SQL · Jupyter · pytest

## 📚 Data Sources & References
- GHG Protocol – Corporate Standard & Scope 3 Standard
- UK DEFRA/DESNZ – GHG Conversion Factors for Company Reporting
- IPCC AR5/AR6 – Global Warming Potentials
- IFRS S2 – Climate-related Disclosures
- Grid emission factors: IFI Harmonised Grid Factors / IEA

## 👤 Author
**Daniel Oyewale**, Data Analyst · Data Strategist · Sustainability Researcher at [Petgrave.io](https://petgrave.io)

## 📄 License
MIT. See [LICENSE](LICENSE).
