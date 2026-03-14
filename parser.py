import requests
from bs4 import BeautifulSoup
import json
import random
import time

def get_lex_news():
    urls = [
        "https://lex.uz/search/unique",
        "https://lex.uz/ru/search/unique",
        "https://lex.uz/uz/search/unique",
        "https://lex.uz/search/official?lang=3"
    ]
    headers = {'User-Agent': random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    ])}
    
    for url in urls:
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=12)
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                
                news_list = []
                today_count = 0
                organs = {}
                
                if table:
                    for tr in table.find_all('tr')[:10]:
                        tds = tr.find_all('td')
                        if len(tds) >= 2:
                            a = tds[1].find('a', href=True)
                            if a and '/docs/' in a['href']:
                                title = a.get_text(strip=True)
                                link = "https://lex.uz" + a['href']
                                full = tds[1].get_text(separator=" | ", strip=True)
                                
                                date = ""
                                organ = ""
                                if 'йилда' in full or '2026' in full:
                                    parts = full.split(',')
                                    organ = parts[0].strip()
                                    date = parts[-1].strip()[:12] + " й."
                                
                                news_list.append({"title": title, "link": link, "date": date, "organ": organ})
                                
                                if "2026" in date and "03." in date:
                                    today_count += 1
                                if organ:
                                    organs[organ] = organs.get(organ, 0) + 1
                
                if news_list:
                    top_organ = max(organs, key=organs.get) if organs else "—"
                    data = {
                        "news": news_list,
                        "today_count": today_count,
                        "top_organ": top_organ,
                        "total": "55 903"
                    }
                    with open('news.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"✅ Готово! Сегодня: {today_count} | Топ-орган: {top_organ}")
                    return
                
            except Exception as e:
                print(f"Попытка {attempt+1} на {url}: {e}")
                time.sleep(2)
    
    print("❌ Не удалось получить данные")

if __name__ == "__main__":
    get_lex_news()
