# データディレクトリ運用ガイド

## 1. この文書の目的

`data/`に保存する入力データの役割、Git管理方針、更新手順を定める。

各統計の公表元、取得方法、読み込み条件は[`docs/reference/data_sources.md`](../docs/reference/data_sources.md)を参照する。

---

## 2. ディレクトリ構成

```text
data/
├── README.md
└── raw/
    ├── hon-maikin-k-jissu.csv
    ├── labor_market/
    │   ├── effective_job_openings_ratio.xlsx
    │   ├── new_job_openings_ratio.xlsx
    │   ├── unemployment_rate.xlsx
    │   └── tankan_employment_di.csv
    ├── real_wage_decomposition/
    │   ├── official_real_wage_index_5plus.xls
    │   └── wage_index_total_5plus.xls
    └── wage_revision/
        ├── wage_revision_amount_rate.xlsx
        ├── wage_revision_factors.xlsx
        └── wage_revision_status.xlsx
```

`data/raw/`には、公表元から取得した入力データを保存する。

加工済みデータ、中間ファイル、アプリから出力したCSVは保存しない。

e-Stat APIから都度取得するCPI・法人企業統計のAPIレスポンスは保存しない。

---

## 3. ファイルの役割

| ファイル                                                         | 内容                                             | 主な利用先                                                                         |
| ---------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `raw/hon-maikin-k-jissu.csv`                                     | 毎月勤労統計の賃金、労働時間、出勤日数、労働者数 | 名目・実質賃金、雇用形態、給与構成、労働投入、産業分析、産業構成、事業所規模別分析 |
| `raw/labor_market/effective_job_openings_ratio.xlsx`             | 有効求人倍率・季節調整値                         | 労働需給分析                                                                       |
| `raw/labor_market/new_job_openings_ratio.xlsx`                   | 新規求人倍率・季節調整値                         | 労働需給分析                                                                       |
| `raw/labor_market/unemployment_rate.xlsx`                        | 完全失業率・季節調整値                           | 労働需給分析                                                                       |
| `raw/labor_market/tankan_employment_di.csv`                      | 企業規模別の雇用人員判断DI                       | 労働需給分析                                                                       |
| `raw/real_wage_decomposition/wage_index_total_5plus.xls`         | 5人以上・就業形態計の名目賃金指数・増減率        | 実質賃金要因分解                                                                   |
| `raw/real_wage_decomposition/official_real_wage_index_5plus.xls` | 厚生労働省公表の実質賃金指数・増減率             | 実質賃金要因分解、再構築系列の整合確認                                             |
| `raw/wage_revision/wage_revision_amount_rate.xlsx`               | 1人平均賃金改定額・改定率                        | 賃金改定行動分析                                                                   |
| `raw/wage_revision/wage_revision_status.xlsx`                    | 賃金引上げ・引下げ・変更なし等の実施状況         | 賃金改定行動分析                                                                   |
| `raw/wage_revision/wage_revision_factors.xlsx`                   | 賃金改定時に重視した要素                         | 賃金改定行動分析                                                                   |

CPIと法人企業統計はe-Stat APIから取得するため、`data/raw/`には保存しない。

---

## 4. Git管理方針

現在の入力データは、分析結果の再現性を確保するためGitで管理する。

更新時は、次の方針に従う。

- 公表元ごとにコミットを分ける。
- 複数の統計ファイルを理由なく同時に更新しない。
- ファイル名を維持する。
- 文字コードやExcelのシート構成を意図なく変更しない。
- 過去値の改定が含まれる場合は、その旨を記録する。
- データ更新と分析ロジック変更を可能な限り別コミットにする。
- Excel / xlsは通常のGit diffで内容を確認できないため、更新年月、ファイルサイズ、主要系列の件数を比較する。
- 大容量化した場合はGit LFSまたは外部保存への移行を別途検討する。

---

## 5. 保存しないファイル

次のファイルは`data/`へ保存・コミットしない。

- Streamlitからダウンロードした分析用CSV
- Tableau等へ一時的に読み込む出力ファイル
- 一時的な加工データ
- Notebookや確認スクリプトの中間出力
- Excelの一時ファイル
- API認証情報
- 個人情報や非公開データ
- e-Stat APIの一時レスポンス

再利用する加工データが必要になった場合は、生成処理、入力元、再生成方法を確立してから保存場所を決める。

---

## 6. ファイル更新手順

### 6.1 更新ブランチ

データ更新は専用ブランチで行う。

```bash
git switch main
git pull --ff-only
git switch -c data/update-statistics-YYYYMM
```

### 6.2 更新前の確認

