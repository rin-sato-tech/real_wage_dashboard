from pathlib import Path

import numpy as np
import pandas as pd

OFFICIAL_REAL_INDEX_TOLERANCE = 0.10


def normalize_text(value: object) -> str:
    """セル文字列を比較用に正規化する。"""
    if pd.isna(value):
        return ""

    import unicodedata

    text = str(value).replace("　", " ").strip()
    return unicodedata.normalize("NFKC", text)


def find_row_containing(
    df: pd.DataFrame,
    keyword: str,
    start_row: int = 0,
) -> int:
    """指定文字列を含む最初の行番号を返す。"""
    for idx in range(start_row, len(df)):
        row = df.iloc[idx].map(normalize_text)
        if row.str.contains(keyword, regex=False).any():
            return idx

    raise ValueError(f"見出しが見つかりません: {keyword}")


def find_year_header_row(
    df: pd.DataFrame,
    start_row: int,
) -> int:
    """先頭列が year または 年 であるヘッダー行を探す。"""
    for idx in range(start_row, len(df)):
        first = normalize_text(df.iloc[idx, 0]).lower()
        if first in {"year", "年"}:
            return idx

    raise ValueError("年ヘッダー行が見つかりません。")


def validate_tl_sheet(df: pd.DataFrame, path: Path) -> None:
    """TLシートが今回の分析条件に対応していることを確認する。"""
    header_text = " ".join(
        normalize_text(value) for value in df.iloc[:6, :8].to_numpy().ravel()
    )

    required_keywords = [
        "調査産業計",
        "5人以上",
        "就業形態計",
    ]

    missing = [keyword for keyword in required_keywords if keyword not in header_text]

    if missing:
        raise ValueError(f"{path} のTLシートが想定条件と一致しません。不足: {missing}")


def read_long_term_sheet(
    path: Path,
    sheet_name: str = "TL",
) -> pd.DataFrame:
    """長期時系列Excelの対象シートを読み込む。"""
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=None,
    )

    validate_tl_sheet(df, path)

    return df


def extract_annual_index(
    path: Path,
    sheet_name: str = "TL",
) -> pd.DataFrame:
    """指数セクションから年平均指数を抽出する。"""
    df = read_long_term_sheet(path, sheet_name)

    indices_row = find_row_containing(df, "指数(Indices)")
    header_row = find_year_header_row(df, indices_row + 1)

    rows: list[dict[str, float | int]] = []

    for idx in range(header_row + 1, len(df)):
        year = pd.to_numeric(df.iloc[idx, 0], errors="coerce")
        annual_average = pd.to_numeric(df.iloc[idx, 1], errors="coerce")

        if pd.isna(year) or pd.isna(annual_average):
            continue

        year = int(year)

        if 1900 <= year <= 2100:
            rows.append(
                {
                    "year": year,
                    "index_value": float(annual_average),
                }
            )

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError(f"指数データを抽出できませんでした: {path}")

    return (
        result.drop_duplicates(subset=["year"], keep="first")
        .sort_values("year")
        .reset_index(drop=True)
    )


def extract_annual_published_yoy(
    path: Path,
    sheet_name: str = "TL",
) -> pd.DataFrame:
    """前年比セクションから年平均の公表前年比を抽出する。"""
    df = read_long_term_sheet(path, sheet_name)

    yoy_row = find_row_containing(df, "前年比")
    header_row = find_year_header_row(df, yoy_row + 1)

    rows: list[dict[str, float | int]] = []

    for idx in range(header_row + 1, len(df)):
        year = pd.to_numeric(df.iloc[idx, 0], errors="coerce")
        yoy = pd.to_numeric(df.iloc[idx, 1], errors="coerce")

        if pd.isna(year) or pd.isna(yoy):
            continue

        year = int(year)

        if 1900 <= year <= 2100:
            rows.append(
                {
                    "year": year,
                    "published_yoy_pct": float(yoy),
                }
            )

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError(f"前年比データを抽出できませんでした: {path}")

    return (
        result.drop_duplicates(subset=["year"], keep="first")
        .sort_values("year")
        .reset_index(drop=True)
    )


