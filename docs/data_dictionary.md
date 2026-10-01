# Data Dictionary — IB Deal Pipeline & Banker Staffing (SYNTHETIC DATA)

All data is **synthetic**. Source extracts mirror Salesforce objects;
warehouse tables implement the Power BI star schema.

## Source extracts (data/)

### sf_accounts.csv (Salesforce Account)
| Column | Type | Description |
|---|---|---|
| account_id | string | `A####` synthetic account key |
| account_name | string | Synthetic client name |
| industry_group | string | Consumer / Healthcare / Industrial / Technology & Services |
| account_type | string | Public Company / Private Company / Sponsor / PE / Family Office |
| hq_state | string | HQ state code |

### sf_opportunities.csv (Salesforce Opportunity)
| Column | Type | Description |
|---|---|---|
| opportunity_id | string | `OPP#####` primary key |
| opportunity_name | string | Group-product-sequence label |
| account_id | string | FK → sf_accounts |
| industry_group | string | One of 4 industry groups |
| product | string | M&A / ECM / Debt Advisory / Restructuring |
| stage | string | Prospecting … Closed Won / Closed Lost |
| stage_index | int | 0–6 stage ordering |
| close_probability | float | Stage probability (0.05–1.00) |
| deal_value_usd | float | Transaction value (USD) |
| fee_pct | float | Fee as fraction of deal value |
| expected_fee_usd | float | deal_value_usd x fee_pct |
| open_date / close_date | date | Close date blank while open |
| is_closed / is_won | bool | Stage-derived flags |
| lead_md_id | string | FK → sf_bankers (Managing Director) |

### sf_bankers.csv (banker roster, User-style)
| Column | Type | Description |
|---|---|---|
| banker_id | string | `B####` primary key |
| banker_name | string | Synthetic name |
| level | string | Analyst / Associate / VP / Executive Director / Managing Director |
| industry_group | string | Home coverage group |
| capacity_deals | int | Max concurrent active deals target |
| capacity_hours_per_week | float | Weekly hours capacity target |
| is_active | bool | Active employee flag |
| hire_date | date | Synthetic hire date |

### sf_staffing.csv (staffing assignments)
| Column | Type | Description |
|---|---|---|
| staffing_id | string | `S######` primary key |
| opportunity_id | string | FK → sf_opportunities |
| banker_id | string | FK → sf_bankers |
| role_on_deal | string | Lead MD / Senior Banker / Deal Lead / Associate / Analyst |
| allocated_hours_per_week | float | Hours/week allocated to the deal |
| assignment_start / assignment_end | date | End blank = active assignment |

## Star schema (Snowflake CORE / Power BI model)

### FACT_DEAL_PIPELINE — one row per deal
opportunity_id (PK), account_id, industry_group_key, product_key, stage_key,
open_date_key, close_date_key, lead_md_key, deal_value_usd, expected_fee_usd,
weighted_fee_usd (= expected_fee_usd x close_probability), close_probability,
days_in_stage, is_open, is_won.

### FACT_STAFFING — one row per banker-deal assignment
staffing_id (PK), opportunity_id (FK → FACT_DEAL_PIPELINE), banker_key,
open_date_key, role_on_deal, allocated_hours_per_week, is_active_assignment.

### DIM_INDUSTRY_GROUP
industry_group_key (PK), industry_group (4 values).

### DIM_PRODUCT
product_key (PK), product (4 values).

### DIM_STAGE
stage_key (= stage_index), stage, close_probability, is_open, is_closed, is_won.

### DIM_BANKER
banker_key (PK), banker_id, banker_name, level, industry_group,
capacity_deals, capacity_hours_per_week, is_active, hire_date.

### DIM_DATE
date_key (YYYYMMDD), full_date, cal_year, cal_quarter, cal_month,
month_name, is_month_end.
