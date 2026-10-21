import csv
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

START_URL = "https://www.musashino-u.ac.jp/"
target_domain = urlparse(START_URL).netloc

sitemap_dict = {}
visited_urls = set()
urls_to_visit = [START_URL]

# 除外したいファイルの拡張子
IGNORE_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".zip",
    ".doc",
    ".docx",
)

# ★取得件数の上限（例: 50件まで取得したら終了）
MAX_PAGES = 50

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("クローリングを開始します...")

while urls_to_visit and len(sitemap_dict) < MAX_PAGES:
    current_url = urls_to_visit.pop(0).split("#")[0]

    # すでに訪問済み、または空の場合はスキップ
    if not current_url or current_url in visited_urls:
        continue

    # ★PDFなどのファイルURLは除外してスキップ
    if current_url.lower().endswith(IGNORE_EXTENSIONS):
        continue

    visited_urls.add(current_url)

    try:
        # 負荷軽減のための1秒待機
        time.sleep(1)

        print(f"取得中 ({len(sitemap_dict)+1}/{MAX_PAGES}): {current_url}")
        response = requests.get(current_url, headers=headers, timeout=10)

        # HTML以外のコンテンツは除外
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            title_tag = soup.find("title")
            title_text = title_tag.get_text(strip=True) if title_tag else "No Title"

            sitemap_dict[current_url] = title_text

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(current_url, href)
                parsed_url = urlparse(full_url)

                if (
                    parsed_url.netloc == target_domain
                    and parsed_url.scheme in ["http", "https"]
                ):
                    clean_url = full_url.split("#")[0]
                    # ★拡張子チェックを追加
                    if (
                        clean_url not in visited_urls
                        and not clean_url.lower().endswith(IGNORE_EXTENSIONS)
                    ):
                        urls_to_visit.append(clean_url)

    except Exception as e:
        print(f"エラー ({current_url}): {e}")

# CSV保存
csv_filename = "musashino_sitemap.csv"
with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["URL", "Title"])
    for url, title in sitemap_dict.items():
        writer.writerow([url, title])

print(f"完了しました！ {len(sitemap_dict)} 件保存されました。")