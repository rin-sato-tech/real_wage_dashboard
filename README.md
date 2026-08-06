# Real Wage Dashboard

e-Stat APIから消費者物価指数を取得し、Streamlitで可視化・分析するダッシュボードです。将来的には名目賃金・実質賃金の分析ページを追加します。

## 現在の機能

- 全国・総合の消費者物価指数をAPIから取得
- 最新指数、前月比、前年同月比を表示
- 表示期間を選択して時系列グラフを表示
- 取得データの一覧表示
- 全期間データのCSV出力
- APIデータの再取得

前月比と前年同月比は、取得した指数からアプリ内で計算しています。

## 使用技術

- Python 3.12
- Streamlit
- pandas
- requests
- uv
- Ruff
- pytest

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

## データ出典

政府統計の総合窓口 e-Stat
消費者物価指数（全国・総合、2020年基準）
