from pathlib import Path

from real_wage_dashboard.wage_distribution_service import (
    load_wage_distribution_history_by_company_size,
)

DATA_DIR = Path("data/raw/wage_distribution")


def main() -> None:
    history = load_wage_distribution_history_by_company_size(
        DATA_DIR,
        start_year=2015,
        end_year=2025,
    )

    print()
    print("=== 2015-2025 企業規模別賃金分布 ===")

    print(history.to_string(index=False))

    print()
    print("rows:", len(history))

    assert len(history) == 33

    assert history[["year", "company_size"]].duplicated().sum() == 0


if __name__ == "__main__":
    main()
