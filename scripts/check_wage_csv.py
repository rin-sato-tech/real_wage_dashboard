from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.wage_service import load_wage_csv


def main() -> None:
    df = load_wage_csv(WAGE_DATA_PATH)

    print("行数・列数:")
    print(df.shape)

    print("\n列名:")
    for index, column in enumerate(df.columns):
        print(index, repr(column))

    print("\nデータ型:")
    print(df.dtypes)

    print("\n先頭10行")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
