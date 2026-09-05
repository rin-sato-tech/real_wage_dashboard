# 確認スクリプト運用ガイド

## 1. この文書の目的

`scripts/` には、実データ・公表Excel・e-Stat API・分析結果を人間が確認するための実行スクリプトを置く。

自動テストは `tests/`、再利用可能な分析ロジックは `src/real_wage_dashboard/` に置き、`scripts/` へ業務ロジックを蓄積しない。

---

## 2. ディレクトリ構成

```text
scripts/
├── README.md
├── wage/
│   ├── check_wage_csv.py
│   ├── check_wage_data.py
│   ├── check_wage_v2_conditions.py
│   ├── check_wage_v2_combinations.py
│   ├── check_working_hours_conditions.py
│   └── check_establishment_size_wage.py
├── cpi/
│   ├── check_estat_api.py
│   ├── check_cpi_data.py
│   ├── check_real_wage_data.py
│   └── check_real_wage_decomposition_index.py
├── corporate/
│   ├── check_corporate_stats_metadata.py
│   ├── check_corporate_performance_data.py
│   ├── check_corporate_performance_comparison.py
│   ├── check_corporate_performance_by_capital_class.py
│   ├── check_corporate_performance_by_industry.py
│   ├── check_corporate_wage_industry_relationship.py
│   ├── check_corporate_wage_time_series.py
│   └── check_corporate_long_term_availability.py
└── wage_revision/
    ├── check_wage_revision_excel_structure.py
    ├── check_wage_revision_amount_rate.py
    ├── check_wage_revision_status.py
    ├── check_wage_revision_factors.py
    ├── check_wage_revision_recent_structure.py
    └── check_wage_revision_analysis.py
```

分類は「何を確認するスクリプトか」という分析領域を基準とする。

---

## 3. `scripts/` と `tests/` の役割

| 項目               | `scripts/`                             | `tests/`                   |
| ------------------ | -------------------------------------- | -------------------------- |
| 主目的             | 実データ・公表ファイルの目視確認、探索 | 自動回帰テスト             |
| 実行               | 必要時に手動                           | 開発時・CIで継続実行       |
| 出力               | 表・件数・検証結果を標準出力           | pass / fail                |
| 外部API            | 使用する場合がある                     | 原則としてモック・固定入力 |
| 正式な業務ロジック | 置かない                               | 置かない                   |
| 再利用処理         | `src/` を呼び出す                      | `src/` を検証する          |

確認スクリプトで有用な処理が増えた場合は、`src/real_wage_dashboard/` へ移してテストを追加する。

---

## 4. 実行方法

リポジトリ直下から実行する。

```bash
uv sync
```

e-Stat APIを使用するスクリプトでは `.streamlit/secrets.toml` に `ESTAT_APP_ID` が必要である。

基本形：

```bash
uv run python scripts/<category>/<script>.py
```

例：

```bash
uv run python scripts/wage/check_wage_data.py
uv run python scripts/cpi/check_cpi_data.py
uv run python scripts/corporate/check_corporate_performance_data.py
uv run python scripts/wage_revision/check_wage_revision_analysis.py
```

---

## 5. 賃金・労働時間

### `check_wage_csv.py`

毎月勤労統計CSVが読み込めることを最小限確認する。

```bash
uv run python scripts/wage/check_wage_csv.py
```

### `check_wage_data.py`

主要賃金系列の件数、対象期間、基本的な値を確認する。

```bash
uv run python scripts/wage/check_wage_data.py
```

### `check_wage_v2_conditions.py`

事業所規模・就業形態・産業等の主要条件を確認する。

```bash
uv run python scripts/wage/check_wage_v2_conditions.py
```

### `check_wage_v2_combinations.py`

分析で使用する条件の組合せが存在することを確認する。

```bash
uv run python scripts/wage/check_wage_v2_combinations.py
```

### `check_working_hours_conditions.py`

労働時間・出勤日数系列の条件と利用可能期間を確認する。

```bash
uv run python scripts/wage/check_working_hours_conditions.py
```

### `check_establishment_size_wage.py`

5人以上・30人以上系列について、2015～2025年の月額賃金、総実労働時間、概算時間当たり賃金、規模間比率、対数分解を確認する。

```bash
uv run python scripts/wage/check_establishment_size_wage.py
```

5人以上系列は30人以上事業所を含むため、独立二群の比較とは解釈しない。

---

## 6. CPI・実質賃金

### `check_estat_api.py`

e-Stat APIとの接続とレスポンスを確認する。

```bash
uv run python scripts/cpi/check_estat_api.py
```

### `check_cpi_data.py`

CPI系列の取得、期間、件数、基本変換を確認する。

```bash
uv run python scripts/cpi/check_cpi_data.py
```

### `check_real_wage_data.py`

毎月勤労統計の名目賃金とCPIの結合・実質化を確認する。

