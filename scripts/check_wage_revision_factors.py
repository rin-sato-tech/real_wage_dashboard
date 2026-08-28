from real_wage_dashboard.wage_revision_service import (
    load_wage_revision_factors,
)

df = load_wage_revision_factors()

print("件数")
print(len(df))

print("\nresponse_type")
print(df["response_type"].value_counts())

print("\n企業規模")
print(df["company_size"].value_counts())

print("\n2025 total / most_important")
print(
    df[
        (df["year"] == 2025)
        & (df["company_size"] == "total")
        & (df["response_type"] == "most_important")
    ].to_string(index=False)
)

print("\n2025 total / multiple")
print(
    df[
        (df["year"] == 2025)
        & (df["company_size"] == "total")
        & (df["response_type"] == "multiple")
    ].to_string(index=False)
)

print("\n年×企業規模×response_type の件数")
print(
    df.groupby(
        [
            "year",
            "company_size",
            "response_type",
        ]
    )
    .size()
    .to_string()
)
