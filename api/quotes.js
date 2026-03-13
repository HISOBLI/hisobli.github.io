export default async function handler(req, res) {
  try {
    const response = await fetch('https://uzex.uz/Quote/GetQuotes', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; HISOBLI-Vercel-Proxy)',
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`UzEx returned ${response.status}`);
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('Proxy error:', error.message);
    res.status(500).json({ 
      error: 'Proxy failed', 
      message: error.message 
    });
  }
}
