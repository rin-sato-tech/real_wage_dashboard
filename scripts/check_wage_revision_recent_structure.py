from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/raw/wage_revision")

FILES = {
    "amount_rate": DATA_DIR / "wage_revision_amount_rate.xlsx",
    "status": DATA_DIR / "wage_revision_status.xlsx",
    "factors": DATA_DIR / "wage_revision_factors.xlsx",
}


def show_recent_rows(path: Path, sheet_name: str, tail_rows: int = 100) -> None:
    print("=" * 100)
    print(path)
    print("=" * 100)

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=None,
    )

    print("shape:", df.shape)
    print()
    print(df.tail(tail_rows).to_string(index=True, header=False))
    print()


show_recent_rows(
    FILES["amount_rate"],
    "時系列第1表",
    tail_rows=40,
)

show_recent_rows(
    FILES["status"],
    "時系列第4表",
    tail_rows=100,
)

show_recent_rows(
    FILES["factors"],
    "時系列第６表",
    tail_rows=120,
)
