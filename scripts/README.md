# 確認スクリプト運用ガイド

## 1. この文書の目的

`scripts/` に配置している確認スクリプトの用途、実行条件、pytestとの違い、利用場面を整理する。

確認スクリプトは、実データまたは実際のe-Stat APIを使って、

- 入力ファイルの構造
- 公表統計の変更
- API取得結果
- 対象期間・欠損・重複
- 分析結果の妥当性

を目視または簡易出力で確認するための補助ツールである。

分析ロジックの正しさを自動判定する `tests/` とは役割が異なる。

---

## 2. pytestとの違い

| 項目       | `scripts/`                              | `tests/`                         |
| ---------- | --------------------------------------- | -------------------------------- |
| 主な目的   | 実データ・実API・公表ファイルの状態確認 | 処理仕様の自動検証               |
| 入力       | 現在の入力ファイル、実API               | テスト用データ、モック           |
| 判定       | 出力を人が確認する場合がある            | `assert` による自動判定          |
| 再現性     | 外部データ・API状態に依存               | 原則として一定                   |
| CIでの利用 | 原則として使用しない                    | 使用可能                         |
| 終了コード | 必ずしも合否を表さない                  | 失敗時は非ゼロ                   |
| 主な用途   | データ更新・新規分析・統計様式変更時    | 開発・リファクタリング・回帰防止 |

確認スクリプトが正常に実行できても、pytest通過の代替にはならない。

---

## 3. 実行条件

リポジトリのルートディレクトリから実行する。

```bash
uv sync
```

e-Stat APIを使用するスクリプトでは、次のファイルにアプリケーションIDを設定する。

```text
.streamlit/secrets.toml
```

```toml
ESTAT_APP_ID = "your-app-id"
```

認証情報はGitへコミットしない。

個別スクリプトは次の形式で実行する。

```bash
uv run python scripts/<script_name>.py
```

---

## 4. スクリプトの分類

現在の確認スクリプトは、用途別に次のグループへ分ける。

| 分類                   | 主なスクリプト                            | 主な確認対象                               |
| ---------------------- | ----------------------------------------- | ------------------------------------------ |
| e-Stat / CPI           | `check_estat_api.py`、`check_cpi_data.py` | API接続、CPI統計表、系列コード、取得期間   |
| 毎月勤労統計・基本賃金 | `check_wage_*.py`                         | CSV構造、条件コード、対象期間、欠損、重複  |
| 労働時間               | `check_working_hours_conditions.py`       | 労働時間系列の条件別完全性                 |
| 基本実質賃金           | `check_real_wage_data.py`                 | CPIと賃金の結合、実質化、基準年指数        |
| 労働需給               | 労働需給分析で使用する実データ確認        | 求人倍率、失業率、短観と賃金系列           |
| 企業業績・生産性       | `check_corporate_*.py`                    | 法人企業統計、規模別・産業別・時系列・相関 |
| 賃金改定行動           | `check_wage_revision_*.py`                | Excel構造、改定率、実施状況、重視要因      |
| 実質賃金要因分解       | `check_real_wage_decomposition_index.py`  | 名目賃金指数、CPI、公式実質賃金との整合性  |
| 事業所規模別賃金       | `check_establishment_size_wage.py`        | 5人以上・30人以上系列、賃金・労働時間差    |

スクリプト数が増えているため、本書ではすべてを一律に詳細解説するのではなく、分析単位で用途を管理する。

---

## 5. 基礎データ確認

### 5.1 `check_estat_api.py`

e-Stat APIの接続とメタデータを確認する。

主な確認内容：

- APIへ接続できるか
- 統計表IDが有効か
- 統計表名
- 分類ID・分類コード
- API設定変更後の初期診断

CPIや法人企業統計の統計表ID・分類コードを変更した場合に実行する。

---

### 5.2 `check_cpi_data.py`

CPIの実取得結果を確認する。

主な確認内容：

- APIレスポンス件数
- DataFrame変換後の件数
- 対象期間
- 年月重複
- データ型
- 先頭・末尾データ

CPI基準改定や系列コード変更時には必ず再確認する。

---

