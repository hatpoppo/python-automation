import logging
import random
import time
from datetime import date
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
USER_AGENT = "Mozilla/5.0 (compatible; BookScraper/1.0)"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def load_robots(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        rp.set_url(robots_url)
        rp.read()
        log.info("robots.txt を読み込みました: %s", robots_url)
    except Exception as e:
        log.warning("robots.txt の読み込みに失敗しました (%s)。全パスを許可として続行します。", e)
    return rp


def can_fetch(rp: RobotFileParser, url: str) -> bool:
    return rp.can_fetch(USER_AGENT, url)


def get(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response


def parse_books(soup: BeautifulSoup) -> list[dict]:
    books = []
    for article in soup.select("article.product_pod"):
        title = article.select_one("h3 > a")["title"]
        price = article.select_one("p.price_color").get_text(strip=True)
        stock_el = article.select_one("p.availability")
        stock = stock_el.get_text(strip=True) if stock_el else "Unknown"
        books.append({"title": title, "price": price, "stock": stock})
    return books


def next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    next_btn = soup.select_one("li.next > a")
    if not next_btn:
        return None
    # current_url のディレクトリを基準に相対パスを解決
    base = current_url.rsplit("/", 1)[0] + "/"
    return urljoin(base, next_btn["href"])


def scrape(base_url: str) -> list[dict]:
    rp = load_robots(base_url)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    all_books: list[dict] = []
    url: str | None = base_url
    page = 1

    while url:
        if not can_fetch(rp, url):
            log.warning("robots.txt により %s へのアクセスは禁止されています。スキップします。", url)
            break

        log.info("ページ %d を取得中: %s", page, url)
        try:
            resp = get(session, url)
        except requests.ConnectionError as e:
            log.error("接続エラーが発生しました: %s", e)
            raise SystemExit(1) from e
        except requests.HTTPError as e:
            log.error("HTTPエラーが発生しました: %s", e)
            raise SystemExit(1) from e
        except requests.Timeout as e:
            log.error("タイムアウトが発生しました: %s", e)
            raise SystemExit(1) from e

        soup = BeautifulSoup(resp.text, "html.parser")
        books = parse_books(soup)
        all_books.extend(books)
        log.info("  → %d 件取得 (累計 %d 件)", len(books), len(all_books))

        url = next_page_url(soup, url)
        page += 1

        if url:
            wait = random.uniform(1, 3)
            log.info("  → %.1f 秒待機します", wait)
            time.sleep(wait)

    return all_books


def save_markdown(books: list[dict], path: str) -> None:
    today = date.today().strftime("%Y-%m-%d")
    lines = [
        f"# Books Scraping Result — {today}",
        "",
        f"収集件数: **{len(books)} 件**  |  出典: <{BASE_URL}>",
        "",
        "| # | タイトル | 価格 | 在庫状況 |",
        "|---|---------|------|---------|",
    ]
    for i, book in enumerate(books, 1):
        title = book["title"].replace("|", "\\|")
        lines.append(f"| {i} | {title} | {book['price']} | {book['stock']} |")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log.info("結果を保存しました: %s", path)


def main() -> None:
    log.info("スクレイピングを開始します: %s", BASE_URL)
    books = scrape(BASE_URL)

    if not books:
        log.warning("書籍データが取得できませんでした。")
        return

    filename = f"books_{date.today().strftime('%Y%m%d')}.md"
    save_markdown(books, filename)
    log.info("完了。合計 %d 件の書籍を収集しました。", len(books))


if __name__ == "__main__":
    main()
