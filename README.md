# Substack Scraper

Scrape paid or free articles from a Substack newsletter, saving both HTML and Markdown versions.

## Setup

1. Clone the repository and enter the directory:
    ```bash
    git clone https://github.com/gitgithan/substack_scraper.git
    cd substack_scraper
    ```

2. (Recommended) Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Install ChromeDriver and ensure it's in your PATH.


## Usage

Substack scraper to download articles from a Substack newsletter.
Supports both free and paid content (with manual login).

## Usage
```
python substack_scraper.py <newsletter_url> [-s <sitemap_path>] [-p] [-o <output_folder>] [-d <delay_seconds>] [-h]

Options:
    <newsletter_url>: Base URL of the Substack newsletter.
    -s, --sitemap: Sitemap path of the Substack newsletter (default: sitemap.xml).
    -p, --paid: Enable scraping paid content (requires manual login).
    -o, --output: Output folder for saving articles (default: current directory).
    -d, --delay: Delay between requests in seconds (default: 0.3).
    -h, --help: Show help message and exit.

Output:
    Articles are saved in both HTML and Markdown formats in separate folders.

## Output

- HTML files: `html/`
- Markdown files: `md/`
- Article metadata: `articles.json`
- List of URLs: `urls.txt`

