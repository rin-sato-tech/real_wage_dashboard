import pandas as pd

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.wage_service import load_wage_csv

WAGE_ITEMS = [
    "現金給与総額",
    "きまって支給する給与",
]


def normalize_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def main() -> None:
    df = load_wage_csv(WAGE_DATA_PATH)

    print("=== 1. 賃金項目の列確認 ===")

    for item in WAGE_ITEMS:
        print(f"{item}: {item in df.columns}")

        if item in df.columns:
            values = pd.to_numeric(
                df[item].astype(str).str.replace(",", "", regex=False).str.strip(),
                errors="coerce",
            )

            print(f"  数値データ件数: {values.notna().sum():,}")

    print("\n=== 2. 就業形態コード ===")

    employment_types = normalize_code(df["就業形態"])

    print(sorted(employment_types.dropna().unique()))

    print("\n件数:")
    print(employment_types.value_counts().sort_index())

    print("\n=== 3. 事業所規模コード ===")

    establishment_sizes = normalize_code(df["規模"])

    print(sorted(establishment_sizes.dropna().unique()))

    print("\n件数:")
    print(establishment_sizes.value_counts().sort_index())

    print("\n=== 4. 調査産業計の月次データを確認 ===")

    industry = normalize_code(df["産業分類"])
    month = normalize_code(df["月"])

    base_df = df.loc[(industry == "TL") & (month != "CY")].copy()

    base_df["employment_type"] = normalize_code(base_df["就業形態"])
    base_df["establishment_size"] = normalize_code(base_df["規模"])

    base_df["year"] = pd.to_numeric(
        base_df["年"],
        errors="coerce",
    )

    base_df["month_number"] = pd.to_numeric(
        base_df["月"],
        errors="coerce",
    )

    base_df["date"] = pd.to_datetime(
        {
            "year": base_df["year"],
            "month": base_df["month_number"],
            "day": 1,
        },
        errors="coerce",
    )

    print("\n調査産業計で存在する 規模 × 就業形態:")
    combinations = (
        base_df[
            [
                "establishment_size",
                "employment_type",
            ]
        ]
        .value_counts()
        .sort_index()
    )
    print(combinations)

    print("\n=== 5. 各条件の期間確認 ===")

    for size in sorted(base_df["establishment_size"].unique()):
        for employment in sorted(base_df["employment_type"].unique()):
            condition_df = base_df.loc[
                (base_df["establishment_size"] == size)
                & (base_df["employment_type"] == employment)
            ].copy()

            if condition_df.empty:
                continue

            dates = condition_df["date"].dropna().drop_duplicates().sort_values()

            if dates.empty:
                continue

            print(
                f"規模={size}, "
                f"就業形態={employment}: "
                f"{dates.min():%Y-%m} ～ "
                f"{dates.max():%Y-%m}, "
                f"{len(dates)}か月"
            )

    print("\n=== 6. 2020年データ確認 ===")

    data_2020 = base_df.loc[base_df["date"].dt.year == 2020]

    print(
        data_2020[
            [
                "establishment_size",
                "employment_type",
            ]
        ]
        .value_counts()
        .sort_index()
    )

    print("\n=== 7. 月の連続性確認 ===")

    for size in sorted(base_df["establishment_size"].unique()):
        for employment in sorted(base_df["employment_type"].unique()):
            condition_df = base_df.loc[
                (base_df["establishment_size"] == size)
                & (base_df["employment_type"] == employment)
            ].copy()

            periods = (
                condition_df["date"]
                .dropna()
                .dt.to_period("M")
                .drop_duplicates()
                .sort_values()
            )

            if periods.empty:
                continue

            expected = pd.period_range(
                periods.iloc[0],
                periods.iloc[-1],
                freq="M",
            )

            missing = expected.difference(periods)

            print(f"規模={size}, 就業形態={employment}: 欠損月={len(missing)}")

            if len(missing) > 0:
                print(
                    "  ",
                    [str(value) for value in missing[:20]],
                )


if __name__ == "__main__":
    main()
