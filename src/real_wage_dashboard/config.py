from pathlib import Path

CPI_STATS_DATA_ID = "0003427113"
LABOR_FORCE_STATS_DATA_ID = "0003005865"
CORPORATE_STATS_DATA_ID = "0003060791"
LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID = "0003009700"
LFS_HOURS_BY_AGE_SEX_STATS_DATA_ID = "0003009701"
LFS_EMPLOYMENT_TYPE_HOURS_STATS_DATA_ID = "0003006654"

SNA_INCOME_GENERATION_STATS_DATA_ID = "0004049810"
SNA_HOUSEHOLD_PRIMARY_INCOME_STATS_DATA_ID = "0004049854"
SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_STATS_DATA_ID = "0004049855"
SNA_HOUSEHOLD_USE_INCOME_STATS_DATA_ID = "0004049857"
SNA_NONFINANCIAL_CAPITAL_ACCOUNT_STATS_DATA_ID = "0004049767"
SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_STATS_DATA_ID = "0004049768"
SNA_SECTOR_NET_LENDING_AMOUNT_STATS_DATA_ID = "0004049961"
SNA_SECTOR_NET_LENDING_RATIO_STATS_DATA_ID = "0004049963"

CPI_BASE_FILTERS = {
    "cdTab": "1",
    "cdArea": "00000",
}

CPI_SERIES = {
    "総合": "0001",
    "生鮮食品を除く総合": "0161",
    "生鮮食品及びエネルギーを除く総合": "0178",
    "持家の帰属家賃を除く総合": "0163",
}

CPI_FILE_NAMES = {
    "総合": "cpi_all_items.csv",
    "生鮮食品を除く総合": "cpi_excluding_fresh_food.csv",
    "生鮮食品及びエネルギーを除く総合": "cpi_excluding_fresh_food_and_energy.csv",
    "持家の帰属家賃を除く総合": "cpi_excluding_imputed_rent.csv",
}

CPI_METADATA = {
    "source": "政府統計の総合窓口 e-Stat",
    "statistics_name": "消費者物価指数",
    "area_name": "全国",
    "base_year": "2020年=100",
}

WAGE_DATA_PATH = Path("data/raw/hon-maikin-k-jissu.csv")

WAGE_ITEMS = {
    "現金給与総額": "現金給与総額",
    "きまって支給する給与": "きまって支給する給与",
}

WAGE_ESTABLISHMENT_SIZES = {
    "5人以上": "T",
    "30人以上": "0",
}

WAGE_EMPLOYMENT_TYPES = {
    "就業形態計": "0",
    "一般労働者": "1",
    "パートタイム労働者": "2",
}

WAGE_DEFAULT_ITEM = "現金給与総額"
WAGE_DEFAULT_ESTABLISHMENT_SIZE = "5人以上"
WAGE_DEFAULT_EMPLOYMENT_TYPE = "就業形態計"

WAGE_BASE_YEAR = 2020
WAGE_MOVING_AVERAGE_WINDOW = 12
WAGE_DEFAULT_SHOW_MOVING_AVERAGE = True

CPI_DEFAULT_SERIES = "総合"

WAGE_METADATA = {
    "source": "政府統計の総合窓口 e-Stat",
    "statistics_name": "毎月勤労統計調査",
    "industry": "調査産業計",
    "unit": "円",
}

CORPORATE_ITEMS = {
    "sales": "045",
    "operating_profit": "048",
    "ordinary_profit": "051",
    "executive_salary": "065",
    "executive_bonus": "057",
    "employee_salary": "066",
    "employee_bonus": "235",
    "welfare_expenses": "067",
    "average_employees": "072",
    "value_added": "073",
    "operating_profit_margin": "126",
    "ordinary_profit_margin": "127",
    "value_added_ratio": "140",
    "labor_productivity": "141",
}

CORPORATE_INDUSTRIES = {
    "全産業（除く金融保険業）": "104",
}

