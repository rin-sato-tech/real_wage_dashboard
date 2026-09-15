import json

from getpass import getpass
from pathlib import Path

import streamlit as st

from real_wage_dashboard.config import (
    LFS_EMPLOYMENT_TYPE_AGE_CODES,
    LFS_EMPLOYMENT_TYPE_CODES,
    LFS_EMPLOYMENT_TYPE_HOURS_BASE_FILTERS,
    LFS_EMPLOYMENT_TYPE_HOURS_CODES,
    LFS_EMPLOYMENT_TYPE_HOURS_STATS_DATA_ID,
    LFS_HOURS_BY_AGE_SEX_BASE_FILTERS,
    LFS_HOURS_BY_AGE_SEX_CODES,
    LFS_HOURS_BY_AGE_SEX_STATS_DATA_ID,
    LFS_HOURS_BY_AGE_SEX_TAB_CODES,
    LFS_WORKING_HOURS_AGE_CODES,
    LFS_WORKING_HOURS_CATEGORY_CODES,
    LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS,
    LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_stats_data
from real_wage_dashboard.labor_force_service import (
    AGE_GROUPS,
    create_lfs_working_hours_time_codes,
)


OUTPUT_DIR = Path("data/raw/labor_input")


def get_app_id() -> str:
    app_id = st.secrets["ESTAT_APP_ID"]

    if app_id:
        return app_id

    app_id = getpass("e-Stat appId: ").strip()

    if not app_id:
        raise ValueError("e-Stat appId が必要です。")

    return app_id


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"saved: {path}")


def main() -> None:
    app_id = get_app_id()

    # ---------------------------------------------------------
    # 表3-3：週間就業時間分布 2000～2025
    # ---------------------------------------------------------
    distribution_filters = {
        **LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS,
        "cdCat02": ",".join(
            LFS_WORKING_HOURS_AGE_CODES.values()
        ),
        "cdCat04": ",".join(
            LFS_WORKING_HOURS_CATEGORY_CODES.values()
        ),
        "cdTime": ",".join(
            create_lfs_working_hours_time_codes(
                start_year=2000,
                end_year=2025,
            )
        ),
    }

    distribution_response = get_stats_data(
        app_id=app_id,
        stats_data_id=LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID,
        filters=distribution_filters,
    )

    save_json(
        distribution_response,
        OUTPUT_DIR
        / "lfs_working_hours_distribution_2000_2025.json",
    )

    # ---------------------------------------------------------
    # 表3-5：男女・年齢別就業時間 2000～2025
    # ---------------------------------------------------------
    age_sex_filters = {
        **LFS_HOURS_BY_AGE_SEX_BASE_FILTERS,
        "cdTab": ",".join(
            LFS_HOURS_BY_AGE_SEX_TAB_CODES.values()
        ),
        "cdCat01": ",".join(
            LFS_HOURS_BY_AGE_SEX_CODES.values()
        ),
        "cdCat02": ",".join(
            LFS_WORKING_HOURS_AGE_CODES[age_group]
            for age_group in AGE_GROUPS
        ),
        "cdTime": ",".join(
            create_lfs_working_hours_time_codes(
                start_year=2000,
                end_year=2025,
            )
        ),
    }

    age_sex_response = get_stats_data(
        app_id=app_id,
        stats_data_id=LFS_HOURS_BY_AGE_SEX_STATS_DATA_ID,
        filters=age_sex_filters,
    )

    save_json(
        age_sex_response,
        OUTPUT_DIR
        / "lfs_hours_by_age_sex_2000_2025.json",
    )

    # ---------------------------------------------------------
    # 表2-10-1：正規・非正規×就業時間 2012～2025
    # ---------------------------------------------------------
    employment_type_filters = {
        **LFS_EMPLOYMENT_TYPE_HOURS_BASE_FILTERS,
        "cdCat01": ",".join(
            LFS_EMPLOYMENT_TYPE_CODES.values()
        ),
        "cdCat02": ",".join(
            LFS_EMPLOYMENT_TYPE_AGE_CODES.values()
        ),
        "cdCat04": ",".join(
            LFS_EMPLOYMENT_TYPE_HOURS_CODES.values()
        ),
        "cdTime": ",".join(
            create_lfs_working_hours_time_codes(
                start_year=2012,
                end_year=2025,
            )
        ),
    }

    employment_type_response = get_stats_data(
        app_id=app_id,
        stats_data_id=LFS_EMPLOYMENT_TYPE_HOURS_STATS_DATA_ID,
        filters=employment_type_filters,
    )

    save_json(
        employment_type_response,
        OUTPUT_DIR
        / "lfs_employment_type_hours_2012_2025.json",
    )


if __name__ == "__main__":
    main()