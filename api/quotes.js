export default async function handler(req, res) {
  try {
    const response = await fetch('https://uzex.uz/Quote/GetQuotes', {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://uzex.uz/',
        'Origin': 'https://uzex.uz',
        'Cache-Control': 'no-cache'
      },
      redirect: 'follow'
    });

    if (!response.ok) {
      throw new Error(`UzEx вернул ошибку: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Если массив пустой — логируем для отладки
    if (!Array.isArray(data) || data.length === 0) {
      console.warn('UzEx вернул пустой массив');
    }

    res.status(200).json(data);
  } catch (error) {
    console.error('Proxy error:', error.message);
    res.status(500).json({ error: 'Не удалось получить котировки UzEx', details: error.message });
  }
}
