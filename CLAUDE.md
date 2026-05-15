# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 環境セットアップ

```powershell
# 仮想環境の有効化（PowerShell）
.venv\Scripts\Activate.ps1

# ライブラリのインストール
.venv\Scripts\python.exe -m pip install requests beautifulsoup4

# スクレイピングの実行
.venv\Scripts\python.exe scrape_books.py
```

## スクリプト構成

`scrape_books.py` は単一ファイルのスクレイパーで、以下の関数に分かれている：

- `load_robots()` — robots.txt を取得・解析し、`RobotFileParser` を返す
- `can_fetch()` — `USER_AGENT` でアクセス可否を判定
- `get()` — `requests.Session` でHTTP GETし、エンコーディングを `utf-8` に固定して返す
- `parse_books()` — `article.product_pod` を選択し、タイトル・価格・在庫状況を抽出
- `next_page_url()` — `li.next > a` から次ページURLを組み立てる（相対パスを `urljoin` で解決）
- `scrape()` — robots.txt チェック → GET → parse → 待機のループで全ページを巡回
- `save_markdown()` — 収集結果を Markdownテーブル形式で `books_YYYYMMDD.md` に保存

## 動作仕様

- **対象サイト**: https://books.toscrape.com/（全50ページ・1,000冊）
- **待機時間**: ページ間に `random.uniform(1, 3)` 秒
- **エラー処理**: `ConnectionError` / `HTTPError` / `Timeout` をそれぞれキャッチしてログ出力後 `SystemExit(1)`
- **出力**: `books_YYYYMMDD.md`（UTF-8、Markdownテーブル）

## 注意点

- `requests` はレスポンスのエンコーディングを Latin-1 と誤判定することがある。`get()` 内で `response.encoding = "utf-8"` を明示的に設定しているため、変更時は維持すること。
- `next_page_url()` はトップページ（`catalogue/` を含まないURL）と内部ページで相対パスの基準が異なる。`urljoin` + `rsplit` による解決方法はこの差異を吸収している。
