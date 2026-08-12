from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.wage_analysis import add_wage_changes
from real_wage_dashboard.wage_service import (
    create_wage_dataframe,
    load_wage_csv,
)


def main() -> None:
    raw_df = load_wage_csv(WAGE_DATA_PATH)

    print("絞り込み前")
    print(raw_df.shape)

    wage_df = create_wage_dataframe(raw_df)
    wage_df = add_wage_changes(wage_df)

    print("\n絞り込み後")
    print(wage_df.shape)

    print("\n先頭10行")
    print(wage_df.head(10).to_string(index=False))

    print("\n末尾10行")
    print(wage_df.tail(10).to_string(index=False))

    print("\nデータ型")
    print(wage_df.dtypes)

    print("\n欠損値")
    print(wage_df.isna().sum())

    print("\n重複年月数:")
    print(wage_df["date"].duplicated().sum())

    print("\n期間")
    print(
        wage_df["date"].min(),
        "～",
        wage_df["date"].max(),
    )


if __name__ == "__main__":
    main()
