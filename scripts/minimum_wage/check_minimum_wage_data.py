from real_wage_dashboard.minimum_wage_service import (
    load_minimum_wage_data,
)


def main() -> None:
    df = load_minimum_wage_data()

    print("=== 最低賃金データ ===")
    print(df.to_string(index=False))

    print()
    print("=== 検証 ===")
    print(f"期間: {df['year'].min()}～{df['year'].max()}")
    print(f"件数: {len(df)}")
    print(f"最低値: {df['minimum_wage'].min()}円")
    print(f"最高値: {df['minimum_wage'].max()}円")
    print(f"欠損: {df.isna().sum().to_dict()}")
    print(f"年度重複: {df['year'].duplicated().sum()}")
    print(
        "単調非減少:",
        df["minimum_wage"].is_monotonic_increasing,
    )


if __name__ == "__main__":
    main()
