"""
SYNTHETIC DATA — banker staffing utilization analysis.

Computes active deal load and allocated hours vs capacity targets by banker
and level, flagging over-staffed (>100% of capacity hours) and under-staffed
(<60%) bankers. Mirrors sql/04_example_queries.sql and the DAX utilization
measures in dax/DAX_CATALOG.md.

Run (after src/generate_data.py):
    python src/staffing_utilization.py
Outputs:
    outputs/staffing_flags.csv, outputs/staffing_summary.md
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "outputs"


def main():
    bankers = pd.read_csv(DATA / "sf_bankers.csv")
    staffing = pd.read_csv(DATA / "sf_staffing.csv")
    opps = pd.read_csv(DATA / "sf_opportunities.csv")

    active = staffing[staffing.assignment_end.isna() | (staffing.assignment_end == "")]
    agg = active.groupby("banker_id").agg(
        active_deals=("opportunity_id", "nunique"),
        allocated_hours=("allocated_hours_per_week", "sum"),
        assignments=("staffing_id", "count"),
    ).reset_index()

    df = bankers.merge(agg, on="banker_id", how="left").fillna(
        {"active_deals": 0, "allocated_hours": 0.0, "assignments": 0})
    df["utilization_pct"] = df.allocated_hours / df.capacity_hours_per_week
    df["deal_load_pct"] = df.active_deals / df.capacity_deals
    df["flag"] = "OK"
    df.loc[df.utilization_pct > 1.0, "flag"] = "OVER_STAFFED"
    df.loc[df.utilization_pct < 0.6, "flag"] = "UNDER_STAFFED"

    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["banker_id", "banker_name", "level", "industry_group", "active_deals",
            "capacity_deals", "allocated_hours", "capacity_hours_per_week",
            "utilization_pct", "deal_load_pct", "flag"]
    df[cols].sort_values(["flag", "utilization_pct"], ascending=[True, False]) \
        .to_csv(OUT / "staffing_flags.csv", index=False)

    over = df[df.flag == "OVER_STAFFED"]
    under = df[df.flag == "UNDER_STAFFED"]
    by_level = df.groupby("level").agg(
        bankers=("banker_id", "count"),
        mean_utilization=("utilization_pct", "mean"),
        mean_deal_load=("active_deals", "mean"),
        over_staffed=("flag", lambda s: (s == "OVER_STAFFED").sum()),
        under_staffed=("flag", lambda s: (s == "UNDER_STAFFED").sum()),
    )

    open_deals = int(active.opportunity_id.nunique())

    lines = [
        "# Staffing Utilization Summary (SYNTHETIC DATA)", "",
        f"- Bankers analyzed: {len(df)}",
        f"- Distinct open deals with an active team: {open_deals}",
        f"- Active assignments: {len(active)}",
        f"- Mean utilization: {df.utilization_pct.mean():.1%} "
        f"(median {df.utilization_pct.median():.1%}, "
        f"p90 {df.utilization_pct.quantile(0.9):.1%}, max {df.utilization_pct.max():.1%})",
        f"- Over-staffed bankers (>100% capacity hours): {len(over)}",
        f"- Under-staffed bankers (<60% capacity hours): {len(under)}",
        f"- Bankers within target band: {len(df) - len(over) - len(under)}",
        "", "## By banker level", "",
        by_level.round(3).to_string(), "",
        "## Most over-staffed bankers", "",
        over.nlargest(5, "utilization_pct")[cols].round(3).to_string(index=False)
        if len(over) else "_None._",
    ]
    summary = "\n".join(lines)
    (OUT / "staffing_summary.md").write_text(summary)

    print("=== staffing utilization (SYNTHETIC) ===")
    print(f"bankers_analyzed       : {len(df)}")
    print(f"active_assignments     : {len(active)}")
    print(f"staffed_open_deals     : {open_deals}")
    print(f"mean_utilization_pct   : {df.utilization_pct.mean():.4f}")
    print(f"median_utilization_pct : {df.utilization_pct.median():.4f}")
    print(f"over_staffed_count     : {len(over)}")
    print(f"under_staffed_count    : {len(under)}")
    print("by_level:")
    print(by_level.round(3).to_string())


if __name__ == "__main__":
    main()
