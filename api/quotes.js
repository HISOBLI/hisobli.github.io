export default async function handler(req, res) {
  try {
    const response = await fetch('https://uzex.uz/Quote/GetQuotes');
    if (!response.ok) throw new Error('UzEx API error');
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch quotes' });
  }
}
