import json
import os
import urllib.request
from bs4 import BeautifulSoup

CISCE_URL = "https://cisce.org"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
MEMORY_FILE = "seen.json"

def get_website_links():
    request = urllib.request.Request(
        CISCE_URL,
        headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}
    )
    html = urllib.request.urlopen(request, timeout=20).read().decode("utf-8", errors="ignore")
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
