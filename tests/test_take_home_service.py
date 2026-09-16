import pytest

import pandas as pd

from real_wage_dashboard.take_home_service import (
    load_income_tax_brackets,
)


def test_load_income_tax_brackets(tmp_path):
    path = tmp_path / "income_tax_brackets.csv"

    pd.DataFrame(
        {
            "effective_from": ["2007-01-01"],
            "effective_to": [""],
            "bracket_order": [1],
            "lower_bound_yen": [0],
            "upper_bound_yen": [1_950_000],
            "marginal_rate": [0.05],
            "quick_deduction_yen": [0],
            "source_key": ["test"],
        }
    ).to_csv(path, index=False)

    result = load_income_tax_brackets(path)

    assert len(result) == 1
    assert result.loc[0, "marginal_rate"] == 0.05
    assert pd.api.types.is_datetime64_any_dtype(
        result["effective_from"]
    )


def test_load_income_tax_brackets_rejects_missing_columns(
    tmp_path,
):
    path = tmp_path / "income_tax_brackets.csv"

    pd.DataFrame(
        {
            "effective_from": ["2007-01-01"],
        }
    ).to_csv(path, index=False)

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        load_income_tax_brackets(path)
