"""The SQL data model must reproduce the Python engine exactly."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from carbon import calculate_emissions, load_activity, load_factors  # noqa: E402


def test_sql_view_matches_python_engine():
    con = sqlite3.connect(":memory:")
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    factors = pd.read_csv(ROOT / "data" / "reference" / "emission_factors.csv")
    act = pd.read_csv(ROOT / "data" / "sample" / "activity_data_sample.csv")
    sites = pd.DataFrame({"site_name": sorted(act.site.unique())})
    sites["site_id"] = range(1, len(sites) + 1)
    sites.to_sql("sites", con, if_exists="append", index=False)
    factors.to_sql("emission_factors", con, if_exists="append", index=False)
    act = act.merge(sites, left_on="site", right_on="site_name").assign(period=lambda d: d.period + "-01")
    act[["period", "site_id", "activity_type", "quantity", "unit"]].to_sql("activity_data", con, if_exists="append", index=False)
    sql_total = con.execute("SELECT SUM(tco2e) FROM v_emissions").fetchone()[0]
    py_total = calculate_emissions(load_activity(), load_factors())["tco2e"].sum()
    assert sql_total == pytest.approx(py_total, rel=1e-9)
