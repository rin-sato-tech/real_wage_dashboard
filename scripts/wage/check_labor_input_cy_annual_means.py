import pandas as pd

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_input_analysis import (
    create_labor_input_dataframe,
    create_yearly_weighted_means,
)
from real_wage_dashboard.wage_service import load_wage_csv


TARGET_YEARS = [1993, 2000, 2015, 2025]

EMPLOYMENT_TYPES = {
    "0": "就業形態計",
    "1": "一般労働者",
    "2": "パートタイム労働者",
}

INDICATORS = {
    "きまって支給する給与": "nominal_wage_amount",
    "総実労働時間": "total_hours",
    "所定内労働時間": "scheduled_hours",
    "所定外労働時間": "overtime_hours",
    "出勤日数": "working_days",
}


def extract_cy_values(
    raw_df: pd.DataFrame,
    employment_type: str,
) -> pd.DataFrame:
    """原表のCY公表年平均を抽出する。"""

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        *INDICATORS.keys(),
    }

    missing = required_columns - set(raw_df.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    industry = raw_df["産業分類"].astype(str).str.strip()
    size = raw_df["規模"].astype(str).str.strip()
    employment = raw_df["就業形態"].astype(str).str.strip()
    month = raw_df["月"].astype(str).str.strip()

    result = raw_df.loc[
        (industry == "TL")
        & (size == "T")
        & (employment == employment_type)
        & (month == "CY"),
        ["年", *INDICATORS.keys()],
    ].copy()

    result["year"] = pd.to_numeric(
        result["年"],
        errors="coerce",
    )

    result = result.loc[result["year"].isin(TARGET_YEARS)].copy()

    if result["year"].duplicated().any():
        duplicated_years = sorted(
            result.loc[result["year"].duplicated(keep=False), "year"]
            .dropna()
            .astype(int)
            .unique()
        )
        raise ValueError(
            f"CY公表値に同一年の重複があります: {duplicated_years}"
        )

    for source_column in INDICATORS:
        result[source_column] = pd.to_numeric(
            result[source_column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip(),
            errors="coerce",
        )

    result = result.rename(
        columns={
            source_column: target_column
            for source_column, target_column in INDICATORS.items()
        }
    )

    return result[
        [
            "year",
            *INDICATORS.values(),
        ]
    ].sort_values("year")


def create_comparison(
    raw_df: pd.DataFrame,
    employment_type: str,
) -> pd.DataFrame:
    """再計算年平均とCY公表値を比較する。"""

    monthly_df = create_labor_input_dataframe(
        raw_df,
        establishment_size="T",
        employment_type=employment_type,
    )

    recalculated = create_yearly_weighted_means(
        monthly_df,
        columns=list(INDICATORS.values()),
    )

    recalculated = recalculated.loc[
        recalculated["year"].isin(TARGET_YEARS)
    ].copy()

    official = extract_cy_values(
        raw_df,
        employment_type=employment_type,
    )

    merged = recalculated.merge(
        official,
        on="year",
        how="inner",
        suffixes=("_recalculated", "_cy"),
        validate="one_to_one",
    )

    expected_years = set(TARGET_YEARS)
    actual_years = set(merged["year"].astype(int))

    if actual_years != expected_years:
        raise ValueError(
            "比較対象年が揃っていません。"
            f" 不足: {sorted(expected_years - actual_years)}"
        )

    records = []

    for _, row in merged.iterrows():
        for source_name, column in INDICATORS.items():
            recalculated_value = row[f"{column}_recalculated"]
            cy_value = row[f"{column}_cy"]

            records.append(
                {
                    "employment_type": EMPLOYMENT_TYPES[employment_type],
                    "year": int(row["year"]),
                    "indicator": source_name,
                    "recalculated": recalculated_value,
                    "official_cy": cy_value,
                    "difference": recalculated_value - cy_value,
                    "difference_pct": (
                        (recalculated_value / cy_value - 1) * 100
                        if cy_value != 0
                        else float("nan")
                    ),
                }
            )

    return pd.DataFrame(records)


def main() -> None:
    raw_df = load_wage_csv(WAGE_DATA_PATH)

    results = pd.concat(
        [
            create_comparison(
                raw_df,
                employment_type=employment_type,
            )
            for employment_type in EMPLOYMENT_TYPES
        ],
        ignore_index=True,
    )

    print("=== 再計算年平均 vs CY公表年平均 ===")
    print(
        results.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print("\n=== 指標別 最大絶対差 ===")
    summary = (
        results.assign(
            absolute_difference=results["difference"].abs(),
            absolute_difference_pct=results["difference_pct"].abs(),
        )
        .groupby("indicator", as_index=False)
        .agg(
            max_absolute_difference=("absolute_difference", "max"),
            max_absolute_difference_pct=("absolute_difference_pct", "max"),
        )
    )

    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )


if __name__ == "__main__":
    main()