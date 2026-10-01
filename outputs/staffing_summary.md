# Staffing Utilization Summary (SYNTHETIC DATA)

- Bankers analyzed: 76
- Distinct open deals with an active team: 38
- Active assignments: 331
- Mean utilization: 86.8% (median 87.7%, p90 141.0%, max 182.5%)
- Over-staffed bankers (>100% capacity hours): 22
- Under-staffed bankers (<60% capacity hours): 20
- Bankers within target band: 34

## By banker level

                    bankers  mean_utilization  mean_deal_load  over_staffed  under_staffed
level                                                                                     
Analyst                  24             0.990           5.792            10              4
Associate                20             0.821           4.700             5              5
Executive Director       10             0.768           2.800             1              3
Managing Director         8             0.859           2.875             3              3
VP                       14             0.804           3.357             3              5

## Most over-staffed bankers

banker_id  banker_name   level industry_group  active_deals  capacity_deals  allocated_hours  capacity_hours_per_week  utilization_pct  deal_load_pct         flag
    B0058 Jesse Foster      VP     Industrial             7               4             73.0                       40            1.825          1.750 OVER_STAFFED
    B0004 Chris Nguyen Analyst       Consumer            10               6             75.8                       45            1.684          1.667 OVER_STAFFED
    B0014 Chris Nguyen Analyst     Industrial             9               6             72.9                       45            1.620          1.500 OVER_STAFFED
    B0001  Avery Patel Analyst     Healthcare             9               6             72.1                       45            1.602          1.500 OVER_STAFFED
    B0009 Chris Nguyen Analyst     Healthcare            10               6             70.3                       45            1.562          1.667 OVER_STAFFED