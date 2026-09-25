from pathlib import Path

import math

import pandas as pd


SNAPSHOT_DIR = Path("data/snapshots")

MAIN_PATH = SNAPSHOT_DIR / "take_home_main_series.csv"

SHAPLEY_PATH = SNAPSHOT_DIR / "take_home_real_shapley_4factor.csv"

FIXED_POLICY_PATH = SNAPSHOT_DIR / "take_home_fixed_policy_comparison.csv"

SCENARIO_PATH = SNAPSHOT_DIR / "take_home_scenario_grid.csv"


def assert_close(
    actual: float,
    expected: float,
    *,
    abs_tol: float,
    label: str,
) -> None:
    """主要値が期待値と一致することを確認する。"""

    if not math.isclose(
        actual,
        expected,
        rel_tol=0.0,
        abs_tol=abs_tol,
    ):
        raise AssertionError(f"{label}: actual={actual}, expected={expected}")


def get_unique_row(
    df: pd.DataFrame,
    condition: pd.Series,
    label: str,
) -> pd.Series:
    """条件に一致する行を一意に取得する。"""

    selected = df.loc[condition]

    if len(selected) != 1:
        raise AssertionError(f"{label} を一意に取得できません: {len(selected)} rows")

    return selected.iloc[0]


def main() -> None:
    main_df = pd.read_csv(MAIN_PATH)

    shapley_df = pd.read_csv(SHAPLEY_PATH)

    fixed_df = pd.read_csv(FIXED_POLICY_PATH)

    scenario_df = pd.read_csv(SCENARIO_PATH)

    # ========================================
    # 1. 2025年主系列
    # ========================================

    main_2025 = get_unique_row(
        main_df,
        main_df["year"] == 2025,
        "2025年主系列",
    )

    assert_close(
        float(main_2025["gross_salary_yen"]),
        4_267_634.0,
        abs_tol=1.0,
        label="2025年額面賃金",
    )

    assert_close(
        float(main_2025["nominal_take_home_yen"]),
        3_381_643.9005,
        abs_tol=1.0,
        label="2025年名目手取り",
    )

    assert_close(
        float(main_2025["real_take_home_yen"]),
        2_965_703.925,
        abs_tol=1.0,
        label="2025年実質手取り",
    )

    assert_close(
        float(main_2025["effective_burden_rate"]),
        0.207607,
        abs_tol=1e-6,
        label="2025年実効負担率",
    )

    # ========================================
    # 2. 1990→2025 Shapley
    # ========================================

    shapley_long = get_unique_row(
        shapley_df,
        shapley_df["period"] == "1990→2025",
        "1990→2025 Shapley",
    )

    expected_shapley = {
        "wage_effect_pct_of_start": 6.491,
        "tax_policy_effect_pct_of_start": 1.274,
        "social_insurance_policy_effect_pct_of_start": -4.727,
        "price_effect_pct_of_start": -21.678,
    }

    for column, expected in expected_shapley.items():
        assert_close(
            float(shapley_long[column]),
            expected,
            abs_tol=0.01,
            label=column,
        )

    # ========================================
    # 3. 1990年制度固定比較
    # ========================================

    fixed_2025 = get_unique_row(
        fixed_df,
        fixed_df["year"] == 2025,
        "2025年固定制度比較",
    )

    assert_close(
        float(fixed_2025["fixed_1990_nominal_take_home_yen"]),
        3_501_446.213,
        abs_tol=1.0,
        label=("2025年 1990年制度固定手取り"),
    )

    assert_close(
        float(fixed_2025["nominal_take_home_yen_difference_yen"]),
        -119_802.3125,
        abs_tol=1.0,
        label=("2025年 実際－1990年制度固定"),
    )

    assert_close(
        float(fixed_2025["burden_rate_difference_pt"]),
        2.807230,
        abs_tol=1e-5,
        label="2025年負担率差",
    )

    # ========================================
    # 4. 年収500万円シナリオ
    # ========================================

    scenario_35 = get_unique_row(
        scenario_df,
        (scenario_df["年"] == 2025)
        & (scenario_df["年齢"] == 35)
        & (scenario_df["年収（万円）"] == 500),
        "2025年・35歳・500万円",
    )

    assert_close(
        float(scenario_35["名目手取り（円）"]),
        3_898_918.0,
        abs_tol=2.0,
        label=("2025年・35歳・500万円 名目手取り"),
    )

    assert_close(
        float(scenario_35["実効負担率（%）"]),
        22.021642,
        abs_tol=1e-5,
        label=("2025年・35歳・500万円 実効負担率"),
    )

    scenario_45 = get_unique_row(
        scenario_df,
        (scenario_df["年"] == 2025)
        & (scenario_df["年齢"] == 45)
        & (scenario_df["年収（万円）"] == 500),
        "2025年・45歳・500万円",
    )

    assert_close(
        float(scenario_45["介護保険（円）"]),
        40_086.1,
        abs_tol=1.0,
        label=("2025年・45歳・500万円 介護保険料"),
    )

    # ========================================
    # 完了
    # ========================================

    print("=== final consistency check ===")
    print("2025年主系列: OK")
    print("1990→2025 Shapley: OK")
    print("1990年制度固定比較: OK")
    print("年収500万円シナリオ: OK")
    print("主要数値の整合性確認: PASS")


if __name__ == "__main__":
    main()
