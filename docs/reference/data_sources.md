# データ出典・取得方法

## 1. この文書の目的

Real Wage Dashboardで現在使用している入力データについて、出典、取得方法、保存場所、読み込み条件、更新時の注意点を整理する。

指標の計算式と定義は`metric_definitions.md`、分析方法の共通方針は`methodology.md`で管理する。

---

## 2. 入力データ一覧

| 分野                   | 統計・系列                               | 公表元               | 取得方法        | リポジトリ内の保存場所                           |
| ---------------------- | ---------------------------------------- | -------------------- | --------------- | ------------------------------------------------ |
| 物価                   | 消費者物価指数                           | 総務省統計局・e-Stat | e-Stat API      | 保存しない                                       |
| 賃金・労働時間         | 毎月勤労統計調査・長期時系列表           | 厚生労働省・e-Stat   | CSVを手動取得   | `data/raw/hon-maikin-k-jissu.csv`                |
| 求人倍率               | 一般職業紹介状況                         | 厚生労働省           | Excelを手動取得 | `data/raw/labor_market/`                         |
| 完全失業率             | 労働力調査・長期時系列データ             | 総務省統計局         | Excelを手動取得 | `data/raw/labor_market/unemployment_rate.xlsx`   |
| 企業の雇用判断         | 全国企業短期経済観測調査（短観）         | 日本銀行             | CSVを手動取得   | `data/raw/labor_market/tankan_employment_di.csv` |
| 企業業績・生産性・分配 | 法人企業統計調査・年次別調査             | 財務省・e-Stat       | e-Stat API      | 保存しない                                       |
| 賃金改定行動           | 賃金引上げ等の実態に関する調査           | 厚生労働省           | Excelを手動取得 | `data/raw/wage_revision/`                        |
| 実質賃金要因分解       | 毎月勤労統計の賃金指数・公式実質賃金指数 | 厚生労働省           | Excelを手動取得 | `data/raw/real_wage_decomposition/`              |

`data/raw/`には公表元から取得した入力データを保存する。アプリからダウンロードする分析用CSVは入力データではなく、Git管理の対象としない。

---

## 3. 消費者物価指数

### 3.1 出典

- 統計：消費者物価指数
- 公表元：総務省統計局
- 取得元：e-Stat「2020年基準消費者物価指数」
- 取得方法：e-Stat API
- 統計表ID：`0003427113`
- 指数基準：2020年平均=100
- 対象地域：全国

### 3.2 API条件

| 条件                             | コード         |
| -------------------------------- | -------------- |
| 表章項目                         | `cdTab=1`      |
| 地域                             | `cdArea=00000` |
| 総合                             | `cdCat01=0001` |
| 生鮮食品を除く総合               | `cdCat01=0161` |
| 生鮮食品及びエネルギーを除く総合 | `cdCat01=0178` |
| 持家の帰属家賃を除く総合         | `cdCat01=0163` |

API通信は`src/real_wage_dashboard/estat_client.py`、CPI固有の変換は`src/real_wage_dashboard/cpi_service.py`で処理する。

取得結果はアプリ実行時に6時間キャッシュする。リポジトリにはAPIレスポンスを保存しない。

### 3.3 認証情報

e-Stat APIのアプリケーションIDは、次のファイルに設定する。

```text
.streamlit/secrets.toml
```

```toml
ESTAT_APP_ID = "your-app-id"
```

認証情報はGitにコミットしない。

### 3.4 基準改定への対応

現在の実装は2020年基準の統計表IDと分類コードに固定されている。

CPIの基準を変更する場合は、次をまとめて検証する。

- 統計表ID
- 品目分類コード
- 地域コード
- 利用可能な対象期間
- 指数の基準年
- 既存分析との時系列接続
- 実質賃金指数の基準年
- テストの期待値

分析結果の再現性を保つため、基準改定は通常のデータ更新と分けて実施する。

---

## 4. 毎月勤労統計調査

### 4.1 出典

- 統計：毎月勤労統計調査（全国調査）
- 公表元：厚生労働省
- 使用表：長期時系列表
- 取得方法：CSVを手動取得
- 保存先：`data/raw/hon-maikin-k-jissu.csv`
- 文字コード：CP932

