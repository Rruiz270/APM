export default async function handler(req, res) {
  const redisUrl = process.env.KV_REST_API_URL;
  const redisToken = process.env.KV_REST_API_TOKEN;

  if (!redisUrl || !redisToken) {
    return res.status(500).json({ error: 'Redis não configurado' });
  }

  const authHeader = req.headers['x-dashboard-key'];
  const dashKey = process.env.DASHBOARD_KEY || 'apm-i10-2026';
  if (authHeader && authHeader !== dashKey) {
    return res.status(401).json({ error: 'Não autorizado' });
  }

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-cache');

  try {
    const redis = async (commands) => {
      const r = await fetch(`${redisUrl}/pipeline`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${redisToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(commands),
      });
      return r.json();
    };

    const [totalRes, municipiosRes] = await redis([
      ['GET', 'dl_total'],
      ['SMEMBERS', 'dl_municipios'],
    ]);

    const total = parseInt(totalRes.result || '0');
    const municipios = municipiosRes.result || [];

    let countCommands = municipios.map(pdf => ['GET', `dl:${pdf}`]);
    let logCommands = municipios.map(pdf => ['LRANGE', `dl_log:${pdf}`, '0', '0']);

    let counts = {};
    let lastAccess = {};

    if (municipios.length > 0) {
      const countResults = await redis(countCommands);
      const logResults = await redis(logCommands);

      municipios.forEach((pdf, i) => {
        const nome = pdf.replace('.pdf', '').replace(/^\d+_/, '').replace(/_/g, ' ');
        const count = parseInt(countResults[i].result || '0');
        counts[pdf] = { nome, count, pdf };

        const lastLog = logResults[i].result?.[0];
        if (lastLog) {
          try {
            const parsed = JSON.parse(lastLog);
            counts[pdf].ultimo_acesso = parsed.ts;
            counts[pdf].ip = parsed.ip;
          } catch (e) {}
        }
      });
    }

    const recentRes = await redis([['LRANGE', 'dl_recent', '0', '49']]);
    const recent = (recentRes[0].result || []).map(entry => {
      try { return JSON.parse(entry); } catch { return null; }
    }).filter(Boolean);

    const municipiosList = Object.values(counts).sort((a, b) => b.count - a.count);
    const comDownload = municipiosList.filter(m => m.count > 0).length;

    res.status(200).json({
      total_downloads: total,
      municipios_com_download: comDownload,
      municipios_total: 645,
      taxa_abertura: ((comDownload / 645) * 100).toFixed(1),
      municipios: municipiosList,
      ultimos_50: recent,
      atualizado_em: new Date().toISOString(),
    });
  } catch (e) {
    console.error('Stats error:', e);
    res.status(500).json({ error: 'Erro ao buscar dados', detail: e.message });
  }
}
