import json

import pandas as pd

from real_wage_dashboard.config import (
    LFS_EMPLOYMENT_BY_AGE_PATH,
    LFS_EMPLOYMENT_TYPE_HOURS_SNAPSHOT_PATH,
    LFS_HOURS_BY_AGE_PATH,
    LFS_HOURS_BY_AGE_SEX_SNAPSHOT_PATH,
    LFS_WORKING_HOURS_DISTRIBUTION_SNAPSHOT_PATH,
    WAGE_DATA_PATH,
)
from real_wage_dashboard.labor_force_analysis import (
    create_age_hours_decomposition,
    create_age_hours_period_summary,
    create_age_sex_hours_period_summary,
    create_detailed_working_hours_distribution_change,
    create_employment_count_decomposition,
    create_employment_structure_summary,
    create_employment_type_hours_period_summary,
    create_total_labor_input_decomposition,
    create_total_labor_input_period_summary,
    create_working_hours_distribution_change,
    create_working_hours_distribution_period_summary,
)
from real_wage_dashboard.labor_force_service import (
    create_lfs_employment_type_hours_dataframe,
    create_lfs_hours_by_age_sex_dataframe,
    create_lfs_working_hours_distribution_dataframe,
    load_lfs_employment_by_age,
    load_lfs_hours_by_age,
)
from real_wage_dashboard.labor_input_analysis import (
    create_employment_type_composition_period_summary,
    create_labor_input_dataframe,
    create_yearly_weighted_means,
    summarize_long_term_wage_decomposition,
)
from real_wage_dashboard.wage_service import load_wage_csv

MAIN_PERIODS = [
    (2000, 2025),
    (2015, 2025),
]

ROBUSTNESS_PERIODS = [
    (2000, 2010),
    (2012, 2019),
    (2012, 2025),
    (2015, 2025),
    (2020, 2025),
    (2000, 2025),
]

EMPLOYMENT_TYPE_PERIODS = [
    (2012, 2019),
    (2012, 2025),
    (2015, 2025),
    (2020, 2025),
]

COMPOSITION_PERIODS = [
    (1993, 2025),
    (2000, 2025),
    (2015, 2025),
]

DISTRIBUTION_PERIODS = [
    *ROBUSTNESS_PERIODS,
    (2019, 2020),
]

AGE_GROUPS = [
    "15～24歳",
    "25～34歳",
    "35～44歳",
    "45～54歳",
    "55～64歳",
    "65歳以上",
]

EMPLOYMENT_TYPES = {
    "0": "就業形態計",
    "1": "一般労働者",
    "2": "パートタイム労働者",
}

ANNUAL_COLUMNS = [
    "nominal_wage_amount",
    "total_hours",
    "scheduled_hours",
    "overtime_hours",
    "working_days",
]


