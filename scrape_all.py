import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

SOURCES = {
    "lex": "https://lex.uz/ru/search/unique",
    "norma": "https://www.norma.uz/novoe_v_zakonodatelstve",
    "bss": "https://www.bss.uz/article",
    "bakiroo": "https://t.me/s/the_bakiroo"
}

MAX_PER_SOURCE = {"lex": 5, "norma": 5, "bss": 5, "bakiroo": 10}

def parse_date(date_str):
    if not date_str:
        return datetime.now()
    date_str = re.sub(r'\s+', ' ', date_str.strip())
    formats = ["%d.%m.%Y", "%Y.%m.%d", "%Y-%m-%d", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            pass
    # Текстовая дата
    month_map = {"января":1, "февраля":2, "марта":3, "апреля":4, "мая":5, "июня":6,
                 "июля":7, "августа":8, "сентября":9, "октября":10, "ноября":11, "декабря":12}
    for ru, m in month_map.items():
        if ru in date_str.lower():
            parts = re.findall(r'\d+', date_str)
            if len(parts) >= 2:
                day, year = int(parts[0]), int(parts[-1])
                return datetime(year, m, day)
    return datetime.now()

def parse_lex():
    try:
        r = requests.get(SOURCES["lex"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for tr in soup.select("table tr")[1:MAX_PER_SOURCE["lex"]+1]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            a = tds[1].find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            date_str = tds[0].get_text(strip=True)
            dt = parse_date(date_str)
            date_out = dt.strftime("%d.%m.%Y")
            link = "https://lex.uz" + a["href"] if a["href"].startswith("/") else a["href"]
            items.append({"source": "lex", "title": title[:140], "date": date_out, "link": link})
        print(f"Lex: {len(items)} items")
        return items
    except Exception as e:
        print(f"Lex error: {e}")
        return []

def parse_norma():
    try:
        r = requests.get(SOURCES["norma"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for block in soup.select("div.article, div.news-block, .item")[:MAX_PER_SOURCE["norma"]]:
            a = block.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            date_el = block.find("span.date, .date, time")
            date_str = date_el.get_text(strip=True) if date_el else ""
            dt = parse_date(date_str)
            date_out = dt.strftime("%d.%m.%Y")
            href = a["href"]
            link = "https://www.norma.uz" + href if href.startswith("/") else href
            items.append({"source": "norma", "title": title[:140], "date": date_out, "link": link})
        print(f"Norma: {len(items)} items")
        return items
    except Exception as e:
        print(f"Norma error: {e}")
        return []

def parse_bss():
    try:
        r = requests.get(SOURCES["bss"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for art in soup.select("div.article, article, .post-item, li.article")[:MAX_PER_SOURCE["bss"]]:
            a = art.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            date_str = ""
            date_el = art.find("span.date, .date, time, small")
            if date_el:
                date_str = date_el.get_text(strip=True)
            dt = parse_date(date_str)
            date_out = dt.strftime("%d.%m.%Y")
            href = a["href"]
            link = "https://www.bss.uz" + href if href.startswith("/") else href
            items.append({"source": "bss", "title": title[:140], "date": date_out, "link": link})
        print(f"BSS: {len(items)} items")
        return items
    except Exception as e:
        print(f"BSS error: {e}")
        return []

def parse_bakiroo():
    try:
        r = requests.get(SOURCES["bakiroo"], timeout=12)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for msg in soup.find_all("div", class_="tgme_widget_message")[:MAX_PER_SOURCE["bakiroo"]]:
            time_tag = msg.find("time")
            if time_tag and "datetime" in time_tag.attrs:
                dt_str = time_tag["datetime"][:10]
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                date_out = dt.strftime("%d.%m.%Y")
            else:
                date_out = datetime.now().strftime("%d.%m.%Y")
            text_div = msg.find("div", class_="tgme_widget_message_text")
            if not text_div:
                continue
            text = text_div.get_text(separator="\n", strip=True)
            lines = text.split("\n")
            title = lines[0] if lines else "Без заголовка"
            link_a = msg.find("a", href=re.compile(r"/the_bakiroo/\d+"))
            link = link_a["href"] if link_a else "#"
            items.append({"source": "bakiroo", "title": title[:140], "date": date_out, "link": link})
        return items
    except Exception as e:
        print("Ошибка bakiroo:", str(e))
        return []

def assign_marker(item):
    t = item["title"].lower()
    s = item["source"]
    if s == "lex" and any(w in t for w in ["закон", "қонун", "qonun", "президент", "prezident"]):
        return "§"
    if s in ["norma", "bss"] and any(w in t for w in ["бухгалтер", "buxgalter", "налог", "soliq"]):
        return "%"
    if s == "bakiroo":
        if any(w in t for w in ["олигарх", "шотир", "ўғри", "валломат", "президент"]) or random.random() < 0.35:
            return "!!!"
    return None

all_items = parse_lex() + parse_norma() + parse_bss() + parse_bakiroo()

random.shuffle(all_items)
selected = []
for src in ["lex", "norma", "bss"]:
    src_items = [i for i in all_items if i["source"] == src]
    if src_items:
        selected.append(random.choice(src_items))

bak_items = [i for i in all_items if i["source"] == "bakiroo"]
selected.extend(random.sample(bak_items, min(2, len(bak_items))))

for i in selected:
    i["marker"] = assign_marker(i)

dates = []
for i in selected:
    try:
        dates.append(datetime.strptime(i["date"], "%d.%m.%Y"))
    except:
        pass

if dates:
    min_dt = min(dates)
    max_dt = max(dates)
    ru_months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    start_ru = f"{min_dt.day}–{max_dt.day} {ru_months[min_dt.month-1]} {min_dt.year}"
    uz_months = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
    start_uz = f"{min_dt.day}–{max_dt.day} {uz_months[min_dt.month-1]} {min_dt.year}"
else:
    start_ru = start_uz = "10–16 марта 2026"

news_data = {
    "period_ru": start_ru,
    "period_uz": start_uz,
    "items": selected
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print(f"Готово: {len(selected)} записей, период {start_ru}")
