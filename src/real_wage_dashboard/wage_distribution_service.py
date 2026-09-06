from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_SHEET_NAME = "産業計(規模計)"

DISTRIBUTION_LABELS = {
    "第1・十分位数": "p10",
    "第1・四分位数": "p25",
    "中位数": "p50",
    "第3・四分位数": "p75",
    "第9・十分位数": "p90",
    "十分位分散係数": "decile_dispersion",
    "四分位分散係数": "quartile_dispersion",
}


def normalize_distribution_label(value: object) -> str:
    if pd.isna(value):
        return ""

    return (
        str(value)
        .replace(" ", "")
        .replace("　", "")
        .replace("\n", "")
        .replace("（千円）", "")
        .replace("(千円)", "")
    )


def find_wage_distribution_file(
    data_dir: Path,
    year: int,
) -> Path:
    candidates = list(data_dir.glob(f"wage_distribution_{year}.xls*"))

    if len(candidates) != 1:
        raise ValueError(f"{year}: ファイルが一意に決まりません: {candidates}")

    return candidates[0]


def _extract_first_numeric_to_right(
    row: pd.Series,
    label_column: int,
) -> float:
    for value in row.iloc[label_column + 1 :]:
        if pd.isna(value):
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    raise ValueError("ラベル右側に数値がありません。")


def extract_main_distribution_from_dataframe(
    df: pd.DataFrame,
    year: int,
) -> dict[str, float | int]:
    result: dict[str, float | int] = {
        "year": year,
    }

    found: set[str] = set()

    for _, row in df.iterrows():
        for column, value in row.items():
            normalized = normalize_distribution_label(value)

            for (
                source_label,
                output_name,
            ) in DISTRIBUTION_LABELS.items():
                if source_label not in normalized:
                    continue

                if output_name in found:
                    continue

                result[output_name] = _extract_first_numeric_to_right(
                    row,
                    column,
                )
                found.add(output_name)

        if len(found) == len(DISTRIBUTION_LABELS):
            break

    missing = set(DISTRIBUTION_LABELS.values()) - found

    if missing:
        raise ValueError(f"{year}: 分布特性値を取得できませんでした: {sorted(missing)}")

    return result


def load_main_wage_distribution(
    path: Path,
    year: int,
    sheet_name: str = DEFAULT_SHEET_NAME,
) -> dict[str, float | int]:
    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=None,
    )

    return extract_main_distribution_from_dataframe(
        df=df,
        year=year,
    )


def load_wage_distribution_history(
    data_dir: Path,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    if start_year > end_year:
        raise ValueError("start_year は end_year 以下である必要があります。")

    rows = []

    for year in range(start_year, end_year + 1):
        path = find_wage_distribution_file(
            data_dir=data_dir,
            year=year,
        )

        rows.append(
            load_main_wage_distribution(
                path=path,
                year=year,
            )
        )

    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
