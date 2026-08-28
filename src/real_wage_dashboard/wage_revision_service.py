from pathlib import Path
import re

import pandas as pd

WAGE_REVISION_DATA_DIR = Path("data/raw/wage_revision")

WAGE_REVISION_AMOUNT_RATE_PATH = (
    WAGE_REVISION_DATA_DIR / "wage_revision_amount_rate.xlsx"
)

WAGE_REVISION_STATUS_PATH = (
    WAGE_REVISION_DATA_DIR / "wage_revision_status.xlsx"
)

WAGE_REVISION_AMOUNT_RATE_SHEET = "時系列第1表"
WAGE_REVISION_STATUS_SHEET = "時系列第4表"

COMPANY_SIZE_LABELS = {
    "計": "total",
    "企業規模計": "total",
    "5,000人以上": "5000_plus",
    "1,000人～4,999人": "1000_4999",
    "1,000～4,999人": "1000_4999",
    "300～999人": "300_999",
    "100～299人": "100_299",
}

STATUS_LABELS = {
    "１人平均賃金を引き上げた・引き上げる": "raised",
    "１人平均賃金を引き下げた・引き下げる": "lowered",
    "１人平均賃金は変わらなかった・変わらない": "unchanged",
    "賃金の改定を実施しない": "no_revision",
    "未定": "undecided",
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

    text = (
        text.replace("，", ",")
        .replace("〜", "～")
        .replace("~", "～")
    )

    if text in {"計", "企業規模計"}:
        return "total"

    if "5,000人以上" in text:
        return "5000_plus"

    if text in {
        "1,000人～4,999人",
        "1,000～4,999人",
    }:
        return "1000_4999"

    if "300～999人" in text:
        return "300_999"

    if "100～299人" in text:
        return "100_299"

    return None


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


def load_wage_revision_status(
    path: Path = WAGE_REVISION_STATUS_PATH,
) -> pd.DataFrame:
    raw_df = pd.read_excel(
        path,
        sheet_name=WAGE_REVISION_STATUS_SHEET,
        header=None,
    )

    records: list[dict[str, object]] = []

    current_company_size: str | None = None
    current_era: str | None = None

    # 表4の列位置
    #
    # 0: 企業規模
    # 1: 年
    # 2: 計
    # 3: 賃金改定実施または予定
    # 4: 額決定済み割合
    # 5: 引上げ
    # 6: 引下げ
    # 7: 変わらない
    # 8～10: 改定時期
    # 11: 改定しない
    # 12: 未定
    status_columns = {
        5: "raised",
        6: "lowered",
        7: "unchanged",
        11: "no_revision",
        12: "undecided",
    }

    for row_index in range(len(raw_df)):
        company_size_value = raw_df.iloc[row_index, 0]
        company_size_text = _clean_text(company_size_value)

        company_size = _normalize_company_size(
            company_size_value
        )

        if company_size is not None:
            current_company_size = company_size
            current_era = "平成"
            continue

        if "人" in company_size_text and "年" not in company_size_text:
            current_company_size = None
            current_era = None
            continue

        if current_company_size is None:
            continue

        # status列を先に取得する
        status_values = {
            status: _clean_numeric_value(
                raw_df.iloc[row_index, column_index]
            )
            for column_index, status in status_columns.items()
        }

        # status列がすべて欠損ならデータ行ではない
        # 注記などを年として誤認しないため、年解析より前に除外する
        if all(pd.isna(value) for value in status_values.values()):
            continue

        year_value = raw_df.iloc[row_index, 1]

        year, current_era = _parse_wage_revision_recent_year(
            year_value,
            current_era,
        )

        if year is None:
            continue

        if not 2015 <= year <= 2025:
            continue

        for status, value in status_values.items():
            comparison_note: str | None = None

            if status == "lowered":
                if year <= 2024:
                    comparison_note = (
                        "includes unchanged through 2024"
                    )

            elif status == "unchanged":
                if year <= 2024:
                    comparison_note = (
                        "not separately reported through 2024"
                    )
                else:
                    comparison_note = (
                        "separate category from 2025"
                    )

            records.append(
                {
                    "year": year,
                    "company_size": current_company_size,
                    "status": status,
                    "company_share_pct": value,
                    "comparison_note": comparison_note,
                }
            )

    df = pd.DataFrame(records)

    duplicate_columns = [
        "year",
        "company_size",
        "status",
    ]

    if df.duplicated(subset=duplicate_columns).any():
        duplicates = df[
            df.duplicated(
                subset=duplicate_columns,
                keep=False,
            )
        ]

        raise ValueError(
            "賃金改定実施状況に重複があります。\n"
            f"{duplicates.to_string(index=False)}"
        )

    df = df.sort_values(
        ["year", "company_size", "status"]
    ).reset_index(drop=True)

    return df


def _parse_wage_revision_recent_year(
    value: object,
    current_era: str,
) -> tuple[int | None, str]:
    if pd.isna(value):
        return None, current_era

    text = _clean_text(value)

    text = text.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789",
        )
    )

    if "平成" in text:
        current_era = "平成"

    elif "令和" in text:
        current_era = "令和"

    if "元年" in text:
        era_year = 1
    else:
        match = re.search(r"\d+", text)

        if match is None:
            return None, current_era

        era_year = int(match.group())

    if current_era == "平成":
        year = 1988 + era_year
    else:
        year = 2018 + era_year

    return year, current_era
