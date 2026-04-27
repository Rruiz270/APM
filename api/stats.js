export default async function handler(req, res) {
  const dbUrl = process.env.POSTGRES_DATABASE_URL_UNPOOLED || process.env.POSTGRES_DATABASE_URL;

  if (!dbUrl) {
    return res.status(500).json({ error: 'Banco de dados não configurado' });
  }

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-cache');

  const host = dbUrl.replace(/.*@/, '').replace(/\/.*/, '');

  async function sql(query, params = []) {
    const r = await fetch(`https://${host}/sql`, {
      method: 'POST',
      headers: {
        'Neon-Connection-String': dbUrl,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, params }),
    });
    return r.json();
  }

  try {
    const [totalRes, perMuniRes, recentRes] = await Promise.all([
      sql('SELECT COUNT(*) as total FROM apm_downloads'),
      sql(`SELECT pdf, municipio, COUNT(*) as count, MAX(created_at) as ultimo_acesso
           FROM apm_downloads GROUP BY pdf, municipio ORDER BY count DESC`),
      sql(`SELECT pdf, municipio, ip, created_at as ts
           FROM apm_downloads ORDER BY created_at DESC LIMIT 50`),
    ]);

    const total = parseInt(totalRes.rows?.[0]?.total || '0');
    const municipios = (perMuniRes.rows || []).map(r => ({
      nome: r.municipio,
      pdf: r.pdf,
      count: parseInt(r.count),
      ultimo_acesso: r.ultimo_acesso,
    }));
    const comDownload = municipios.filter(m => m.count > 0).length;
    const recent = (recentRes.rows || []).map(r => ({
      municipio: r.municipio,
      pdf: r.pdf,
      ts: r.ts,
      ip: r.ip,
    }));

    res.status(200).json({
      total_downloads: total,
      municipios_com_download: comDownload,
      municipios_total: 645,
      taxa_abertura: ((comDownload / 645) * 100).toFixed(1),
      municipios: municipios,
      ultimos_50: recent,
      atualizado_em: new Date().toISOString(),
    });
  } catch (e) {
    console.error('Stats error:', e);
    res.status(500).json({ error: 'Erro ao buscar dados', detail: e.message });
  }
}
