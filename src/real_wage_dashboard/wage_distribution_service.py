from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

EMPLOYMENT_DISTRIBUTION_STATS_ID_2015_2019 = "0003268283"
EMPLOYMENT_DISTRIBUTION_STATS_ID_2020_2023 = "0003446899"

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

EMPLOYMENT_CODE_MAP = {
    "02": "regular",
    "03": "nonregular",
}

QUANTILE_CODE_MAP = {
    "1280": "p10",
    "1290": "p25",
    "1300": "p50",
    "1310": "p75",
    "1320": "p90",
    "1330": "decile_dispersion",
    "1340": "quartile_dispersion",
}

EMPLOYMENT_TYPES = [
    "regular",
    "nonregular",
]


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


SEX_LABELS = {
    "total": "男女計学歴計",
    "male": "男学歴計",
    "female": "女学歴計",
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""

    return str(value).replace(" ", "").replace("　", "").replace("\n", "")


def find_sex_block_start(
    df: pd.DataFrame,
    sex: str,
) -> int:
    if sex not in SEX_LABELS:
        raise ValueError(f"未対応の性別です: {sex}")

    target = SEX_LABELS[sex]

    for row_index, row in df.iterrows():
        for value in row:
            normalized = normalize_text(value)

            if normalized == target:
                return row_index

    raise ValueError(f"性別ブロックが見つかりません: {sex}")


def extract_distribution_by_sex_from_dataframe(
    df: pd.DataFrame,
    year: int,
    sex: str,
) -> dict[str, float | int | str]:
    start_row = find_sex_block_start(
        df=df,
        sex=sex,
    )

    block = df.iloc[start_row:].copy()

    result = extract_main_distribution_from_dataframe(
        df=block,
        year=year,
    )

    result["sex"] = sex

    return result


def load_wage_distribution_history_by_sex(
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

        df = pd.read_excel(
            path,
            sheet_name=DEFAULT_SHEET_NAME,
            header=None,
        )

        for sex in [
            "total",
            "male",
            "female",
        ]:
            rows.append(
                extract_distribution_by_sex_from_dataframe(
                    df=df,
                    year=year,
                    sex=sex,
                )
            )

    return pd.DataFrame(rows).sort_values(["year", "sex"]).reset_index(drop=True)


def find_employment_distribution_file(
    data_dir: Path,
    year: int,
    employment: str,
) -> Path:
    if employment not in EMPLOYMENT_TYPES:
        raise ValueError(
            f"Unknown employment type: {employment}"
        )

    pattern = (
        f"wage_distribution_employment_"
        f"{year}_{employment}.xls*"
    )

    matches = list(data_dir.glob(pattern))

    if len(matches) != 1:
        raise FileNotFoundError(
            f"{pattern}: expected 1 file, "
            f"found {len(matches)}"
        )

    return matches[0]


def load_employment_distribution(
    path: Path,
    year: int,
    employment: str,
    sheet_name: str = "産業計",
) -> dict:
    if employment not in EMPLOYMENT_TYPES:
        raise ValueError(
            f"Unknown employment type: {employment}"
        )

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=None,
    )

    result = extract_main_distribution_from_dataframe(
        df,
        year,
    )

    result["employment"] = employment

    return result


def parse_employment_distribution_values(
    values: list[dict],
) -> pd.DataFrame:
    records: dict[tuple[int, str], dict] = {}

    for value in values:
        year = int(value["@time"][:4])

        employment = EMPLOYMENT_CODE_MAP[
            value["@cat05"]
        ]

        metric = QUANTILE_CODE_MAP[
            value["@cat02"]
        ]

        key = (year, employment)

        if key not in records:
            records[key] = {
                "year": year,
                "employment": employment,
            }

        records[key][metric] = float(value["$"])

    return (
        pd.DataFrame(records.values())
        .sort_values(["employment", "year"])
        .reset_index(drop=True)
    )


def load_employment_distribution_2015_2019(
    app_id: str,
) -> pd.DataFrame:
    url = (
        "https://api.e-stat.go.jp/"
        "rest/3.0/app/json/getStatsData"
    )

    params = {
        "appId": app_id,
        "statsDataId":
            EMPLOYMENT_DISTRIBUTION_STATS_ID_2015_2019,
        "cdCat01": "010",
        "cdCat02":
            "1280,1290,1300,1310,1320,1330,1340",
        "cdCat03": "01",
        "cdCat04": "01",
        "cdCat05": "02,03",
        "cdCat06": "100010",
        "cdCat07": "01",
        "cdTime": ",".join(
            [
                "2015000000",
                "2016000000",
                "2017000000",
                "2018000000",
                "20190000000",
            ]
        ),
        "limit": 1000,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    result = payload["GET_STATS_DATA"]["RESULT"]

    if result["STATUS"] != 0:
        raise RuntimeError(
            f"e-Stat API error: {result}"
        )

    values = (
        payload["GET_STATS_DATA"]
        ["STATISTICAL_DATA"]
        ["DATA_INF"]
        ["VALUE"]
    )

    return parse_employment_distribution_values(
        values
    )


def load_employment_distribution_2020_2023(
    app_id: str,
) -> pd.DataFrame:
    url = (
        "https://api.e-stat.go.jp/"
        "rest/3.0/app/json/getStatsData"
    )

    params = {
        "appId": app_id,
        "statsDataId":
            EMPLOYMENT_DISTRIBUTION_STATS_ID_2020_2023,
        "cdCat01": "01",
        "cdCat02":
            "1280,1290,1300,1310,1320,1330,1340",
        "cdCat03": "01",
        "cdCat04": "01",
        "cdCat05": "02,03",
        "cdCat06": "01",
        "cdCat07": "01",
        "cdCat08": "02",
        "cdTime": ",".join(
            [
                "2020000000",
                "2021000000",
                "2022000000",
                "2023000000",
            ]
        ),
        "limit": 1000,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    result = payload["GET_STATS_DATA"]["RESULT"]

    if result["STATUS"] != 0:
        raise RuntimeError(
            f"e-Stat API error: {result}"
        )

    values = (
        payload["GET_STATS_DATA"]
        ["STATISTICAL_DATA"]
        ["DATA_INF"]
        ["VALUE"]
    )

    return parse_employment_distribution_values(
        values
    )


def load_employment_distribution_2024_2025(
    data_dir: Path,
) -> pd.DataFrame:
    records = []

    for year in [2024, 2025]:
        for employment in [
            "regular",
            "nonregular",
        ]:
            path = find_employment_distribution_file(
                data_dir,
                year,
                employment,
            )

            record = load_employment_distribution(
                path,
                year,
                employment,
            )

            records.append(record)

    return (
        pd.DataFrame(records)
        .sort_values(["employment", "year"])
        .reset_index(drop=True)
    )


def load_wage_distribution_history_by_employment(
    app_id: str,
    excel_data_dir: Path,
) -> pd.DataFrame:
    historical = load_employment_distribution_2015_2019(app_id)

    recent_api = load_employment_distribution_2020_2023(app_id)

    recent_excel = load_employment_distribution_2024_2025(excel_data_dir)

    result = pd.concat(
        [
            historical,
            recent_api,
            recent_excel,
        ],
        ignore_index=True,
    )

    return (
        result.sort_values(
            ["employment", "year"]
        )
        .reset_index(drop=True)
    )
