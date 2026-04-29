export default async function handler(req, res) {
  const { pdf, source } = req.query;

  if (!pdf || !pdf.endsWith('.pdf')) {
    return res.status(400).json({ error: 'Parâmetro pdf inválido' });
  }

  const dbUrl = process.env.POSTGRES_DATABASE_URL_UNPOOLED || process.env.POSTGRES_DATABASE_URL;

  if (dbUrl) {
    const ip = (req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || 'unknown').split(',')[0].trim();
    const ua = req.headers['user-agent'] || 'unknown';
    const municipio = pdf.replace('.pdf', '').replace(/^\d+_/, '').replace(/_/g, ' ');

    const host = dbUrl.replace(/.*@/, '').replace(/\/.*/, '');
    try {
      await fetch(`https://${host}/sql`, {
        method: 'POST',
        headers: {
          'Neon-Connection-String': dbUrl,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: 'INSERT INTO apm_downloads (pdf, municipio, ip, user_agent, source) VALUES ($1, $2, $3, $4, $5)',
          params: [pdf, municipio, ip, ua, source || 'direct'],
        }),
      });
    } catch (e) {
      console.error('DB tracking error:', e);
    }
  }

  const pdfUrl = `/relatorios-apm/${encodeURIComponent(pdf).replace(/%20/g, '_')}`;
  res.writeHead(302, { Location: pdfUrl });
  res.end();
}
