import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

# ===================== НАСТРОЙКИ =====================
SOURCES = {
    "lex":   "https://lex.uz/ru/search/unique",
    "norma": "https://www.norma.uz/novoe_v_zakonodatelstve",
    "bss":   "https://www.bss.uz/article",
    "bakiroo": "https://t.me/s/the_bakiroo"
}

MAX_PER_SOURCE = {"lex": 4, "norma": 4, "bss": 4, "bakiroo": 10}

# ===================== УЛУЧШЕННЫЙ ПАРСЕР ДАТ =====================
def parse_date(date_str):
    if not date_str:
        return datetime.now()
    date_str = date_str.strip().replace(" ", "")
    
    # Пробуем разные форматы
    formats = [
        "%d.%m.%Y",          # 16.03.2026
        "%Y.%m.%d",          # 2026.03.16
        "%Y-%m-%d",          # 2026-03-16
        "%d %B %Y",          # 12 марта 2026 (но без перевода пока)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    
    # Если текстовая дата типа "12 марта 2026"
    month_ru = {"января":1, "февраля":2, "марта":3, "апреля":4, "мая":5, "июня":6,
                "июля":7, "августа":8, "сентября":9, "октября":10, "ноября":11, "декабря":12}
    for ru, num in month_ru.items():
        if ru in date_str.lower():
            try:
                day_year = re.sub(r'[а-яА-Я]+', '', date_str.lower()).strip()
                day, year = day_year.split()[:2]
                return datetime(int(year), num, int(day))
            except:
                pass
    
    # fallback
    return datetime.now()

# ===================== ПАРСЕРЫ (обновлённые) =====================
def parse_lex():
    try:
        r = requests.get(SOURCES["lex"], timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for row in soup.select("div.search-result-item")[:MAX_PER_SOURCE["lex"]]:
            a = row.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            date_el = row.find(string=re.compile(r"\d{2}\.\d{2}\.\d{4}"))
            date_str = date_el.strip() if date_el else ""
            dt = parse_date(date_str)
            date_out = dt.strftime("%d.%m.%Y")
            link = "https://lex.uz" + a["href"]
            items.append({"source": "lex", "title": title[:140], "date": date_out, "link": link})
        return items
    except Exception as e:
        print("Ошибка lex:", str(e))
        return []

def parse_norma():
    try:
        r = requests.get(SOURCES["norma"], timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for item in soup.select(".news-item, .article-item")[:MAX_PER_SOURCE["norma"]]:
            a = item.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            date_el = item.find(class_="date") or item.find(string=re.compile(r"\d{2}\.\d{2}\.\d{4}"))
            date_str = date_el.get_text(strip=True) if date_el else ""
            dt = parse_date(date_str)
            date_out = dt.strftime("%d.%m.%Y")
            link = "https://www.norma.uz" + a["href"] if a["href"].startswith("/") else a["href"]
            items.append({"source": "norma", "title": title[:140], "date": date_out, "link": link})
        return items
    except Exception as e:
        print("Ошибка norma:", str(e))
        return []

def parse_bss():
    try:
        r = requests.get(SOURCES["bss"], timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for art in soup.select("article, .article")[:MAX_PER_SOURCE["bss"]]:
            a = art.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            date_str = ""
            date_el = art.find(class_="date") or art.find(string=re.compile(r"\d{1,2}\s*марта|апреля|\d{2}\.\d{2}"))
            if date_el:
                date_str = date_el.get_text(strip=True)
            dt = parse_date(date_str)
            date_out = dt.strftime("%d.%m.%Y")
            link = "https://www.bss.uz" + a["href"] if a["href"].startswith("/") else a["href"]
            items.append({"source": "bss", "title": title[:140], "date": date_out, "link": link})
        return items
    except Exception as e:
        print("Ошибка bss:", str(e))
        return []

def parse_bakiroo():
    try:
        r = requests.get(SOURCES["bakiroo"], timeout=12)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for msg in soup.find_all("div", class_="tgme_widget_message")[:MAX_PER_SOURCE["bakiroo"]]:
            time_tag = msg.find("time")
            if time_tag and "datetime" in time_tag.attrs:
                dt_str = time_tag["datetime"][:10]  # 2026-03-16
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                date_out = dt.strftime("%d.%m.%Y")
            else:
                date_out = datetime.now().strftime("%d.%m.%Y")
            
            text_div = msg.find("div", class_="tgme_widget_message_text")
            if not text_div: continue
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

# ===================== КЛАССИФИКАТОР (без изменений) =====================
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

# ===================== ОСНОВНОЙ БЛОК =====================
all_items = parse_lex() + parse_norma() + parse_bss() + parse_bakiroo()

random.shuffle(all_items)
selected = []
for src in ["lex", "norma", "bss"]:
    src_items = [i for i in all_items if i["source"] == src]
    if src_items:
        selected.append(random.choice(src_items))  # по 1 случайному из каждого

bak_items = [i for i in all_items if i["source"] == "bakiroo"]
selected.extend(random.sample(bak_items, min(2, len(bak_items))))  # 2 из bakiroo

for i in selected:
    i["marker"] = assign_marker(i)

# Период
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