def print_section(title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def print_df(df: pd.DataFrame) -> None:
    print(
        df.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )


def load_json(path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def create_annual_levels(
    df: pd.DataFrame,
    employment_type: str,
) -> pd.DataFrame:
    yearly = create_yearly_weighted_means(
        df,
        columns=ANNUAL_COLUMNS,
    )

    yearly["weighted_approx_hourly_wage"] = (
        yearly["nominal_wage_amount"]
        / yearly["total_hours"]
    )

    yearly["scheduled_hours_per_workday"] = (
        yearly["scheduled_hours"]
        / yearly["working_days"]
    )

    yearly.insert(
        0,
        "employment_type",
        employment_type,
    )

    return yearly


def main() -> None:
    # ============================================================
    # 毎月勤労統計
    # ============================================================

    raw_wage = load_wage_csv(WAGE_DATA_PATH)

    labor_input = {
        label: create_labor_input_dataframe(
            raw_wage,
            establishment_size="T",
            employment_type=code,
        )
        for code, label in EMPLOYMENT_TYPES.items()
    }

    # ------------------------------------------------------------
    # 3.2 / 3.3 年平均水準
    # ------------------------------------------------------------
    print_section("3.2 / 3.3 毎月勤労統計 年平均水準")

    annual_levels = pd.concat(
        [
            create_annual_levels(df, label)
            for label, df in labor_input.items()
        ],
        ignore_index=True,
    )

    annual_levels = annual_levels.loc[
        annual_levels["year"].isin(
            [1990, 1993, 2000, 2015, 2025]
        )
    ]

    print_df(
        annual_levels[
            [
                "employment_type",
                "year",
                "nominal_wage_amount",
                "weighted_approx_hourly_wage",
                "total_hours",
                "scheduled_hours",
                "overtime_hours",
                "working_days",
                "scheduled_hours_per_workday",
            ]
        ]
    )

    # ------------------------------------------------------------
    # 3.3 月額賃金 = 時間当たり賃金 × 労働時間
    # ------------------------------------------------------------
    print_section("3.3 月額賃金・時間当たり賃金・総実労働時間")

    wage_rows = []

    for employment_type, df in labor_input.items():
        for start_year, end_year in MAIN_PERIODS:
            result = summarize_long_term_wage_decomposition(
                df,
                start_year=start_year,
                end_year=end_year,
            )

            wage_rows.append(
                {
                    "employment_type": employment_type,
                    **result,
                }
            )

    wage_summary = pd.DataFrame(wage_rows)

    print_df(
        wage_summary[
            [
                "employment_type",
                "start_year",
                "end_year",
                "wage_change_pct",
                "hourly_wage_change_pct",
                "total_hours_change_pct",
                "wage_log_change",
                "hourly_wage_log_contribution",
                "total_hours_log_contribution",
            ]
        ]
    )

    # ------------------------------------------------------------
    # 3.2 / 3.3 / 4.3 就業形態構成分解
    # ------------------------------------------------------------
    print_section("3.2 / 3.3 / 4.3 就業形態構成分解")

    composition = create_employment_type_composition_period_summary(
        total_df=labor_input["就業形態計"],
        regular_df=labor_input["一般労働者"],
        part_time_df=labor_input["パートタイム労働者"],
        periods=COMPOSITION_PERIODS,
    )

    print_df(
        composition[
            [
                "start_year",
                "end_year",
                "indicator",
                "published_change_pct",
                "within_contribution_pct",
                "composition_contribution_pct",
                "residual_contribution_pct",
                "part_time_share_start",
                "part_time_share_end",
            ]
        ]
    )

    # ============================================================
    # 労働力調査：保存済み年齢別データ
    # ============================================================

    employment_df = load_lfs_employment_by_age(
        LFS_EMPLOYMENT_BY_AGE_PATH,
        start_year=2000,
        end_year=2025,
    )

    hours_df = load_lfs_hours_by_age(
        LFS_HOURS_BY_AGE_PATH,
    )

    # ------------------------------------------------------------
    # 3.4 年齢別就業者数・就業率
    # ------------------------------------------------------------
    for start_year, end_year in MAIN_PERIODS:
        print_section(
            f"3.4 年齢別就業構造 {start_year}→{end_year}"
        )

        structure = create_employment_structure_summary(
            employment_df,
            start_year=start_year,
            end_year=end_year,
        )

        structure = create_employment_count_decomposition(
            structure
        )

        print_df(
            structure[
                [
                    "age_group",
                    "start_employed_persons",
                    "end_employed_persons",
                    "employed_persons_change",
                    "employed_persons_change_pct",
                    "start_employment_rate",
                    "end_employment_rate",
                    "employment_rate_change_pt",
                    "population_effect",
                    "employment_rate_effect",
                    "decomposition_error",
                ]
            ]
        )

    # ------------------------------------------------------------
    # 3.5 平均週間就業時間
    # ------------------------------------------------------------
    print_section("3.5 平均週間就業時間 期間要約")

    age_hours_summary = create_age_hours_period_summary(
        hours_df,
        periods=MAIN_PERIODS,
    )

    print_df(age_hours_summary)

    for start_year, end_year in MAIN_PERIODS:
        print_section(
            f"3.5 年齢別平均週間就業時間分解 "
            f"{start_year}→{end_year}"
        )

        decomposition = create_age_hours_decomposition(
            hours_df,
            start_year=start_year,
            end_year=end_year,
        )

        print_df(
            decomposition[
                [
                    "age_group",
                    "start_hours",
                    "end_hours",
                    "within_effect",
                    "composition_effect",
                ]
            ]
        )

    # ------------------------------------------------------------
    # 3.7 / 4.2 総労働投入
    # ------------------------------------------------------------
    print_section("3.7 / 4.2 総労働投入 期間要約")

    total_input = create_total_labor_input_period_summary(
        hours_df,
        periods=ROBUSTNESS_PERIODS,
    )

    print_df(total_input)

    for start_year, end_year in MAIN_PERIODS:
        print_section(
            f"3.7 年齢階級別総労働投入 "
            f"{start_year}→{end_year}"
        )

        decomposition = create_total_labor_input_decomposition(
            hours_df,
            start_year=start_year,
            end_year=end_year,
        )

        decomposition["change_pct"] = (
            decomposition["aggregate_weekly_hours_change"]
            / decomposition["start_aggregate_weekly_hours"]
            * 100
        )

        print_df(
            decomposition[
                [
                    "age_group",
                    "start_aggregate_weekly_hours",
                    "end_aggregate_weekly_hours",
                    "aggregate_weekly_hours_change",
                    "change_pct",
                    "persons_effect",
                    "hours_effect",
                    "decomposition_error",
                ]
            ]
        )

    # ============================================================
    # 労働力調査：固定したe-Stat APIレスポンス
    # ============================================================

    distribution_response = load_json(
        LFS_WORKING_HOURS_DISTRIBUTION_SNAPSHOT_PATH
    )

    distribution_df = (
        create_lfs_working_hours_distribution_dataframe(
            distribution_response
        )
    )

    sex_response = load_json(
        LFS_HOURS_BY_AGE_SEX_SNAPSHOT_PATH
    )

    sex_df = create_lfs_hours_by_age_sex_dataframe(
        sex_response
    )

    employment_type_response = load_json(
        LFS_EMPLOYMENT_TYPE_HOURS_SNAPSHOT_PATH
    )

    employment_type_hours_df = (
        create_lfs_employment_type_hours_dataframe(
            employment_type_response
        )
    )

    # ------------------------------------------------------------
    # 3.6 / 4.2 就業時間分布
    # ------------------------------------------------------------
    print_section("3.6 / 4.2 就業時間3区分 期間要約")

    distribution_summary = (
        create_working_hours_distribution_period_summary(
            distribution_df,
            periods=DISTRIBUTION_PERIODS,
            age_group="15歳以上",
        )
    )

    print_df(distribution_summary)

    for start_year, end_year in MAIN_PERIODS:
        print_section(
            f"3.6 年齢別就業時間3区分 "
            f"{start_year}→{end_year}"
        )

        change = create_working_hours_distribution_change(
            distribution_df,
            start_year=start_year,
            end_year=end_year,
        )

        change = change.loc[
            change["age_group"].isin(AGE_GROUPS)
        ]

        print_df(
            change[
                [
                    "age_group",
                    "hours_1_34_share_change_pt",
                    "hours_35_48_share_change_pt",
                    "hours_49_plus_share_change_pt",
                ]
            ]
        )

    print_section("3.6 詳細7区分 2018→2025")

    detailed = create_detailed_working_hours_distribution_change(
        distribution_df,
        start_year=2018,
        end_year=2025,
    )

    detailed = detailed.loc[
        detailed["age_group"] == "15歳以上"
    ].copy()

    print_df(
        detailed[
            [
                "age_group",
                "hours_1_14_share_change_pt",
                "hours_15_29_share_change_pt",
                "hours_30_34_share_change_pt",
                "hours_35_39_share_change_pt",
                "hours_40_48_share_change_pt",
                "hours_49_59_share_change_pt",
                "hours_60_plus_share_change_pt",
            ]
        ]
    )

    # ------------------------------------------------------------
    # 3.5 / 4.4 性別追加分解
    # ------------------------------------------------------------
    print_section("3.5 / 4.4 年齢層内効果の性別分解")

    sex_summary = create_age_sex_hours_period_summary(
        hours_df,
        sex_df,
        periods=ROBUSTNESS_PERIODS,
    )

    sex_summary["sex_within_share_pct"] = (
        sex_summary["sex_within_effect_hours"]
        / sex_summary["within_age_effect_hours"]
        * 100
    )

    print_df(sex_summary)

    # ------------------------------------------------------------
    # 3.6 / 4.4 正規・非正規別時間分布
    # ------------------------------------------------------------
    for share_column, label in [
        ("hours_1_34_share", "週1～34時間"),
        ("hours_49_plus_share", "週49時間以上"),
    ]:
        print_section(
            f"3.6 / 4.4 正規・非正規別 {label}"
        )

        result = create_employment_type_hours_period_summary(
            employment_type_hours_df,
            periods=EMPLOYMENT_TYPE_PERIODS,
            share_column=share_column,
        ).copy()

        percentage_columns = [
            "published_change",
            "within_employment_type_effect",
            "employment_composition_effect",
            "reconstruction_residual",
        ]

        result[percentage_columns] = (
            result[percentage_columns] * 100
        )

        print_df(
            result[
                [
                    "start_year",
                    "end_year",
                    "age_group",
                    "published_change",
                    "within_employment_type_effect",
                    "employment_composition_effect",
                    "reconstruction_residual",
                ]
            ]
        )


if __name__ == "__main__":
    main()