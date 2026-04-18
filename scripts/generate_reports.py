#!/usr/bin/env python3
"""
Gerador de Relatórios PDF 1-Página — APM + Instituto i10
Diagnóstico FUNDEB SP 2026 | Resumo Executivo
White-label: APM principal + i10 parceiro técnico
"""

import json
import os
import sys
from datetime import datetime

try:
    from weasyprint import HTML
except ImportError:
    print("ERRO: weasyprint não instalado. Instale com: pip install weasyprint")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # APM root
DATA_PATH = os.path.join(BASE_DIR, "fundeb-sp", "data.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "relatorios-apm")

TODAY = datetime.now().strftime("%d/%m/%Y")


def fmt(v):
    if v is None:
        return "–"
    if abs(v) >= 1e9:
        return f"R$ {v/1e9:,.1f}B".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(v) >= 1e6:
        return f"R$ {v/1e6:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_n(v):
    if v is None:
        return "–"
    return f"{v:,.0f}".replace(",", ".")


def fmt_pct(v):
    if v is None:
        return "–"
    return f"{v:.1f}%".replace(".", ",")


def tier_bar_width(val, max_val):
    if max_val <= 0:
        return 0
    return min(100, max(2, val / max_val * 100))


def generate_1page_html(mun, rank_pos, total_muns):
    p = mun["potencial"]
    pot_total = p["pot_total_novo"]
    pct_total = p["pct_pot_total"]
    rec_total = p.get("recursos_totais", mun.get("rec_intra", 0))
    t5 = p["t5"]
    t6 = p["t6"]

    tiers = [
        ("T1 Expansão VAAF", p["pot_t1"], "#0D7377"),
        ("T2 Conversão Integral", p["pot_t2"], "#0E8B7D"),
        ("T3 AEE Dupla Matrícula", p["pot_t3"], "#11998E"),
        ("T4 Reclassificação", p["pot_t4"], "#1B8A5C"),
        ("T5 VAAR Federal", p["pot_t5_vaar"], "#2ECC71"),
        ("T6 EC 135 + BNCC", p.get("pot_t6_4pct", 0), "#E8A838"),
    ]
    max_tier = max(v for _, v, _ in tiers) if tiers else 1

    vaar_html = ""
    if not t5["recebe_vaar"]:
        vaar_html = f"""<div class="alert-box">
            <b>ALERTA:</b> {mun['nome']} <b>não recebe</b> complementação VAAR (R$ 7,5 bi disponíveis).
            Potencial: <b>{fmt(t5['vaar_potencial'])}</b>/ano se cumprir as 5 condicionalidades.
        </div>"""
    else:
        vaar_html = f"""<div class="success-box">
            <b>DESTAQUE:</b> {mun['nome']} recebe VAAR: {fmt(t5['vaar_atual'])}. Manter compliance.
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Source+Serif+4:wght@400;600;700&display=swap" rel="stylesheet">
<style>
@page {{
    size: A4;
    margin: 12mm 15mm 15mm 15mm;
    @bottom-center {{
        content: "APM — Associação Paulista de Municípios | Parceria técnica: Instituto i10";
        font-size: 6.5pt; color: #718096; font-family: 'Inter', sans-serif;
    }}
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; font-size: 8.5pt; color: #1A202C; line-height: 1.5; }}

.header {{
    background: linear-gradient(135deg, #0A5C5F, #0D7377);
    color: #fff; padding: 8mm 10mm; border-radius: 3mm; margin-bottom: 4mm;
    display: flex; justify-content: space-between; align-items: flex-start;
    position: relative; overflow: hidden;
}}
.header::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-conic-gradient(rgba(255,255,255,0.03) 0% 25%, transparent 0% 50%) 0 0 / 20px 20px;
}}
.header-left {{ position: relative; flex: 1; }}
.header-right {{ position: relative; text-align: right; }}
.header .logos {{
    display: flex; align-items: center; gap: 3mm; margin-bottom: 3mm;
}}
.header .logos .apm-img {{ height: 12mm; }}
.header .logos .partner {{ font-size: 7pt; opacity: 0.8; margin-left: 2mm; }}
.header .logos .partner b {{ display: block; font-size: 8pt; opacity: 1; }}
.header h1 {{ font-family: 'Source Serif 4', serif; font-size: 18pt; font-weight: 700; line-height: 1.2; }}
.header .sub {{ font-size: 8pt; opacity: 0.8; margin-top: 1.5mm; }}
.header .big-number {{ font-size: 30pt; font-weight: 800; color: #00E5A0; }}
.header .big-label {{ font-size: 9pt; opacity: 0.85; }}
.header .pct {{ display: inline-block; border: 1.5px solid #00E5A0; padding: 1mm 4mm; border-radius: 2mm; font-size: 10pt; font-weight: 700; color: #00E5A0; margin-top: 2mm; }}

.summary-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 2mm; margin-bottom: 4mm; }}
.summary-card {{
    background: #F7FAFC; border: 0.3mm solid #E2E8F0; border-radius: 2mm;
    padding: 2.5mm; text-align: center;
}}
.summary-card .label {{ font-size: 6pt; color: #718096; text-transform: uppercase; letter-spacing: 0.3pt; font-weight: 600; white-space: nowrap; }}
.summary-card .val {{ font-size: 10pt; font-weight: 700; margin-top: 0.5mm; white-space: nowrap; }}
.summary-card .val.green {{ color: #0D7377; }}
.summary-card .val.orange {{ color: #E8A838; }}
.summary-card .val.red {{ color: #D4553A; }}

h2 {{
    font-family: 'Source Serif 4', serif; font-size: 11pt; color: #0A5C5F;
    margin: 3mm 0 2mm 0; padding-bottom: 1.5mm;
    border-bottom: 1.5px solid; border-image: linear-gradient(90deg, #0D7377, #11998E) 1;
}}

.tiers {{ margin-bottom: 3mm; }}
.tier-bar {{ display: flex; align-items: center; gap: 2mm; margin: 1.2mm 0; font-size: 7.5pt; }}
.tier-label {{ width: 28mm; font-weight: 500; white-space: nowrap; }}
.tier-fill {{ height: 4.5mm; border-radius: 1mm; min-width: 1mm; }}
.tier-value {{ font-weight: 700; white-space: nowrap; margin-left: 1mm; }}

.alert-box {{
    background: rgba(212,85,58,0.06); border: 0.3mm solid rgba(212,85,58,0.3); border-radius: 2mm;
    padding: 2.5mm 3mm; margin: 2mm 0; font-size: 7.5pt;
}}
.alert-box b {{ color: #D4553A; }}
.success-box {{
    background: rgba(46,125,50,0.06); border: 0.3mm solid rgba(46,125,50,0.3); border-radius: 2mm;
    padding: 2.5mm 3mm; margin: 2mm 0; font-size: 7.5pt;
}}
.success-box b {{ color: #0D7377; }}

.cta-footer {{
    background: #0B6669;
    color: #fff; border-radius: 3mm; padding: 6mm 8mm; margin-top: 4mm;
    text-align: center;
}}
.cta-footer h3 {{
    font-family: 'Source Serif 4', serif; font-size: 11pt; font-weight: 700;
    color: #00E5A0; margin-bottom: 2mm;
}}
.cta-footer .cta-sub {{
    font-size: 8pt; opacity: 0.9; margin-bottom: 4mm;
}}
.cta-footer .cta-pills {{
    display: flex; justify-content: center; gap: 3mm; flex-wrap: wrap;
}}
.cta-footer .cta-pill {{
    display: inline-block; border: 0.4mm solid rgba(255,255,255,0.4);
    padding: 1.5mm 4mm; border-radius: 50px; font-size: 7.5pt; font-weight: 500;
    color: rgba(255,255,255,0.9);
}}

.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}

.info-row {{ display: flex; justify-content: space-between; padding: 1mm 0; font-size: 7.5pt; border-bottom: 0.1mm solid #F0F3F7; }}
.info-row .il {{ color: #718096; }}
.info-row .iv {{ font-weight: 600; }}

.date-badge {{
    display: inline-block; background: rgba(212,85,58,0.1); color: #D4553A;
    padding: 1mm 3mm; border-radius: 1.5mm; font-size: 7pt; font-weight: 700;
    margin-top: 1mm;
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <div class="logos">
            <img src="file://{os.path.join(BASE_DIR, 'assets', 'apm-logo-pill.png')}" alt="APM" class="apm-img">
            <div class="partner">
                <b>Associação Paulista de Municípios</b>
                Parceria técnica: Instituto i10
            </div>
        </div>
        <div class="sub">Diagnóstico FUNDEB 2026 · Potencial de Captação</div>
        <h1>{mun['nome']}</h1>
        <div class="sub">São Paulo · {fmt_n(mun['tot_mat'])} matrículas · Ordem {mun['ordem']} · Ranking potencial: {rank_pos}º/{total_muns}</div>
    </div>
    <div class="header-right">
        <div class="big-number">{fmt(pot_total)}</div>
        <div class="big-label">em recursos não captados</div>
        <div class="pct">+{fmt_pct(pct_total)} sobre receita atual</div>
    </div>
</div>

<div class="summary-grid">
    <div class="summary-card">
        <div class="label">Receita Atual</div>
        <div class="val">{fmt(rec_total)}</div>
    </div>
    <div class="summary-card">
        <div class="label">Potencial</div>
        <div class="val green">{fmt(pot_total)}</div>
    </div>
    <div class="summary-card">
        <div class="label">Ganho %</div>
        <div class="val green">+{fmt_pct(pct_total)}</div>
    </div>
    <div class="summary-card">
        <div class="label">Cat. Ativas</div>
        <div class="val">{p['n_ativas']}/15</div>
    </div>
    <div class="summary-card">
        <div class="label">Cat. Faltantes</div>
        <div class="val orange">{p['n_faltantes']}</div>
    </div>
    <div class="summary-card">
        <div class="label">VAAR</div>
        <div class="val {'green' if t5['recebe_vaar'] else 'red'}">{'SIM' if t5['recebe_vaar'] else 'NÃO'}</div>
    </div>
</div>

<div class="two-col">
    <div>
        <h2>Decomposição por Alavanca</h2>
        <div class="tiers">
            {''.join(f"""<div class="tier-bar">
                <div class="tier-label">{name}</div>
                <div class="tier-fill" style="width:{tier_bar_width(val, max_tier)}%;background:{color}"></div>
                <div class="tier-value" style="color:{color}">{fmt(val)}</div>
            </div>""" for name, val, color in tiers if val > 0)}
            <div class="tier-bar" style="border-top:0.5mm solid #CBD5E0;padding-top:1.5mm;margin-top:1.5mm">
                <div class="tier-label" style="font-weight:700">TOTAL</div>
                <div class="tier-value" style="font-size:11pt;color:#0D7377;font-weight:800">{fmt(pot_total)}</div>
            </div>
        </div>
    </div>
    <div>
        <h2>Dados Adicionais</h2>
        <div class="info-row"><span class="il">Matrículas totais</span><span class="iv">{fmt_n(mun['tot_mat'])}</span></div>
        <div class="info-row"><span class="il">Tempo integral</span><span class="iv">{fmt_pct(t6['pct_integral'])}</span></div>
        <div class="info-row"><span class="il">EC 135 (4% FUNDEB)</span><span class="iv" style="color:#E8A838">{fmt(t6['valor_4pct'])}</span></div>
        <div class="info-row"><span class="il">VAAR potencial</span><span class="iv">{fmt(t5['vaar_potencial']) if not t5['recebe_vaar'] else 'Já recebe'}</span></div>
        <div class="info-row"><span class="il">Novas vagas integral</span><span class="iv">~{fmt_n(t6['novas_mat_possiveis'])}</span></div>

        <div class="date-badge">CENSO ESCOLAR: 27 DE MAIO DE 2026</div>
    </div>
</div>

{vaar_html}

<div class="cta-footer">
    <h3>A APM e o Instituto i10 podem implementar este plano para {mun['nome']}</h3>
    <div class="cta-sub">Consultoria especializada: Tecnologia · Dados · Suporte Jurídico · BNCC Computação</div>
    <div class="cta-pills">
        <span class="cta-pill">Diagnóstico Completo</span>
        <span class="cta-pill">Compliance VAAR</span>
        <span class="cta-pill">Busca Ativa AEE</span>
        <span class="cta-pill">Suporte Jurídico</span>
        <span class="cta-pill">BNCC Computação</span>
    </div>
</div>

<div style="text-align:center;margin-top:3mm;font-size:6.5pt;color:#718096">
    Relatório gerado em {TODAY} · Dados: MEC/FNDE FUNDEB 2026 (parâmetros definitivos)
</div>

</body>
</html>"""

    return html


def main():
    print("=" * 60)
    print("APM + Instituto i10 — Gerador de Relatórios 1-Página")
    print("=" * 60)

    print("\nCarregando dados...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    muns = data["municipios"]
    print(f"  {len(muns)} municípios carregados")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"  Diretório de saída: {OUTPUT_DIR}")

    ranked = sorted(muns, key=lambda m: -m["potencial"]["pot_total_novo"])
    rank_map = {m["id"]: i + 1 for i, m in enumerate(ranked)}

    target = None
    if len(sys.argv) > 1:
        target = " ".join(sys.argv[1:]).lower()
        muns_to_process = [m for m in muns if target in m["nome"].lower()]
        if not muns_to_process:
            print(f"\n  ERRO: Nenhum município encontrado com '{target}'")
            sys.exit(1)
        print(f"\n  Filtro: '{target}' → {len(muns_to_process)} municípios")
    else:
        muns_to_process = muns

    total = len(muns_to_process)
    errors = []
    skipped = 0

    import gc

    print(f"\nGerando {total} relatórios PDF (1-página, white-label APM)...")
    for i, mun in enumerate(muns_to_process):
        nome_safe = (
            mun["nome"]
            .replace(" ", "_")
            .replace("/", "_")
            .replace("'", "")
            .replace('"', "")
        )
        filename = f"{mun['ordem']:03d}_{nome_safe}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            skipped += 1
            continue

        try:
            rank_pos = rank_map[mun["id"]]
            html = generate_1page_html(mun, rank_pos, len(muns))
            HTML(string=html).write_pdf(filepath)

            generated = i + 1 - skipped
            gc.collect()
            if generated % 20 == 0 or (i + 1) == total:
                print(f"  [{i+1}/{total}] {mun['nome']} → {filename}", flush=True)
        except Exception as e:
            errors.append((mun["nome"], str(e)))
            print(f"  ERRO [{i+1}/{total}] {mun['nome']}: {e}")

    if skipped:
        print(f"  ({skipped} já existentes, pulados)")

    print(f"\n{'=' * 60}")
    print(f"Concluído: {total - len(errors)}/{total} relatórios gerados")
    if errors:
        print(f"Erros: {len(errors)}")
        for nome, err in errors[:10]:
            print(f"  — {nome}: {err}")
    print(f"Diretório: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
