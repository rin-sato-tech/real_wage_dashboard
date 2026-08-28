from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/raw/wage_revision")

FILES = [
    DATA_DIR / "wage_revision_amount_rate.xlsx",
    DATA_DIR / "wage_revision_status.xlsx",
    DATA_DIR / "wage_revision_factors.xlsx",
]


for path in FILES:
    print("=" * 80)
    print(path)
    print("=" * 80)

    excel = pd.ExcelFile(path)

    print("sheet_names:")
    print(excel.sheet_names)

    for sheet_name in excel.sheet_names:
        print()
        print(f"[{sheet_name}]")

        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            header=None,
        )

        print("shape:", df.shape)
        print(df.head(20).to_string(index=True, header=False))