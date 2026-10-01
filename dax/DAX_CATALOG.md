# DAX Measure Catalog — IB Deal Pipeline & Banker Staffing Semantic Model

> **SYNTHETIC DATA.** The Power BI semantic model behind this catalog sits on
> the synthetic Snowflake star schema in `sql/`. Exactly **35 measures**.

Model tables: `FactDealPipeline`, `FactStaffing`, `DimIndustryGroup`,
`DimProduct`, `DimStage`, `DimBanker`, `DimDate`.

## Dynamic row-level security (RLS) approach

Static RLS alone cannot express "a banker sees their group's deals plus any
deal they are staffed on", so the model uses **dynamic RLS**:

1. A `UserAccess` table maps `USERPRINCIPALNAME()` (the signed-in email) to
   the industry groups and banker rows the user may see.
2. DAX security roles filter `DimIndustryGroup` and `DimBanker` with
   `TREATAS ( VALUES ( UserAccess[...] ), ... )` so filters propagate to both
   facts through the conformed dimensions.
3. `Weighted Fee Forecast (Dynamic RLS)` demonstrates the pattern at measure
   level; the same `TREATAS` guard wraps the pipeline-value measures in the
   secured role. Managing Directors mapped with `Group = "ALL"` bypass the
   group filter via an `ALL`-check on the access table.

## Measures (35)

### Pipeline & fees
1. **Total Deals** — `COUNTROWS ( FactDealPipeline )`
   Count of all deals in the pipeline, any stage.
2. **Open Deals** — `CALCULATE ( [Total Deals], DimStage[IsOpen] = TRUE )`
   Deals in an open stage (Prospecting through Execution).
3. **Closed Deals** — `CALCULATE ( [Total Deals], DimStage[IsClosed] = TRUE )`
   Deals that reached Closed Won or Closed Lost.
4. **Total Pipeline Value** — `SUM ( FactDealPipeline[DealValueUSD] )`
   Sum of transaction value across all deals in scope.
5. **Open Pipeline Value** — `CALCULATE ( [Total Pipeline Value], DimStage[IsOpen] = TRUE )`
   Deal value sitting in open stages only.
6. **Total Expected Fees** — `SUM ( FactDealPipeline[ExpectedFeeUSD] )`
   Sum of expected fee (deal value x fee %) across all deals.
7. **Weighted Fee Forecast** — `SUMX ( FactDealPipeline, FactDealPipeline[ExpectedFeeUSD] * FactDealPipeline[CloseProbability] )`
   Probability-weighted fee forecast: expected fee x stage close probability.
8. **Weighted Pipeline Value** — `CALCULATE ( SUMX ( FactDealPipeline, FactDealPipeline[DealValueUSD] * FactDealPipeline[CloseProbability] ), DimStage[IsOpen] = TRUE )`
   Probability-weighted deal value for open deals.
9. **Average Deal Value** — `AVERAGE ( FactDealPipeline[DealValueUSD] )`
   Mean transaction value per deal.
10. **Average Fee Pct** — `AVERAGE ( FactDealPipeline[FeePct] )`
    Mean fee percentage across deals.

### Outcomes & conversion
11. **Deals Won** — `CALCULATE ( [Total Deals], DimStage[IsWon] = TRUE )`
    Count of Closed Won deals.
12. **Deals Lost** — `CALCULATE ( [Total Deals], FactDealPipeline[IsWon] = 0, DimStage[IsClosed] = TRUE )`
    Count of Closed Lost deals.
13. **Win Rate** — `DIVIDE ( [Deals Won], [Closed Deals] )`
    Share of closed deals that were won.
14. **Loss Rate** — `DIVIDE ( [Deals Lost], [Closed Deals] )`
    Share of closed deals that were lost.
15. **Average Days in Stage** — `AVERAGE ( FactDealPipeline[DaysInStage] )`
    Mean days since open (open deals) or until close (closed deals).
16. **Average Days to Close** — `CALCULATE ( [Average Days in Stage], DimStage[IsClosed] = TRUE )`
    Mean open-to-close duration for closed deals.
17. **Pipeline Conversion Rate** — `DIVIDE ( [Deals Won], [Total Deals] )`
    Won deals as a share of all deals ever opened in scope.
