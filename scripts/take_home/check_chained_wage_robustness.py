from pathlib import Path

import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    CPI_SERIES,
)
from real_wage_dashboard.cpi_analysis import (
    prepare_annual_cpi,
)
from real_wage_dashboard.cpi_service import (
    load_cpi_dataframe,
)


YOY_PATH = Path(
    "data/raw/take_home/"
    "official_nominal_wage_yoy.csv"
)

START_YEAR = 1990
END_YEAR = 2025


def create_chained_wage_index(
    yoy_df: pd.DataFrame,
    base_year: int = 1990,
) -> pd.DataFrame:
    """公表前年比を連鎖して名目賃金指数を作成する。"""

    required_columns = {
        "year",
        "yoy_pct",
    }

    missing = (
        required_columns
        - set(yoy_df.columns)
    )

    if missing:
        raise ValueError(
            "前年比データに必要な列がありません: "
            f"{sorted(missing)}"
        )

    data = yoy_df.copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data["yoy_pct"] = pd.to_numeric(
        data["yoy_pct"],
        errors="coerce",
    )

    if data[
        [
            "year",
            "yoy_pct",
        ]
    ].isna().any().any():
        raise ValueError(
            "前年比データに不正な値があります。"
        )

    data["year"] = (
        data["year"].astype(int)
    )

    expected_years = set(
        range(
            base_year + 1,
            END_YEAR + 1,
        )
    )

    actual_years = set(
        data["year"]
    )

    missing_years = sorted(
        expected_years
        - actual_years
    )

    if missing_years:
        raise ValueError(
            "前年比データに不足年があります: "
            f"{missing_years}"
        )

    data = (
        data.loc[
            data["year"].between(
                base_year + 1,
                END_YEAR,
            )
        ]
        .sort_values("year")
        .reset_index(drop=True)
    )

    rows = [
        {
            "year": base_year,
            "chained_nominal_wage_index": 100.0,
        }
    ]

    current_index = 100.0

    for row in data.itertuples(
        index=False
    ):
        current_index *= (
            1
            + float(row.yoy_pct)
            / 100
        )

        rows.append(
            {
                "year": int(row.year),
                "chained_nominal_wage_index":
                    current_index,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    # ----------------------------------------
    # 1. 公表前年比
    # ----------------------------------------

    yoy_df = pd.read_csv(
        YOY_PATH
    )

    chained = (
        create_chained_wage_index(
            yoy_df=yoy_df,
            base_year=START_YEAR,
        )
    )

    # ----------------------------------------
    # 2. CPI
    # ----------------------------------------

    app_id = st.secrets[
        "ESTAT_APP_ID"
    ]

    cpi_df = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES[
            "持家の帰属家賃を除く総合"
        ],
    )

    annual_cpi = prepare_annual_cpi(
        cpi_df=cpi_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    # ----------------------------------------
    # 3. CPIを1990=100へ基準化
    # ----------------------------------------

    base_cpi = float(
        annual_cpi.loc[
            annual_cpi["year"]
            == START_YEAR,
            "cpi",
        ].iloc[0]
    )

    annual_cpi[
        "cpi_index_1990"
    ] = (
        annual_cpi["cpi"]
        / base_cpi
        * 100
    )

    # ----------------------------------------
    # 4. 実質賃金指数
    # ----------------------------------------

    result = chained.merge(
        annual_cpi[
            [
                "year",
                "cpi",
                "cpi_index_1990",
            ]
        ],
        on="year",
        how="inner",
        validate="one_to_one",
    )

    result[
        "chained_real_wage_index"
    ] = (
        result[
            "chained_nominal_wage_index"
        ]
        / result[
            "cpi_index_1990"
        ]
        * 100
    )

    # ----------------------------------------
    # 5. 主要期間
    # ----------------------------------------

    periods = [
        (1990, 2025),
        (2015, 2025),
    ]

    print(
        "=== 公表前年比連鎖系列 ==="
    )

    for start_year, end_year in periods:
        start = result.loc[
            result["year"] == start_year
        ].iloc[0]

        end = result.loc[
            result["year"] == end_year
        ].iloc[0]

        nominal_change = (
            end[
                "chained_nominal_wage_index"
            ]
            / start[
                "chained_nominal_wage_index"
            ]
            - 1
        ) * 100

        real_change = (
            end[
                "chained_real_wage_index"
            ]
            / start[
                "chained_real_wage_index"
            ]
            - 1
        ) * 100

        cpi_change = (
            end["cpi"]
            / start["cpi"]
            - 1
        ) * 100

        print(
            f"{start_year}→{end_year}"
        )

        print(
            "  nominal:",
            f"{nominal_change:+.3f}%",
        )

        print(
            "  CPI:",
            f"{cpi_change:+.3f}%",
        )

        print(
            "  real:",
            f"{real_change:+.3f}%",
        )


if __name__ == "__main__":
    main()
