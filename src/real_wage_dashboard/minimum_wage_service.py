from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/raw/minimum_wage/regional_minimum_wage_history.xlsx")

SHEET_NAME = "H14～R７"
NATIONAL_AVERAGE_LABEL = "全国加重平均額"

YEAR_MAP = {
    "平成27年度": 2015,
    "平成28年度": 2016,
    "平成29年度": 2017,
    "平成30年度": 2018,
    "令和元年度": 2019,
    "令和２年度": 2020,
    "令和３年度": 2021,
    "令和４年度": 2022,
    "令和５年度": 2023,
    "令和６年度": 2024,
    "令和７年度": 2025,
}


def load_minimum_wage_data(
    path: Path = DATA_PATH,
) -> pd.DataFrame:
    raw = pd.read_excel(
        path,
        sheet_name=SHEET_NAME,
        header=None,
    )

    year_labels = raw.iloc[0, 1:].ffill()
    metrics = raw.iloc[1, 1:]

    national_rows = raw[
        raw.iloc[:, 0].astype(str).str.strip() == NATIONAL_AVERAGE_LABEL
    ]

    if len(national_rows) != 1:
        raise ValueError("全国加重平均額の行を一意に取得できません。")

    records: list[dict[str, int]] = []

    for column_index, (year_label, metric) in enumerate(
        zip(year_labels, metrics, strict=True),
        start=1,
    ):
        if year_label not in YEAR_MAP:
            continue

        if metric != "改定額(円)":
            continue

        value = raw.loc[
            national_rows.index[0],
            column_index,
        ]

        records.append(
            {
                "year": YEAR_MAP[year_label],
                "minimum_wage": round(float(value)),
            }
        )

    df = pd.DataFrame(records).sort_values("year").reset_index(drop=True)

    df["minimum_wage_yoy"] = df["minimum_wage"].pct_change()

    _validate_minimum_wage_data(df)

    return df


def _validate_minimum_wage_data(df: pd.DataFrame) -> None:
    expected_years = list(range(2015, 2026))

    if df["year"].tolist() != expected_years:
        raise ValueError(f"年度が想定と一致しません: {df['year'].tolist()}")

    if df["year"].duplicated().any():
        raise ValueError("年度が重複しています。")

    if df["minimum_wage"].isna().any():
        raise ValueError("最低賃金に欠損があります。")

    if (df["minimum_wage"] <= 0).any():
        raise ValueError("最低賃金に0以下の値があります。")

    if not df["minimum_wage"].is_monotonic_increasing:
        raise ValueError("最低賃金系列が単調非減少ではありません。")
