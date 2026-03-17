import json
import random
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

SOURCES = {
    "lex":   "https://lex.uz/ru/search/unique",
    "norma": "https://www.norma.uz/novoe_v_zakonodatelstve",
    "bss":   "https://www.bss.uz/article",
    "bakiroo": "https://t.me/s/the_bakiroo"
}

MAX_PER_SOURCE = 5   # сколько максимум берём с каждого источника сырыми

# ===================== ПАРСЕР ДАТ =====================
def parse_date(text):
    if not text:
        return None
    text = re.sub(r'\s+', ' ', text.strip()).lower()
    months = {
        "января":1, "февраля":2, "марта":3, "апреля":4, "мая":5, "июня":6,
        "июля":7, "августа":8, "сентября":9, "октября":10, "ноября":11, "декабря":12
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

# ===================== ДЕДУПЛИКАЦИЯ =====================
def deduplicate(items):
    seen = set()
    result = []
    for item in items:
        key = item["title"].lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result

# ===================== СКОРИНГ =====================
def score(item):
    t = item["title"].lower()
    s = 0
    if "закон" in t or "қонун" in t or "qonun" in t: s += 5
    if "президент" in t or "prezident" in t: s += 4
    if "налог" in t or "soliq" in t or "бухгалтер" in t or "buxgalter" in t: s += 3
    if "указ" in t or "постановление" in t: s += 2
    return s

# ===================== ПАРСЕРЫ =====================
def parse_lex():
    try:
        r = requests.get(SOURCES["lex"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for tr in soup.select("table tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 2: continue
            a = tds[1].find("a")
            if not a: continue
            title = a.get_text(strip=True)
            date_str = tds[0].get_text(strip=True)
            dt = parse_date(date_str)
            if not dt or dt < datetime.now() - timedelta(days=14): continue
            link = "https://lex.uz" + a["href"] if a["href"].startswith("/") else a["href"]
            items.append({"source": "lex", "title": title[:140], "date": dt.strftime("%d.%m.%Y"), "link": link})
        print(f"Lex: {len(items)}")
        return items[:MAX_PER_SOURCE]
    except Exception as e:
        print(f"Lex error: {e}")
        return []

def parse_norma():
    try:
        r = requests.get(SOURCES["norma"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for h3 in soup.find_all("h3"):
            a = h3.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            text = h3.parent.get_text(" ", strip=True)
            dt = parse_date(text)
            if not dt or dt < datetime.now() - timedelta(days=14): continue
            href = a["href"]
            link = "https://www.norma.uz" + href if href.startswith("/") else href
            items.append({"source": "norma", "title": title[:140], "date": dt.strftime("%d.%m.%Y"), "link": link})
        print(f"Norma: {len(items)}")
        return items[:MAX_PER_SOURCE]
    except Exception as e:
        print(f"Norma error: {e}")
        return []

def parse_bss():
    try:
        r = requests.get(SOURCES["bss"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for tag in soup.find_all(["h2", "h3"]):
            a = tag.find("a")
            if not a: continue
            title = a.get_text(strip=True)
            text = tag.parent.get_text(" ", strip=True)
            dt = parse_date(text)
            if not dt or dt < datetime.now() - timedelta(days=14): continue
            href = a["href"]
            link = "https://www.bss.uz" + href if href.startswith("/") else href
            items.append({"source": "bss", "title": title[:140], "date": dt.strftime("%d.%m.%Y"), "link": link})
        print(f"BSS: {len(items)}")
        return items[:MAX_PER_SOURCE]
    except Exception as e:
        print(f"BSS error: {e}")
        return []

def parse_bakiroo():
    try:
        r = requests.get(SOURCES["bakiroo"], timeout=12)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for msg in soup.find_all("div", class_="tgme_widget_message")[:15]:
            text_div = msg.find("div", class_="tgme_widget_message_text")
            if not text_div: continue
            text = text_div.get_text("\n", strip=True)
            title = text.split("\n")[0]
            link_a = msg.find("a", href=re.compile(r"/the_bakiroo/\d+"))
            link = link_a["href"] if link_a else "#"
            date_out = datetime.now().strftime("%d.%m.%Y")  # bakiroo даты надёжны, но можно улучшить позже
            items.append({"source": "bakiroo", "title": title[:140], "date": date_out, "link": link})
        print(f"Bakiroo: {len(items)}")
        return items
    except Exception as e:
        print(f"Bakiroo error: {e}")
        return []

# ===================== МАРКЕРЫ =====================
def assign_marker(item):
    t = item["title"].lower()
    s = item["source"]
    if s == "lex" and any(w in t for w in ["закон", "қонун", "qonun", "президент", "prezident"]):
        return "§"
    if s in ["norma", "bss"] and any(w in t for w in ["бухгалтер", "buxgalter", "налог", "soliq"]):
        return "%"
    if s == "bakiroo" and (any(w in t for w in ["олигарх", "шотир", "ўғри", "валломат", "президент"]) or random.random() < 0.35):
        return "!!!"
    return None

# ===================== ОСНОВНОЙ БЛОК =====================
all_items = parse_lex() + parse_norma() + parse_bss() + parse_bakiroo()

all_items = deduplicate(all_items)          # убираем дубли
all_items.sort(key=score, reverse=True)     # умный приоритет

selected = []
for src in ["lex", "norma", "bss"]:
    src_items = [i for i in all_items if i["source"] == src]
    selected.extend(src_items[:4])          # по 4 с каждого

bak_items = [i for i in all_items if i["source"] == "bakiroo"]
selected.extend(random.sample(bak_items, min(4, len(bak_items))))  # 4 из телеграма

for i in selected:
    i["marker"] = assign_marker(i)

# Период (реальный диапазон)
dates = [datetime.strptime(i["date"], "%d.%m.%Y") for i in selected if "." in i["date"]]
if dates:
    min_d = min(dates)
    max_d = max(dates)
    ru_months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
    period_ru = f"{min_d.day}–{max_d.day} {ru_months[min_d.month-1]} {min_d.year}"
    period_uz = f"{min_d.day}–{max_d.day} {['yanvar','fevral','mart','aprel','may','iyun','iyul','avgust','sentabr','oktabr','noyabr','dekabr'][min_d.month-1]} {min_d.year}"
else:
    period_ru = period_uz = "13–17 марта 2026"

news_data = {
    "period_ru": period_ru,
    "period_uz": period_uz,
    "items": selected
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print(f"✅ ГОТОВО: {len(selected)} записей | Период: {period_ru}")
