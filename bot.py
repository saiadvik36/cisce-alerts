import json
import os
import urllib.request
import xml.etree.ElementTree as ET

RSS_URL = "https://news.google.com/rss/search?q=CISCE+ICSE+ISC+(circular+OR+notice+OR+timetable+OR+result+OR+datesheet)&hl=en-IN&gl=IN&ceid=IN:en"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
MEMORY_FILE = "seen.json"

def get_updates():
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    xml_data = urllib.request.urlopen(req, timeout=20).read()
    root = ET.fromstring(xml_data)

    found = {}
    for item in root.findall(".//item")[:20]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title and link:
            found[link] = title
    return found

def send_to_discord(title, link):
    data = {
        "username": "CISCE Alerts",
        "embeds": [{
            "title": title[:250],
            "url": link,
            "description": "New CISCE / ICSE / ISC update detected.",
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
    current_updates = get_updates()

    for link, title in current_updates.items():
        if link not in seen_links:
            seen_links.add(link)
            if not is_first_run:
                send_to_discord(title, link)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen_links)), f, indent=2)

if __name__ == "__main__":
    main()

