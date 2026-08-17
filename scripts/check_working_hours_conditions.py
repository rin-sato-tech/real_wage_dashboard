import pandas as pd

from real_wage_dashboard.config import WAGE_DATA_PATH


TIME_ITEMS = [
    "総実労働時間",
    "所定内労働時間",
    "所定外労働時間",
]

EMPLOYMENT_TYPES = {
    "一般労働者": "1",
    "パートタイム労働者": "2",
}

ESTABLISHMENT_SIZES = {
    "5人以上": "T",
    "30人以上": "0",
}


def main() -> None:
    raw_df = pd.read_csv(
        WAGE_DATA_PATH,
        encoding="cp932",
    )

    industry = raw_df["産業分類"].astype(str).str.strip()

    size = raw_df["規模"].astype(str).str.strip()

    employment = raw_df["就業形態"].astype(str).str.strip()

    month = raw_df["月"].astype(str).str.strip()

    for time_item in TIME_ITEMS:
        if time_item not in raw_df.columns:
            print(f"{time_item}: 列なし")
            continue

        print(f"\n=== {time_item} ===")

        for size_label, size_code in ESTABLISHMENT_SIZES.items():
            for employment_label, employment_code in EMPLOYMENT_TYPES.items():
                df = raw_df.loc[
                    (industry == "TL")
                    & (size == size_code)
                    & (employment == employment_code)
                    & (month != "CY"),
                    [
                        "年",
                        "月",
                        time_item,
                    ],
                ].copy()

                df["year"] = pd.to_numeric(
                    df["年"],
                    errors="coerce",
                )

                df["month_num"] = pd.to_numeric(
                    df["月"],
                    errors="coerce",
                )

                df["value"] = pd.to_numeric(
                    df[time_item]
                    .astype(str)
                    .str.replace(
                        ",",
                        "",
                        regex=False,
                    )
                    .str.strip(),
                    errors="coerce",
                )

                df["date"] = pd.to_datetime(
                    {
                        "year": df["year"],
                        "month": df["month_num"],
                        "day": 1,
                    },
                    errors="coerce",
                )

                df = (
                    df.dropna(
                        subset=[
                            "date",
                            "value",
                        ]
                    )
                    .sort_values("date")
                    .reset_index(drop=True)
                )

                if df.empty:
                    print(f"{size_label} × {employment_label}: データなし")
                    continue

                periods = df["date"].dt.to_period("M")

                full_periods = pd.period_range(
                    periods.min(),
                    periods.max(),
                    freq="M",
                )

                missing_months = full_periods.difference(periods)

                print(f"{size_label} × {employment_label}")

                print(
                    "  件数:",
                    len(df),
                )

                print(
                    "  期間:",
                    df["date"].min().strftime("%Y-%m"),
                    "〜",
                    df["date"].max().strftime("%Y-%m"),
                )

                print(
                    "  欠損月:",
                    len(missing_months),
                )

                base_2020 = df[df["date"].dt.year == 2020]

                print(
                    "  2020年:",
                    len(base_2020),
                    "か月",
                )


if __name__ == "__main__":
    main()
