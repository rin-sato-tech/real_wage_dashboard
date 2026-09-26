import pandas as pd
import pytest

from real_wage_dashboard.cpi_analysis import add_cpi_changes
from real_wage_dashboard.real_wage_analysis import add_real_wage_changes
from real_wage_dashboard.wage_analysis import add_wage_changes


@pytest.mark.parametrize(
    ("calculate", "value_column", "mom", "yoy"),
    [
        (add_cpi_changes, "index_value", "mom_pct", "yoy_pct"),
        (add_wage_changes, "nominal_wage_amount", "mom_pct", "yoy_pct"),
        (
            add_real_wage_changes,
            "real_wage_amount",
            "real_wage_mom_pct",
            "real_wage_yoy_pct",
        ),
    ],
)
def test_monthly_changes_sort_preserve_metadata_and_do_not_fill_missing(
    calculate, value_column, mom, yoy
):
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=14, freq="MS"),
            value_column: [100.0, None, 110.0] + [110.0] * 9 + [120.0, 130.0],
            "real_wage_index": [100.0] * 14,
            "source": ["fixture"] * 14,
        }
    ).iloc[::-1]
    original = df.copy(deep=True)

    result = calculate(df)

    assert result[mom].iloc[:3].isna().all()
    assert result[mom].iloc[12] == pytest.approx((120 / 110 - 1) * 100)
    assert result[yoy].iloc[:12].isna().all()
    assert result[yoy].iloc[12] == pytest.approx(20.0)
    assert pd.isna(result[yoy].iloc[13])
    assert list(result.columns) == list(df.columns) + [mom, yoy]
    assert result["source"].tolist() == ["fixture"] * 14
    pd.testing.assert_frame_equal(df, original)


def test_real_wage_changes_still_require_real_index():
    df = pd.DataFrame(
        {"date": pd.to_datetime(["2025-01-01"]), "real_wage_amount": [100.0]}
    )
    with pytest.raises(ValueError, match="real_wage_index"):
        add_real_wage_changes(df)