CORPORATE_CAPITAL_CLASSES = {
    "全規模": "26",
    "大企業": "25",
    "中堅企業": "24",
    "中小企業": "22",
}

CORPORATE_INDUSTRY_MAPPING = {
    "C": "106",  # 鉱業、採石業、砂利採取業
    "D": "107",  # 建設業
    "E": "108",  # 製造業
    "G": "142",  # 情報通信業
    "H": "134",  # 運輸業、郵便業(集約)
    "I": "129",  # 卸売業・小売業(集約)
    "K": "155",  # 不動産業、物品賃貸業(集約)
    "L": "161",  # 学術研究、専門・技術サービス業(集約)
    "M": "156",  # 宿泊業、飲食サービス業(集約)
    "N": "157",  # 生活関連サービス業、娯楽業(集約)
    "O": "153",  # 教育、学習支援業
    "P": "152",  # 医療、福祉業
}

CORPORATE_INDUSTRY_NAMES = {
    "C": "鉱業、採石業等",
    "D": "建設業",
    "E": "製造業",
    "G": "情報通信業",
    "H": "運輸業、郵便業",
    "I": "卸売業、小売業",
    "K": "不動産・物品賃貸業",
    "L": "学術研究等",
    "M": "宿泊・飲食サービス業",
    "N": "生活関連サービス等",
    "O": "教育、学習支援業",
    "P": "医療、福祉",
}

CORPORATE_ANALYSIS_START_YEAR = 2015
CORPORATE_ANALYSIS_END_YEAR = 2024

LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS = {
    "cdTab": "01",  # 実数(人口)
    "cdCat01": "0",  # 性別：総数
    "cdCat03": "03",  # 就業状態：従業者
    "cdCat05": "000",  # 産業：全産業
    "cdCat06": "00",  # 従業上の地位：総数
    "cdArea": "00000",  # 全国
}

LFS_WORKING_HOURS_AGE_CODES = {
    "15歳以上": "00",
    "15～24歳": "01",
    "25～34歳": "06",
    "35～44歳": "09",
    "45～54歳": "12",
    "55～64歳": "15",
    "65歳以上": "18",
}

LFS_WORKING_HOURS_CATEGORY_CODES = {
    "persons_at_work": "03",
    # 長期比較用
    "hours_1_34": "95",
    "hours_35_48": "17",
    "hours_49_plus": "94",
    # 詳細区分
    "hours_1_14": "04",
    "hours_15_29": "15",
    "hours_30_34": "16",
    "hours_35_39": "18",
    "hours_40_48": "19",
    "hours_49_59": "12",
    "hours_60_plus": "13",
}

LFS_EMPLOYMENT_BY_AGE_PATH = Path(
    "data/raw/labor_input/lfs_employment_by_age_annual.xlsx"
)

LFS_HOURS_BY_AGE_PATH = Path("data/raw/labor_input/lfs_hours_by_age_annual.csv")

LFS_WORKING_HOURS_DISTRIBUTION_SNAPSHOT_PATH = Path(
    "data/raw/labor_input/lfs_working_hours_distribution_2000_2025.json"
)

LFS_HOURS_BY_AGE_SEX_SNAPSHOT_PATH = Path(
    "data/raw/labor_input/lfs_hours_by_age_sex_2000_2025.json"
)

LFS_EMPLOYMENT_TYPE_HOURS_SNAPSHOT_PATH = Path(
    "data/raw/labor_input/lfs_employment_type_hours_2012_2025.json"
)

LFS_HOURS_BY_AGE_SEX_BASE_FILTERS = {
    "cdCat03": "00",  # 従業上の地位：総数
    "cdCat04": "000",  # 産業：全産業
    "cdArea": "00000",  # 全国
}

LFS_HOURS_BY_AGE_SEX_TAB_CODES = {
    "average_weekly_hours": "03",
    "aggregate_weekly_hours": "13",
}

