# Real Wage Dashboard

消費者物価指数、名目賃金、実質賃金の推移を可視化・比較するStreamlitダッシュボードです。

e-Statの消費者物価指数と毎月勤労統計調査の賃金データを組み合わせ、
賃金項目・就業形態・事業所規模・CPI系列を切り替えながら、
名目賃金と物価、実質的な購買力の変化を分析できます。

---

## 主な機能

### 消費者物価指数

- e-Stat APIから全国の消費者物価指数を取得
- 以下の4系列を切り替えて表示
  - 総合
  - 生鮮食品を除く総合
  - 生鮮食品及びエネルギーを除く総合
  - 持家の帰属家賃を除く総合

- 最新指数、前月比、前年同月比を表示
- 表示期間を選択して時系列グラフを表示
- CSV出力
- APIデータの再取得

---

### 名目賃金

毎月勤労統計調査の長期時系列データから、条件を選択して名目賃金を分析します。

選択可能な条件：

- 賃金項目
  - 現金給与総額
  - きまって支給する給与
- 就業形態
  - 就業形態計
  - 一般労働者
  - パートタイム労働者
- 事業所規模
  - 5人以上
  - 30人以上

産業分類は「調査産業計」に固定しています。

主な表示内容：

- 最新月の名目賃金
- 前月比
- 前年同月比
- 月次名目賃金
- 12か月移動平均
- 名目賃金前年同月比
- CSV出力

12か月移動平均は初期状態で表示され、
ユーザーがON/OFFを切り替えられます。

---

### 実質賃金

選択した名目賃金と消費者物価指数を年月で結合し、
物価変動を考慮した実質賃金をアプリ内で算出します。

実質賃金額は次の式で計算しています。

```text
実質賃金額 = 名目賃金 ÷ CPI × 100
```

実質賃金の12か月移動平均は、

```text
月次名目賃金
↓
同月CPIで実質化
↓
月次実質賃金
↓
12か月移動平均
```

の順で算出します。

名目賃金指数と実質賃金指数は、それぞれ独立して
2020年平均=100として指数化しています。

主な表示内容：

- 最新月の名目賃金
- 最新月のCPI
- 最新月の実質賃金
- 実質賃金前年同月比
- 名目賃金指数とCPIの比較
- 実質賃金指数（月次）
- 実質賃金指数（12か月移動平均）
- 実質賃金前年同月比
- CSV出力

---

## 使用データ

### 消費者物価指数

- 出典：政府統計の総合窓口 e-Stat
- 統計：消費者物価指数
- 地域：全国
- 基準：2020年=100

e-Stat APIから取得します。

### 名目賃金

- 出典：政府統計の総合窓口 e-Stat
- 統計：毎月勤労統計調査
- 産業：調査産業計
- 賃金項目：現金給与総額 / きまって支給する給与
- 事業所規模：5人以上 / 30人以上
- 就業形態：就業形態計 / 一般労働者 / パートタイム労働者

使用ファイル：

```text
data/raw/hon-maikin-k-jissu.csv
```

CSVは`cp932`で読み込みます。

---

## 使用技術

- Python 3.12
- Streamlit
- pandas
- requests
- pytest
- Ruff
- uv

---

## ディレクトリ構成

```text
real_wage_dashboard/
├── app.py
├── docs/
│   ├── v2_requirements.md
│   ├── v2_wbs.md
│   └── v2_release_notes.md
├── pages/
│   ├── 2_名目賃金.py
│   └── 3_実質賃金.py
├── data/
│   └── raw/
│       └── hon-maikin-k-jissu.csv
├── scripts/
│   ├── check_estat_api.py
│   ├── check_cpi_data.py
│   ├── check_wage_csv.py
│   ├── check_wage_data.py
│   └── check_real_wage_data.py
├── src/
│   └── real_wage_dashboard/
│       ├── config.py
│       ├── estat_client.py
│       ├── cpi_service.py
│       ├── cpi_analysis.py
│       ├── wage_service.py
│       ├── wage_analysis.py
│       └── real_wage_analysis.py
└── tests/
```

---

## セットアップ

```bash
uv sync
```

`.streamlit/secrets.toml`を作成し、e-Stat APIのアプリケーションIDを設定します。

```toml
ESTAT_APP_ID = "your-app-id"
```

---

## 実行

```bash
uv run streamlit run app.py
```

---

## テスト・コード品質確認

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

---

## CSV出力

### 名目賃金

`nominal_wage.csv`

主な列：

```text
year
month
wage_item
employment_type
establishment_size
nominal_wage_amount
nominal_wage_ma_12
mom_pct
yoy_pct
```

### 実質賃金

`real_wage.csv`

主な列：

```text
year
month
wage_item
employment_type
establishment_size
cpi_series
nominal_wage_amount
nominal_wage_ma_12
index_value
real_wage_amount
real_wage_ma_12
nominal_wage_index
real_wage_index
real_wage_index_ma_12
real_wage_mom_pct
real_wage_yoy_pct
```

---

## データ更新

名目賃金データを更新する場合は、毎月勤労統計調査の長期時系列CSVを取得し、

```text
data/raw/hon-maikin-k-jissu.csv
```

を置き換えます。

消費者物価指数は、アプリ実行時にe-Stat APIから取得します。

---

## 注意事項

このダッシュボードの実質賃金は、毎月勤労統計調査の現金給与総額と選択した消費者物価指数を用いて、アプリ内で独自に算出しています。

厚生労働省等が公表する公式の実質賃金指数とは、使用する指数・算出条件・丸め処理などの違いにより一致しない場合があります。
