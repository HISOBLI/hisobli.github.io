import json
import random
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

MAX_PER_SOURCE = 10


# ===================== DATE =====================
def parse_date(text):
    if not text:
        return None

    text = re.sub(r'\s+', ' ', text.strip()).lower()

    months = {
        "января":1,"февраля":2,"марта":3,"апреля":4,"мая":5,
        "июня":6,"июля":7,"августа":8,"сентября":9,
        "октября":10,"ноября":11,"декабря":12
    }

    nums = re.findall(r'\d+', text)

    for m_name, m_num in months.items():
        if m_name in text and len(nums) >= 2:
            try:
                return datetime(int(nums[-1]), m_num, int(nums[0]))
            except:
                pass

    try:
        return datetime.strptime(text[:10], "%d.%m.%Y")
    except:
        return None


# ===================== DEDUP =====================
def deduplicate(items):
    seen = set()
    result = []

    for item in items:
        key = re.sub(r'[^a-zа-я0-9 ]', '', item["title"].lower())[:70]

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


# ===================== SCORE =====================
def score(item):
    t = item["title"].lower()
    s = 0

    if any(w in t for w in ["закон","қонун","qonun"]): s += 5
    if any(w in t for w in ["президент","prezident"]): s += 4
    if any(w in t for w in ["налог","soliq","бухгалтер","buxgalter"]): s += 3
    if any(w in t for w in ["указ","постановление"]): s += 2

    return s


# ===================== LEX =====================
def parse_lex():
    items = []

    for page in range(1, 4):
        try:
            url = f"https://lex.uz/ru/search/unique?page={page}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                if "/docs/" not in a["href"]:
                    continue

                title = a.get_text(strip=True)
                if len(title) < 20:
                    continue

                link = "https://lex.uz" + a["href"]

                items.append({
                    "source": "lex",
                    "title": title[:140],
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "link": link
                })

        except Exception as e:
            print("Lex page error:", e)

    print(f"Lex total: {len(items)}")
    return items[:MAX_PER_SOURCE]


# ===================== NORMA =====================
def parse_norma():
    items = []

    for page in range(1, 4):
        try:
            url = f"https://www.norma.uz/novoe_v_zakonodatelstve?page={page}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]

                if "/novoe_v_zakonodatelstve/" not in href:
                    continue

                title = a.get_text(strip=True)
                if len(title) < 20:
                    continue

                # пытаемся найти дату рядом
                parent_text = a.parent.get_text(" ", strip=True)
                dt = parse_date(parent_text)

                if not dt:
                    dt = datetime.now()

                if dt < datetime.now() - timedelta(days=14):
                    continue

                link = "https://www.norma.uz" + href

                items.append({
                    "source": "norma",
                    "title": title[:140],
                    "date": dt.strftime("%d.%m.%Y"),
                    "link": link
                })

        except Exception as e:
            print("Norma page error:", e)

    print(f"Norma total: {len(items)}")
    return items[:MAX_PER_SOURCE]


# ===================== BSS =====================
def parse_bss():
    items = []

    for page in range(1, 4):
        try:
            url = f"https://www.bss.uz/article/?PAGEN_1={page}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]

                if "/article/" not in href:
                    continue

                title = a.get_text(strip=True)
                if len(title) < 20:
                    continue

                dt = datetime.now()

                link = "https://www.bss.uz" + href if href.startswith("/") else href

                items.append({
                    "source": "bss",
                    "title": title[:140],
                    "date": dt.strftime("%d.%m.%Y"),
                    "link": link
                })

        except Exception as e:
            print("BSS page error:", e)

    print(f"BSS total: {len(items)}")
    return items[:MAX_PER_SOURCE]


# ===================== BAKIROO =====================
def parse_bakiroo():
    try:
        r = requests.get("https://t.me/s/the_bakiroo", timeout=12)
        soup = BeautifulSoup(r.text, "lxml")

        items = []

        for msg in soup.find_all("div", class_="tgme_widget_message")[:20]:
            text_div = msg.find("div", class_="tgme_widget_message_text")
            if not text_div:
                continue

            title = text_div.get_text("\n", strip=True).split("\n")[0]

            time_tag = msg.find("time")
            if time_tag and time_tag.has_attr("datetime"):
                dt = datetime.strptime(time_tag["datetime"][:10], "%Y-%m-%d")
            else:
                dt = datetime.now()

            link_a = msg.find("a", href=re.compile(r"/the_bakiroo/\d+"))
            link = link_a["href"] if link_a else "#"

            items.append({
                "source": "bakiroo",
                "title": title[:140],
                "date": dt.strftime("%d.%m.%Y"),
                "link": link
            })

        print(f"Bakiroo: {len(items)}")
        return items

    except Exception as e:
        print("Bakiroo error:", e)
        return []


# ===================== MAIN =====================
all_items = (
    parse_lex()
    + parse_norma()
    + parse_bss()
    + parse_bakiroo()
)

all_items = deduplicate(all_items)
all_items.sort(key=score, reverse=True)

selected = []

for src in ["lex", "norma", "bss"]:
    src_items = [i for i in all_items if i["source"] == src]
    selected.extend(src_items[:5])

bak_items = [i for i in all_items if i["source"] == "bakiroo"]
if bak_items:
    selected.extend(random.sample(bak_items, min(5, len(bak_items))))

news_data = {
    "period": datetime.now().strftime("%d.%m.%Y"),
    "items": selected
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print(f"✅ DONE: {len(selected)} items")