### 4.2 使用する主な項目

- 現金給与総額
- きまって支給する給与
- 所定内給与
- 所定外給与
- 特別給与
- 総実労働時間
- 所定内労働時間
- 所定外労働時間
- 出勤日数
- 本月末労働者数
- 前月末労働者数

これらを産業、就業形態、事業所規模の条件で抽出する。

### 4.3 主な条件コード

| 分類       | 表示名             | コード |
| ---------- | ------------------ | ------ |
| 就業形態   | 就業形態計         | `0`    |
| 就業形態   | 一般労働者         | `1`    |
| 就業形態   | パートタイム労働者 | `2`    |
| 事業所規模 | 5人以上            | `T`    |
| 事業所規模 | 30人以上           | `0`    |
| 産業       | 調査産業計         | `TL`   |

産業別分析では、調査産業計以外の産業コードも使用する。

データの読み込みと条件抽出は`src/real_wage_dashboard/wage_service.py`で処理する。

### 4.4 事業所規模別分析での利用

`docs/analysis/10_establishment_size_wage.md` では、この同じ長期時系列CSVから、

```text
5人以上
30人以上
```

の2系列を抽出して比較する。

主な対象：

- きまって支給する給与
- 総実労働時間
- 就業形態計
- 一般労働者
- パートタイム労働者

5人以上系列は30人以上事業所を含むため、両系列は独立した二群ではない。

したがって、

```text
5～29人事業所
vs
30人以上事業所
```

の直接比較とは扱わない。

分析処理は`src/real_wage_dashboard/establishment_size_wage_analysis.py`で行う。

確認には、

```bash
uv run python scripts/wage/check_establishment_size_wage.py
```

を使用する。

### 4.5 更新時の注意点

毎月勤労統計では、訂正や時系列データの更新によって過去値が変更される場合がある。

ファイル更新時は次を確認する。

1. 公表元から最新の長期時系列CSVを取得する。
2. ファイル名を`hon-maikin-k-jissu.csv`に統一する。
3. 文字コードがCP932で読み込めることを確認する。
4. 必須列が維持されていることを確認する。
5. 年月、産業、就業形態、事業所規模の重複を確認する。
6. 主要条件の対象期間と件数を更新前後で比較する。
7. 5人以上・30人以上の主要系列の12か月完全性を確認する。
8. 全自動テストとデータ確認スクリプトを実行する。
9. 分析結果が変化した場合は個別分析文書と概要文書を更新する。

---

## 5. 一般職業紹介状況

### 5.1 出典

- 統計：一般職業紹介状況（職業安定業務統計）
- 公表元：厚生労働省
- 取得方法：長期時系列Excelを手動取得

### 5.2 使用ファイル

| 指標         | 保存先                                                    | 使用シート                 | 使用系列         |
| ------------ | --------------------------------------------------------- | -------------------------- | ---------------- |
| 有効求人倍率 | `data/raw/labor_market/effective_job_openings_ratio.xlsx` | `第３表ー１（パート含む）` | 季節調整値・月次 |
| 新規求人倍率 | `data/raw/labor_market/new_job_openings_ratio.xlsx`       | `第２表ー１（パート含む）` | 季節調整値・月次 |

読み込みと整形は`src/real_wage_dashboard/labor_market_service.py`で処理する。

公表ファイルのシート名や列配置が変更された場合は、読み込み処理とテストも更新する。

---

## 6. 労働力調査

### 6.1 出典

- 統計：労働力調査
- 公表元：総務省統計局
- 取得方法：Excelを手動取得
- 保存先：`data/raw/labor_market/unemployment_rate.xlsx`
- 使用シート：`季節調整値`
- 使用系列：完全失業率・全国・月次

読み込みと整形は`src/real_wage_dashboard/labor_market_service.py`で処理する。

労働力調査の季節調整値は過去に遡って改定される可能性があるため、更新時は分析期間全体を再検証する。

---

## 7. 全国企業短期経済観測調査

### 7.1 出典

