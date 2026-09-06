from pathlib import Path

import pandas as pd
import pytest

from real_wage_dashboard.wage_distribution_service import (
    extract_distribution_by_sex_from_dataframe,
    extract_main_distribution_from_dataframe,
    find_wage_distribution_file,
    normalize_distribution_label,
)


def test_normalize_distribution_label() -> None:
    assert normalize_distribution_label("中　 位 　数 （千円）") == "中位数"

    assert normalize_distribution_label("第1・十分位数（千円）") == "第1・十分位数"


def test_extract_main_distribution_from_dataframe() -> None:
    df = pd.DataFrame(
        [
            [
                None,
                "第1・十分位数（千円）",
                None,
                166.0,
            ],
            [
                None,
                "第1・四分位数（千円）",
                None,
                204.1,
            ],
            [
                None,
                "中　 位 　数 （千円）",
                None,
                263.4,
            ],
            [
                None,
                "第3・四分位数（千円）",
                None,
                359.3,
            ],
            [
                None,
                "第9・十分位数（千円）",
                None,
                487.9,
            ],
            [
                None,
                None,
                "十分位分散係数",
                0.61,
            ],
            [
                None,
                None,
                "四分位分散係数",
                0.29,
            ],
        ]
    )

    result = extract_main_distribution_from_dataframe(
        df=df,
        year=2015,
    )

    assert result == {
        "year": 2015,
        "p10": 166.0,
        "p25": 204.1,
        "p50": 263.4,
        "p75": 359.3,
        "p90": 487.9,
        "decile_dispersion": 0.61,
        "quartile_dispersion": 0.29,
    }


def test_extract_uses_first_matching_block() -> None:
    df = pd.DataFrame(
        [
            ["第1・十分位数（千円）", 166.0],
            ["第1・四分位数（千円）", 204.1],
            ["中位数（千円）", 263.4],
            ["第3・四分位数（千円）", 359.3],
            ["第9・十分位数（千円）", 487.9],
            ["十分位分散係数", 0.61],
            ["四分位分散係数", 0.29],
            ["第1・十分位数（千円）", 183.2],
            ["第1・四分位数（千円）", 225.8],
            ["中位数（千円）", 290.0],
            ["第3・四分位数（千円）", 399.4],
            ["第9・十分位数（千円）", 534.5],
            ["十分位分散係数", 0.60],
            ["四分位分散係数", 0.30],
        ]
    )

    result = extract_main_distribution_from_dataframe(
        df=df,
        year=2015,
    )

    assert result["p10"] == 166.0
    assert result["p90"] == 487.9


def test_extract_raises_when_value_missing() -> None:
    df = pd.DataFrame(
        [
            ["第1・十分位数（千円）", 166.0],
        ]
    )

    with pytest.raises(
        ValueError,
        match="分布特性値を取得できませんでした",
    ):
        extract_main_distribution_from_dataframe(
            df=df,
            year=2015,
        )


def test_find_wage_distribution_file(
    tmp_path: Path,
) -> None:
    target = tmp_path / "wage_distribution_2015.xls"
    target.touch()

    result = find_wage_distribution_file(
        data_dir=tmp_path,
        year=2015,
    )

    assert result == target


def test_find_wage_distribution_file_rejects_duplicates(
    tmp_path: Path,
) -> None:
    (tmp_path / "wage_distribution_2015.xls").touch()

    (tmp_path / "wage_distribution_2015.xlsx").touch()

    with pytest.raises(
        ValueError,
        match="ファイルが一意に決まりません",
    ):
        find_wage_distribution_file(
            data_dir=tmp_path,
            year=2015,
        )


def test_extract_distribution_by_sex_uses_separate_blocks() -> None:
    df = pd.DataFrame(
        [
            ["男女計\n学歴計"],
            ["第1・十分位数（千円）", 166.0],
            ["第1・四分位数（千円）", 204.1],
            ["中位数（千円）", 263.4],
            ["第3・四分位数（千円）", 359.3],
            ["第9・十分位数（千円）", 487.9],
            ["十分位分散係数", 0.61],
            ["四分位分散係数", 0.29],
            ["男\n学歴計"],
            ["第1・十分位数（千円）", 183.2],
            ["第1・四分位数（千円）", 225.8],
            ["中位数（千円）", 293.8],
            ["第3・四分位数（千円）", 399.4],
            ["第9・十分位数（千円）", 534.5],
            ["十分位分散係数", 0.60],
            ["四分位分散係数", 0.30],
            ["女\n学歴計"],
            ["第1・十分位数（千円）", 149.3],
            ["第1・四分位数（千円）", 176.9],
            ["中位数（千円）", 218.2],
            ["第3・四分位数（千円）", 276.8],
            ["第9・十分位数（千円）", 357.4],
            ["十分位分散係数", 0.48],
            ["四分位分散係数", 0.23],
        ]
    )

    male = extract_distribution_by_sex_from_dataframe(
        df,
        year=2015,
        sex="male",
    )

    female = extract_distribution_by_sex_from_dataframe(
        df,
        year=2015,
        sex="female",
    )

    assert male["p50"] == pytest.approx(293.8)
    assert female["p50"] == pytest.approx(218.2)
