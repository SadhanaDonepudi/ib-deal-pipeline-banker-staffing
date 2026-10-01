# Architecture — IB Deal Pipeline & Banker Staffing Semantic Model

> **SYNTHETIC DATA.** Every record in this project is generated synthetically
> (`src/generate_data.py`, fixed seed) to mirror the shape of a real
> Salesforce → Snowflake → Power BI investment-banking pipeline. No real
> client, deal, or banker data is used anywhere.

## Flow

1. **Salesforce-style extracts** (`data/*.csv`) — Account, Opportunity,
   banker roster (User-style), and staffing assignments, generated to land
   exactly like scheduled Salesforce extracts would.
2. **Snowflake staging** (`sql/01_staging_sfdc.sql`) — 1:1 landing tables
   plus cleansing views mirroring the Salesforce objects.
3. **Snowflake star schema** (`sql/02_star_schema_ddl.sql`,
   `sql/03_load_facts.sql`) — two facts (`FACT_DEAL_PIPELINE`,
   `FACT_STAFFING`) sharing conformed dimensions, designed for direct
   import into a Power BI semantic model.
4. **Power BI / DAX** (`dax/`) — a 35-measure catalog (pipeline value,
   weighted fee forecast, win rate, days in stage, banker utilization)
   with dynamic row-level security via a `UserAccess` table and
   `USERPRINCIPALNAME()`.
5. **Staffing analytics** (`src/staffing_utilization.py`) — active deal
   load and allocated hours vs capacity targets by banker level
   (Analyst → Managing Director), flagging over/under-staffed bankers.

## Entity-relationship diagram

```mermaid
erDiagram
    SF_ACCOUNT ||--o{ SF_OPPORTUNITY : "has deals"
    SF_BANKER  ||--o{ SF_OPPORTUNITY : "lead MD"
    SF_BANKER  ||--o{ SF_STAFFING    : "staffed via"
    SF_OPPORTUNITY ||--o{ SF_STAFFING : "staffed by"

    DIM_INDUSTRY_GROUP ||--o{ FACT_DEAL_PIPELINE : classifies
    DIM_PRODUCT        ||--o{ FACT_DEAL_PIPELINE : classifies
    DIM_STAGE          ||--o{ FACT_DEAL_PIPELINE : "current stage"
    DIM_DATE           ||--o{ FACT_DEAL_PIPELINE : "open / close date"
    DIM_BANKER         ||--o{ FACT_DEAL_PIPELINE : "lead MD"
    DIM_BANKER         ||--o{ FACT_STAFFING      : staffed
    FACT_DEAL_PIPELINE ||--o{ FACT_STAFFING      : "deal team"
    DIM_DATE           ||--o{ FACT_STAFFING      : "assignment start"

    FACT_DEAL_PIPELINE {
        string OPPORTUNITY_ID PK
        string ACCOUNT_ID
        number INDUSTRY_GROUP_KEY FK
        number PRODUCT_KEY FK
        number STAGE_KEY FK
        number OPEN_DATE_KEY FK
        number CLOSE_DATE_KEY FK
        number LEAD_MD_KEY FK
        number DEAL_VALUE_USD
        number EXPECTED_FEE_USD
        number WEIGHTED_FEE_USD
        number DAYS_IN_STAGE
    }
    FACT_STAFFING {
        string STAFFING_ID PK
        string OPPORTUNITY_ID FK
        number BANKER_KEY FK
        number OPEN_DATE_KEY FK
        string ROLE_ON_DEAL
        number ALLOCATED_HOURS_PER_WEEK
        number IS_ACTIVE_ASSIGNMENT
    }
    DIM_BANKER {
        number BANKER_KEY PK
        string BANKER_ID
        string BANKER_NAME
        string LEVEL
        number CAPACITY_DEALS
        number CAPACITY_HOURS_PER_WEEK
    }
```

## Design notes

- **Conformed `DimBanker`** serves both as the lead-MD role on
  `FactDealPipeline` and the staffed banker on `FactStaffing`, so
  utilization and pipeline measures share one security filter path.
- **Stage probability** lives on `DimStage`, keeping the weighted fee
  forecast (`ExpectedFeeUSD x CloseProbability`) consistent between DAX
  and SQL.
- **Dynamic RLS** (see `dax/DAX_CATALOG.md`) filters dimensions through a
  `UserAccess` mapping rather than hard-coded roles, because coverage
  bankers cross industry groups when staffed on a deal.
