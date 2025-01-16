import os
import requests
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

BASE_URL = "https://www.concordiahanoi.org/"
DOMAIN = "www.concordiahanoi.org"

# Where we'll store discovered downloadable links
LINKS_OUTPUT_FILE = "downloadable_links.txt"

# Where we'll store all text from the crawled pages
WEBSITE_TEXT_FILE = "website_text.txt"

# Clear or create the output file
with open(LINKS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("")

with open(WEBSITE_TEXT_FILE, 'w', encoding='utf-8') as f:
    f.write("")

visited_pages = set()  # Set of HTML pages we've crawled
collected_urls = set()  # Set of downloadable URLs we've already recorded

# File extensions we consider "downloadable"
DOWNLOADABLE_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip",
    ".rar", ".7z", ".csv", ".txt"  # Add more as needed
}

# Partial matches for Google-related links (drive, docs, spreadsheets, etc.)
GOOGLE_DOMAINS = [
    "drive.google.com",
    "docs.google.com",
    "slides.google.com",
    "spreadsheets.google.com",
    "calendar.google.com",
    "forms.gle"  # some shortened forms
]

PROTECTED_URLS = [
    "https://www.concordiahanoi.org/student/hs/news",
    "https://www.concordiahanoi.org/es-counseling",
    "https://www.concordiahanoi.org/faculty",
    "https://www.concordiahanoi.org/parent/dashboard"
]


def is_same_domain(url):
    """
    Return True if 'url' is either relative or within the specified DOMAIN.
    """
    parsed = urlparse(url)
    if not parsed.netloc or parsed.netloc.lower() == DOMAIN.lower():
        return True
    return False


def is_google_link(url):
    """
    Return True if URL points to Google Drive/Docs/Sheets, etc.
    """
    parsed = urlparse(url)
    # Check if any known google domain is inside the netloc or path
    netloc = parsed.netloc.lower()
    path = parsed.path.lower()
    for gd in GOOGLE_DOMAINS:
        if gd in netloc or gd in path:
            return True
    return False


def has_downloadable_extension(url):
    """
    Return True if the URL ends with any of the known file extensions
    from DOWNLOADABLE_EXTENSIONS (case-insensitive).
    """
    parsed = urlparse(url)
    # Extract the path part (e.g. /files/document.pdf) to see if it ends with .pdf, etc.
    path = parsed.path.lower()
    for ext in DOWNLOADABLE_EXTENSIONS:
        if path.endswith(ext):
            return True
    return False


def record_downloadable_link(url):
    """
    Write this URL to 'downloadable_links.txt' if not already recorded.
    """
    if url not in collected_urls:
        collected_urls.add(url)
        with open(LINKS_OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(url + "\n")
        print(f"[Found Downloadable] {url}")


def crawl_website(start_url):
    """
    BFS-based crawler.
    1. Only follows HTML pages on the same domain.
    2. For each link found, if it's google or has a known extension -> record it.
    3. Otherwise, if it's same-domain HTML, queue it for further crawling.
    """
    queue = deque([start_url])

    while queue:
        current_url = queue.popleft()

        # Skip if visited
        if current_url in visited_pages:
            continue

        # Only proceed if it's on the same domain
        if not is_same_domain(current_url):
            # But if it's a google link or file link, record it before skipping
            if is_google_link(current_url) or has_downloadable_extension(current_url):
                record_downloadable_link(current_url)
            continue

        try:
            print(f"[Crawling] {current_url}")
            response = requests.get(current_url, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()

            # If this is an HTML page, parse it
            if "text/html" in content_type:
                visited_pages.add(current_url)

                soup = BeautifulSoup(response.text, "html.parser")

                page_text = soup.get_text(strip=True)
                with open(WEBSITE_TEXT_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"\nURL: {current_url}\n")
                    f.write(page_text)
                    f.write("\n" + ("-" * 80) + "\n")

                # Extract <a href=...> links
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag['href'].strip()
                    full_url = urljoin(current_url, href)

                    # If it's Google or a known file type, record it
                    if is_google_link(full_url) or has_downloadable_extension(full_url):
                        record_downloadable_link(full_url)
                    # Otherwise, if it's same-domain HTML, queue it
                    elif is_same_domain(full_url):
                        if full_url not in visited_pages:
                            queue.append(full_url)
            else:
                # Not an HTML content => treat as downloadable
                record_downloadable_link(current_url)

        except Exception as e:
            print(f"[Error] {current_url}: {e}")


if __name__ == "__main__":
    crawl_website(BASE_URL)
