from pathlib import Path
import re

import pandas as pd

WAGE_REVISION_DATA_DIR = Path("data/raw/wage_revision")

WAGE_REVISION_AMOUNT_RATE_PATH = (
    WAGE_REVISION_DATA_DIR / "wage_revision_amount_rate.xlsx"
)

WAGE_REVISION_AMOUNT_RATE_SHEET = "時系列第1表"

COMPANY_SIZE_LABELS = {
    "計": "total",
    "企業規模計": "total",
    "5,000人以上": "5000_plus",
    "1,000～4,999人": "1000_4999",
    "300～999人": "300_999",
    "100～299人": "100_299",
}


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""

    return str(value).replace("\n", "").replace(" ", "").strip()


def _clean_numeric_value(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()

    if text in {"", "…", "・", "･", "-", "－"}:
        return pd.NA

    text = text.replace(",", "")

    try:
        return float(text)
    except ValueError:
        return pd.NA


def _parse_japanese_year(
    value: object,
    current_era: str | None,
) -> tuple[int | None, str | None]:
    if pd.isna(value):
        return None, current_era

    text = str(value).strip()
    text = text.replace("　", "").replace(" ", "")

    text = text.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789",
        )
    )

    era_match = re.search(r"(昭和|平成|令和)", text)

    if era_match:
        current_era = era_match.group(1)

    if current_era is None:
        return None, None

    if "元年" in text:
        era_year = 1
    else:
        number_match = re.search(r"\d+", text)

        if number_match is None:
            return None, current_era

        era_year = int(number_match.group())

    era_offsets = {
        "昭和": 1925,
        "平成": 1988,
        "令和": 2018,
    }

    return era_offsets[current_era] + era_year, current_era


def _normalize_company_size(value: object) -> str | None:
    text = _clean_text(value)

    if not text:
        return None

    text = text.replace("，", ",")

    return COMPANY_SIZE_LABELS.get(text)


def load_wage_revision_amount_rate(
    path: Path = WAGE_REVISION_AMOUNT_RATE_PATH,
) -> pd.DataFrame:
    raw_df = pd.read_excel(
        path,
        sheet_name=WAGE_REVISION_AMOUNT_RATE_SHEET,
        header=None,
    )

    header_row = None

    for index, row in raw_df.iterrows():
        values = [_clean_text(value) for value in row]

        if (
            "5,000人以上" in values
            and "1,000～4,999人" in values
            and "300～999人" in values
            and "100～299人" in values
        ):
            header_row = index
            break

    if header_row is None:
        raise ValueError("企業規模の見出し行を検出できませんでした。")

    company_size_columns: list[tuple[int, str, str]] = []

    for column_index in range(2, raw_df.shape[1]):
        company_size = _normalize_company_size(
            raw_df.iloc[header_row, column_index]
        )

        if company_size is None:
            continue

        metric = (
            "revision_amount_yen"
            if column_index < 7
            else "revision_rate_pct"
        )

        company_size_columns.append(
            (column_index, company_size, metric)
        )

    records: dict[tuple[int, str], dict[str, object]] = {}

    current_era: str | None = None

    for row_index in range(header_row + 1, len(raw_df)):
        year_value = raw_df.iloc[row_index, 1]
        year_text = _clean_text(year_value)

        # 注記に入ったらデータ部分は終了
        if year_text.startswith("注"):
            break

        # 数値データが存在しない行は無視する
        data_values = [
            _clean_numeric_value(
                raw_df.iloc[row_index, column_index]
            )
            for column_index, _, _ in company_size_columns
        ]

        if all(pd.isna(value) for value in data_values):
            continue

        year, current_era = _parse_japanese_year(
            year_value,
            current_era,
        )

        if year is None:
            continue

        for (
            column_index,
            company_size,
            metric,
        ), value in zip(
            company_size_columns,
            data_values,
            strict=True,
        ):
            key = (year, company_size)

            if key not in records:
                records[key] = {
                    "year": year,
                    "company_size": company_size,
                    "revision_amount_yen": pd.NA,
                    "revision_rate_pct": pd.NA,
                }

            records[key][metric] = value

    df = pd.DataFrame(records.values())

    # 今回必要な範囲外の異常な年を除外
    df = df[
        df["year"].between(1975, 2025)
    ].copy()

    df = df.sort_values(
        ["year", "company_size"],
    ).reset_index(drop=True)

    return df