### 5.3 `check_wage_csv.py`

毎月勤労統計CSVそのものの構造を確認する。

主な確認内容：

- 行数・列数
- 列名
- データ型
- 先頭データ
- 文字コード・読込可否

元CSVを差し替えた直後の初期確認に使用する。

---

### 5.4 `check_wage_data.py`

標準条件で毎月勤労統計を読み込み、基本系列を確認する。

主な確認内容：

- 抽出件数
- 対象期間
- 欠損値
- 重複年月
- 先頭・末尾データ

---

### 5.5 `check_wage_v2_conditions.py`

毎月勤労統計に存在する条件コードを広く確認する。

主な確認内容：

- 賃金項目
- 就業形態コード
- 事業所規模コード
- 産業コード
- 条件別対象期間
- 欠損月
- 2020年のデータ件数

新しい分析条件を追加する前の探索に使用する。

---

### 5.6 `check_wage_v2_combinations.py`

アプリが正式対応する賃金条件の完全性を確認する。

主な確認対象：

```text
賃金項目
× 事業所規模
× 就業形態
```

各条件について、

- 有効月数
- 開始年月
- 終了年月
- 基準年データ
- 欠損月

を確認する。

---

### 5.7 `check_working_hours_conditions.py`

労働時間系列の条件別完全性を確認する。

主な対象：

- 総実労働時間
- 所定内労働時間
- 所定外労働時間
- 一般労働者
- パートタイム労働者
- 5人以上
- 30人以上

雇用形態比較、労働投入、事業所規模別分析の前提確認に使用する。

---

## 6. 実質賃金関連

### 6.1 `check_real_wage_data.py`

アプリ側の実質賃金処理を実データで確認する。

主な確認内容：

- CPI件数
- 名目賃金件数
- 結合後件数
- 対象期間
- 欠損・重複
- 2020年基準指数

これはアプリ内で算出する実質賃金のスモークテストである。

---

### 6.2 `check_real_wage_decomposition_index.py`

`09_real_wage_decomposition.md` の分析で使用する系列を確認する。

主な確認内容：

- 名目賃金指数・増減率
- CPI系列
- 公式実質賃金指数
- 公表前年比から連鎖した系列
- 機械的に再構築した実質系列との整合性
- 2015～2025年の累積変化

アプリの実質賃金処理とは目的が異なるため、`check_real_wage_data.py` と分けて残す。

---

## 7. 企業業績・生産性分析

法人企業統計関連は `check_corporate_*.py` として複数の確認スクリプトに分かれている。

主な確認対象：

- 統計表メタデータ
- 利用可能な年度
- 長期系列の欠損
- 企業規模別比較
- 産業別比較
- 毎月勤労統計との接続
- 長期時系列
- 相関・ラグ相関
- 感応度分析

主なスクリプト例：

- `check_corporate_stats_metadata.py`
- `check_corporate_performance_data.py`
- `check_corporate_long_term_availability.py`
- `check_corporate_performance_comparison.py`
- `check_corporate_performance_by_capital_class.py`
- `check_corporate_performance_by_industry.py`
- `check_corporate_wage_time_series.py`
- `check_corporate_wage_industry_relationship.py`

企業業績分析は複数統計の接続とAPIメタデータに依存するため、単一スクリプトへ無理に統合しない。

---

## 8. 賃金改定行動分析

賃金引上げ等の実態に関する調査の確認スクリプトは `check_wage_revision_*.py` として管理する。

主なスクリプト：

- `check_wage_revision_excel_structure.py`
- `check_wage_revision_amount_rate.py`
- `check_wage_revision_status.py`
- `check_wage_revision_factors.py`
- `check_wage_revision_recent_structure.py`
- `check_wage_revision_analysis.py`

確認内容：

- 公表Excelのシート・列構造
- 1人平均賃金改定額・改定率
- 賃金引上げ実施企業割合
- 賃金改定状況の回答区分
- 賃金改定時に重視した要素
- 年次による設問・回答区分変更
- 企業規模別比較

この統計は年によって回答区分が変更されるため、ファイル構造の確認を残す。

---

## 9. 事業所規模別賃金分析

