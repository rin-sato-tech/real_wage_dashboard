from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/raw/minimum_wage/regional_minimum_wage_history.xlsx")


def main() -> None:
    excel = pd.ExcelFile(DATA_PATH)

    print("=== シート一覧 ===")
    print(excel.sheet_names)

    for sheet_name in excel.sheet_names:
        # print()
        # print(f"=== {sheet_name} ===")

        df = pd.read_excel(
            DATA_PATH,
            sheet_name=sheet_name,
            header=None,
        )

        # print(f"shape: {df.shape}")
        # print(df.head(20).to_string(index=False, header=False))

        print()
        print("=== 末尾5行 ===")
        print(df.tail(5).to_string(index=False, header=False))

        print()
        print("=== 第1列の末尾10件 ===")
        print(df.iloc[-10:, 0].tolist())


if __name__ == "__main__":
    main()
