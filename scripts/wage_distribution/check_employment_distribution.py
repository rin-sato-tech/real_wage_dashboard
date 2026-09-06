from pathlib import Path

import pandas as pd

from real_wage_dashboard.wage_distribution_service import (
    find_wage_distribution_file,
    normalize_text,
)

# DATA_DIR = Path("data/raw/wage_distribution")

# START_YEAR = 2015
# END_YEAR = 2025
# BASE_YEAR = 2015

# EMPLOYMENT_KEYWORDS = [
#     "正社員・正職員",
#     "正社員・正職員以外",
# ]

# print()
# print("=== 雇用形態ラベル確認 ===")

# for year in [START_YEAR, END_YEAR]:
#     path = find_wage_distribution_file(
#         data_dir=DATA_DIR,
#         year=year,
#     )

#     excel = pd.ExcelFile(path)

#     print()
#     print(f"=== {year} ===")

#     for sheet_name in excel.sheet_names:
#         df = pd.read_excel(
#             path,
#             sheet_name=sheet_name,
#             header=None,
#         )

#         for row_index, row in df.iterrows():
#             row_text = "".join(
#                 normalize_text(value)
#                 for value in row
#                 if pd.notna(value)
#             )

#             if any(
#                 keyword in row_text
#                 for keyword in EMPLOYMENT_KEYWORDS
#             ):
#                 print(
#                     "sheet=",
#                     sheet_name,
#                     "row=",
#                     row_index,
#                     "text=",
#                     row_text,
#                 )

DATA_DIR = Path(
    "data/raw/wage_distribution/employment"
)

FILES = {
    (2015, "regular"): DATA_DIR / (
        "wage_distribution_employment_2015_regular.xls"
    ),
    (2015, "nonregular"): DATA_DIR / (
        "wage_distribution_employment_2015_nonregular.xls"
    ),
    (2025, "regular"): DATA_DIR / (
        "wage_distribution_employment_2025_regular.xlsx"
    ),
    (2025, "nonregular"): DATA_DIR / (
        "wage_distribution_employment_2025_nonregular.xlsx"
    ),
}


for (year, employment), path in FILES.items():
    print()
    print(f"=== {year} {employment} ===")

    excel = pd.ExcelFile(path)

    for sheet_name in excel.sheet_names[:1]:
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            header=None,
        )

        print()
        print(f"sheet: {sheet_name}")
        print("shape:", df.shape)

        total_row = None

        for row_index, row in df.iterrows():
            row_text = "".join(
                normalize_text(value)
                for value in row
                if pd.notna(value)
            )

            if "男女計" in row_text:
                total_row = row_index
                break

        if total_row is None:
            print("男女計が見つかりません")
            continue

        print("男女計 row:", total_row)

        block = df.iloc[total_row:]

        found = 0

        for row_index, row in block.iterrows():
            row_text = " | ".join(
                str(value)
                for value in row
                if pd.notna(value)
            )

            if any(
                keyword in row_text
                for keyword in [
                    "第1・十分位数",
                    "第1・四分位数",
                    "中　 位",
                    "第3・四分位数",
                    "第9・十分位数",
                    "十分位分散係数",
                    "四分位分散係数",
                ]
            ):
                print("row:", row_index, row_text)
                found += 1

                if found == 7:
                    break