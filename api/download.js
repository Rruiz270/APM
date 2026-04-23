export default async function handler(req, res) {
  const { pdf } = req.query;

  if (!pdf || !pdf.endsWith('.pdf')) {
    return res.status(400).json({ error: 'Parâmetro pdf inválido' });
  }

  const redisUrl = process.env.KV_REST_API_URL;
  const redisToken = process.env.KV_REST_API_TOKEN;

  if (redisUrl && redisToken) {
    const now = new Date().toISOString();
    const ip = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || 'unknown';
    const ua = req.headers['user-agent'] || 'unknown';
    const municipio = pdf.replace('.pdf', '').replace(/^\d+_/, '').replace(/_/g, ' ');

    const entry = JSON.stringify({ ts: now, ip: ip.split(',')[0].trim(), ua, pdf, municipio });

    const commands = [
      ['INCR', 'dl_total'],
      ['INCR', `dl:${pdf}`],
      ['LPUSH', `dl_log:${pdf}`, entry],
      ['LPUSH', 'dl_recent', entry],
      ['LTRIM', 'dl_recent', '0', '999'],
      ['SADD', 'dl_municipios', pdf],
    ];

    try {
      await fetch(`${redisUrl}/pipeline`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${redisToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(commands),
      });
    } catch (e) {
      console.error('Redis error:', e);
    }
  }

  const pdfUrl = `/relatorios-apm/${encodeURIComponent(pdf).replace(/%20/g, '_')}`;
  res.writeHead(302, { Location: pdfUrl });
  res.end();
}