def create_complete_annual_cpi(
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """月次CPIから12か月揃った年の年平均と前年比を作成する。"""
    required_columns = {"date", "index_value"}

    if not required_columns.issubset(cpi_df.columns):
        missing = required_columns - set(cpi_df.columns)
        raise ValueError(f"CPIに必要な列がありません: {sorted(missing)}")

    work = cpi_df[["date", "index_value"]].copy()
    work["year"] = work["date"].dt.year
    work["month"] = work["date"].dt.month

    annual = work.groupby("year", as_index=False).agg(
        month_count=("month", "nunique"),
        cpi=("index_value", "mean"),
    )

    annual = (
        annual.loc[annual["month_count"] == 12, ["year", "cpi"]]
        .sort_values("year")
        .reset_index(drop=True)
    )

    annual["cpi_yoy_pct"] = annual["cpi"].pct_change(fill_method=None).mul(100)

    return annual


def build_real_wage_decomposition_data(
    wage_index_df: pd.DataFrame,
    wage_yoy_df: pd.DataFrame,
    official_real_index_df: pd.DataFrame,
    official_real_yoy_df: pd.DataFrame,
    cpi_annual_df: pd.DataFrame,
) -> pd.DataFrame:
    """名目賃金・CPI・公式実質賃金を統合し、分解指標を作成する。"""
    wage_index = wage_index_df.rename(columns={"index_value": "nominal_wage_index"})
    wage_yoy = wage_yoy_df.rename(
        columns={"published_yoy_pct": "published_nominal_yoy_pct"}
    )
    official_real_index = official_real_index_df.rename(
        columns={"index_value": "official_real_wage_index"}
    )
    official_real_yoy = official_real_yoy_df.rename(
        columns={"published_yoy_pct": "published_real_yoy_pct"}
    )

    result = (
        wage_index.merge(wage_yoy, on="year", how="inner", validate="one_to_one")
        .merge(cpi_annual_df, on="year", how="inner", validate="one_to_one")
        .merge(
            official_real_index,
            on="year",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            official_real_yoy,
            on="year",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    result["calculated_real_wage_index_raw"] = (
        result["nominal_wage_index"] / result["cpi"] * 100
    )

    base = result.loc[result["year"] == 2020]

    if len(base) != 1:
        raise ValueError("2020年の基準データを一意に取得できません。")

    base_value = base["calculated_real_wage_index_raw"].iloc[0]

    result["calculated_real_wage_index"] = (
        result["calculated_real_wage_index_raw"] / base_value * 100
    )

    result["real_index_difference"] = (
        result["calculated_real_wage_index"] - result["official_real_wage_index"]
    )

    result["calculated_nominal_yoy_pct"] = (
        result["nominal_wage_index"].pct_change(fill_method=None).mul(100)
    )

    result["calculated_real_yoy_pct"] = (
        result["calculated_real_wage_index"].pct_change(fill_method=None).mul(100)
    )

    result["official_real_yoy_from_index_pct"] = (
        result["official_real_wage_index"].pct_change(fill_method=None).mul(100)
    )

    result["wage_price_gap"] = (
        result["published_nominal_yoy_pct"] - result["cpi_yoy_pct"]
    )

    nominal_rate = result["published_nominal_yoy_pct"] / 100
    price_rate = result["cpi_yoy_pct"] / 100

    result["nominal_log_contribution"] = np.log1p(nominal_rate) * 100
    result["price_log_contribution"] = -np.log1p(price_rate) * 100
    result["real_log_change"] = (
        result["nominal_log_contribution"] + result["price_log_contribution"]
    )

    result["mechanical_real_yoy_pct"] = (
        (1 + nominal_rate) / (1 + price_rate) - 1
    ) * 100

    result["published_vs_mechanical_real_gap"] = (
        result["published_real_yoy_pct"] - result["mechanical_real_yoy_pct"]
    )

    return result


def summarize_chained_period_change(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.Series:
    """公表前年比を連鎖し、指定期間の累積変化を要約する。"""
    if end_year <= start_year:
        raise ValueError("end_year は start_year より後である必要があります。")

    required_years = set(range(start_year + 1, end_year + 1))

    period = df.loc[df["year"].between(start_year + 1, end_year)].copy()

    available_years = set(period["year"].astype(int))
    missing_years = sorted(required_years - available_years)

    if missing_years:
        raise ValueError(f"期間集計に必要な年が不足しています: {missing_years}")

    required_columns = [
        "published_nominal_yoy_pct",
        "cpi_yoy_pct",
    ]

    if period[required_columns].isna().any().any():
        raise ValueError("期間集計に必要な前年比に欠損があります。")

    nominal_rates = period["published_nominal_yoy_pct"] / 100
    price_rates = period["cpi_yoy_pct"] / 100

    nominal_factor = np.prod(1 + nominal_rates)
    price_factor = np.prod(1 + price_rates)
    real_factor = nominal_factor / price_factor

    nominal_log = np.log1p(nominal_rates).sum() * 100
    price_log = -np.log1p(price_rates).sum() * 100
    real_log = nominal_log + price_log

    return pd.Series(
        {
            "start_year": start_year,
            "end_year": end_year,
            "nominal_change_pct": (nominal_factor - 1) * 100,
            "cpi_change_pct": (price_factor - 1) * 100,
            "mechanical_real_change_pct": (real_factor - 1) * 100,
            "nominal_log_contribution": nominal_log,
            "price_log_contribution": price_log,
            "real_log_change": real_log,
        }
    )


def build_cpi_sensitivity(
    wage_yoy_df: pd.DataFrame,
    main_cpi_df: pd.DataFrame,
    sensitivity_cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """主CPIと代替CPIで機械的実質賃金変化を比較する。"""
    wage = wage_yoy_df.rename(
        columns={"published_yoy_pct": "published_nominal_yoy_pct"}
    )

    main = main_cpi_df.rename(
        columns={
            "cpi": "main_cpi",
            "cpi_yoy_pct": "main_cpi_yoy_pct",
        }
    )

    sensitivity = sensitivity_cpi_df.rename(
        columns={
            "cpi": "sensitivity_cpi",
            "cpi_yoy_pct": "sensitivity_cpi_yoy_pct",
        }
    )

    result = (
        wage.merge(
            main[["year", "main_cpi", "main_cpi_yoy_pct"]],
            on="year",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            sensitivity[
                [
                    "year",
                    "sensitivity_cpi",
                    "sensitivity_cpi_yoy_pct",
                ]
            ],
            on="year",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    nominal_rate = result["published_nominal_yoy_pct"] / 100

    result["real_yoy_main_cpi_pct"] = (
        (1 + nominal_rate) / (1 + result["main_cpi_yoy_pct"] / 100) - 1
    ) * 100

    result["real_yoy_sensitivity_cpi_pct"] = (
        (1 + nominal_rate) / (1 + result["sensitivity_cpi_yoy_pct"] / 100) - 1
    ) * 100

    result["real_yoy_sensitivity_gap"] = (
        result["real_yoy_sensitivity_cpi_pct"] - result["real_yoy_main_cpi_pct"]
    )

    return result


def validate_analysis_results(
    analysis_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    tolerance: float = OFFICIAL_REAL_INDEX_TOLERANCE,
) -> None:
    """分析結果の基本整合性を検証する。"""
    period = analysis_df.loc[analysis_df["year"].between(start_year, end_year)].copy()

    if period.empty:
        raise ValueError("検証対象期間のデータがありません。")

    if analysis_df["year"].duplicated().any():
        raise AssertionError("年が重複しています。")

    positive_columns = [
        "nominal_wage_index",
        "cpi",
        "official_real_wage_index",
        "calculated_real_wage_index",
    ]

    if (analysis_df[positive_columns] <= 0).any().any():
        raise AssertionError("指数に0以下の値があります。")

    max_index_difference = period["real_index_difference"].abs().max()

    if max_index_difference > tolerance:
        raise AssertionError(
            "自前実質賃金指数と公式指数の差が許容範囲を超えています。"
            f" 最大差={max_index_difference:.6f}"
        )

    decomposition_error = (
        (
            period["nominal_log_contribution"]
            + period["price_log_contribution"]
            - period["real_log_change"]
        )
        .abs()
        .max()
    )

    if decomposition_error > 1e-10:
        raise AssertionError(
            f"対数分解の恒等式が成立していません。 最大誤差={decomposition_error:.12f}"
        )
