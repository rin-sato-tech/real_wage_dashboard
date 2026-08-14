from pathlib import Path

CPI_STATS_DATA_ID = "0003427113"

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
    "item_name": "現金給与総額",
    "industry": "調査産業計",
    "establishment_size": "事業所規模5人以上",
    "employment_type": "就業形態計",
    "unit": "円",
}