- 統計：全国企業短期経済観測調査（短観）
- 公表元：日本銀行
- 取得方法：CSVを手動取得
- 保存先：`data/raw/labor_market/tankan_employment_di.csv`
- 文字コード：CP932
- 頻度：四半期

### 7.2 使用系列

全国・全産業の雇用人員判断DIについて、次の企業規模を使用する。

- 大企業
- 中堅企業
- 中小企業

公表値は「過剰－不足」であるため、分析時に符号を反転し、値が大きいほど人手不足感が強い方向へ統一する。

短観には調査対象や集計区分の変更による時系列上の段差があるため、長期比較では日本銀行の注釈を確認する。

---

## 8. 法人企業統計調査

### 8.1 出典

- 統計：法人企業統計調査
- 公表元：財務省
- 取得元：e-Stat
- 使用表：年次別調査
- 統計表ID：`0003060791`
- 取得方法：e-Stat API
- 頻度：年度
- リポジトリへのAPIレスポンス保存：行わない

企業業績・生産性・付加価値・人件費・労働分配率と賃金の関係を分析するために使用する。

API通信は`src/real_wage_dashboard/estat_client.py`、法人企業統計固有の取得・整形・派生指標計算は`src/real_wage_dashboard/corporate_performance_service.py`で処理する。

### 8.2 主な使用項目

| 分析用列                  | 内容                      | `cat01` |
| ------------------------- | ------------------------- | ------- |
| `sales`                   | 売上高                    | `045`   |
| `operating_profit`        | 営業利益                  | `048`   |
| `ordinary_profit`         | 経常利益                  | `051`   |
| `executive_salary`        | 役員給与                  | `065`   |
| `executive_bonus`         | 役員賞与                  | `057`   |
| `employee_salary`         | 従業員給与                | `066`   |
| `employee_bonus`          | 従業員賞与                | `235`   |
| `welfare_expenses`        | 福利厚生費                | `067`   |
| `average_employees`       | 期中平均従業員数          | `072`   |
| `value_added`             | 付加価値額                | `073`   |
| `operating_profit_margin` | 売上高営業利益率          | `126`   |
| `ordinary_profit_margin`  | 売上高経常利益率          | `127`   |
| `value_added_ratio`       | 付加価値率                | `140`   |
| `labor_productivity`      | 従業員1人当たり付加価値額 | `141`   |

### 8.3 派生指標

#### 人件費

```text
人件費 = 役員給与 + 役員賞与 + 従業員給与 + 従業員賞与 + 福利厚生費
```

分析用列：`personnel_expenses`

#### 労働分配率

```text
労働分配率 = 人件費 ÷ 付加価値額 × 100
```

分析用列：`labor_share`

#### 1人当たり人件費

```text
1人当たり人件費 = 人件費 ÷ 期中平均従業員数 × 100
```

分析用列：`personnel_expenses_per_employee`

#### 労働生産性の再計算値

```text
労働生産性 = 付加価値額 ÷ 期中平均従業員数 × 100
```

分析では、公表されている`labor_productivity`と再計算値を比較し、単位・計算条件の整合性を確認する。

### 8.4 産業条件

主分析では、

```text
全産業（金融業・保険業を除く）
```

を使用する。

産業コードは`cat02`で指定する。

産業別比較では、毎月勤労統計との対応可能性を考慮して対象産業を限定する。

統計間で産業分類や対象範囲が完全には一致しないため、産業別結果は完全に同一母集団の比較とは扱わない。

### 8.5 企業規模条件

企業規模は`cat03`で指定する。

| 区分                      | コード |
| ------------------------- | ------ |
| 全規模                    | `26`   |
| 資本金10億円以上          | `25`   |
| 資本金1億円以上10億円未満 | `24`   |
| 資本金1億円未満           | `22`   |

法人企業統計の企業規模区分は資本金基準である。

毎月勤労統計の「事業所規模5人以上・30人以上」とは定義が異なるため、両者を同一の規模区分として直接対応させない。

### 8.6 分析期間

構造比較：

```text
2015年度 ～ 2024年度
```

長期時系列：

```text
2000年度 ～ 2024年度
```

ただし、`employee_bonus`は2000～2006年度で欠損している。

そのため、

