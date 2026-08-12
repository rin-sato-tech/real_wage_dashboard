import streamlit as st

from real_wage_dashboard.config import (
    CPI_BASE_FILTERS,
    CPI_SERIES,
    CPI_STATS_DATA_ID,
    WAGE_DATA_PATH,
)
from real_wage_dashboard.cpi_analysis import add_cpi_changes
from real_wage_dashboard.cpi_service import create_cpi_dataframe
from real_wage_dashboard.estat_client import get_stats_data
from real_wage_dashboard.real_wage_analysis import (
    add_real_wage_changes,
    create_real_wage_dataframe,
)
from real_wage_dashboard.wage_analysis import add_wage_changes
from real_wage_dashboard.wage_service import (
    create_wage_dataframe,
    load_wage_csv,
)


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    # CPI
    cpi_filters = {
        **CPI_BASE_FILTERS,
        "cdCat01": CPI_SERIES["総合"],
    }

    cpi_response = get_stats_data(
        app_id=app_id,
        stats_data_id=CPI_STATS_DATA_ID,
        filters=cpi_filters,
    )

    cpi_df = create_cpi_dataframe(cpi_response)
    cpi_df = add_cpi_changes(cpi_df)

    # 名目賃金
    raw_wage_df = load_wage_csv(WAGE_DATA_PATH)
    wage_df = create_wage_dataframe(raw_wage_df)
    wage_df = add_wage_changes(wage_df)

    # 実質賃金
    real_wage_df = create_real_wage_dataframe(
        wage_df,
        cpi_df,
        base_year=2020,
    )
    real_wage_df = add_real_wage_changes(real_wage_df)

    print("CPI件数:")
    print(cpi_df.shape)

    print("\n名目賃金件数:")
    print(wage_df.shape)

    print("\n結合後件数:")
    print(real_wage_df.shape)

    print("\n期間")
    print(
        real_wage_df["date"].min(),
        "～",
        real_wage_df["date"].max(),
    )

    print("\n先頭10行")
    print(real_wage_df.head(10).to_string(index=False))

    print("\n末尾10行")
    print(real_wage_df.tail(10).to_string(index=False))

    print("\nデータ型")
    print(real_wage_df.dtypes)

    print("\n欠損値:")
    print(real_wage_df.isna().sum())

    print("\n重複年月数:")
    print(real_wage_df["date"].duplicated().sum())

    base_year_df = real_wage_df[real_wage_df["date"].dt.year == 2020]

    print("\n2020年平均（基準値100の確認）:")
    print("2020年データ件数:", len(base_year_df))
    print(
        "名目賃金指数:",
        base_year_df["nominal_wage_index"].mean(),
    )
    print(
        "実質賃金指数:",
        base_year_df["real_wage_index"].mean(),
    )


if __name__ == "__main__":
    main()
