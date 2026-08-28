from real_wage_dashboard.wage_revision_service import (
    load_wage_revision_amount_rate,
)


df = load_wage_revision_amount_rate()

print(df.tail(30).to_string(index=False))

print()
print("2015-2025")
print(
    df[df["year"].between(2015, 2025)].to_string(index=False)
)