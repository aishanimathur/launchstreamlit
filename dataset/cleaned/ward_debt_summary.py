import pandas as pd
from pathlib import Path

BASE = Path('/Users/taharashid/Library/CloudStorage/OneDrive-HigherEducationCommission/UChicago/Courses/5. Winter 2026/1. Data Visualizations/final_project_dataviz_group2')

debt = pd.read_excel(BASE / "Updated_Accounts with Outstanding Debt 365+ 20260302.xlsx")

category_cols = {
    "Water (Service)":     "Total Water Balance",
    "Sewer (Service)":     "Total Sewer Balance",
    "Garbage (Service)":   "Total GB Balance",
    "Water Tax (Service)": "Total Water Tax Balance",
    "Sewer Tax (Service)": "Total Sewer Tax Balance",
    "Water Penalty":       "Total Water Penalty Balance",
    "Sewer Penalty":       "Total Sewer Penalty Balance",
    "Garbage Penalty":     "Total Garbage Penalty Balance",
    "Water Tax Penalty":   "Total Water Tax Penalty Balance",
    "Sewer Tax Penalty":   "Total Sewer Tax Penalty Balance",
    "Other":               "Total Other Balance",
}

for label, col in category_cols.items():
    debt[label] = debt[col].fillna(0) if col in debt.columns else 0

zip_ward = pd.read_csv(BASE / "dataset" / "cleaned" / "zip_ward_lookup.csv")
zip_ward["ZIP5"] = zip_ward["ZIP5"].astype(str).str[:5]
debt["ZIP5"] = debt["ZIP"].astype(str).str[:5]
debt = debt.merge(zip_ward, on="ZIP5", how="left")
debt = debt.dropna(subset=["ward"])
debt["ward"] = debt["ward"].astype(int)

agg_cols = list(category_cols.keys())
ward_debt = debt.groupby("ward")[agg_cols].sum().reset_index()

ward_debt.to_csv(BASE / "dataset" / "cleaned" / "ward_debt_summary.csv", index=False)
print(f"Saved. Shape: {ward_debt.shape}")
print(f"File size: {(BASE / 'dataset' / 'cleaned' / 'ward_debt_summary.csv').stat().st_size / 1024:.1f} KB")