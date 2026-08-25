# 確認スクリプト運用ガイド

## 1. この文書の目的

`scripts/`に配置している確認スクリプトの用途、実行条件、pytestとの違い、継続して残す理由を整理する。

これらは、実データまたは実際のe-Stat APIを使って状態を確認するための補助ツールである。

---

## 2. pytestとの違い

| 項目 | `scripts/` | `tests/` |
| ---- | ---------- | -------- |
| 主な目的 | 実データ・実APIの状態確認 | 処理仕様の自動検証 |
| 入力 | 現在の入力ファイル、e-Stat API | テスト用データ、モック |
| 判定 | 出力を人が確認 | assertによる自動判定 |
| 再現性 | 外部データやAPI状態に依存 | 原則として一定 |
| CIでの利用 | 原則として使用しない | 使用可能 |
| 失敗時の終了コード | 必ずしも非ゼロにならない | テスト失敗として非ゼロになる |

確認スクリプトの成功だけで、自動テスト通過とみなさない。

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

---

## 4. スクリプト一覧

| スクリプト | 分類 | 確認内容 | API認証 | 方針 |
| ---------- | ---- | -------- | -------- | ---- |
| `check_estat_api.py` | API診断 | API接続、統計表情報、分類コード | 必要 | 残す |
| `check_cpi_data.py` | API・データ確認 | CPI取得件数、期間、重複、変換結果 | 必要 | 残す |
| `check_real_wage_data.py` | 結合スモークテスト | CPI・賃金結合、実質化、基準年指数 | 必要 | 残す |
| `check_wage_csv.py` | 生データ確認 | CSV形状、列名、型、先頭行 | 不要 | 残す |
| `check_wage_data.py` | 基本系列確認 | 標準条件の抽出、期間、欠損、重複 | 不要 | 残す |
| `check_wage_v2_conditions.py` | コード体系確認 | 賃金項目、規模、就業形態、期間、欠損月 | 不要 | 残す |
| `check_wage_v2_combinations.py` | 対応条件確認 | v2対象12条件の件数、期間、2020年、欠損月 | 不要 | 残す |
| `check_working_hours_conditions.py` | 労働時間確認 | 労働時間3項目の規模・雇用形態別完全性 | 不要 | 残す |

---

## 5. 各スクリプトの役割

### 5.1 `check_estat_api.py`

実行：

```bash
uv run python scripts/check_estat_api.py
```

確認内容：

- e-Stat APIへ接続できるか
- CPI統計表IDが有効か
- 統計表名と表題
- 分類ID、分類名、分類コード

API認証、統計表ID、分類コードを変更した場合の初期診断に使用する。

単体テストでは実APIへ接続しないため、継続して残す。

---

### 5.2 `check_cpi_data.py`

実行：

```bash
uv run python scripts/check_cpi_data.py
```

確認内容：

- APIレスポンスの取得件数
- DataFrame変換後の件数
- 先頭・末尾データ
- データ型
- 年月の重複
- 対象期間

CPI統計表ID、系列コード、APIレスポンス構造を変更した場合に使用する。

---

### 5.3 `check_real_wage_data.py`

実行：

```bash
uv run python scripts/check_real_wage_data.py
```

確認内容：

- CPI件数
- 名目賃金件数
- 結合後件数
- 結合後の対象期間
- 欠損値と重複年月
- 2020年の名目・実質賃金指数平均

実APIのCPIと実際の賃金CSVを結合するため、実質賃金処理の実データスモークテストとして残す。

---

### 5.4 `check_wage_csv.py`

実行：

```bash
uv run python scripts/check_wage_csv.py
```

確認内容：

- CSVの行数・列数
- 全列名
- pandasで読み込んだデータ型
- 先頭データ

毎月勤労統計CSVの様式変更、列名変更、文字コード問題の初期確認に使用する。

---

### 5.5 `check_wage_data.py`

実行：

```bash
uv run python scripts/check_wage_data.py
```

確認内容：

- CSV全体と標準条件抽出後の件数
- 先頭・末尾データ
- データ型
- 欠損値
- 重複年月
- 対象期間

標準条件で賃金サービスと変化率計算を通した結果を確認する。

---

### 5.6 `check_wage_v2_conditions.py`

実行：

```bash
uv run python scripts/check_wage_v2_conditions.py
```

確認内容：

- 対象賃金項目の存在
- 就業形態コードの全体像
- 事業所規模コードの全体像
- 調査産業計に存在する条件
- 条件別の対象期間
- 2020年のデータ件数
- 月次系列の連続性

元CSVにどのコードと条件が存在するかを調査するために使用する。

`check_wage_v2_combinations.py`より対象範囲が広く、データ構造の探索に使用するため残す。

---

### 5.7 `check_wage_v2_combinations.py`

実行：

```bash
uv run python scripts/check_wage_v2_combinations.py
```

確認対象：

```text
賃金項目2系列
× 事業所規模2区分
× 就業形態3区分
= 12条件
```

各条件について次を表示する。

- 有効な月数
- 開始年月と終了年月
- 2020年の月数
- 欠損月数

アプリが正式に対応する12条件をまとめて確認するために残す。

---

### 5.8 `check_working_hours_conditions.py`

実行：

```bash
uv run python scripts/check_working_hours_conditions.py
```

確認対象：

- 総実労働時間
- 所定内労働時間
- 所定外労働時間
- 一般労働者
- パートタイム労働者
- 5人以上
- 30人以上

各条件について件数、期間、欠損月、2020年の月数を確認する。

雇用形態比較や労働投入分析で使用する労働時間系列の実データ確認として残す。

---

## 6. 推奨する実行順序

### 6.1 新しい環境でAPI接続を確認する場合

```bash
uv run python scripts/check_estat_api.py
uv run python scripts/check_cpi_data.py
uv run python scripts/check_real_wage_data.py
```

### 6.2 毎月勤労統計CSVを更新した場合

```bash
uv run python scripts/check_wage_csv.py
uv run python scripts/check_wage_v2_conditions.py
uv run python scripts/check_wage_v2_combinations.py
uv run python scripts/check_wage_data.py
uv run python scripts/check_working_hours_conditions.py
```

### 6.3 CPI設定または実質賃金処理を変更した場合

```bash
uv run python scripts/check_estat_api.py
uv run python scripts/check_cpi_data.py
uv run python scripts/check_real_wage_data.py
```

確認スクリプトの後に自動テストを実行する。

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

---

## 7. 現在の棚卸し結果

現時点では、8本すべてを残す。

理由：

- 実データの様式や対象期間を確認できる。
- e-Stat APIの実接続を確認できる。
- pytestとは入力と目的が異なる。
- データ更新時の調査手順として利用できる。
- スクリプト数が少なく、現状では細分化による利点が小さい。

現時点では`api/`、`wage/`等のサブディレクトリへ分割しない。

---

## 8. 今後の見直し基準

次の場合は、スクリプトの統合、削除、自動テスト化を検討する。

- 同じ出力を行うスクリプトが増えた場合
- 目視確認では見落としやすい判定が増えた場合
- データ更新を自動化する場合
- CIで定期的に確認する必要が生じた場合
- 対応する処理やデータが削除された場合
- 長期間使用されず、用途も説明できない場合

機械的に合否判定できる処理は、確認スクリプトではなくpytestへ移す。

---

## 9. 更新ルール

次の場合は本書を更新する。

- スクリプトを追加、削除、改名した場合
- 実行条件や必要な認証情報が変わった場合
- 確認対象となる統計や条件が変わった場合
- スクリプトをpytestへ移行した場合
