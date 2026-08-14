import pandas as pd

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.wage_service import load_wage_csv

TARGET_SIZES = {
    "5人以上": "T",
    "30人以上": "0",
}

TARGET_EMPLOYMENT_TYPES = {
    "就業形態計": "0",
    "一般労働者": "1",
    "パートタイム労働者": "2",
}

TARGET_WAGE_ITEMS = [
    "現金給与総額",
    "きまって支給する給与",
]


def normalize_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def main() -> None:
    df = load_wage_csv(WAGE_DATA_PATH)

    industry = normalize_code(df["産業分類"])
    size = normalize_code(df["規模"])
    employment_type = normalize_code(df["就業形態"])
    month = normalize_code(df["月"])

    print("=== v2対象12パターン確認 ===")

    for wage_item in TARGET_WAGE_ITEMS:
        for size_name, size_code in TARGET_SIZES.items():
            for employment_name, employment_code in TARGET_EMPLOYMENT_TYPES.items():
                target = df.loc[
                    (industry == "TL")
                    & (size == size_code)
                    & (employment_type == employment_code)
                    & (month != "CY")
                ].copy()

                values = pd.to_numeric(
                    target[wage_item]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.strip(),
                    errors="coerce",
                )

                target["year"] = pd.to_numeric(
                    target["年"],
                    errors="coerce",
                )

                target["month_number"] = pd.to_numeric(
                    target["月"],
                    errors="coerce",
                )

                target["date"] = pd.to_datetime(
                    {
                        "year": target["year"],
                        "month": target["month_number"],
                        "day": 1,
                    },
                    errors="coerce",
                )

                valid = target.loc[values.notna() & target["date"].notna()].copy()

                dates = valid["date"].drop_duplicates().sort_values()

                data_2020 = dates[dates.dt.year == 2020]

                if dates.empty:
                    print(f"{wage_item} | {size_name} | {employment_name} | データなし")
                    continue

                expected = pd.period_range(
                    dates.min().to_period("M"),
                    dates.max().to_period("M"),
                    freq="M",
                )

                actual = dates.dt.to_period("M")

                missing = expected.difference(actual)

                print(
                    f"{wage_item} | "
                    f"{size_name} | "
                    f"{employment_name} | "
                    f"有効={len(dates)}か月 | "
                    f"期間={dates.min():%Y-%m}～{dates.max():%Y-%m} | "
                    f"2020={len(data_2020)}か月 | "
                    f"欠損月={len(missing)}"
                )


if __name__ == "__main__":
    main()
