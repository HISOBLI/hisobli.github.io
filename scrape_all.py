import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

SOURCES = {
    "lex":   "https://lex.uz/ru/search/unique",
    "norma": "https://www.norma.uz/novoe_v_zakonodatelstve",
    "bss":   "https://www.bss.uz/article",
    "bakiroo": "https://t.me/s/the_bakiroo"
}

MAX_PER_SOURCE = {"lex": 5, "norma": 5, "bss": 5, "bakiroo": 10}

def parse_date(date_str):
    if not date_str: return datetime.now()
    date_str = re.sub(r'\s+', ' ', date_str.strip())
    formats = ["%d.%m.%Y", "%Y.%m.%d", "%Y-%m-%d", "%d %B %Y"]
    for fmt in formats:
        try: return datetime.strptime(date_str, fmt)
        except: pass
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
        # Новый селектор: строки таблицы результатов
        for tr in soup.select("table tr")[1:MAX_PER_SOURCE["lex"]+1]:  # пропускаем заголовок
            # В parse_lex, внутри for tr in soup.select("table tr")[1:]:
		tds = tr.find_all("td")
		if len(tds) < 2: continue
		a = tds[1].find("a")
		if not a: continue
		title = a.get_text(strip=True)
		# Дата часто в tds[1] после title или в tds[0]
		full_text = tds[1].get_text(strip=True)
		date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', full_text)
		date_str = date_match.group(0) if date_match else tds[0].get_text(strip=True)
		dt = parse_date(date_str)
		date_out = dt.strftime("%d.%m.%Y")
		link = "https://lex.uz" + a["href"] if a["href"].startswith("/") else a["href"]
        print(f"Lex: {len(items)} items")
        return items
		print(f"{source.upper()} raw items: {len(items)}")
		if items:
		print("Пример первого: ", items[0])
		except Exception as e:
        print(f"Lex error: {e}")
        return []

def parse_norma():
    try:
        r = requests.get(SOURCES["norma"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        text = soup.get_text(separator="\n", strip=True)
        lines = text.splitlines()
        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            if re.match(r'^\d{2}\.\d{2}\.\d{4}$', line):
                date_str = line
                i += 1
                if i >= len(lines): break
                title_line = lines[i].strip()
                if title_line and not title_line.startswith('['):
                    title = title_line
                    i += 1
                    if i < len(lines) and '[Читать подробно]' in lines[i]:
                        href_match = re.search(r'\((/ru/novoe_v_zakonodatelstve/[^)]+)\)', lines[i])
                        href = href_match.group(1) if href_match else ""
                        link = "https://www.norma.uz" + href if href else ""
                        dt = parse_date(date_str)
                        date_out = dt.strftime("%d.%m.%Y")
                        items.append({"source": "norma", "title": title[:140], "date": date_out, "link": link})
            i += 1
        print(f"Norma: {len(items)} items")
        return items
		print(f"{source.upper()} raw items: {len(items)}")
		if items:
		print("Пример первого: ", items[0])
    except Exception as e:
        print(f"Norma error: {e}")
        return []

def parse_bss():
    try:
        r = requests.get(SOURCES["bss"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = []
        for h in soup.find_all(['h2', 'h3']):
            a = h.find('a')
            if not a: continue
            title = a.get_text(strip=True)
            # Дата — следующий sibling или в meta
            date_str = ""
            next_el = h.find_next(['span', 'small', 'time', 'div'])
            if next_el:
                date_str = next_el.get_text(strip=True)
                if not re.search(r'\d', date_str):
                    date_str = h.find_next(string=re.compile(r'\d{1,2}\s*марта|апреля|\d{2}\.\d{2}'))
            dt = parse_date(date_str or "17.03.2026")  # fallback
            date_out = dt.strftime("%d.%m.%Y")
            href = a["href"]
            link = "https://www.bss.uz" + href if href.startswith("/") else href
            items.append({"source": "bss", "title": title[:140], "date": date_out, "link": link})
            if len(items) >= MAX_PER_SOURCE["bss"]: break
        print(f"BSS: {len(items)} items")
        return items
		print(f"{source.upper()} raw items: {len(items)}")
		if items:
		print("Пример первого: ", items[0])
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
                dt_str = time_tag["datetime"][:10]  # 2026-03-16
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                date_out = dt.strftime("%d.%m.%Y")
            else:
                date_out = datetime.now().strftime("%d.%m.%Y")
            
            text = text_div.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            title = lines[0] if lines else "Без заголовка"
            # Если первый line короткий и жирный — берём его
            if len(title) < 20 and '**' in text:  # простой чек
                title = lines[0]
            link_a = msg.find("a", href=re.compile(r"/the_bakiroo/\d+"))
            link = link_a["href"] if link_a else "#"
            
            items.append({"source": "bakiroo", "title": title[:140], "date": date_out, "link": link})
        return items
		print(f"{source.upper()} raw items: {len(items)}")
		if items:
		print("Пример первого: ", items[0])
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
