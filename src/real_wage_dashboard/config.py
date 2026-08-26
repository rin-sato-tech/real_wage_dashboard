from pathlib import Path

CPI_STATS_DATA_ID = "0003427113"
LABOR_FORCE_STATS_DATA_ID = "0003005865"
CORPORATE_STATS_DATA_ID = "0003060791"

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

CORPORATE_ANALYSIS_START_YEAR = 2015
CORPORATE_ANALYSIS_END_YEAR = 2024
