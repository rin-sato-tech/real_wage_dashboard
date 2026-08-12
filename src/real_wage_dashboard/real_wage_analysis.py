import pandas as pd


def merge_wage_and_cpi(
    wage_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """名目賃金とCPIを年月で内部結合する。"""

    wage_required = {
        "date",
        "nominal_wage_amount",
    }

    cpi_required = {
        "date",
        "index_value",
    }

    if not wage_required.issubset(wage_df.columns):
        missing = wage_required - set(wage_df.columns)
        raise ValueError(f"名目賃金データに必要な列がありません: {sorted(missing)}")

    if not cpi_required.issubset(cpi_df.columns):
        missing = cpi_required - set(cpi_df.columns)
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    wage = wage_df[
        [
            "date",
            "nominal_wage_amount",
        ]
    ].copy()

    cpi = cpi_df[
        [
            "date",
            "index_value",
        ]
    ].copy()

    result = wage.merge(
        cpi,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_real_wage_amount(df: pd.DataFrame) -> pd.DataFrame:
    """CPIで実質化した賃金額を計算する。"""

    required_columns = {
        "nominal_wage_amount",
        "index_value",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["index_value"] <= 0).any():
        raise ValueError("CPIには0より大きい値が必要です。")

    result["real_wage_amount"] = (
        result["nominal_wage_amount"] / result["index_value"] * 100
    )

    return result


def add_wage_indices(
    df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """名目賃金と実質賃金を基準年平均=100に指数化する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
        "real_wage_amount",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    base_df = result[result["date"].dt.year == base_year]

    if base_df.empty:
        raise ValueError(f"{base_year}年の基準データがありません。")

    nominal_base = base_df["nominal_wage_amount"].mean()

    real_base = base_df["real_wage_amount"].mean()

    if nominal_base <= 0 or real_base <= 0:
        raise ValueError("基準年平均は0より大きい必要があります。")

    result["nominal_wage_index"] = result["nominal_wage_amount"] / nominal_base * 100

    result["real_wage_index"] = result["real_wage_amount"] / real_base * 100

    return result


def create_real_wage_dataframe(
    wage_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """名目賃金とCPIを結合し、実質賃金を計算する。"""

    result = merge_wage_and_cpi(wage_df, cpi_df)

    result = add_real_wage_amount(result)

    result = add_wage_indices(result, base_year=base_year)

    return result
