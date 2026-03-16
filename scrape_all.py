import json
import random
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# ===================== НАСТРОЙКИ =====================
SOURCES = {
    "lex":   "https://lex.uz/ru/search/unique",
    "norma": "https://www.norma.uz/novoe_v_zakonodatelstve",
    "bss":   "https://www.bss.uz/article",
    "bakiroo": "https://t.me/s/the_bakiroo"
}

MAX_PER_SOURCE = {"lex": 3, "norma": 3, "bss": 3, "bakiroo": 8}  # беру с запасом, потом отберём

# ===================== ПАРСЕРЫ =====================
def parse_lex():
    r = requests.get(SOURCES["lex"], timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.find_all("a", href=lambda h: h and "/docs/" in h)[:MAX_PER_SOURCE["lex"]]:
        title = a.get_text(strip=True)
        # дата рядом в тексте
        date_str = " ".join([t for t in a.parent.get_text().split() if "." in t and len(t)>8][:1]) or datetime.now().strftime("%d.%m.%Y")
        link = "https://lex.uz" + a["href"]
        items.append({"source": "lex", "title": title[:140], "date": date_str, "link": link})
    return items

def parse_norma():
    r = requests.get(SOURCES["norma"], timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for h3 in soup.select("h3")[:MAX_PER_SOURCE["norma"]]:
        title = h3.get_text(strip=True)
        p = h3.find_next("p")
        date = p.get_text(strip=True)[:10] if p else datetime.now().strftime("%d.%m.%Y")
        a = h3.find_next("a")
        link = "https://www.norma.uz" + a["href"] if a else "#"
        items.append({"source": "norma", "title": title[:140], "date": date, "link": link})
    return items

def parse_bss():
    r = requests.get(SOURCES["bss"], timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.find_all("a", href=lambda h: h and "/article/" in h)[:MAX_PER_SOURCE["bss"]]:
        title = a.get_text(strip=True)
        # дата обычно сразу после
        date_text = a.find_next_sibling(string=lambda t: t and "марта" in t or "." in t)
        date = date_text.strip()[:12] if date_text else datetime.now().strftime("%d.%m.%Y")
        link = "https://www.bss.uz" + a["href"]
        items.append({"source": "bss", "title": title[:140], "date": date, "link": link})
    return items

def parse_bakiroo():
    r = requests.get(SOURCES["bakiroo"], timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for msg in soup.find_all("div", class_="tgme_widget_message")[:MAX_PER_SOURCE["bakiroo"]]:
        time_tag = msg.find("time")
        date = time_tag["datetime"][:10].replace("-", ".") if time_tag else datetime.now().strftime("%d.%m.%Y")
        text = msg.get_text(strip=True)
        title = text.split("\n")[0][:140]  # первая строка — заголовок
        link = "https://t.me/the_bakiroo/" + msg.find("a", href=lambda h: "/the_bakiroo/" in h)["href"].split("/")[-1] if msg.find("a") else "#"
        items.append({"source": "bakiroo", "title": title, "date": date, "link": link})
    return items

# ===================== КЛАССИФИКАТОР МАРКЕРОВ =====================
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

# ===================== ОСНОВНОЙ СКРИПТ =====================
all_items = parse_lex() + parse_norma() + parse_bss() + parse_bakiroo()

# Перемешиваем и отбираем нужное соотношение
random.shuffle(all_items)
selected = []
for src in ["lex", "norma", "bss"]:
    selected.extend([i for i in all_items if i["source"] == src][:1])
selected.extend([i for i in all_items if i["source"] == "bakiroo"][:2])  # ровно 2 из bakiroo

# Добавляем маркеры + период
for i in selected:
    i["marker"] = assign_marker(i)

# Период (берём мин-макс дату из отобранных)
dates = [datetime.strptime(i["date"], "%d.%m.%Y") for i in selected if "." in i["date"]]
start = min(dates).strftime("%d–%m марта %Y") if dates else "10–16 марта 2026"
end_uz = min(dates).strftime("%d–%m mart %Y") if dates else "10–16 mart 2026"

news_data = {
    "period_ru": start,
    "period_uz": end_uz,
    "items": selected
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print(f"✅ Готово: {len(selected)} записей, период {start}")