18. **Fee Realization Rate** — `DIVIDE ( CALCULATE ( [Total Expected Fees], DimStage[IsWon] = TRUE ), CALCULATE ( [Total Expected Fees], DimStage[IsClosed] = TRUE ) )`
    Won expected fees as a share of all closed-deal expected fees.
19. **Average Won Fee** — `CALCULATE ( AVERAGE ( FactDealPipeline[ExpectedFeeUSD] ), DimStage[IsWon] = TRUE )`
    Mean expected fee on won deals.
20. **Mandate Conversion Rate** — `DIVIDE ( CALCULATE ( [Total Deals], DimStage[StageIndex] >= 3 ), CALCULATE ( [Total Deals], DimStage[StageIndex] >= 2 ) )`
    Share of pitched deals that reached Mandate or beyond.
21. **Execution Win Rate** — `DIVIDE ( [Deals Won], CALCULATE ( [Total Deals], DimStage[StageIndex] >= 4 ) )`
    Win rate among deals that reached the Execution stage or beyond.
22. **Fees per Closed Deal** — `DIVIDE ( CALCULATE ( [Total Expected Fees], DimStage[IsClosed] = TRUE ), [Closed Deals] )`
    Total expected fees divided by closed deals.

### Staffing & utilization
23. **Active Assignments** — `CALCULATE ( COUNTROWS ( FactStaffing ), FactStaffing[IsActiveAssignment] = 1 )`
    Count of active banker-deal staffing assignments.
24. **Active Deal Load** — `CALCULATE ( DISTINCTCOUNT ( FactStaffing[OpportunityID] ), FactStaffing[IsActiveAssignment] = 1 )`
    Distinct open deals a banker (or group of bankers) is staffed on.
25. **Allocated Hours** — `CALCULATE ( SUM ( FactStaffing[AllocatedHoursPerWeek] ), FactStaffing[IsActiveAssignment] = 1 )`
    Total allocated hours per week across active assignments.
26. **Capacity Hours** — `SUM ( DimBanker[CapacityHoursPerWeek] )`
    Weekly capacity hours for the bankers in scope.
27. **Capacity Deals** — `SUM ( DimBanker[CapacityDeals] )`
    Concurrent-deal capacity for the bankers in scope.
28. **Banker Utilization %** — `DIVIDE ( [Allocated Hours], [Capacity Hours] )`
    Allocated hours as a percentage of capacity hours; >100% flags over-staffing.
29. **Deal Load vs Capacity %** — `DIVIDE ( [Active Deal Load], [Capacity Deals] )`
    Active deal load as a percentage of concurrent-deal capacity.
30. **Over Capacity Bankers** — `COUNTROWS ( FILTER ( VALUES ( DimBanker[BankerID] ), [Banker Utilization %] > 1 ) )`
    Bankers whose utilization exceeds 100% of capacity hours.
31. **Under Utilized Bankers** — `COUNTROWS ( FILTER ( VALUES ( DimBanker[BankerID] ), [Banker Utilization %] < 0.6 ) )`
    Bankers below 60% utilization (bench / under-staffed).
32. **Avg Deals per Banker** — `DIVIDE ( [Active Deal Load], DISTINCTCOUNT ( FactStaffing[BankerKey] ) )`
    Active deal load divided by distinct staffed bankers.
33. **Avg Hours per Deal** — `DIVIDE ( [Allocated Hours], [Active Deal Load] )`
    Allocated hours divided by distinct active deals.

### Dynamic / scenario
34. **Pipeline Value Selected Stage** — `VAR Sel = SELECTEDVALUE ( DimStage[Stage] ) RETURN IF ( ISBLANK ( Sel ), [Open Pipeline Value], CALCULATE ( [Total Pipeline Value], DimStage[Stage] = Sel ) )`
    Pipeline value for the slicer-selected stage; falls back to all open stages.
35. **Weighted Fee Forecast Dynamic RLS** — `CALCULATE ( [Weighted Fee Forecast], TREATAS ( VALUES ( UserAccess[IndustryGroup] ), DimIndustryGroup[IndustryGroup] ) )`
    Weighted fee forecast restricted by the dynamic-RLS `UserAccess` mapping (see above).
