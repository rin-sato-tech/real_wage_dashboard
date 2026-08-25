# データディレクトリ運用ガイド

## 1. この文書の目的

`data/`に保存する入力データの役割、Git管理方針、更新手順を定める。

各統計の公表元、取得ページ、読み込み条件は[`docs/reference/data_sources.md`](../docs/reference/data_sources.md)を参照する。

---

## 2. ディレクトリ構成

```text
data/
├── README.md
└── raw/
    ├── hon-maikin-k-jissu.csv
    └── labor_market/
        ├── effective_job_openings_ratio.xlsx
        ├── new_job_openings_ratio.xlsx
        ├── unemployment_rate.xlsx
        └── tankan_employment_di.csv
```

現在は、公表元から取得した入力データだけを`data/raw/`に保存する。

加工済みデータ、中間ファイル、アプリから出力したCSVは保存しない。

---

## 3. ファイルの役割

| ファイル                                             | 内容                                             | 主な利用先                                             |
| ---------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| `raw/hon-maikin-k-jissu.csv`                         | 毎月勤労統計の賃金、労働時間、出勤日数、労働者数 | 名目・実質賃金、雇用形態、給与構成、労働投入、産業分析 |
| `raw/labor_market/effective_job_openings_ratio.xlsx` | 有効求人倍率・季節調整値                         | 労働需給分析                                           |
| `raw/labor_market/new_job_openings_ratio.xlsx`       | 新規求人倍率・季節調整値                         | 労働需給分析                                           |
| `raw/labor_market/unemployment_rate.xlsx`            | 完全失業率・季節調整値                           | 労働需給分析                                           |
| `raw/labor_market/tankan_employment_di.csv`          | 企業規模別の雇用人員判断DI                       | 労働需給分析                                           |

CPIはe-Stat APIから取得するため、`data/raw/`には保存しない。

---

## 4. Git管理方針

現在の入力データは、分析結果の再現性を確保するためGitで管理する。

更新時は、次の方針に従う。

- 公表元ごとにコミットを分ける。
- 複数の統計ファイルを理由なく同時に更新しない。
- ファイル名を維持する。
- 文字コードやExcelのシート構成を無断で変更しない。
- 過去値の改定が含まれる場合は、その旨を記録する。
- データ更新と分析ロジック変更を可能な限り別コミットにする。
- 大容量化した場合は、Git LFSまたは外部保存への移行を別途検討する。

Excelは通常のGit diffで内容を確認できないため、更新年月、ファイルサイズ、主要系列の件数を更新前後で比較する。

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

更新前の次の情報を記録する。

- ファイル名
- 最終年月
- 行数または観測数
- ファイルサイズ
- 対象となる統計系列

### 6.3 ファイルの置換

1. 公表元から最新ファイルを取得する。
2. 既存ファイルと同じファイル名にする。
3. 対象ファイルだけを置き換える。
4. 読み込み可能な形式か確認する。
5. 対象期間、欠損、重複、主要条件を確認する。

元データの列名、シート名、文字コードが変更されている場合は、単純に置換せず、サービス処理とテストへの影響を確認する。

---

## 7. 更新後の検証

各確認スクリプトの用途と推奨実行順序は、[`scripts/README.md`](../scripts/README.md)を参照する。

最低限、次を実行する。

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

毎月勤労統計を更新した場合：

```bash
uv run python scripts/check_wage_csv.py
uv run python scripts/check_wage_data.py
uv run python scripts/check_wage_v2_combinations.py
uv run python scripts/check_wage_v2_conditions.py
uv run python scripts/check_working_hours_conditions.py
```

CPIとの結合結果も確認する場合：

```bash
uv run python scripts/check_real_wage_data.py
```

労働需給データを更新した場合：

```bash
uv run pytest tests/test_labor_market_service.py
uv run pytest tests/test_labor_market_analysis.py
```

更新後は次を更新前と比較する。

- 最新年月
- 観測数
- 欠損数
- 重複数
- 分析対象となる条件の件数
- 主要な年平均値
- 個別分析文書に記載した主要結果

---

## 8. 更新時に確認する文書

データ更新によって対象期間、数値、計算結果が変わった場合は、次を確認する。

1. `docs/reference/data_sources.md`
2. 対応する`docs/analysis/`の個別分析文書
3. `docs/analysis/00_overview.md`
4. `docs/planning/wage_analysis_roadmap.md`
5. `docs/reference/implementation_map.md`

単なる最新月追加で主要結論が変わらない場合は、すべての文書へ最新値を重複して追記しない。

---

## 9. 新しいデータを追加する場合

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

追加後は`docs/reference/data_sources.md`と`docs/reference/implementation_map.md`を更新する。