```bash
git status
git log -1 --oneline -- data/
```

更新前に次を記録する。

- ファイル名
- 最終年月・年度
- 行数または観測数
- ファイルサイズ
- 対象となる統計系列

### 6.3 ファイルの置換

1. 公表元から最新ファイルを取得する。
2. 既存ファイルと同じファイル名にする。
3. 対象ファイルだけを置き換える。
4. 読み込み可能な形式か確認する。
5. 対象期間、欠損、重複、主要条件を確認する。

元データの列名、シート名、文字コード、回答区分等が変更されている場合は、単純に置換せず、サービス処理とテストへの影響を確認する。

---

## 7. 更新後の検証

各確認スクリプトの用途と推奨実行順序は、[`scripts/README.md`](../scripts/README.md)を参照する。

最低限、次を実行する。

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### 7.1 毎月勤労統計を更新した場合

```bash
uv run python scripts/wage/check_wage_csv.py
uv run python scripts/wage/check_wage_v2_conditions.py
uv run python scripts/wage/check_wage_v2_combinations.py
uv run python scripts/wage/check_wage_data.py
uv run python scripts/wage/check_working_hours_conditions.py
uv run python scripts/wage/check_establishment_size_wage.py
```

CPIとの結合結果も確認する場合：

```bash
uv run python scripts/cpi/check_real_wage_data.py
```

実質賃金要因分解への影響も確認する場合：

```bash
uv run python scripts/cpi/check_real_wage_decomposition_index.py
```

### 7.2 労働需給データを更新した場合

```bash
uv run pytest tests/test_labor_market_service.py
uv run pytest tests/test_labor_market_analysis.py
```

### 7.3 賃金改定調査を更新した場合

まず、公表Excelの構造を確認する。

```bash
uv run python scripts/wage_revision/check_wage_revision_excel_structure.py
```

次に、

```bash
uv run python scripts/wage_revision/check_wage_revision_amount_rate.py
uv run python scripts/wage_revision/check_wage_revision_status.py
uv run python scripts/wage_revision/check_wage_revision_factors.py
uv run python scripts/wage_revision/check_wage_revision_analysis.py
```

を実行する。

さらに、

```bash
uv run pytest tests/test_wage_revision_service.py
uv run pytest tests/test_wage_revision_analysis.py
```

を実行する。

### 7.4 実質賃金要因分解用ファイルを更新した場合

```bash
uv run python scripts/cpi/check_real_wage_decomposition_index.py
uv run pytest tests/test_real_wage_decomposition_analysis.py
```

更新後は次を更新前と比較する。

- 最新年月・年度
- 観測数
- 欠損数
- 重複数
- 分析対象となる条件の件数
- 主要な年平均値
- 長期累積変化
- 個別分析文書に記載した主要結果

---

## 8. データ別の注意点

### 8.1 毎月勤労統計

毎月勤労統計では、過去値が改定される場合がある。

特に、

- 賃金
- 労働時間
- 出勤日数
- 事業所規模別系列

の変更が、複数分析へ波及する可能性がある。

### 8.2 賃金改定調査

年によって、

- 設問文
- 回答区分
- 企業規模区分
- 列配置

が変わる場合がある。

とくに「引下げ」と「変更なし」の扱いは年によって異なるため、単純連結しない。

### 8.3 実質賃金要因分解

公表前年比を連鎖して作る分析用指数は、年平均実額から直接計算した変化率とは計算経路が異なる。

両者を同一系列として比較しない。

---

## 9. 更新時に確認する文書

データ更新によって対象期間、数値、計算結果が変わった場合は、次を確認する。

1. `docs/reference/data_sources.md`
2. 対応する`docs/analysis/`の個別分析文書
3. `docs/analysis/00_overview.md`
4. `docs/planning/wage_analysis_roadmap.md`
5. `docs/reference/implementation_map.md`
6. `docs/reference/metric_definitions.md`
7. `docs/reference/methodology.md`

単なる最新月追加で主要結論が変わらない場合は、すべての文書へ最新値を重複して追記しない。

---

## 10. 新しいデータを追加する場合

新しい統計を追加する場合は、ファイルを先に置かず、次を決める。

- 分析上の問い
- 公表元と取得方法
- 統計の定義
- 保存形式とファイル名
- 更新頻度
- 読み込み処理
- データ検証
- 自動テスト
- 分析文書との対応

追加後は、

- `docs/reference/data_sources.md`
- `docs/reference/implementation_map.md`
- 必要に応じて`docs/reference/metric_definitions.md`
- 必要に応じて`docs/reference/methodology.md`

を更新する。
