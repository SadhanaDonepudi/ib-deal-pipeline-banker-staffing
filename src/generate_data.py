"""
SYNTHETIC DATA generator — IB Deal Pipeline & Banker Staffing.

All data in this project is SYNTHETIC, generated deterministically (fixed seed)
to mirror the shape of a Salesforce -> Snowflake -> Power BI investment-banking
pipeline: opportunities, accounts, bankers, and staffing assignments.

It reproduces, by construction, the resume claims:
  * exactly 2,400 deals
  * across 4 industry groups x 4 products (16 combinations, all present)

Run:
    python src/generate_data.py
Outputs (Salesforce-style extract CSVs in data/):
    sf_accounts.csv, sf_bankers.csv, sf_opportunities.csv, sf_staffing.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
N_DEALS = 2400

RNG = np.random.default_rng(SEED)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

INDUSTRY_GROUPS = ["Consumer", "Healthcare", "Industrial", "Technology & Services"]
PRODUCTS = ["M&A", "ECM", "Debt Advisory", "Restructuring"]

STAGES = ["Prospecting", "Qualification", "Pitch", "Mandate", "Execution", "Closed Won", "Closed Lost"]
STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}
OPEN_STAGES = STAGES[:5]

# close probability by stage (Salesforce-style stage probability mapping)
STAGE_PROB = {
    "Prospecting": 0.05, "Qualification": 0.15, "Pitch": 0.30,
    "Mandate": 0.55, "Execution": 0.80, "Closed Won": 1.00, "Closed Lost": 0.00,
}

BANKER_LEVELS = ["Analyst", "Associate", "VP", "Executive Director", "Managing Director"]
# capacity: max concurrent active deals and weekly hours target by level
CAPACITY_DEALS = {"Analyst": 6, "Associate": 5, "VP": 4, "Executive Director": 3, "Managing Director": 3}
CAPACITY_HOURS = {"Analyst": 45, "Associate": 42, "VP": 40, "Executive Director": 38, "Managing Director": 35}

BANKERS_PER_LEVEL = {"Analyst": 24, "Associate": 20, "VP": 14, "Executive Director": 10, "Managing Director": 8}

FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Quinn", "Drew",
         "Sam", "Chris", "Pat", "Robin", "Cameron", "Devon", "Emerson", "Finley", "Harper", "Jesse"]
LAST = ["Smith", "Johnson", "Lee", "Patel", "Garcia", "Kim", "Brown", "Nguyen", "Wilson", "Chen",
        "Murphy", "Davis", "Khan", "O'Brien", "Rossi", "Park", "Thompson", "Ali", "Brooks", "Foster"]


def build_bankers():
    rows = []
    bid = 1
    for level in BANKER_LEVELS:
        for k in range(BANKERS_PER_LEVEL[level]):
            rows.append({
                "banker_id": f"B{bid:04d}",
                "banker_name": f"{FIRST[(bid * 7 + k) % len(FIRST)]} {LAST[(bid * 3 + k * 5) % len(LAST)]}",
                "level": level,
                "industry_group": INDUSTRY_GROUPS[bid % 4],
                "capacity_deals": CAPACITY_DEALS[level],
                "capacity_hours_per_week": CAPACITY_HOURS[level],
                "is_active": True,
                "hire_date": pd.Timestamp("2016-01-04") + pd.Timedelta(days=int(RNG.integers(0, 3000))),
            })
            bid += 1
    return pd.DataFrame(rows)


def build_accounts(n=320):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "account_id": f"A{i:04d}",
            "account_name": f"Synthetic Client {i:03d} {['Holdings','Group','Partners','Industries','Capital'][i % 5]}",
            "industry_group": INDUSTRY_GROUPS[i % 4],
            "account_type": ["Public Company", "Private Company", "Sponsor / PE", "Family Office"][i % 4],
            "hq_state": ["NY", "CA", "TX", "IL", "MA", "WA", "FL", "CO"][i % 8],
        })
    return pd.DataFrame(rows)


def build_opportunities(accounts, bankers):
    # guarantee all 16 group x product combos appear: first 16 deals cycle the grid
    rows = []
    base = pd.Timestamp("2023-01-02")
    md_ids = bankers.loc[bankers.level == "Managing Director", "banker_id"].tolist()
    for i in range(1, N_DEALS + 1):
        if i <= 16:
            ig = INDUSTRY_GROUPS[(i - 1) // 4]
            prod = PRODUCTS[(i - 1) % 4]
        else:
            ig = INDUSTRY_GROUPS[int(RNG.integers(0, 4))]
            prod = PRODUCTS[int(RNG.integers(0, 4))]
        stage = STAGES[int(RNG.choice(len(STAGES), p=[0.16, 0.15, 0.14, 0.13, 0.12, 0.18, 0.12]))]
        open_date = base + pd.Timedelta(days=int(RNG.integers(0, 1000)))
        is_closed = stage in ("Closed Won", "Closed Lost")
        close_date = open_date + pd.Timedelta(days=int(RNG.integers(30, 540))) if is_closed else pd.NaT
        value = float(np.round(RNG.lognormal(mean=17.6, sigma=0.9), 0))  # ~ tens of $M
        fee_pct = float(np.round(RNG.uniform(0.004, 0.02), 5))
        rows.append({
            "opportunity_id": f"OPP{i:05d}",
            "opportunity_name": f"{ig[:4].upper()}-{prod.replace(' ', '')}-{i:04d}",
            "account_id": accounts.account_id.iloc[int(RNG.integers(0, len(accounts)))],
            "industry_group": ig,
            "product": prod,
            "stage": stage,
            "stage_index": STAGE_INDEX[stage],
            "close_probability": STAGE_PROB[stage],
            "deal_value_usd": value,
            "fee_pct": fee_pct,
            "expected_fee_usd": round(value * fee_pct, 2),
            "open_date": open_date.date().isoformat(),
            "close_date": close_date.date().isoformat() if is_closed else "",
            "is_closed": is_closed,
            "is_won": stage == "Closed Won",
            "lead_md_id": md_ids[int(RNG.integers(0, len(md_ids)))],
        })
    df = pd.DataFrame(rows)
    return df


ROLE_BY_LEVEL = {
    "Managing Director": "Lead MD", "Executive Director": "Senior Banker",
    "VP": "Deal Lead", "Associate": "Associate", "Analyst": "Analyst",
}
STAGE_PREFERENCE = ["Execution", "Mandate", "Pitch", "Qualification", "Prospecting"]
# typical allocated hours per deal per week by seniority (senior bankers
# spread thinner across more, smaller touches; juniors carry heavier loads)
HOURS_PER_DEAL = {"Analyst": 7.5, "Associate": 7.0, "VP": 9.0,
                  "Executive Director": 10.0, "Managing Director": 10.0}


def build_staffing(opps, bankers):
    """Staffing models the *active engagement snapshot*: each banker carries a
    realistic concurrent load around their capacity (a deterministic ~15% are
    loaded at 1.4x, ~15% at 0.4x, to exercise the over/under flags). Deals are
    drawn from open-stage deals, later stages first, home group preferred."""
    open_opps = opps[opps.stage.isin(OPEN_STAGES)].copy()
    open_opps["stage_rank"] = open_opps.stage.map(
        {s: i for i, s in enumerate(STAGE_PREFERENCE)})
    pool = open_opps.sort_values("stage_rank")
    pool_by_group = {g: gdf.opportunity_id.tolist()
                     for g, gdf in pool.groupby("industry_group")}
    pool_all = pool.opportunity_id.tolist()
    open_date = dict(zip(opps.opportunity_id, opps.open_date))

    rows, sid = [], 1
    for _, b in bankers.iterrows():
        u = RNG.random()
        load_factor = 1.4 if u < 0.15 else (0.4 if u < 0.30 else 0.9)
        n = int(np.clip(round(b.capacity_deals * load_factor
                              + RNG.normal(0, 0.8)), 0, b.capacity_deals + 4))
        candidates = pool_by_group.get(b.industry_group, []) + pool_all
        seen, chosen = set(), []
        for oid in candidates:
            if len(chosen) >= n:
                break
            if oid not in seen:
                seen.add(oid)
                chosen.append(oid)
        for oid in chosen:
            hrs = HOURS_PER_DEAL[b.level] * float(RNG.uniform(0.8, 1.25))
            rows.append({
                "staffing_id": f"S{sid:06d}",
                "opportunity_id": oid,
                "banker_id": b.banker_id,
                "role_on_deal": ROLE_BY_LEVEL[b.level],
                "allocated_hours_per_week": round(float(hrs), 1),
                "assignment_start": open_date[oid],
                "assignment_end": "",
            })
            sid += 1
    return pd.DataFrame(rows)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    bankers = build_bankers()
    accounts = build_accounts()
    opps = build_opportunities(accounts, bankers)
    staffing = build_staffing(opps, bankers)

    assert len(opps) == 2400, f"deal count {len(opps)} != 2400"
    combos = opps.groupby(["industry_group", "product"]).size()
    assert len(combos) == 16, f"only {len(combos)} group/product combos present"

    bankers.to_csv(DATA_DIR / "sf_bankers.csv", index=False)
    accounts.to_csv(DATA_DIR / "sf_accounts.csv", index=False)
    opps.to_csv(DATA_DIR / "sf_opportunities.csv", index=False)
    staffing.to_csv(DATA_DIR / "sf_staffing.csv", index=False)

    won = opps[opps.stage == "Closed Won"]
    closed = opps[opps.is_closed]
    print("=== SYNTHETIC data generation (seed=42) ===")
    print(f"deals_total            : {len(opps)}")
    print(f"industry_groups        : {opps.industry_group.nunique()} {sorted(opps.industry_group.unique())}")
    print(f"products               : {opps['product'].nunique()} {sorted(opps['product'].unique())}")
    print(f"group_x_product_combos : {len(combos)}")
    print(f"bankers_total          : {len(bankers)}")
    print(bankers.level.value_counts().to_string())
    print(f"accounts_total         : {len(accounts)}")
    print(f"staffing_rows          : {len(staffing)}")
    print(f"total_deal_value_usd   : {opps.deal_value_usd.sum():,.0f}")
    print(f"total_expected_fee_usd : {opps.expected_fee_usd.sum():,.0f}")
    print(f"closed_deals           : {len(closed)}  won={len(won)}  win_rate={len(won)/max(len(closed),1):.4f}")
    print(f"open_pipeline_value    : {opps.loc[opps.stage.isin(OPEN_STAGES),'deal_value_usd'].sum():,.0f}")


if __name__ == "__main__":
    main()
