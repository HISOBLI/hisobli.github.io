import json
import random
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re

SOURCES = {
    "lex": "https://lex.uz/ru/search/unique",
    "norma": "https://www.norma.uz/novoe_v_zakonodatelstve",
    "bss": "https://www.bss.uz/article",
    "bakiroo": "https://t.me/s/the_bakiroo"
}

MAX_PER_SOURCE = {"lex": 12, "norma": 12, "bss": 12, "bakiroo": 15}  # больше, чтобы захватить неделю

def parse_date(date_str):
    if not date_str:
        return datetime.now()
    date_str = re.sub(r'\s+', ' ', date_str.strip())
    formats = ["%d.%m.%Y", "%d %B %Y", "%d %B %Y йилдаги", "%Y.%m.%d", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            pass
    month_map = {"января":1, "февраля":2, "марта":3, "апреля":4, "мая":5, "июня":6,
                 "июля":7, "августа":8, "сентября":9, "октября":10, "ноября":11, "декабря":12,
                 "mart":3, "yanvar":1, "fevral":2, "aprel":4}
    for ru, m in month_map.items():
        if ru in date_str.lower():
            parts = re.findall(r'\d+', date_str)
            if len(parts) >= 2:
                day = int(parts[0])
                year = int(parts[-1])
                return datetime(year, m, day)
    return datetime.now()

def parse_lex():
    try:
        r = requests.get(SOURCES["lex"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for tr in soup.select("table tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 2: continue
            date_td = tds[0].get_text(strip=True)
            a = tds[1].find("a")
            if not a: continue
            title = a.get_text(strip=True)
            dt = parse_date(date_td)
            if dt < datetime.now() - timedelta(days=14): continue  # только за 2 недели
            date_out = dt.strftime("%d.%m.%Y")
            link = "https://lex.uz" + a["href"] if a["href"].startswith("/") else a["href"]
            items.append({"source": "lex", "title": title[:140], "date": date_out, "link": link})
        print(f"Lex: {len(items)} items | Пример: {items[0] if items else 'пусто'}")
        return items
    except Exception as e:
        print(f"Lex error: {e}")
        return []

def parse_norma():
    try:
        r = requests.get(SOURCES["norma"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for h3 in soup.find_all("h3"):
            a = h3.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            # дата часто сразу после h3 в тексте
            next_text = h3.next_sibling
            date_str = ""
            if next_text and isinstance(next_text, str):
                date_str = next_text.strip()[:10]
            dt = parse_date(date_str or h3.get_text(strip=True))
            if dt < datetime.now() - timedelta(days=14): continue
            date_out = dt.strftime("%d.%m.%Y")
            href = a["href"]
            link = "https://www.norma.uz" + href if href.startswith("/") else href
            items.append({"source": "norma", "title": title[:140], "date": date_out, "link": link})
        print(f"Norma: {len(items)} items | Пример: {items[0] if items else 'пусто'}")
        return items
    except Exception as e:
        print(f"Norma error: {e}")
        return []

def parse_bss():
    try:
        r = requests.get(SOURCES["bss"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for h2 in soup.find_all(["h2", "h3"]):
            a = h2.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            date_str = ""
            next_sib = h2.next_sibling
            if next_sib and isinstance(next_sib, str):
                date_str = next_sib.strip()
            dt = parse_date(date_str)
            if dt < datetime.now() - timedelta(days=14): continue
            date_out = dt.strftime("%d.%m.%Y")
            href = a["href"]
            link = "https://www.bss.uz" + href if href.startswith("/") else href
            items.append({"source": "bss", "title": title[:140], "date": date_out, "link": link})
        print(f"BSS: {len(items)} items | Пример: {items[0] if items else 'пусто'}")
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
print("Всего raw items:", len(all_items))
print("Selected sources:", [i["source"] for i in selected])
