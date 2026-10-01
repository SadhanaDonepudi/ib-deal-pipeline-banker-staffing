# IB Deal Pipeline & Banker Staffing Semantic Model

> ## ⚠️ SYNTHETIC DATA
> **Every deal, account, banker, and fee in this project is SYNTHETIC** —
> generated deterministically (`src/generate_data.py`, fixed seed 42) to
> mirror the shape of a real Salesforce → Snowflake → Power BI
> investment-banking pipeline. No real client, transaction, or personnel
> data is used anywhere in this repository.

A masters-level analytics engineering project: Salesforce-style opportunity,
account, and staffing extracts modeled in **Snowflake** as a **star-schema
semantic model** for **Power BI**, with a **35-measure DAX catalog**, a
**staffing utilization** report, and **dynamic row-level security**.

## What it reproduces

| Claim | Reproduced |
|---|---|
| Deals modeled | **2,400 exactly** (asserted in code and tests) |
| Coverage | **4 industry groups** (Consumer, Healthcare, Industrial, Technology & Services) × **4 products** (M&A, ECM, Debt Advisory, Restructuring) — all 16 combinations present |
| DAX measures | **35 exactly** (`dax/measures.json`, `dax/DAX_CATALOG.md`), incl. pipeline value, win rate, weighted fee forecast, days in stage, banker utilization, dynamic RLS |
| Staffing report | Active deal load and hours vs capacity targets by banker level (Analyst → Managing Director), flagging over/under-staffed bankers |

## Architecture

```
Salesforce-style extracts (data/*.csv, synthetic)
        │
        ▼
Snowflake STAGING  ── 1:1 landing tables + cleansing views (sql/01)
        │
        ▼
Snowflake CORE star schema (sql/02, sql/03)
  FACT_DEAL_PIPELINE · FACT_STAFFING
  DIM_INDUSTRY_GROUP · DIM_PRODUCT · DIM_STAGE · DIM_BANKER · DIM_DATE
        │
        ├──────────────► Power BI semantic model ── 35 DAX measures (dax/)
        │                     + dynamic RLS (UserAccess + USERPRINCIPALNAME)
        │
        └──────────────► Staffing utilization (src/staffing_utilization.py)
                              → outputs/staffing_flags.csv, staffing_summary.md
```

See `docs/architecture.md` (includes a Mermaid ERD) and
`docs/data_dictionary.md` (every table and column).

## Repository layout

```
├── data/            synthetic Salesforce-style extracts (CSV)
├── sql/             Snowflake DDL: staging, star schema, loads, example queries
├── dax/             35-measure catalog (measures.json + DAX_CATALOG.md)
├── src/             generate_data.py · staffing_utilization.py
├── outputs/         staffing_flags.csv · staffing_summary.md
├── docs/            architecture.md · data_dictionary.md
└── tests/           pytest data-integrity suite
```

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python src/generate_data.py          # writes the 4 extract CSVs to data/
python src/staffing_utilization.py   # writes outputs/staffing_flags.csv + summary
pytest tests/ -q                     # 6 integrity tests
```

Snowflake DDL in `sql/` runs in order (01 → 04) against a Snowflake account;
the CSVs in `data/` load into the staging tables.

## Results (actual output of the scripts above)

Generator (`python src/generate_data.py`):

```
deals_total            : 2400
industry_groups        : 4 ['Consumer', 'Healthcare', 'Industrial', 'Technology & Services']
products               : 4 ['Debt Advisory', 'ECM', 'M&A', 'Restructuring']
group_x_product_combos : 16
bankers_total          : 76        (Analyst 24 · Associate 20 · VP 14 ·
                                    Executive Director 10 · Managing Director 8)
accounts_total         : 320
staffing_rows          : 331
total_deal_value_usd   : 154,240,531,692
total_expected_fee_usd : 1,829,753,880
closed_deals           : 702  won=409  win_rate=0.5826
open_pipeline_value    : 108,992,034,692
```

Staffing utilization (`python src/staffing_utilization.py`) — utilization is
allocated hours ÷ capacity hours per week; **over-staffed > 100%**,
**under-staffed < 60%**:

```
bankers_analyzed       : 76
active_assignments     : 331
staffed_open_deals     : 38
mean_utilization_pct   : 0.8681   (median 0.8773, max 1.825)
over_staffed_count     : 22
under_staffed_count    : 20
bankers within target  : 34

by level (mean utilization / mean active deals / over / under):
  Analyst             0.990 / 5.79 / 10 / 4
  Associate           0.821 / 4.70 /  5 / 5
  VP                  0.804 / 3.36 /  3 / 5
  Executive Director  0.768 / 2.80 /  1 / 3
  Managing Director   0.859 / 2.88 /  3 / 3
```

Findings: analysts run hottest (99.0% mean utilization, 10 of 24
over-staffed); the most stretched banker sits at 182.5% of capacity hours.
Full per-banker flags are in `outputs/staffing_flags.csv`.

Tests: `6 passed` — deal count, 4×4 coverage, exactly 35 DAX measures,
staffing foreign-key integrity, non-null unique keys, complete banker
level hierarchy.

## Notes on scope

- The model behind the resume bullet is fully reproducible here: Snowflake
  DDL, the DAX catalog, and the utilization logic are all in-repo.
- Staffing assignments model the *active engagement snapshot* (bankers carry
  a realistic concurrent load around their capacity); the pipeline fact
  carries all 2,400 deals across their lifecycle.
