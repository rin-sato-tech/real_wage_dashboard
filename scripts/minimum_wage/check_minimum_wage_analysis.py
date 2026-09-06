import tomllib
from pathlib import Path

# from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.minimum_wage_analysis import (
    # add_real_minimum_wage,
    build_minimum_wage_analysis,
    # prepare_annual_cpi,
    prepare_minimum_wage_wage_data,
    # summarize_minimum_wage_correlations,
    summarize_minimum_wage_lag_correlations,
)
from real_wage_dashboard.minimum_wage_service import (
    load_minimum_wage_data,
)
from real_wage_dashboard.wage_service import load_wage_csv

WAGE_DATA_PATH = Path("data/raw/hon-maikin-k-jissu.csv")

SECRETS_PATH = Path(".streamlit/secrets.toml")


def load_estat_app_id() -> str:
    with SECRETS_PATH.open("rb") as file:
        secrets = tomllib.load(file)

    app_id = secrets.get("ESTAT_APP_ID")

    if not app_id:
        raise ValueError(
            ".streamlit/secrets.toml に ESTAT_APP_ID が設定されていません。"
        )

    return str(app_id)


def main() -> None:
    minimum_wage_df = load_minimum_wage_data()

    raw_wage_df = load_wage_csv(
        file_path=WAGE_DATA_PATH,
    )

    wage_df = prepare_minimum_wage_wage_data(
        raw_wage_df,
        start_year=2015,
        end_year=2025,
    )

    analysis_df = build_minimum_wage_analysis(
        minimum_wage_df,
        wage_df,
    )

    # correlation_df = summarize_minimum_wage_correlations(
    #     analysis_df
    # )

    # print()
    # print("=== 前年比相関 ===")
    # print(
    #     correlation_df.to_string(
    #         index=False
    #     )
    # )

    # lag_df = summarize_minimum_wage_lag_correlations(
    #     analysis_df,
    #     max_lag_years=1,
    # )

    # print()
    # print("=== 前年比ラグ相関 ===")
    # print(
    #     lag_df.to_string(
    #         index=False
    #     )
    # )

    # print()
    # print("=== 最低賃金・賃金前年比 ===")

    # yoy_columns = [
    #     "year",
    #     "size_name",
    #     "employment_name",
    #     "minimum_wage_yoy",
    #     "scheduled_hourly_wage_yoy",
    # ]

    # print(
    #     analysis_df[
    #         yoy_columns
    #     ].to_string(
    #         index=False
    #     )
    # )

    without_2020_df = analysis_df[analysis_df["year"] != 2020].copy()

    print()
    print("=== 2020年除外・前年比ラグ相関 ===")

    without_2020_correlation_df = summarize_minimum_wage_lag_correlations(
        without_2020_df,
        max_lag_years=1,
    )

    print(without_2020_correlation_df.to_string(index=False))

    # app_id = load_estat_app_id()

    # cpi_df = load_cpi_dataframe(
    #     app_id=app_id,
    #     series_code="0163",
    # )

    # annual_cpi_df = prepare_annual_cpi(
    #     cpi_df,
    #     start_year=2015,
    #     end_year=2025,
    # )

    # analysis_df = add_real_minimum_wage(
    #     analysis_df,
    #     annual_cpi_df,
    # )


if __name__ == "__main__":
    main()
