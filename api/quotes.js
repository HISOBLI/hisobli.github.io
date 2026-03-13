export default async function handler(req, res) {
  try {
    const response = await fetch('https://uzex.uz/Quote/GetQuotes', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; HISOBLI-Vercel-Proxy/1.0)',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache'
      }
    });

    if (!response.ok) throw new Error(`UzEx HTTP ${response.status}`);
    
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('Proxy failed:', error.message);
    res.status(500).json({ error: error.message });
  }
}
