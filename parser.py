def get_lex_news():
    urls = [
        "https://lex.uz/search/unique",              # дефолт (часто узб.)
        "https://lex.uz/ru/search/unique",           # русский — самый надёжный для твоего сайта
        "https://lex.uz/search/official?lang=3",     # официальные, узб.
        "https://lex.uz/uz/search/unique"            # узб. латиница
    ]
    
    headers = {'User-Agent': random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    ])}
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            
            if table:
                # ... (весь твой текущий код обработки таблицы остаётся без изменений)
                # просто вставь сюда блок с news_list, today_count, organs и т.д.
                # как в твоей последней версии
                
                # Если нашёл таблицу и новости — выходим из цикла
                if news_list:
                    print(f"Успех с URL: {url}")
                    # сохранение json
                    with open('news.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    return
        except Exception as e:
            print(f"Пропуск {url}: {e}")
    
    print("Все URL не сработали")
