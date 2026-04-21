import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ status: 'error', message: 'Method not allowed' });

  try {
    const { nome, email, telefone, municipioId, municipioNome } = req.body;

    if (!nome || !email || !telefone || !municipioId || !municipioNome) {
      return res.status(400).json({ status: 'error', message: 'Todos os campos s\u00e3o obrigat\u00f3rios' });
    }

    const normalizedEmail = email.toLowerCase().trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(normalizedEmail)) {
      return res.status(400).json({ status: 'error', message: 'E-mail inv\u00e1lido' });
    }

    const paddedId = String(municipioId).padStart(3, '0');
    const safeName = municipioNome.replace(/ /g, '_');
    const pdfFilename = `${paddedId}_${safeName}.pdf`;
    const pdfUrl = `/relatorios-apm-completos/${pdfFilename}`;

    let kvAvailable = false;
    try {
      if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
        kvAvailable = true;
      }
    } catch {}

    if (kvAvailable) {
      try {
        const kvKey = `fundeb:${normalizedEmail}`;
        const existing = await kv.get(kvKey);

        if (existing) {
          return res.status(200).json({
            status: 'already_sent',
            message: 'Relat\u00f3rio j\u00e1 enviado para este e-mail'
          });
        }

        await kv.set(kvKey, {
          nome,
          email: normalizedEmail,
          telefone,
          municipioId,
          municipioNome,
          pdfFilename,
          timestamp: new Date().toISOString()
        });
      } catch (kvError) {
        console.error('KV error (allowing download):', kvError.message);
      }
    }

    return res.status(200).json({
      status: 'ok',
      pdfUrl,
      message: 'Relat\u00f3rio liberado com sucesso'
    });

  } catch (error) {
    console.error('Download API error:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Erro interno. Tente novamente.'
    });
  }
}
