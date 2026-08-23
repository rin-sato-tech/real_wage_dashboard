from __future__ import annotations

import pandas as pd

from real_wage_dashboard.industry_analysis import (
    INDUSTRY_NAMES,
    MAIN_INDUSTRIES,
    create_industry_monthly_dataframe,
    create_industry_yearly_dataframe,
)

COMPOSITION_INDUSTRIES = [code for code in MAIN_INDUSTRIES if code != "TL"]


def create_industry_employment_monthly_dataframe(
    raw_df: pd.DataFrame,
    industry_code: str,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """産業別の月次労働者数DataFrameを作成する。"""

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        "前月末労働者数",
        "本月末労働者数",
    }

    missing_columns = required_columns - set(raw_df.columns)

    if missing_columns:
        raise ValueError(f"必要な列がありません: {sorted(missing_columns)}")

    industry = raw_df["産業分類"].astype(str).str.strip()
    size = raw_df["規模"].astype(str).str.strip()
    employment = raw_df["就業形態"].astype(str).str.strip()
    month = raw_df["月"].astype(str).str.strip()

    df = raw_df.loc[
        (industry == industry_code)
        & (size == establishment_size)
        & (employment == employment_type)
        & (month != "CY"),
        [
            "年",
            "月",
            "前月末労働者数",
            "本月末労働者数",
        ],
    ].copy()

    if df.empty:
        raise ValueError("選択した条件に該当する労働者数データがありません。")

    df["year"] = pd.to_numeric(
        df["年"],
        errors="coerce",
    )

    df["month"] = pd.to_numeric(
        df["月"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month"],
            "day": 1,
        },
        errors="coerce",
    )

    for column in [
        "前月末労働者数",
        "本月末労働者数",
    ]:
        df[column] = pd.to_numeric(
            df[column].astype(str).str.replace(",", "", regex=False).str.strip(),
            errors="coerce",
        )

    df = df.rename(
        columns={
            "前月末労働者数": "previous_month_end_employment",
            "本月末労働者数": "current_month_end_employment",
        }
    )

    df["monthly_employment"] = (
        df["previous_month_end_employment"] + df["current_month_end_employment"]
    ) / 2

    df["industry"] = industry_code

    df = (
        df.dropna(
            subset=[
                "date",
                "previous_month_end_employment",
                "current_month_end_employment",
                "monthly_employment",
            ]
        )
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError("有効な労働者数データを取得できません。")

    if (df["monthly_employment"] <= 0).any():
        raise ValueError("労働者数に0以下の値が含まれています。")

    return df[
        [
            "date",
            "industry",
            "previous_month_end_employment",
            "current_month_end_employment",
            "monthly_employment",
        ]
    ]


def create_all_industry_employment_monthly_dataframe(
    raw_df: pd.DataFrame,
    industry_codes: list[str] | None = None,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """複数産業の月次労働者数DataFrameをまとめて作成する。"""

    if industry_codes is None:
        industry_codes = COMPOSITION_INDUSTRIES

    frames = [
        create_industry_employment_monthly_dataframe(
            raw_df,
            industry_code=industry_code,
            establishment_size=establishment_size,
            employment_type=employment_type,
        )
        for industry_code in industry_codes
    ]

    return (
        pd.concat(
            frames,
            ignore_index=True,
        )
        .sort_values(
            [
                "industry",
                "date",
            ]
        )
        .reset_index(drop=True)
    )


def create_industry_employment_yearly_dataframe(
    monthly_df: pd.DataFrame,
) -> pd.DataFrame:
    """月次労働者数から産業別の年平均労働者数を作成する。"""

    df = monthly_df.copy()

    df["year"] = df["date"].dt.year

    yearly = df.groupby(
        [
            "industry",
            "year",
        ],
        as_index=False,
    ).agg(
        annual_employment=("monthly_employment", "mean"),
        month_count=("date", "nunique"),
    )

    yearly = (
        yearly.loc[yearly["month_count"] == 12]
        .sort_values(
            [
                "industry",
                "year",
            ]
        )
        .reset_index(drop=True)
    )

    return yearly


def add_industry_employment_share(
    yearly_df: pd.DataFrame,
) -> pd.DataFrame:
    """各年の主要16産業内における雇用シェアを算出する。"""

    df = yearly_df.copy()

    annual_total = df.groupby("year")["annual_employment"].transform("sum")

    df["employment_share"] = df["annual_employment"] / annual_total

    return df


def create_industry_wage_yearly_dataframe(
    raw_df: pd.DataFrame,
    industry_codes: list[str] | None = None,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """主要産業の年次賃金DataFrameを作成する。"""

    if industry_codes is None:
        industry_codes = COMPOSITION_INDUSTRIES

    frames = []

    for industry_code in industry_codes:
        monthly_df = create_industry_monthly_dataframe(
            raw_df,
            industry_code=industry_code,
            establishment_size=establishment_size,
            employment_type=employment_type,
        )

        yearly_df = create_industry_yearly_dataframe(
            monthly_df,
        )

        frames.append(
            yearly_df[
                [
                    "industry",
                    "year",
                    "monthly_wage",
                    "month_count",
                ]
            ]
        )

    return (
        pd.concat(
            frames,
            ignore_index=True,
        )
        .sort_values(
            [
                "industry",
                "year",
            ]
        )
        .reset_index(drop=True)
    )


def create_industry_composition_base_dataframe(
    wage_yearly_df: pd.DataFrame,
    employment_yearly_df: pd.DataFrame,
) -> pd.DataFrame:
    """産業別年次賃金と雇用ウェイトを結合する。"""

    employment_columns = [
        "industry",
        "year",
        "annual_employment",
        "employment_share",
    ]

    df = wage_yearly_df.merge(
        employment_yearly_df[employment_columns],
        on=[
            "industry",
            "year",
        ],
        how="inner",
        validate="one_to_one",
    )

    return df.sort_values(
        [
            "industry",
            "year",
        ]
    ).reset_index(drop=True)


def create_reconstructed_average_wage_dataframe(
    base_df: pd.DataFrame,
) -> pd.DataFrame:
    """産業別賃金と雇用シェアから年次の再構築平均賃金を作成する。"""

    df = base_df.copy()

    df["weighted_wage"] = df["monthly_wage"] * df["employment_share"]

    reconstructed = (
        df.groupby(
            "year",
            as_index=False,
        )
        .agg(
            reconstructed_wage=("weighted_wage", "sum"),
            employment_share_sum=("employment_share", "sum"),
            industry_count=("industry", "nunique"),
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    return reconstructed


def create_industry_composition_decomposition(
    base_df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    """平均賃金変化を産業内賃金効果・産業構成効果・交差効果に分解する。"""

    start_df = base_df.loc[
        base_df["year"] == start_year,
        [
            "industry",
            "monthly_wage",
            "employment_share",
        ],
    ].rename(
        columns={
            "monthly_wage": "start_wage",
            "employment_share": "start_share",
        }
    )

    end_df = base_df.loc[
        base_df["year"] == end_year,
        [
            "industry",
            "monthly_wage",
            "employment_share",
        ],
    ].rename(
        columns={
            "monthly_wage": "end_wage",
            "employment_share": "end_share",
        }
    )

    df = start_df.merge(
        end_df,
        on="industry",
        how="inner",
        validate="one_to_one",
    )

    if df["industry"].nunique() != len(COMPOSITION_INDUSTRIES):
        raise ValueError("分解対象年で主要16産業が揃っていません。")

    df["wage_change"] = df["end_wage"] - df["start_wage"]

    df["share_change"] = df["end_share"] - df["start_share"]

    df["within_wage_effect"] = df["start_share"] * df["wage_change"]

    df["composition_effect"] = df["start_wage"] * df["share_change"]

    df["interaction_effect"] = df["wage_change"] * df["share_change"]

    df["total_contribution"] = (
        df["within_wage_effect"] + df["composition_effect"] + df["interaction_effect"]
    )

    start_average_wage = (df["start_wage"] * df["start_share"]).sum()

    df["centered_composition_effect"] = (df["start_wage"] - start_average_wage) * df[
        "share_change"
    ]

    df["centered_composition_effect_pt"] = (
        df["centered_composition_effect"] / start_average_wage * 100
    )

    df["wage_level_group"] = df["start_wage"].apply(
        lambda x: "平均以上" if x >= start_average_wage else "平均未満"
    )

    df["share_change_group"] = df["share_change"].apply(
        lambda x: "シェア上昇" if x > 0 else "シェア低下"
    )

    df["composition_pattern"] = (
        df["wage_level_group"] + " × " + df["share_change_group"]
    )

    return df.sort_values("industry").reset_index(drop=True)


def identify_composition_notable_industries(
    decomposition_df: pd.DataFrame,
) -> dict[str, str]:
    """産業構成効果分析で特徴的な産業を抽出する。"""

    return {
        "share_increase_max": decomposition_df.loc[
            decomposition_df["share_change"].idxmax(),
            "industry",
        ],
        "share_decrease_max": decomposition_df.loc[
            decomposition_df["share_change"].idxmin(),
            "industry",
        ],
        "within_effect_max": decomposition_df.loc[
            decomposition_df["within_wage_effect"].idxmax(),
            "industry",
        ],
        "composition_effect_max": decomposition_df.loc[
            decomposition_df["centered_composition_effect"].idxmax(),
            "industry",
        ],
        "composition_effect_min": decomposition_df.loc[
            decomposition_df["centered_composition_effect"].idxmin(),
            "industry",
        ],
        "total_contribution_max": decomposition_df.loc[
            decomposition_df["total_contribution"].idxmax(),
            "industry",
        ],
        "total_contribution_min": decomposition_df.loc[
            decomposition_df["total_contribution"].idxmin(),
            "industry",
        ],
    }


def create_industry_composition_analysis_results(
    decomposition_df: pd.DataFrame,
    reconstructed_df: pd.DataFrame,
) -> list[str]:
    """産業構成効果分析の主要結果を文章化する。"""

    start_wage = reconstructed_df.loc[
        reconstructed_df["year"] == 2015,
        "reconstructed_wage",
    ].iloc[0]

    end_wage = reconstructed_df.loc[
        reconstructed_df["year"] == 2025,
        "reconstructed_wage",
    ].iloc[0]

    total_change = end_wage - start_wage
    total_change_pt = total_change / start_wage * 100

    within = decomposition_df["within_wage_effect"].sum()
    composition = decomposition_df["composition_effect"].sum()
    interaction = decomposition_df["interaction_effect"].sum()

    within_pt = within / start_wage * 100
    composition_pt = composition / start_wage * 100
    interaction_pt = interaction / start_wage * 100

    return [
        (
            "分析対象16産業から再構築した平均賃金は、"
            f"2015→2025で {total_change_pt:+.2f}% "
            f"（{total_change:+,.0f}円）変化した。"
        ),
        (
            f"産業内賃金効果は {within_pt:+.2f}pt、"
            f"産業構成効果は {composition_pt:+.2f}pt、"
            f"交差効果は {interaction_pt:+.2f}pt だった。"
        ),
        ("平均賃金上昇の大部分は、各産業内での賃金上昇によって説明される。"),
    ]


def create_industry_composition_analysis_discussion(
    decomposition_df: pd.DataFrame,
) -> list[str]:
    """産業構成効果分析の考察を文章化する。"""

    composition = decomposition_df["centered_composition_effect_pt"]

    composition_max_industry = decomposition_df.loc[
        composition.idxmax(),
        "industry",
    ]

    composition_min_industry = decomposition_df.loc[
        composition.idxmin(),
        "industry",
    ]

    composition_max_name = INDUSTRY_NAMES.get(
        composition_max_industry,
        composition_max_industry,
    )

    composition_min_name = INDUSTRY_NAMES.get(
        composition_min_industry,
        composition_min_industry,
    )

    return [
        (
            "産業構成の変化は、2015→2025全体では"
            "平均賃金をわずかに押し下げる方向に作用した。"
        ),
        (
            "ただし構成効果は期間を通じて一定ではなく、"
            "2015→2019はマイナス、2019→2020はほぼゼロ、"
            "2020→2025はプラスだった。"
        ),
        (
            f"産業別の構成寄与では {composition_max_name} が"
            f"最も押し上げ方向、{composition_min_name} が"
            "最も押し下げ方向に寄与した。"
        ),
        (
            "産業構成効果と各産業の総寄与は別物であり、"
            "雇用規模・産業内賃金上昇・シェア変化を分けて解釈する必要がある。"
        ),
    ]