- 労働生産性
- 営業利益率
- 経常利益率
- 付加価値率

などは2000～2024年度を利用できる一方、

- 人件費
- 1人当たり人件費
- 労働分配率

は原則として2007年度以降を使用する。

欠損値を0として補完したり、過去値を推計して埋めたりはしない。

### 8.7 毎月勤労統計との接続

法人企業統計は年度データであるため、毎月勤労統計との時系列比較では、月次データを4月から翌年3月までの年度単位へ集計する。

```text
2024年度 = 2024年4月 ～ 2025年3月
```

月額賃金は年度平均を使用する。

概算時間当たり賃金は、

```text
年度内の月額賃金合計 ÷ 年度内の総実労働時間合計
```

で算出する。

年度内の12か月が揃っていない年度は時系列分析から除外する。

### 8.8 API取得条件と更新時の注意

データ更新時は次を確認する。

1. 統計表IDが継続して利用可能か。
2. `cat01`、`cat02`、`cat03`の分類コードに変更がないか。
3. 最新年度が取得できるか。
4. 年度が連続して取得できるか。
5. 主要項目の欠損状況に変化がないか。
6. `employee_bonus`の利用可能期間に変更がないか。
7. 公表労働生産性と再計算値の差が許容範囲内か。
8. 主要指標が既存分析と整合するか。
9. 自動テストと確認スクリプトを実行する。
10. 結果が変化した場合は`07_corporate_performance.md`と`00_overview.md`を更新する。

---

## 9. 賃金引上げ等の実態に関する調査

### 9.1 出典

- 統計：賃金引上げ等の実態に関する調査
- 公表元：厚生労働省
- 取得方法：公表Excelを手動取得
- 主分析期間：2015年～2025年
- 保存先：`data/raw/wage_revision/`

企業が実際にどの程度賃金を改定したか、また賃金改定時に何を重視したかを分析するために使用する。

読み込み・整形は`src/real_wage_dashboard/wage_revision_service.py`、分析処理は`src/real_wage_dashboard/wage_revision_analysis.py`で行う。

### 9.2 使用ファイル

| ファイル                         | 主な内容                                 |
| -------------------------------- | ---------------------------------------- |
| `wage_revision_amount_rate.xlsx` | 1人平均賃金改定額・改定率                |
| `wage_revision_status.xlsx`      | 賃金引上げ・引下げ・改定なし等の実施状況 |
| `wage_revision_factors.xlsx`     | 賃金改定時に重視した要素                 |

### 9.3 主な使用系列

- 1人平均賃金改定額
- 1人平均賃金改定率
- 賃金を引き上げた企業割合
- 賃金改定時に最も重視した要素
- 企業規模別の改定率・回答割合

### 9.4 比較上の注意

年によって、

- 設問文
- 回答区分
- 企業規模区分
- 表の列配置

が変更される場合がある。

特に、2024年以前と2025年では「引下げ」と「変更なし」の扱いが異なる。

そのため、長期比較では「賃金を引き上げた企業割合」を主な実施状況指標として使用し、「引下げ」「変更なし」を単純連結しない。

### 9.5 更新時の確認

公表ファイルを更新した場合は、

```bash
uv run python scripts/wage_revision/check_wage_revision_excel_structure.py
uv run python scripts/wage_revision/check_wage_revision_amount_rate.py
uv run python scripts/wage_revision/check_wage_revision_status.py
uv run python scripts/wage_revision/check_wage_revision_factors.py
uv run python scripts/wage_revision/check_wage_revision_analysis.py
```

を実行する。

加えて、

```bash
uv run pytest tests/test_wage_revision_service.py
uv run pytest tests/test_wage_revision_analysis.py
```

を実行する。

結果が変化した場合は、

- `docs/analysis/08_wage_revision.md`
- `docs/analysis/00_overview.md`

を更新する。

---

## 10. 実質賃金要因分解用データ

### 10.1 出典

- 統計：毎月勤労統計調査
- 公表元：厚生労働省
- 取得方法：公表Excelを手動取得
- 保存先：`data/raw/real_wage_decomposition/`
- 主分析期間：2015年～2025年

