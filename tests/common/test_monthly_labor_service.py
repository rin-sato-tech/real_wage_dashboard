"""共通抽出を使う公開サービスの入力・出力契約。"""

import pandas as pd
import pytest

from real_wage_dashboard.wage_service import create_wage_dataframe
from real_wage_dashboard.working_days_service import create_working_days_dataframe
from real_wage_dashboard.working_hours_service import create_working_hours_dataframe


@pytest.fixture(
    params=[
        (create_wage_dataframe, "現金給与総額", "nominal_wage_amount", "賃金"),
        (create_working_hours_dataframe, "総実労働時間", "working_hours", "労働時間"),
        (create_working_days_dataframe, "出勤日数", "working_days", "出勤日数"),
    ],
    ids=["wage", "hours", "days"],
)
def monthly_service(request):
    return request.param


def test_monthly_services_clean_select_and_deduplicate_without_mutation(
    monthly_service,
) -> None:
    create, item, output_column, _ = monthly_service
    raw = pd.DataFrame(
        {
            "年": [2025] * 11,
            "月": ["02", "01", "01", "CY", "03", "13", "01", "01", "01", "04", "02"],
            "産業分類": [" TL "] * 6 + ["C", "TL", "TL", "TL", "TL"],
            "規模": [" T "] * 7 + ["0", "T", "T", "T"],
            "就業形態": [" 0 "] * 8 + ["2", "0", "0"],
            item: [
                " 1,200.5 ",
                "100",
                "110",
                "999",
                "…",
                "50",
                "60",
                "70",
                "80",
                "0",
                "-",
            ],
        },
        index=range(20, 31),
    )
    original = raw.copy(deep=True)

    result = create(raw, employment_type="0")

    expected = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-04-01"]),
            output_column: [110.0, 1200.5, 0.0],
        }
    )
    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(raw, original)


@pytest.mark.parametrize("case", ["missing_column", "no_match", "invalid_value"])
def test_monthly_services_preserve_errors(monthly_service, case) -> None:
    create, item, _, label = monthly_service
    raw = pd.DataFrame(
        {
            "年": [2025],
            "月": ["01"],
            "産業分類": ["TL"],
            "規模": ["T"],
            "就業形態": ["0"],
            item: [10],
        }
    )
    if case == "missing_column":
        raw = raw.drop(columns=[item])
        message = f"必要な列がありません: {sorted([item])}"
    elif case == "no_match":
        raw["産業分類"] = "C"
        message = f"選択した条件に該当する{label}データがありません。"
    else:
        raw[item] = "…"
        message = f"選択した条件では有効な{label}データを取得できません。"

    with pytest.raises(ValueError) as error:
        create(raw, employment_type="0")
    assert str(error.value) == message
