from pathlib import Path

from real_wage_dashboard.establishment_size_wage_analysis import (
    prepare_establishment_size_annual_data,
)
from real_wage_dashboard.wage_service import load_wage_csv

DATA_PATH = Path("data/raw/hon-maikin-k-jissu.csv")


def main() -> None:
    wage_df = load_wage_csv(file_path=DATA_PATH)

    annual_df = prepare_establishment_size_annual_data(
        wage_df,
        start_year=2015,
        end_year=2025,
    )

    columns = [
        "year",
        "size_name",
        "employment_name",
        "所定内給与",
        "所定内労働時間",
        "scheduled_hourly_wage",
    ]

    print("=== 最低賃金比較用賃金系列 ===")
    print(annual_df[columns].to_string(index=False))

    print()
    print("=== 件数 ===")
    print(annual_df.groupby(["size_name", "employment_name"]).size())

    print()
    print("=== 欠損 ===")
    print(
        annual_df[
            [
                "所定内給与",
                "所定内労働時間",
                "scheduled_hourly_wage",
            ]
        ]
        .isna()
        .sum()
    )

    print()
    print("=== 2015 → 2025 ===")

    for (size_name, employment_name), group in annual_df.groupby(
        ["size_name", "employment_name"]
    ):
        start = group.loc[group["year"] == 2015].iloc[0]
        end = group.loc[group["year"] == 2025].iloc[0]

        change = (
            end["scheduled_hourly_wage"] / start["scheduled_hourly_wage"] - 1
        ) * 100

        print(
            f"{size_name} / {employment_name}: "
            f"{start['scheduled_hourly_wage']:.1f}円"
            f" → {end['scheduled_hourly_wage']:.1f}円"
            f" ({change:+.2f}%)"
        )


if __name__ == "__main__":
    main()
