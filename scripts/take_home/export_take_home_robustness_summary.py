from pathlib import Path

import pandas as pd

OUTPUT_PATH = Path("data/snapshots/take_home_robustness_summary.csv")


def main() -> None:
    rows = [
        # ------------------------------------
        # 住民税タイミング
        # ------------------------------------
        {
            "check": "resident_tax_timing",
            "comparison": "income_year",
            "period": "1991→2025",
            "metric": "real_take_home_change_pct",
            "value": -19.363,
            "unit": "pct",
            "note": ("主分析。所得年tに賦課年度t+1の住民税を対応。"),
        },
        {
            "check": "resident_tax_timing",
            "comparison": "cash_flow",
            "period": "1991→2025",
            "metric": "real_take_home_change_pct",
            "value": -19.480,
            "unit": "pct",
            "note": ("前年所得に基づく年税額を当年へ対応する感応度分析。"),
        },
        # ------------------------------------
        # 男女差
        # ------------------------------------
        {
            "check": "sex",
            "comparison": "male",
            "period": "1990→2025",
            "metric": "real_take_home_change_pct",
            "value": -18.640,
            "unit": "pct",
            "note": "主分析。",
        },
        {
            "check": "sex",
            "comparison": "female",
            "period": "1990→2025",
            "metric": "real_take_home_change_pct",
            "value": -18.784,
            "unit": "pct",
            "note": ("厚生年金保険料率の男女差を反映。差は1990～1993年のみ。"),
        },
        # ------------------------------------
        # 年齢・介護保険
        # ------------------------------------
        {
            "check": "age_long_term_care",
            "comparison": "age35",
            "period": "1990→2025",
            "metric": "real_take_home_change_pct",
            "value": -18.640,
            "unit": "pct",
            "note": "主分析。介護保険第2号被保険者外。",
        },
        {
            "check": "age_long_term_care",
            "comparison": "age45",
            "period": "1990→2025",
            "metric": "real_take_home_change_pct",
            "value": -19.315,
            "unit": "pct",
            "note": ("40～64歳の介護保険料を反映。"),
        },
        {
            "check": "age_long_term_care",
            "comparison": "age45_minus_age35",
            "period": "2025",
            "metric": "nominal_take_home_difference_yen",
            "value": -28043.1,
            "unit": "yen",
            "note": ("介護保険料33,243.1円の一部を所得税・住民税減が相殺。"),
        },
        # ------------------------------------
        # 賃金系列
        # ------------------------------------
        {
            "check": "wage_series",
            "comparison": "level_series",
            "period": "1990→2025",
            "metric": "real_gross_wage_change_pct",
            "value": -14.763,
            "unit": "pct",
            "note": ("毎月勤労統計の実額月次値から年平均を作成。"),
        },
        {
            "check": "wage_series",
            "comparison": "official_yoy_chained",
            "period": "1990→2025",
            "metric": "real_gross_wage_change_pct",
            "value": -14.364,
            "unit": "pct",
            "note": "公表前年比を1990年から連鎖。",
        },
        {
            "check": "wage_series",
            "comparison": "level_series",
            "period": "2015→2025",
            "metric": "real_gross_wage_change_pct",
            "value": -3.320,
            "unit": "pct",
            "note": ("毎月勤労統計の実額月次値から年平均を作成。"),
        },
        {
            "check": "wage_series",
            "comparison": "official_yoy_chained",
            "period": "2015→2025",
            "metric": "real_gross_wage_change_pct",
            "value": -5.881,
            "unit": "pct",
            "note": "公表前年比を連鎖。",
        },
        # ------------------------------------
        # 一時的税制措置
        # ------------------------------------
        {
            "check": "temporary_tax_measures",
            "comparison": "actual_policy",
            "period": "1990→2025",
            "metric": "interpretation",
            "value": None,
            "unit": None,
            "note": ("一時的減税を含む実際の制度。実質手取りのピークは1996年。"),
        },
        {
            "check": "temporary_tax_measures",
            "comparison": "structural_policy",
            "period": "1990→2025",
            "metric": "interpretation",
            "value": None,
            "unit": None,
            "note": (
                "1994～1996、1998、2024年等の"
                "一時的減税を除外しても、"
                "実質手取りのピークは1996年。"
            ),
        },
    ]

    result = pd.DataFrame(rows)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"saved: {OUTPUT_PATH} ({len(result)} rows)")

    print("\n=== robustness summary ===")
    print(
        result.to_string(
            index=False,
        )
    )


if __name__ == "__main__":
    main()