LFS_HOURS_BY_AGE_SEX_CODES = {
    "total": "0",
    "male": "1",
    "female": "2",
}

LFS_EMPLOYMENT_TYPE_HOURS_BASE_FILTERS = {
    "cdTab": "07",  # 就業者
    "cdCat03": "0",  # 性別：総数
    "cdArea": "00000",  # 全国
}

LFS_EMPLOYMENT_TYPE_CODES = {
    "total_excluding_executives": "02",
    "regular": "03",
    "nonregular": "10",
}

LFS_EMPLOYMENT_TYPE_AGE_CODES = {
    "15～24歳": "01",
    "25～34歳": "03",
    "35～44歳": "04",
    "45～54歳": "05",
    "55～64歳": "06",
    "65歳以上": "07",
}

LFS_EMPLOYMENT_TYPE_HOURS_CODES = {
    "persons_at_work": "06",
    "hours_1_34": "01",
    "hours_1_29": "02",
    "hours_35_plus": "03",
    "hours_49_plus": "04",
}

SNA_ANALYSIS_START_YEAR = 1994
SNA_ANALYSIS_END_YEAR = 2024

SNA_INCOME_GENERATION_ITEMS = {
    "employee_compensation": "11",
    "taxes_on_production_and_imports": "16",
    "subsidies": "22",
    "net_operating_surplus_mixed_income": "23",
    "net_operating_surplus": "24",
    "net_mixed_income": "25",
    "gross_operating_surplus_mixed_income": "26",
    "gross_operating_surplus": "27",
    "gross_mixed_income": "28",
    "consumption_fixed_capital": "29",
    "net_domestic_product": "31",
    "gross_domestic_product": "32",
}

SNA_HOUSEHOLD_PRIMARY_INCOME_ITEMS = {
    "property_income_paid": "11",
    "net_primary_income_balance": "19",
    "gross_primary_income_balance": "20",
    "net_operating_surplus_mixed_income": "23",
    "net_operating_surplus_imputed_rent": "24",
    "net_mixed_income": "25",
    "employee_compensation_received": "30",
    "property_income_received": "35",
    "interest_received": "36",
    "dividends_received": "37",
    "other_investment_income_received": "44",
    "rent_received": "39",
}

SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_ITEMS = {
    "current_taxes_paid": "11",
    "net_social_contributions_paid": "44",
    "other_current_transfers_paid": "23",
    "net_disposable_income": "28",
    "net_primary_income_balance": "32",
    "social_benefits_received": "35",
    "other_current_transfers_received": "40",
}

SNA_HOUSEHOLD_USE_INCOME_ITEMS = {
    "household_final_consumption": "11",
    "net_saving": "12",
    "gross_saving": "13",
    "net_disposable_income": "16",
    "gross_disposable_income": "17",
    "pension_entitlement_adjustment": "22",
    "published_saving_rate": "21",
}

SNA_NONFINANCIAL_CAPITAL_ACCOUNT_ITEMS = {
    "gross_fixed_capital_formation": "11",
    "consumption_fixed_capital": "12",
    "changes_in_inventories": "25",
    "net_land_purchases": "14",
    "net_lending_capital_account": "15",
    "net_saving": "17",
    "capital_transfers_received": "18",
    "capital_transfers_paid": "21",
}

SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_ITEMS = {
    "net_lending_financial_account": "200",
}

SNA_SECTOR_NET_LENDING_ITEMS = {
    "capital_nonfinancial_corporations": "12",
    "capital_financial_corporations": "13",
    "capital_general_government": "14",
    "capital_households": "15",
    "capital_npish": "16",
    "capital_rest_of_world": "17",
    "statistical_discrepancy": "18",
    "financial_nonfinancial_corporations": "20",
    "financial_financial_corporations": "21",
    "financial_general_government": "22",
    "financial_households": "23",
    "financial_npish": "24",
    "financial_rest_of_world": "25",
}
