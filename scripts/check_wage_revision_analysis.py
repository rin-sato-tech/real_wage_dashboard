from real_wage_dashboard.wage_revision_analysis import (
    summarize_company_size_revision,
    summarize_factor_changes,
    summarize_revision_factors,
    summarize_revision_trend,
)

df = summarize_revision_trend()

# print(df.to_string(index=False))

company_size_df = summarize_company_size_revision()

factor_df = summarize_revision_factors()

factor_change_df = summarize_factor_changes()

print("\n2015 -> 2025 factor change / total")
print(
    factor_change_df[factor_change_df["company_size"] == "total"].to_string(index=False)
)

print("\n2015 -> 2025 factor change / major factors")
print(
    factor_change_df[
        factor_change_df["factor"].isin(
            [
                "business_performance",
                "market_rate",
                "labor_retention",
                "consumer_prices",
                "employment_maintenance",
            ]
        )
    ]
    .sort_values(
        [
            "factor",
            "company_size",
        ]
    )
    .to_string(index=False)
)
