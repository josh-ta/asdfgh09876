from drop_pl import DropPL
from drop_ie import DropIE
from drop_de import DropDE
from drop_ch import DropCH
import json
import os
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from dotenv import load_dotenv
import requests

load_dotenv()


def make_dropchecker(url: str):
    if "ticketmaster.pl" in url:
        return DropPL(url)
    elif "ticketmaster.ie" in url:
        return DropIE(url)
    elif "ticketmaster.de" in url:
        return DropDE(url)
    elif "ticketmaster.ch" in url:
        return DropCH(url)
    else:
        return None

def run_one(url):
    dropchecker = make_dropchecker(url)
    if not dropchecker:
        return f"Unsupported URL: {url}"
    dropchecker.run()
    return {
            "event_id": dropchecker.event_id,
            "url": dropchecker.url,
            "count": dropchecker.count,
            "sections": ",".join(str(s) for s in dropchecker.sections)
        }

def send_discord_webhook(data_dict, event_id):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    
    sections_list = data_dict["sections"].split(",") if data_dict["sections"] else []
    sections_text = "\n".join(f"• {s}" for s in sections_list) if sections_list else "None"
    
    embed = {
        "title": "🎫 Tickets Available!",
        "description": f"Sections available: {data_dict['count']}",
        "color": 3066993,
        "fields": [
            {
                "name": "URL",
                "value": data_dict["url"],
                "inline": False
            },
            {
                "name": "Sections",
                "value": sections_text,
                "inline": False
            }
        ]
    }
    
    payload = {"embeds": [embed]}
    
    screenshot_path = f"Screenshots/{event_id}.png"
    if os.path.isfile(screenshot_path):
        with open(screenshot_path, "rb") as f:
            data = {"payload_json": json.dumps(payload)}
            files = {"file": f}
            requests.post(webhook_url, data=data, files=files)
    else:
        requests.post(webhook_url, json=payload)


def save_to_csv(data_dict):
    csv_file = "results.csv"
    file_exists = os.path.isfile(csv_file)
    fieldnames = ["event_id", "url", "count", "sections"]

    existing_data = []
    if file_exists:
        with open(csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)

    event_id = data_dict["event_id"]
    found = False
    old_count = 0
    
    for row in existing_data:
        if row["event_id"] == event_id:
            old_count = int(row["count"])
            row.update(data_dict)
            found = True
            break
    
    if not found:
        existing_data.append(data_dict)
        if int(data_dict["count"]) > 0:
            send_discord_webhook(data_dict, event_id)
    else:
        if old_count == 0 and int(data_dict["count"]) > 0:
            send_discord_webhook(data_dict, event_id)

    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_data)

if __name__ == "__main__":
    with open("events.json") as f:
        events = json.load(f)["events"]

    with ProcessPoolExecutor(max_workers=min(10, len(events))) as ex:
        futures = [ex.submit(run_one, url) for url in events]
        for fut in as_completed(futures):
            result = fut.result()
            if isinstance(result, dict):
                save_to_csv(result)
                print(f"Done: {result['url']} - Found {result['count']} sections")
            else:
                print(result)