実質賃金の長期変化を、名目賃金要因と物価要因へ分解するために使用する。

### 10.2 使用ファイル

| ファイル                             | 主な内容                                      |
| ------------------------------------ | --------------------------------------------- |
| `wage_index_total_5plus.xls`         | 5人以上・就業形態計の名目賃金指数または増減率 |
| `official_real_wage_index_5plus.xls` | 厚生労働省公表の公式実質賃金指数・増減率      |

分析処理は`src/real_wage_dashboard/real_wage_decomposition_analysis.py`で行う。

### 10.3 CPIとの接続

実質賃金要因分解では、名目賃金と物価の関係を確認するためCPI系列を併用する。

主分析で使用するCPI系列は個別分析文書で明示する。

アプリ内の実質賃金ページで用いるCPI実質化と、長期要因分解用の再構築系列は目的が異なる。

### 10.4 公表前年比の連鎖

長期累積変化では、各年の公表前年比を連鎖して分析用指数を構築する。

これは、

- 長期累積変化
- 名目賃金とCPIの差
- 機械的な実質賃金変化

を比較するための分析用系列である。

元の年平均実額から直接計算した変化率とは計算経路が異なるため、両者を同一の指標として扱わない。

### 10.5 公式系列との整合確認

再構築した実質系列は、厚生労働省の公式実質賃金系列と比較する。

確認対象：

- 年次変化の符号
- 累積変化
- 使用するCPI系列
- 基準化方法
- 丸めの影響

確認には、

```bash
uv run python scripts/cpi/check_real_wage_decomposition_index.py
```

を使用する。

自動テスト：

```bash
uv run pytest tests/test_real_wage_decomposition_analysis.py
```

結果が変化した場合は、

- `docs/analysis/09_real_wage_decomposition.md`
- `docs/analysis/00_overview.md`

を更新する。

---

## 11. データ更新後の確認

入力データを更新した場合は、最低限次を実行する。

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

毎月勤労統計・CPI：

```bash
uv run python scripts/wage/check_wage_csv.py
uv run python scripts/wage/check_wage_data.py
uv run python scripts/wage/check_wage_v2_combinations.py
uv run python scripts/wage/check_wage_v2_conditions.py
uv run python scripts/wage/check_working_hours_conditions.py
uv run python scripts/cpi/check_cpi_data.py
uv run python scripts/cpi/check_real_wage_data.py
uv run python scripts/wage/check_establishment_size_wage.py
uv run python scripts/cpi/check_real_wage_decomposition_index.py
```

労働需給：

```bash
uv run pytest tests/test_labor_market_service.py
uv run pytest tests/test_labor_market_analysis.py
```

法人企業統計：

```bash
uv run pytest tests/test_corporate_performance_service.py
uv run pytest tests/test_corporate_performance_analysis.py
```

必要に応じて、

```bash
uv run python scripts/corporate/check_corporate_stats_metadata.py
uv run python scripts/corporate/check_corporate_performance_data.py
uv run python scripts/corporate/check_corporate_performance_comparison.py
uv run python scripts/corporate/check_corporate_performance_by_capital_class.py
uv run python scripts/corporate/check_corporate_performance_by_industry.py
uv run python scripts/corporate/check_corporate_wage_industry_relationship.py
uv run python scripts/corporate/check_corporate_wage_time_series.py
uv run python scripts/corporate/check_corporate_long_term_availability.py
```

を実行する。

賃金改定調査：

```bash
uv run python scripts/wage_revision/check_wage_revision_excel_structure.py
uv run python scripts/wage_revision/check_wage_revision_amount_rate.py
uv run python scripts/wage_revision/check_wage_revision_status.py
uv run python scripts/wage_revision/check_wage_revision_factors.py
uv run python scripts/wage_revision/check_wage_revision_analysis.py
```

---

## 12. 更新記録の方針

データファイルを更新するコミットでは、次の情報をコミットメッセージまたは関連文書に残す。

- 更新した統計
- 公表元
- データの最終年月・年度
- 過去値の改定有無
- 分析結果への影響
- 実行した検証

公表値の訂正によって分析結果が変わった場合は、過去の結果を黙って上書きせず、変更理由を記録する。
