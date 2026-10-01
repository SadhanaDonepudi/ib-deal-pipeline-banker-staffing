"""SYNTHETIC DATA project — integrity tests over the generated extracts
and the DAX catalog. Run: pytest tests/ -q"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name):
    return pd.read_csv(DATA / name)


def test_exactly_2400_deals():
    assert len(load("sf_opportunities.csv")) == 2400


def test_all_group_product_combos_present():
    opps = load("sf_opportunities.csv")
    combos = opps.groupby(["industry_group", "product"]).size()
    assert opps.industry_group.nunique() == 4
    assert opps["product"].nunique() == 4
    assert len(combos) == 16


def test_dax_catalog_exactly_35_measures():
    measures = json.loads((ROOT / "dax" / "measures.json").read_text())
    assert len(measures) == 35
    names = [m["name"] for m in measures]
    assert len(set(names)) == 35
    catalog = (ROOT / "dax" / "DAX_CATALOG.md").read_text()
    for n in names:
        assert n in catalog, f"measure missing from catalog: {n}"


def test_staffing_fk_integrity():
    staffing, opps, bankers = (load("sf_staffing.csv"),
                               load("sf_opportunities.csv"),
                               load("sf_bankers.csv"))
    assert staffing.opportunity_id.isin(opps.opportunity_id).all()
    assert staffing.banker_id.isin(bankers.banker_id).all()
    assert opps.account_id.isin(load("sf_accounts.csv").account_id).all()
    assert opps.lead_md_id.isin(bankers.banker_id).all()


def test_no_null_keys():
    for name, key in [("sf_opportunities.csv", "opportunity_id"),
                      ("sf_accounts.csv", "account_id"),
                      ("sf_bankers.csv", "banker_id"),
                      ("sf_staffing.csv", "staffing_id")]:
        df = load(name)
        assert df[key].notna().all() and df[key].is_unique


def test_banker_levels_complete():
    bankers = load("sf_bankers.csv")
    assert set(bankers.level) == {"Analyst", "Associate", "VP",
                                  "Executive Director", "Managing Director"}
