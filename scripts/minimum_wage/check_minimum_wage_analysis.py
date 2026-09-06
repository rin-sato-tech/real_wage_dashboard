from pathlib import Path

from real_wage_dashboard.establishment_size_wage_analysis import (
    prepare_establishment_size_annual_data,
)
from real_wage_dashboard.minimum_wage_analysis import (
    build_minimum_wage_analysis,
)
from real_wage_dashboard.minimum_wage_service import (
    load_minimum_wage_data,
)
from real_wage_dashboard.wage_service import load_wage_csv

WAGE_DATA_PATH = Path("data/raw/hon-maikin-k-jissu.csv")


def main() -> None:
    minimum_wage_df = load_minimum_wage_data()

    raw_wage_df = load_wage_csv(
        file_path=WAGE_DATA_PATH,
    )

    wage_df = prepare_establishment_size_annual_data(
        raw_wage_df,
        start_year=2015,
        end_year=2025,
    )

    analysis_df = build_minimum_wage_analysis(
        minimum_wage_df,
        wage_df,
    )

    columns = [
        "year",
        "size_name",
        "employment_name",
        "minimum_wage",
        "scheduled_hourly_wage",
        "simple_kaitz",
        "minimum_wage_index",
        "wage_index",
    ]

    print("=== 最低賃金分析データ ===")
    print(analysis_df[columns].to_string(index=False))

    print()
    print("=== 2015 → 2025 ===")

    for (
        size_name,
        employment_name,
    ), group in analysis_df.groupby(["size_name", "employment_name"]):
        start = group.loc[group["year"] == 2015].iloc[0]
        end = group.loc[group["year"] == 2025].iloc[0]

        print(
            f"{size_name} / {employment_name}: "
            f"Kaitz "
            f"{start['simple_kaitz']:.3f}"
            f" → {end['simple_kaitz']:.3f}, "
            f"賃金指数 "
            f"{end['wage_index']:.1f}, "
            f"最低賃金指数 "
            f"{end['minimum_wage_index']:.1f}"
        )


if __name__ == "__main__":
    main()