### `check_establishment_size_wage.py`

`10_establishment_size_wage.md` の分析で使用する5人以上系列と30人以上系列を確認する。

主な確認内容：

- 2015年・2025年の年平均
- 月額賃金
- 概算時間当たり賃金
- 総実労働時間
- 30人以上 / 5人以上の比率
- 規模差の対数分解
- 就業形態別比較

毎月勤労統計の5人以上系列と30人以上系列は包含関係にあるため、独立した二群の比較として解釈しない。

---

## 10. 推奨する実行順序

### 10.1 新しい環境でAPI接続を確認する場合

```bash
uv run python scripts/check_estat_api.py
uv run python scripts/check_cpi_data.py
uv run python scripts/check_real_wage_data.py
```

---

### 10.2 毎月勤労統計CSVを更新した場合

```bash
uv run python scripts/check_wage_csv.py
uv run python scripts/check_wage_v2_conditions.py
uv run python scripts/check_wage_v2_combinations.py
uv run python scripts/check_wage_data.py
uv run python scripts/check_working_hours_conditions.py
uv run python scripts/check_establishment_size_wage.py
```

分析結果の再現性に影響する場合は、

```bash
uv run python scripts/check_real_wage_decomposition_index.py
```

も実行する。

---

### 10.3 CPI設定を変更した場合

```bash
uv run python scripts/check_estat_api.py
uv run python scripts/check_cpi_data.py
uv run python scripts/check_real_wage_data.py
uv run python scripts/check_real_wage_decomposition_index.py
```

---

### 10.4 法人企業統計を更新・変更した場合

まず、

```bash
uv run python scripts/check_corporate_stats_metadata.py
uv run python scripts/check_corporate_performance_data.py
uv run python scripts/check_corporate_long_term_availability.py
```

を実行し、その後、変更内容に応じて `check_corporate_*.py` を実行する。

---

### 10.5 賃金改定調査を更新した場合

まず公表ファイル構造を確認し、

```bash
uv run python scripts/check_wage_revision_excel_structure.py
```

その後、

```bash
uv run python scripts/check_wage_revision_amount_rate.py
uv run python scripts/check_wage_revision_status.py
uv run python scripts/check_wage_revision_factors.py
uv run python scripts/check_wage_revision_analysis.py
```

を実行する。

---

## 11. 確認後に実行する自動テスト

確認スクリプトの後は、原則として次を実行する。

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

分析値の更新だけでコード変更がない場合でも、入力ファイル差し替えによって前提条件が変わっていないか確認する。

---

## 12. スクリプトを残す基準

次のいずれかに該当する確認スクリプトは残す。

- 実APIへ接続する。
- 公表ファイルの実構造を確認する。
- データ更新時に対象期間・欠損・重複を確認する。
- pytestでは代替しにくいメタデータを確認する。
- 個別分析の再現確認に利用する。
- 公表統計の仕様変更を検知する役割がある。

一方、次の場合は統合・削除・pytest化を検討する。

- 同じ入力に対して同じ情報を出力するスクリプトが複数ある。
- 判定条件が完全に機械化できる。
- 対応する分析・機能が削除された。
- 長期間利用されず、用途を説明できない。
- 一時的な調査コードで、再現性確保にも不要である。

---

## 13. ディレクトリ構成の方針

現時点では `scripts/` 直下に配置している。

スクリプト数がさらに増え、

```text
scripts/
├── wage/
├── cpi/
├── corporate/
├── wage_revision/
└── validation/
```

のように分類した方が探索性が高くなった時点でサブディレクトリ化を検討する。

現状では、ファイル名の接頭辞によって分析単位を識別できるため、直下配置を維持する。

---

## 14. 更新ルール

次の場合は本書を更新する。

- スクリプトを追加、削除、改名した場合
- 新しい分析用の確認スクリプトを追加した場合
- 実行条件や必要な認証情報が変わった場合
- 確認対象となる統計・入力ファイルが変わった場合
- スクリプトをpytestへ移行した場合
- サブディレクトリ構成へ変更した場合

個別分析文書、`docs/reference/implementation_map.md`、本書の対応がずれない状態を維持する。