```bash
uv run python scripts/cpi/check_real_wage_data.py
```

### `check_real_wage_decomposition_index.py`

名目賃金指数、公表前年比、CPI、公式実質賃金指数を用いて、2015～2025年の長期要因分解と整合性を確認する。

```bash
uv run python scripts/cpi/check_real_wage_decomposition_index.py
```

---

## 7. 法人企業統計・企業業績

### 基本確認

```bash
uv run python scripts/corporate/check_corporate_stats_metadata.py
uv run python scripts/corporate/check_corporate_performance_data.py
uv run python scripts/corporate/check_corporate_long_term_availability.py
```

### 構造比較

```bash
uv run python scripts/corporate/check_corporate_performance_comparison.py
uv run python scripts/corporate/check_corporate_performance_by_capital_class.py
uv run python scripts/corporate/check_corporate_performance_by_industry.py
```

### 賃金との接続

```bash
uv run python scripts/corporate/check_corporate_wage_time_series.py
uv run python scripts/corporate/check_corporate_wage_industry_relationship.py
```

企業側指標と毎月勤労統計は、母集団・集計単位・規模定義が異なることに注意する。

---

## 8. 賃金改定調査

### Excel構造確認

```bash
uv run python scripts/wage_revision/check_wage_revision_excel_structure.py
uv run python scripts/wage_revision/check_wage_revision_recent_structure.py
```

公表Excelのシート・列配置・年次差を確認する。

### 個別系列確認

```bash
uv run python scripts/wage_revision/check_wage_revision_amount_rate.py
uv run python scripts/wage_revision/check_wage_revision_status.py
uv run python scripts/wage_revision/check_wage_revision_factors.py
```

### 統合分析確認

```bash
uv run python scripts/wage_revision/check_wage_revision_analysis.py
```

設問・回答区分が年によって変わるため、長期系列を機械的に連結しない。

---

## 9. 推奨実行順序

### 毎月勤労統計を更新した場合

```bash
uv run python scripts/wage/check_wage_csv.py
uv run python scripts/wage/check_wage_v2_conditions.py
uv run python scripts/wage/check_wage_v2_combinations.py
uv run python scripts/wage/check_wage_data.py
uv run python scripts/wage/check_working_hours_conditions.py
uv run python scripts/wage/check_establishment_size_wage.py
```

### CPI・実質賃金を確認する場合

```bash
uv run python scripts/cpi/check_estat_api.py
uv run python scripts/cpi/check_cpi_data.py
uv run python scripts/cpi/check_real_wage_data.py
uv run python scripts/cpi/check_real_wage_decomposition_index.py
```

### 法人企業統計を更新・再検証する場合

```bash
uv run python scripts/corporate/check_corporate_stats_metadata.py
uv run python scripts/corporate/check_corporate_performance_data.py
uv run python scripts/corporate/check_corporate_long_term_availability.py
uv run python scripts/corporate/check_corporate_performance_comparison.py
uv run python scripts/corporate/check_corporate_performance_by_capital_class.py
uv run python scripts/corporate/check_corporate_performance_by_industry.py
uv run python scripts/corporate/check_corporate_wage_time_series.py
uv run python scripts/corporate/check_corporate_wage_industry_relationship.py
```

### 賃金改定調査を更新した場合

```bash
uv run python scripts/wage_revision/check_wage_revision_excel_structure.py
uv run python scripts/wage_revision/check_wage_revision_recent_structure.py
uv run python scripts/wage_revision/check_wage_revision_amount_rate.py
uv run python scripts/wage_revision/check_wage_revision_status.py
uv run python scripts/wage_revision/check_wage_revision_factors.py
uv run python scripts/wage_revision/check_wage_revision_analysis.py
```

---

## 10. スクリプト実行後

確認スクリプトで異常がなければ、最後に自動テストと静的チェックを実行する。

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

分析結果が変化した場合は、対応する `docs/analysis/` と `docs/analysis/00_overview.md` を確認する。

---

## 11. 新しい確認スクリプトを追加する場合

配置先は対象データ・分析領域で決める。

- 毎月勤労統計・労働時間・事業所規模：`scripts/wage/`
- CPI・実質賃金：`scripts/cpi/`
- 法人企業統計・企業業績：`scripts/corporate/`
- 賃金改定調査：`scripts/wage_revision/`

新しい分析領域で複数の確認スクリプトが必要になった場合だけ、新しいサブディレクトリを追加する。

`misc/`、`validation/`、`temp/` のように目的の曖昧な分類は作らない。

---

## 12. 削除・統合の基準

次の場合はスクリプトの削除・統合を検討する。

- 同じ確認を別スクリプトが完全に代替している。
- 探索用コードが正式な分析ロジックとテストへ移行済みである。
- 対象データや分析が廃止された。
- 一時的な構造調査が終了し、再利用予定がない。

削除前に、README・データ更新手順・分析文書から参照されていないことを確認する。
