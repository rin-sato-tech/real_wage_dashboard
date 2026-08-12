# Real Wage Dashboard

消費者物価指数、名目賃金、実質賃金の推移を可視化・比較するStreamlitダッシュボードです。

e-Stat APIから消費者物価指数を取得し、毎月勤労統計調査の現金給与総額と組み合わせて、物価変動を考慮した実質賃金を分析します。

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

### 名目賃金

毎月勤労統計調査の長期時系列データから、以下の条件で現金給与総額を抽出します。

- 産業：調査産業計
- 事業所規模：5人以上
- 就業形態：就業形態計
- 項目：現金給与総額

主な表示内容：

- 最新の現金給与総額
- 前月比
- 前年同月比
- 時系列グラフ
- CSV出力

### 実質賃金

名目賃金と消費者物価指数を年月で結合し、物価変動を考慮した実質賃金を算出します。

実質賃金額は次の式で計算しています。

```text
実質賃金額 = 名目賃金 ÷ CPI × 100
```

また、名目賃金と実質賃金を2020年平均=100として指数化し、物価との比較を行います。

主な表示内容：

- 最新の名目賃金
- 最新の消費者物価指数
- 実質賃金額
- 実質賃金前年同月比
- 名目賃金指数とCPIの比較
- 実質賃金指数の推移
- CSV出力

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
- 項目：現金給与総額
- 産業：調査産業計
- 事業所規模：5人以上
- 就業形態：就業形態計

使用ファイル：

```text
data/raw/hon-maikin-k-jissu.csv
```

CSVは`cp932`で読み込みます。

## 使用技術

- Python 3.12
- Streamlit
- pandas
- requests
- pytest
- Ruff
- uv

## ディレクトリ構成

```text
real_wage_dashboard/
├── app.py
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

## セットアップ

```bash
uv sync
```

`.streamlit/secrets.toml`を作成し、e-Stat APIのアプリケーションIDを設定します。

```toml
ESTAT_APP_ID = "your-app-id"
```

## 実行

```bash
uv run streamlit run app.py
```

## テスト・コード品質確認

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## データ更新

名目賃金データを更新する場合は、毎月勤労統計調査の長期時系列CSVを取得し、

```text
data/raw/hon-maikin-k-jissu.csv
```

を置き換えます。

消費者物価指数は、アプリ実行時にe-Stat APIから取得します。

## 注意事項

このダッシュボードの実質賃金は、毎月勤労統計調査の現金給与総額と選択した消費者物価指数を用いて、アプリ内で独自に算出しています。

厚生労働省等が公表する公式の実質賃金指数とは、使用する指数・算出条件・丸め処理などの違いにより一致しない場合があります。
