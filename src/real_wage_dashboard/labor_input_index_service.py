from pathlib import Path

import pandas as pd


def load_annual_hours_index(
    file_path: str | Path,
    value_column: str,
) -> pd.DataFrame:
    """毎月勤労統計のTLシートから年平均労働時間指数を読み込む。"""

    raw = pd.read_excel(
        file_path,
        sheet_name="TL",
        header=None,
    )

    first_column = raw.iloc[:, 0].astype(str).str.strip()

    index_rows = raw.index[first_column.str.startswith("指数(Indices)")]

    yoy_rows = raw.index[first_column.str.startswith("前年比(Year-on-year")]

    if len(index_rows) != 1:
        raise ValueError(f"指数セクションを一意に特定できません: {list(index_rows)}")

    if len(yoy_rows) != 1:
        raise ValueError(f"前年比セクションを一意に特定できません: {list(yoy_rows)}")

    index_start = int(index_rows[0])
    index_end = int(yoy_rows[0])

    if index_start >= index_end:
        raise ValueError("指数セクションと前年比セクションの位置関係が不正です。")

    # 第1列=年、第2列=年平均指数
    block = raw.iloc[
        index_start:index_end,
        [0, 1],
    ].copy()

    block.columns = [
        "year",
        value_column,
    ]

    block["year"] = pd.to_numeric(
        block["year"],
        errors="coerce",
    )

    block[value_column] = pd.to_numeric(
        block[value_column],
        errors="coerce",
    )

    result = (
        block.dropna(
            subset=[
                "year",
                value_column,
            ]
        )
        .assign(year=lambda x: x["year"].astype(int))
        .drop_duplicates(
            subset=["year"],
            keep="last",
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    if result.empty:
        raise ValueError("有効な年平均労働時間指数を取得できません。")

    return result


def create_official_working_hours_index_dataframe(
    total_hours_path: str | Path,
    scheduled_hours_path: str | Path,
    overtime_hours_path: str | Path,
) -> pd.DataFrame:
    """公式の総実・所定内・所定外労働時間指数を結合する。"""

    total = load_annual_hours_index(
        total_hours_path,
        "official_total_hours_index",
    )

    scheduled = load_annual_hours_index(
        scheduled_hours_path,
        "official_scheduled_hours_index",
    )

    overtime = load_annual_hours_index(
        overtime_hours_path,
        "official_overtime_hours_index",
    )

    return total.merge(
        scheduled,
        on="year",
        how="inner",
        validate="one_to_one",
    ).merge(
        overtime,
        on="year",
        how="inner",
        validate="one_to_one",
    )
