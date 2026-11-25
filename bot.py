import json
import os
import urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CISCE_URL = "https://cisce.org"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
MEMORY_FILE = "seen.json"

def get_website_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        resp = page.goto(CISCE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        if resp and resp.status >= 400:
            browser.close()
            raise RuntimeError(f"Blocked by cisce.org with HTTP {resp.status}")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    found_updates = {}
    keywords = ["icse", "isc", "circular", "notice", "result", "timetable", "date sheet", "syllabus", ".pdf"]

    for tag in soup.find_all("a", href=True):
        title = " ".join(tag.get_text().split())
        link = tag["href"].strip()
        combined = (title + " " + link).lower()
        if len(title) > 6 and any(word in combined for word in keywords):
            if not link.startswith("http"):
                link = f"{CISCE_URL.rstrip('/')}/{link.lstrip('/')}"
            found_updates[link] = title

    return found_updates

def send_to_discord(title, link):
    data = {
        "username": "CISCE Official Alerts",
        "embeds": [{
            "title": title[:250],
            "url": link,
            "description": "New circular or update posted on cisce.org",
            "color": 3447003
        }]
    }
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    urllib.request.urlopen(req, timeout=15)

def main():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            seen_links = set(json.load(f))
    else:
        seen_links = set()

    is_first_run = (len(seen_links) == 0)
    current_updates = get_website_links()

    for link, title in current_updates.items():
        if link not in seen_links:
            seen_links.add(link)
            if not is_first_run:
                send_to_discord(title, link)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen_links)), f, indent=2)

if __name__ == "__main__":
    main()

