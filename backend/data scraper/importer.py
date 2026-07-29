import requests
from bs4 import BeautifulSoup
import csv

URL = "https://rebjorn-wiki.com/dqmj2/monsters?lang=en"

resp = requests.get(URL)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

table = soup.find("table")
rows = table.find_all("tr")

# --- STEP 1: Read header row and build column index map ---
header_cells = rows[0].find_all("th")
header_map = {}

for idx, th in enumerate(header_cells):
    name = th.get_text(strip=True).lower()

    if "id" in name:
        header_map["id"] = idx
    elif "english" in name:
        header_map["english"] = idx
    elif "japanese" in name:
        header_map["japanese"] = idx
    elif "french" in name:
        header_map["french"] = idx
    elif "family" in name:
        header_map["family"] = idx
    elif "rank" in name:
        header_map["rank"] = idx

# --- STEP 2: Scrape rows using header map ---
with open("dqmj2_monsters.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["monster_id", "name_en", "family", "rank", "size", "name_jp"])

    for tr in rows[1:]:
        tds = tr.find_all("td")
        if len(tds) < len(header_map):
            continue

        monster_id    = tds[header_map["id"]].get_text(strip=True)
        english_name  = tds[header_map["english"]].get_text(strip=True)
        japanese_name = tds[header_map["japanese"]].get_text(strip=True)
        family        = tds[header_map["family"]].get_text(strip=True)
        rank          = tds[header_map["rank"]].get_text(strip=True)

        size = "S"  # auto-populated default

        writer.writerow([
            monster_id,
            english_name,
            family,
            rank,
            size,
            japanese_name
        ])
