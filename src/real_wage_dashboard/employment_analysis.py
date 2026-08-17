import numpy as np
import pandas as pd


def merge_wage_and_working_hours(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """月次賃金と労働時間を年月でone-to-one結合する。"""

    wage_required = {
        "date",
        "nominal_wage_amount",
    }

    hours_required = {
        "date",
        "working_hours",
    }

    if not wage_required.issubset(wage_df.columns):
        missing = wage_required - set(wage_df.columns)
        raise ValueError(f"賃金データに必要な列がありません: {sorted(missing)}")

    if not hours_required.issubset(working_hours_df.columns):
        missing = hours_required - set(working_hours_df.columns)
        raise ValueError(f"労働時間データに必要な列がありません: {sorted(missing)}")

    wage = wage_df[
        [
            "date",
            "nominal_wage_amount",
        ]
    ].copy()

    hours = working_hours_df[
        [
            "date",
            "working_hours",
        ]
    ].copy()

    result = wage.merge(
        hours,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_approx_hourly_wage(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """月額賃金と総実労働時間から概算時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "working_hours",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["working_hours"] <= 0).any():
        raise ValueError("労働時間は0より大きい必要があります。")

    result["approx_hourly_wage"] = (
        result["nominal_wage_amount"] / result["working_hours"]
    )

    return result


def create_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """賃金・労働時間・概算時間当たり賃金をまとめたDataFrameを作成する。"""

    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    result = add_approx_hourly_wage(result)

    return result


def add_base_year_index(
    df: pd.DataFrame,
    column: str,
    output_column: str,
    base_year: int = 2020,
) -> pd.DataFrame:
    """指定列を基準年平均=100として指数化する。"""

    required_columns = {
        "date",
        column,
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    base_df = result[result["date"].dt.year == base_year].copy()

    base_months = base_df["date"].dt.to_period("M").drop_duplicates()

    if len(base_months) != 12:
        raise ValueError(f"{base_year}年の基準データが12か月揃っていません。")

    base_value = base_df[column].mean()

    if pd.isna(base_value) or base_value <= 0:
        raise ValueError("基準年平均は0より大きい必要があります。")

    result[output_column] = result[column] / base_value * 100

    return result


def add_employment_comparison_indices(
    df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """雇用形態比較で使用する2020年基準指数を追加する。"""

    index_columns = {
        "nominal_wage_amount": "regular_wage_index",
        "working_hours": "working_hours_index",
        "approx_hourly_wage": "approx_hourly_wage_index",
    }

    result = df.copy()

    for column, output_column in index_columns.items():
        result = add_base_year_index(
            result,
            column=column,
            output_column=output_column,
            base_year=base_year,
        )

    return result


def add_employment_changes(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較で使用する主要指標の前年同月比を追加する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["regular_wage_yoy_pct"] = (
        result["nominal_wage_amount"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    result["working_hours_yoy_pct"] = (
        result["working_hours"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    result["approx_hourly_wage_yoy_pct"] = (
        result["approx_hourly_wage"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    return result


def merge_employment_analysis_with_cpi(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較データとCPIを年月でone-to-one結合する。"""

    analysis_required = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }

    cpi_required = {
        "date",
        "index_value",
    }

    if not analysis_required.issubset(df.columns):
        missing = analysis_required - set(df.columns)
        raise ValueError(f"雇用形態比較データに必要な列がありません: {sorted(missing)}")

    if not cpi_required.issubset(cpi_df.columns):
        missing = cpi_required - set(cpi_df.columns)
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    analysis = df.copy()

    cpi = cpi_df[
        [
            "date",
            "index_value",
        ]
    ].copy()

    result = analysis.merge(
        cpi,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_real_employment_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """CPIで実質月額賃金と実質概算時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "approx_hourly_wage",
        "index_value",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["index_value"] <= 0).any():
        raise ValueError("CPIには0より大きい値が必要です。")

    result["real_regular_wage"] = (
        result["nominal_wage_amount"] / result["index_value"] * 100
    )

    result["real_approx_hourly_wage"] = (
        result["approx_hourly_wage"] / result["index_value"] * 100
    )

    return result


def add_real_employment_analysis(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較データにCPIと実質値を追加する。"""

    result = merge_employment_analysis_with_cpi(
        df,
        cpi_df,
    )

    result = add_real_employment_values(result)

    return result


def add_real_employment_indices(
    df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """実質賃金系の2020年基準指数を追加する。"""

    result = df.copy()

    result = add_base_year_index(
        result,
        column="real_regular_wage",
        output_column="real_regular_wage_index",
        base_year=base_year,
    )

    result = add_base_year_index(
        result,
        column="real_approx_hourly_wage",
        output_column="real_approx_hourly_wage_index",
        base_year=base_year,
    )

    return result


def add_real_employment_changes(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """実質賃金系の前年同月比を追加する。"""

    required_columns = {
        "date",
        "real_regular_wage",
        "real_approx_hourly_wage",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["real_regular_wage_yoy_pct"] = (
        result["real_regular_wage"].pct_change(periods=12, fill_method=None).mul(100)
    )

    result["real_approx_hourly_wage_yoy_pct"] = (
        result["real_approx_hourly_wage"]
        .pct_change(periods=12, fill_method=None)
        .mul(100)
    )

    return result


def add_wage_change_decomposition(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """月額賃金の前年同月変化を時間当たり賃金要因と労働時間要因に分解する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    if (
        (result["nominal_wage_amount"] <= 0).any()
        or (result["working_hours"] <= 0).any()
        or (result["approx_hourly_wage"] <= 0).any()
    ):
        raise ValueError("要因分解には0より大きい賃金・労働時間データが必要です。")

    result["wage_log_change_pct"] = (
        np.log(result["nominal_wage_amount"])
        - np.log(result["nominal_wage_amount"].shift(12))
    ) * 100

    result["hourly_wage_contribution_pct"] = (
        np.log(result["approx_hourly_wage"])
        - np.log(result["approx_hourly_wage"].shift(12))
    ) * 100

    result["working_hours_contribution_pct"] = (
        np.log(result["working_hours"]) - np.log(result["working_hours"].shift(12))
    ) * 100

    return result


def create_full_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """雇用形態比較に必要な分析列をまとめて作成する。"""

    result = create_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
    )

    result = add_employment_comparison_indices(
        result,
        base_year=base_year,
    )

    result = add_employment_changes(result)

    result = add_real_employment_analysis(
        result,
        cpi_df,
    )

    result = add_real_employment_indices(
        result,
        base_year=base_year,
    )

    result = add_real_employment_changes(result)

    result = add_wage_change_decomposition(result)

    return result
