import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    CPI_SERIES,
    WAGE_DATA_PATH,
)
from real_wage_dashboard.cpi_analysis import (
    prepare_annual_cpi,
)
from real_wage_dashboard.cpi_service import (
    load_cpi_dataframe,
)
from real_wage_dashboard.take_home_analysis import (
    add_real_take_home_metrics,
    calculate_take_home_time_series,
)
from real_wage_dashboard.take_home_service import (
    load_take_home_rule_tables,
)
from real_wage_dashboard.wage_service import (
    load_wage_csv,
)

START_YEAR = 1990
END_YEAR = 2025

SELECTED_YEARS = [
    1990,
    2000,
    2003,
    2010,
    2015,
    2020,
    2025,
]


def create_annual_wage_dataframe(
    raw_df: pd.DataFrame,
) -> pd.DataFrame:
    """毎月勤労統計の月次値から手取り分析用の年平均賃金を作成する。"""

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        "現金給与総額",
        "きまって支給する給与",
        "特別給与",
    }

    missing = required_columns - set(raw_df.columns)

    if missing:
        raise ValueError(f"年平均賃金の作成に必要な列がありません: {sorted(missing)}")

    industry = raw_df["産業分類"].astype(str).str.strip()

    size = raw_df["規模"].astype(str).str.strip()

    employment = raw_df["就業形態"].astype(str).str.strip()

    # 調査産業計・5人以上・就業形態計
    # CY公表値ではなく、1～12月の月次値を使用する。
    data = raw_df.loc[
        (industry == "TL") & (size == "T") & (employment == "0"),
        [
            "年",
            "月",
            "現金給与総額",
            "きまって支給する給与",
            "特別給与",
        ],
    ].copy()

    data["year"] = pd.to_numeric(
        data["年"],
        errors="coerce",
    )

    data["month"] = pd.to_numeric(
        data["月"],
        errors="coerce",
    )

    value_columns = {
        "現金給与総額": "total_cash_earnings",
        "きまって支給する給与": "regular_earnings",
        "特別給与": "special_earnings",
    }

    for source_column, target_column in value_columns.items():
        data[target_column] = pd.to_numeric(
            data[source_column]
            .astype(str)
            .str.replace(
                ",",
                "",
                regex=False,
            )
            .str.strip(),
            errors="coerce",
        )

    # CY は month の数値変換で NaN になる。
    # 1～12月だけを残す。
    data = data.loc[
        data["year"].between(
            START_YEAR,
            END_YEAR,
        )
        & data["month"].between(
            1,
            12,
        )
    ].copy()

    data = data.dropna(
        subset=[
            "year",
            "month",
            *value_columns.values(),
        ]
    )

    data["year"] = data["year"].astype(int)

    data["month"] = data["month"].astype(int)

    # 同一年月に複数行ある場合は、
    # 他の月次抽出処理と同様に末尾を採用する。
    data = (
        data.sort_index()
        .drop_duplicates(
            subset=[
                "year",
                "month",
            ],
            keep="last",
        )
        .sort_values(
            [
                "year",
                "month",
            ]
        )
        .reset_index(drop=True)
    )

    # 各年12か月揃っていることを確認する。
    month_counts = data.groupby("year")["month"].nunique()

    incomplete = month_counts.loc[month_counts != 12]

    if not incomplete.empty:
        raise ValueError(f"12か月揃っていない賃金年があります: {incomplete.to_dict()}")

    # 月次値の単純平均を年平均月額とする。
    annual = (
        data.groupby(
            "year",
            as_index=False,
        )
        .agg(
            total_cash_earnings=(
                "total_cash_earnings",
                "mean",
            ),
            regular_earnings=(
                "regular_earnings",
                "mean",
            ),
            special_earnings=(
                "special_earnings",
                "mean",
            ),
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    actual_years = set(annual["year"])

    missing_years = sorted(expected_years - actual_years)

    if missing_years:
        raise ValueError(f"年平均賃金に不足年があります: {missing_years}")

    # 月次で
    # 現金給与総額 =
    # きまって支給する給与 + 特別給与
    # が成立しているので、年平均でも成立する。
    identity_diff = annual["total_cash_earnings"] - (
        annual["regular_earnings"] + annual["special_earnings"]
    )

    if (identity_diff.abs() > 1e-6).any():
        raise ValueError("給与構成の恒等式が成立しない年があります。")

    return annual


def period_change_pct(
    df: pd.DataFrame,
    column: str,
    start_year: int,
    end_year: int,
) -> float:
    """指定列の期間変化率を計算する。"""

    start = float(
        df.loc[
            df["year"] == start_year,
            column,
        ].iloc[0]
    )

    end = float(
        df.loc[
            df["year"] == end_year,
            column,
        ].iloc[0]
    )

    return (end / start - 1) * 100


def main() -> None:
    # ----------------------------------------
    # 1. 賃金データ
    # ----------------------------------------

    raw_wage_df = load_wage_csv(WAGE_DATA_PATH)

    annual_wage_df = create_annual_wage_dataframe(raw_wage_df)

    print("=== 賃金系列確認 ===")

    for year in [
        1990,
        2025,
    ]:
        row = annual_wage_df.loc[annual_wage_df["year"] == year].iloc[0]

        print(
            year,
            "gross:",
            f"{row['total_cash_earnings'] * 12:,.0f}",
            "regular:",
            f"{row['regular_earnings'] * 12:,.0f}",
            "bonus:",
            f"{row['special_earnings'] * 12:,.0f}",
        )

    # ----------------------------------------
    # 2. CPI
    # ----------------------------------------

    app_id = st.secrets["ESTAT_APP_ID"]

    cpi_df = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES["持家の帰属家賃を除く総合"],
    )

    annual_cpi_df = prepare_annual_cpi(
        cpi_df=cpi_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    # ----------------------------------------
    # 3. 制度表
    # ----------------------------------------

    rules = load_take_home_rule_tables()

    # ----------------------------------------
    # 4. 35歳・45歳
    # ----------------------------------------

    age35 = calculate_take_home_time_series(
        annual_wage_df=annual_wage_df,
        rule_tables=rules,
        start_year=START_YEAR,
        end_year=END_YEAR,
        sex="male",
        age=35,
    )

    age45 = calculate_take_home_time_series(
        annual_wage_df=annual_wage_df,
        rule_tables=rules,
        start_year=START_YEAR,
        end_year=END_YEAR,
        sex="male",
        age=45,
    )

    age35 = add_real_take_home_metrics(
        take_home_df=age35,
        annual_cpi_df=annual_cpi_df,
        base_year=1990,
    )

    age45 = add_real_take_home_metrics(
        take_home_df=age45,
        annual_cpi_df=annual_cpi_df,
        base_year=1990,
    )

    # ----------------------------------------
    # 5. 比較表
    # ----------------------------------------

    comparison = (
        age35[
            [
                "year",
                "nominal_take_home_yen",
                "real_take_home_yen",
                "effective_burden_rate",
            ]
        ]
        .rename(
            columns={
                "nominal_take_home_yen": "nominal_take_home_age35",
                "real_take_home_yen": "real_take_home_age35",
                "effective_burden_rate": "burden_age35",
            }
        )
        .merge(
            age45[
                [
                    "year",
                    "long_term_care_yen",
                    "nominal_take_home_yen",
                    "real_take_home_yen",
                    "effective_burden_rate",
                ]
            ].rename(
                columns={
                    "nominal_take_home_yen": "nominal_take_home_age45",
                    "real_take_home_yen": "real_take_home_age45",
                    "effective_burden_rate": "burden_age45",
                }
            ),
            on="year",
            how="inner",
            validate="one_to_one",
        )
    )

    comparison["nominal_take_home_diff_yen"] = (
        comparison["nominal_take_home_age45"] - comparison["nominal_take_home_age35"]
    )

    comparison["real_take_home_diff_yen"] = (
        comparison["real_take_home_age45"] - comparison["real_take_home_age35"]
    )

    comparison["burden_diff_pt"] = (
        comparison["burden_age45"] - comparison["burden_age35"]
    ) * 100

    # ----------------------------------------
    # 6. 主要年
    # ----------------------------------------

    print("=== 35歳 vs 45歳：主要年 ===")

    print(
        comparison.loc[
            comparison["year"].isin(SELECTED_YEARS),
            [
                "year",
                "long_term_care_yen",
                "nominal_take_home_diff_yen",
                "real_take_home_diff_yen",
                "burden_diff_pt",
            ],
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:+,.3f}",
        )
    )

    # ----------------------------------------
    # 7. 1990→2025
    # ----------------------------------------

    print("\n=== 1990→2025 実質手取り ===")

    for label, df in [
        ("age35", age35),
        ("age45", age45),
    ]:
        change = period_change_pct(
            df=df,
            column="real_take_home_yen",
            start_year=1990,
            end_year=2025,
        )

        start = float(
            df.loc[
                df["year"] == 1990,
                "real_take_home_yen",
            ].iloc[0]
        )

        end = float(
            df.loc[
                df["year"] == 2025,
                "real_take_home_yen",
            ].iloc[0]
        )

        print(f"{label}: {start:,.0f}円 → {end:,.0f}円 ({change:+.3f}%)")

    # ----------------------------------------
    # 8. 2025年の税による相殺
    # ----------------------------------------

    row35 = age35.loc[age35["year"] == 2025].iloc[0]

    row45 = age45.loc[age45["year"] == 2025].iloc[0]

    print("\n=== 2025年 35歳→45歳 ===")

    print(
        "介護保険料:",
        f"{row45['long_term_care_yen']:,.0f}円",
    )

    print(
        "所得税差:",
        f"{row45['income_tax_yen'] - row35['income_tax_yen']:+,.0f}円",
    )

    print(
        "住民税差:",
        f"{row45['resident_tax_yen'] - row35['resident_tax_yen']:+,.0f}円",
    )

    print(
        "名目手取り差:",
        f"{row45['nominal_take_home_yen'] - row35['nominal_take_home_yen']:+,.0f}円",
    )

    print(
        "実質手取り差:",
        f"{row45['real_take_home_yen'] - row35['real_take_home_yen']:+,.0f}円",
    )

    print(
        "負担率差:",
        (
            f"{(row45['effective_burden_rate'] - row35['effective_burden_rate']) * 100:+.3f} pt"
        ),
    )


if __name__ == "__main__":
    main()
