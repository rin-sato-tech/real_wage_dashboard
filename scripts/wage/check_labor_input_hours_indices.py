from pathlib import Path

import pandas as pd

START_YEAR = 1990
END_YEAR = 2025
SHEET_NAME = "TL"

INDEX_FILES = {
    "総実労働時間": Path("data/raw/labor_input/total_hours_index_5plus.xls"),
    "所定内労働時間": Path("data/raw/labor_input/scheduled_hours_index_5plus.xls"),
    "所定外労働時間": Path("data/raw/labor_input/overtime_hours_index_5plus.xls"),
}


def load_annual_index(
    path: Path,
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> tuple[float, float]:
    """公式労働時間指数の年平均から開始年・終了年を取得する。"""

    df = pd.read_excel(
        path,
        sheet_name=SHEET_NAME,
        header=None,
        engine="xlrd",
    )

    # TLシート先頭の「指数（Indices）」表を利用する。
    # 同一シート後半にも年を持つ別表があるため、各年の最初の出現を採用する。
    data = pd.DataFrame(
        {
            "year": pd.to_numeric(df.iloc[:, 0], errors="coerce"),
            "annual_index": pd.to_numeric(df.iloc[:, 1], errors="coerce"),
        }
    )

    data = (
        data.dropna(subset=["year", "annual_index"])
        .drop_duplicates(subset=["year"], keep="first")
        .copy()
    )

    data["year"] = data["year"].astype(int)

    start = data.loc[
        data["year"] == start_year,
        "annual_index",
    ]

    end = data.loc[
        data["year"] == end_year,
        "annual_index",
    ]

    if len(start) != 1 or len(end) != 1:
        raise ValueError(
            f"{path.name}: "
            f"{start_year}年または{end_year}年の年平均指数を取得できません。"
        )

    return float(start.iloc[0]), float(end.iloc[0])


def main() -> None:
    records = []

    for indicator, path in INDEX_FILES.items():
        start_index, end_index = load_annual_index(path)

        change_pct = (end_index / start_index - 1) * 100

        records.append(
            {
                "indicator": indicator,
                "start_year": START_YEAR,
                "start_index": start_index,
                "end_year": END_YEAR,
                "end_index": end_index,
                "change_pct": change_pct,
            }
        )

    result = pd.DataFrame(records)

    print("=== 公式労働時間指数 1990→2025年 ===")
    print(
        result.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )


if __name__ == "__main__":
    main()
