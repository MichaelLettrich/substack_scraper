#!/usr/bin/env python3

"""
Substack scraper to download articles from a Substack newsletter.
Supports both free and paid content (with manual login).

Usage:
    python substack_scraper.py <newsletter_url> [-s <sitemap_path>] [-p]
    [-o <output_folder>] [-d <delay_seconds>] [-h]
Options:
    <newsletter_url>: Base URL of the Substack newsletter.
    -s, --sitemap: Sitemap path of the Substack newsletter (default: sitemap.xml).
    -p, --paid: Enable scraping paid content (requires manual login).
    -o, --output: Output folder for saving articles (default: current directory).
    -d, --delay: Delay between requests in seconds (default: 0.3).
    -h, --help: Show help message and exit.

Output:
    Articles are saved in both HTML and Markdown formats in separate folders.
"""

from time import sleep
import argparse
import json
import shutil
from pathlib import Path
import enum

import requests
from bs4 import BeautifulSoup
import markdownify
from selenium import webdriver


SITEMAP_STRING = "sitemap.xml"  # Change if your sitemap path is different
OUTPUT_FILE = "articles.json"
TIMEOUT_SECONDS = 10
SLEEP_SECONDS = 0.3


class OutputOption(enum.Enum):
    HTML = "html"
    MD = "md"


def selenium_login():
    driver = webdriver.Chrome()
    driver.get("https://substack.com/sign-in")
    input(
        "After you have logged in and see your account, press Enter here to continue..."
    )
    print("Continuing with scraping...")
    return driver


def get_article_urls_and_lastmod(sitemap_url, timeout):
    resp = requests.get(sitemap_url, timeout=timeout)
    soup = BeautifulSoup(resp.content, "xml")
    url_to_lastmod = {}
    urls = []
    for url_tag in soup.find_all("url"):
        loc = url_tag.find("loc")
        lastmod = url_tag.find("lastmod")
        if loc:
            url_text = loc.text
            urls.append(url_text)
            url_to_lastmod[url_text] = lastmod.text if lastmod else ""
    return urls, url_to_lastmod


def convert_to_md(html_content):
    return markdownify.markdownify(html_content, heading_style="ATX")


def extract_article_html(soup):
    # Prioritize content containers
    return str(soup.find("div", class_="available-content"))


def convert_to(html_content, output_option):
    match output_option:
        case OutputOption.HTML:
            return html_content
        case OutputOption.MD:
            return convert_to_md(html_content)
        case _:
            raise ValueError(f"Unsupported output option: {output_option}")


def scrape_article_selenium(driver, url, delay):
    driver.get(url)
    sleep(delay)
    soup = BeautifulSoup(driver.page_source, "lxml")
    return extract_article_html(soup)


def scrape_article_requests(url, timeout):
    resp = requests.get(url, timeout=timeout)
    soup = BeautifulSoup(resp.content, "lxml")
    return extract_article_html(soup)


def store_sitemap(path, urls):
    with open(path, "w", encoding="utf-8") as url_file:
        url_file.writelines(url + "\n" for url in urls)
    print(f"Saved URLs to {path}")


def make_file_path(url, lastmod, base_dir, output_option):
    date_part = lastmod.split("T")[0] if lastmod else ""
    base_name = url.rstrip("/").split("/")[-1]
    if date_part:
        base_name = f"{date_part}_{base_name}"

    ext = output_option.value
    return base_dir / (base_name + f".{ext}")


def main():
    parser = argparse.ArgumentParser(description="Substack scraper")
    parser.add_argument(
        "url",
        type=str,
        help="Base URL of the Substack newsletter",
    )
    parser.add_argument(
        "-s",
        "--sitemap",
        type=str,
        default=SITEMAP_STRING,
        help="Sitemap path of the Substack newsletter",
    )
    parser.add_argument(
        "-p",
        "--paid",
        action="store_true",
        help="Enable scraping paid content (manual login required)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="Output folder for saving articles (default: current directory)",
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=SLEEP_SECONDS,
        help=f"Delay between requests in seconds (default: {SLEEP_SECONDS})",
    )

    args = parser.parse_args()

    url = args.url
    url = url.rstrip("/") + "/" + args.sitemap.lstrip("/")

    if args.output != ".":
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

    driver = None
    if args.paid:
        print("Paid mode enabled. Manual login required.")
        driver = selenium_login()
    else:
        print("Scraping free content only.")

    print("Fetching sitemap...")

    urls, url_to_lastmod = get_article_urls_and_lastmod(url, TIMEOUT_SECONDS)
    print(f"Found {len(urls)} articles.")

    store_sitemap(output_dir / "urls.txt", urls)

    for output_option in OutputOption:
        base_dir = output_dir / output_option.value
        shutil.rmtree(base_dir, ignore_errors=True)
        base_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for url in urls:
        print(f"Scraping {url}")

        content = None
        if args.paid:
            content = scrape_article_selenium(driver, url, args.delay)
        else:
            content = scrape_article_requests(url, TIMEOUT_SECONDS)

        if not content:
            print(f"No content found for {url}, skipping.")
            continue
        lastmod = url_to_lastmod.get(url, "")
        for output_option in OutputOption:
            base_dir = output_dir / output_option.value
            path = make_file_path(url, lastmod, base_dir, output_option)
            with open(path, "w", encoding="utf-8") as f:
                f.write(convert_to(content, output_option))

        results.append(
            {
                "url": url,
                "lastmod": lastmod,
            }
        )

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} articles to {summary_path}")
    if driver:
        driver.quit()


if __name__ == "__main__":
    main()
