from real_wage_dashboard.wage_revision_service import (
    load_wage_revision_status,
)

df = load_wage_revision_status()

print(df.to_string(index=False))

print()
print("2025 total")
print(df[(df["year"] == 2025) & (df["company_size"] == "total")].to_string(index=False))

print("\n件数")
print(len(df))

print("\n年×企業規模の件数")
print(df.groupby(["year", "company_size"]).size().to_string())
