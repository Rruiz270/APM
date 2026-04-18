#!/usr/bin/env python3
"""
Gerador de Relatórios PDF Completos (6 páginas) — APM + Instituto i10
Diagnóstico FUNDEB SP 2026 | Potencial Máximo de Captação
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "fundeb-sp", "data.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "relatorios-apm-completos")

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


def generate_full_html(mun, data, rank_pos, total_muns, peers):
    p = mun["potencial"]
    t1, t2, t3, t4, t5, t6 = p["t1"], p["t2"], p["t3"], p["t4"], p["t5"], p["t6"]

    pot_total = p["pot_total_novo"]
    pct_total = p["pct_pot_total"]
    rec_total = p.get("recursos_totais", mun.get("rec_intra", 0))

    tiers = [
        ("T1 VAAF", p["pot_t1"], "#0D7377"),
        ("T2 Integral", p["pot_t2"], "#0E8B7D"),
        ("T3 AEE", p["pot_t3"], "#11998E"),
        ("T4 Localidade", p["pot_t4"], "#1B8A5C"),
        ("T5 VAAR", p["pot_t5_vaar"], "#2ECC71"),
        ("T6 EC 135", p.get("pot_t6_4pct", 0), "#E8A838"),
    ]
    max_tier = max(v for _, v, _ in tiers) if tiers else 1

    # Peers
    peers_rows = ""
    for peer in peers[:5]:
        pp = peer["potencial"]
        peers_rows += f"""<tr>
            <td>{peer['nome']}</td>
            <td class="num">{fmt_n(peer['tot_mat'])}</td>
            <td class="num">{fmt(peer.get('rec_intra', 0))}</td>
            <td class="num" style="color:#0D7377;font-weight:600">{fmt(pp['pot_total_novo'])}</td>
            <td class="num">{fmt_pct(pp['pct_pot_total'])}</td>
        </tr>"""

    # T1
    t1_rows = ""
    if t1["detalhe"]:
        for d in t1["detalhe"]:
            high = "color:#0D7377;font-weight:600" if d["vaaf_u"] >= 9000 else ""
            t1_rows += f"""<tr>
                <td style="{high}">{d['cat']}</td>
                <td class="num">{fmt(d['vaaf_u'])}</td>
                <td class="num">{fmt(10 * d['vaaf_u'])}</td>
                <td class="num">{fmt(50 * d['vaaf_u'])}</td>
            </tr>"""

    # T2
    t2_rows = ""
    if t2["detalhe"]:
        for d in t2["detalhe"]:
            t2_rows += f"""<tr>
                <td>{d['de']}</td>
                <td style="color:#0D7377">{d['para']}</td>
                <td class="num">{fmt_n(d['mat'])}</td>
                <td class="num">+{fmt(d['diff_por_aluno'])}</td>
                <td class="num" style="color:#0D7377;font-weight:600">{fmt(d['ganho_total'])}</td>
            </tr>"""

    # T3
    t3_rows = ""
    if t3["detalhe"]:
        for d in t3["detalhe"]:
            t3_rows += f"""<tr>
                <td>{d['cat']}</td>
                <td class="num">{fmt_n(d['mat_especial'])}</td>
                <td class="num">{fmt(d['vaaf_aee'])}</td>
                <td class="num" style="color:#0D7377;font-weight:600">{fmt(d['ganho_100pct'])}</td>
            </tr>"""

    # Strategies
    strat_html = ""
    for e in p.get("estrategias", [])[:6]:
        imp_color = {"alto": "#0D7377", "medio": "#E8A838", "baixo": "#718096"}.get(e["impacto"], "#718096")
        imp_bg = {"alto": "rgba(13,115,119,0.1)", "medio": "rgba(232,168,56,0.1)", "baixo": "rgba(113,128,150,0.1)"}.get(e["impacto"], "rgba(113,128,150,0.1)")
        strat_html += f"""<div class="strat">
            <span class="strat-badge" style="background:{imp_bg};color:{imp_color}">{e['impacto'].upper()}</span>
            <span class="strat-tier">{e['tier']}</span>
            <b>{e['titulo']}</b><br>
            <span class="strat-desc">{e['descricao']}</span>
        </div>"""

    # Action plan
    action_short, action_mid, action_long = [], [], []

    if t1["n_faltantes"] > 0:
        action_short.append(f"Mapear {t1['n_faltantes']} categorias não captadas e planejar abertura de vagas")
    if t3["detalhe"]:
        action_short.append("Busca ativa de alunos com deficiência para AEE (dupla matrícula)")
    if not t5["recebe_vaar"]:
        action_short.append("Iniciar compliance das 5 condicionalidades VAAR")
    action_short.append("Implementar BNCC Computação (obrigatório 2026)")

    if t2["detalhe"]:
        action_mid.append(f"Converter {fmt_n(sum(d['mat'] for d in t2['detalhe']))} alunos de parcial para integral")
    action_mid.append("Adesão ao PETI (Programa Escola em Tempo Integral)")
    conv_falt = [c for c in p["categorias_faltantes"] if "Conveniada" in c]
    if conv_falt:
        action_mid.append(f"Formalizar {len(conv_falt)} parcerias com instituições conveniadas")

    if t4["mat_urbano_total"] > 0 and not t4["has_campo"]:
        action_long.append("Reclassificar escolas rurais para fator Campo (+15%)")
    action_long.append("Monitoramento contínuo do Censo Escolar")
    action_long.append("Dashboard de acompanhamento de indicadores VAAR")
    if t6["pct_integral"] < 50:
        action_long.append(f"Ampliar tempo integral de {fmt_pct(t6['pct_integral'])} para meta PNE 50%")

    def action_list(items):
        return "".join(f"<li>{item}</li>" for item in items)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Source+Serif+4:wght@400;600;700&display=swap" rel="stylesheet">
<style>
@page {{
    size: A4;
    margin: 15mm 18mm 20mm 18mm;
    @bottom-center {{
        content: "APM — Associação Paulista de Municípios | Parceria técnica: Instituto i10";
        font-size: 7pt; color: #718096; font-family: 'Inter', sans-serif;
    }}
    @bottom-right {{
        content: counter(page) " / " counter(pages);
        font-size: 7pt; color: #718096; font-family: 'Inter', sans-serif;
    }}
}}
@page :first {{
    margin: 0;
    @bottom-center {{ content: none; }}
    @bottom-right {{ content: none; }}
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; font-size: 9pt; color: #1A202C; line-height: 1.55; }}

/* === CAPA === */
.cover {{
    height: 100vh; width: 100%;
    background: #0A5C5F;
    color: #fff; display: flex; flex-direction: column;
    justify-content: center; padding: 50mm 30mm;
    page-break-after: always; position: relative; overflow: hidden;
}}
.cover::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-conic-gradient(rgba(255,255,255,0.03) 0% 25%, transparent 0% 50%) 0 0 / 30px 30px;
    pointer-events: none;
}}
.cover .brand {{
    display: flex; align-items: center; gap: 5mm; margin-bottom: 20mm; position: relative;
}}
.cover .brand .apm-img {{ height: 16mm; }}
.cover .brand .partner-text {{ font-size: 9pt; opacity: 0.8; }}
.cover .brand .partner-text b {{ display: block; font-size: 10pt; opacity: 1; }}
.cover .subtitle {{ font-size: 11pt; opacity: 0.7; margin-bottom: 25mm; font-weight: 300; position: relative; }}
.cover h1 {{ font-family: 'Source Serif 4', serif; font-size: 30pt; font-weight: 700; margin-bottom: 6mm; line-height: 1.15; position: relative; }}
.cover .sub2 {{ font-size: 11pt; opacity: 0.7; margin-bottom: 25mm; font-weight: 300; position: relative; }}
.cover .big-number {{ font-family: 'Inter', sans-serif; font-size: 48pt; font-weight: 800; color: #00E5A0; margin-bottom: 3mm; position: relative; }}
.cover .big-label {{ font-family: 'Source Serif 4', serif; font-size: 13pt; opacity: 0.85; margin-bottom: 12mm; position: relative; }}
.cover .pct-badge {{
    display: inline-block; border: 2px solid #00E5A0; background: rgba(0,229,160,0.1);
    padding: 3mm 8mm; border-radius: 4mm; font-size: 16pt; font-weight: 700; color: #00E5A0;
    font-family: 'Inter', sans-serif; position: relative;
}}
.cover .footer {{ margin-top: auto; font-size: 8.5pt; opacity: 0.45; position: relative; }}
.cover .footer b {{ opacity: 1; color: #00E5A0; }}

/* === PÁGINAS INTERNAS === */
h2 {{
    font-family: 'Source Serif 4', serif; font-size: 14pt; color: #0A5C5F;
    margin: 6mm 0 3mm 0; padding-bottom: 2mm;
    border-bottom: 2px solid; border-image: linear-gradient(90deg, #0D7377, #11998E) 1;
}}
h3 {{ font-family: 'Inter', sans-serif; font-size: 10pt; color: #0A5C5F; margin: 4mm 0 2mm 0; font-weight: 600; }}

.summary-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 3mm; margin-bottom: 5mm; }}
.summary-card {{
    background: #F7FAFC; border: 0.3mm solid #E2E8F0; border-radius: 2.5mm;
    padding: 3.5mm; text-align: center;
}}
.summary-card .label {{ font-size: 6.5pt; color: #718096; text-transform: uppercase; letter-spacing: 0.5pt; font-weight: 600; white-space: nowrap; }}
.summary-card .val {{ font-size: 13pt; font-weight: 700; margin-top: 1mm; color: #0A5C5F; white-space: nowrap; }}
.summary-card .val.green {{ color: #0D7377; }}
.summary-card .val.teal {{ color: #11998E; }}
.summary-card .val.alert {{ color: #D4553A; }}

table {{ width: 100%; border-collapse: collapse; font-size: 8pt; margin-bottom: 3mm; color: #1A202C; }}
th {{ background: #0A5C5F; color: #E2E8F0; padding: 2.5mm 2mm; text-align: left; font-weight: 600; font-size: 7pt; text-transform: uppercase; letter-spacing: 0.3pt; }}
td {{ padding: 1.8mm 2mm; border-bottom: 0.2mm solid #EDF0F4; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}

.tier-bar {{ display: flex; align-items: center; gap: 2mm; margin: 1.5mm 0; font-size: 8pt; color: #1A202C; }}
.tier-label {{ width: 22mm; font-weight: 500; white-space: nowrap; }}
.tier-fill {{ height: 5.5mm; border-radius: 1.5mm; min-width: 1mm; }}
.tier-value {{ font-weight: 700; white-space: nowrap; margin-left: 1mm; }}

.strat {{ padding: 2mm 0; border-bottom: 0.2mm solid #EDF0F4; font-size: 8pt; color: #1A202C; }}
.strat-badge {{ display: inline-block; padding: 0.5mm 2.5mm; border-radius: 2mm; font-size: 6pt; font-weight: 700; margin-right: 1mm; text-transform: uppercase; letter-spacing: 0.3pt; }}
.strat-tier {{ display: inline-block; background: #EDF0F4; padding: 0.5mm 2mm; border-radius: 2mm; font-size: 6pt; color: #718096; margin-right: 1mm; font-weight: 600; }}
.strat-desc {{ color: #718096; font-size: 7.5pt; }}

.action-phase {{ margin-bottom: 3mm; }}
.action-phase .phase-title {{
    font-weight: 700; font-size: 8.5pt; padding: 1.5mm 3mm; border-radius: 2mm;
    display: inline-block; margin-bottom: 1.5mm;
}}
.action-phase ul {{ margin-left: 5mm; font-size: 8pt; color: #1A202C; }}
.action-phase li {{ margin-bottom: 1mm; }}

.cta {{
    background: #0B6669;
    color: #fff; padding: 7mm; border-radius: 3mm; margin-top: 5mm; text-align: center;
}}
.cta h3 {{ color: #00E5A0; font-size: 13pt; margin-bottom: 2mm; font-family: 'Source Serif 4', serif; }}
.cta p {{ font-size: 9pt; opacity: 0.9; }}
.cta .cta-items {{ display: flex; justify-content: center; gap: 6mm; margin-top: 3mm; font-size: 7.5pt; }}
.cta .cta-item {{ border: 0.3mm solid rgba(255,255,255,0.35); padding: 2mm 4mm; border-radius: 2mm; color: rgba(255,255,255,0.9); font-weight: 500; }}

.page-break {{ page-break-before: always; }}

.alert-box {{
    background: rgba(212,85,58,0.06); border: 0.3mm solid rgba(212,85,58,0.3); border-radius: 2.5mm;
    padding: 3mm; margin: 2mm 0; font-size: 8pt; color: #1A202C;
}}
.alert-box b {{ color: #D4553A; }}

.success-box {{
    background: rgba(13,115,119,0.06); border: 0.3mm solid rgba(13,115,119,0.3); border-radius: 2.5mm;
    padding: 3mm; margin: 2mm 0; font-size: 8pt; color: #1A202C;
}}
.success-box b {{ color: #0D7377; }}

.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}

.info-row {{ display: flex; justify-content: space-between; padding: 1.2mm 0; font-size: 8pt; border-bottom: 0.1mm solid #F0F3F7; color: #1A202C; }}
.info-row .il {{ color: #718096; }}
.info-row .iv {{ font-weight: 600; }}

.divider {{ height: 2px; background: linear-gradient(90deg, #0D7377, #11998E); border-radius: 1px; margin: 3mm 0; }}
</style>
</head>
<body>

<!-- CAPA -->
<div class="cover">
    <div class="brand">
        <img src="file://{os.path.join(BASE_DIR, 'assets', 'apm-logo-pill.png')}" alt="APM" class="apm-img">
        <div class="partner-text">
            <b>Associação Paulista de Municípios</b>
            Parceria técnica: Instituto i10
        </div>
    </div>
    <div class="subtitle">Diagnóstico FUNDEB 2026 · Potencial Máximo de Captação</div>
    <h1>{mun['nome']}</h1>
    <div class="sub2">Estado de São Paulo · {fmt_n(mun['tot_mat'])} matrículas · Ordem {mun['ordem']}</div>
    <div class="big-number">{fmt(pot_total)}</div>
    <div class="big-label">em recursos FUNDEB que {mun['nome']} não está captando</div>
    <div class="pct-badge">+{fmt_pct(pct_total)} sobre a receita atual</div>
    <div class="footer">
        <b>APM</b> — Associação Paulista de Municípios | Parceria técnica: <b>Instituto i10</b><br>
        Relatório gerado em {TODAY} · Dados: MEC/FNDE FUNDEB 2026 (parâmetros definitivos)
    </div>
</div>

<!-- PÁGINA 2: RESUMO EXECUTIVO -->
<h2>Resumo Executivo</h2>

<div class="summary-grid">
    <div class="summary-card">
        <div class="label">Receita FUNDEB Atual</div>
        <div class="val">{fmt(rec_total)}</div>
    </div>
    <div class="summary-card">
        <div class="label">Potencial Não Captado</div>
        <div class="val green">{fmt(pot_total)}</div>
    </div>
    <div class="summary-card">
        <div class="label">Ganho Percentual</div>
        <div class="val green">+{fmt_pct(pct_total)}</div>
    </div>
    <div class="summary-card">
        <div class="label">Ranking Potencial</div>
        <div class="val teal">{rank_pos}º / {total_muns}</div>
    </div>
</div>

<div class="summary-grid">
    <div class="summary-card">
        <div class="label">Matrículas Totais</div>
        <div class="val">{fmt_n(mun['tot_mat'])}</div>
    </div>
    <div class="summary-card">
        <div class="label">Categorias Ativas</div>
        <div class="val">{p['n_ativas']} / 15</div>
    </div>
    <div class="summary-card">
        <div class="label">Categorias Faltantes</div>
        <div class="val alert">{p['n_faltantes']}</div>
    </div>
    <div class="summary-card">
        <div class="label">Recebe VAAR</div>
        <div class="val {'green' if t5['recebe_vaar'] else 'alert'}">{'SIM' if t5['recebe_vaar'] else 'NÃO'}</div>
    </div>
</div>

<h3>Decomposição do Potencial por Alavanca</h3>
{''.join(f"""<div class="tier-bar">
    <div class="tier-label">{name}</div>
    <div class="tier-fill" style="width:{tier_bar_width(val, max_tier)}%;background:{color}"></div>
    <div class="tier-value" style="color:{color}">{fmt(val)}</div>
</div>""" for name, val, color in tiers if val > 0)}

<div class="tier-bar" style="border-top:0.5mm solid #CBD5E0;padding-top:2mm;margin-top:2mm">
    <div class="tier-label" style="font-weight:700">TOTAL</div>
    <div class="tier-value" style="font-size:12pt;color:#0D7377;font-weight:800">{fmt(pot_total)}</div>
</div>

{f"""<div class="alert-box">
    <b>ALERTA CRÍTICO:</b> {mun['nome']} <b>não recebe</b> complementação VAAR (R$ 7,5 bilhões disponíveis nacionalmente).
    Potencial estimado: <b>{fmt(t5['vaar_potencial'])}</b>/ano se cumprir as 5 condicionalidades MEC.
    Dos 645 municípios de SP, 448 também não recebem — oportunidade crítica.
</div>""" if not t5['recebe_vaar'] else f"""<div class="success-box">
    <b>DESTAQUE:</b> {mun['nome']} recebe VAAR: {fmt(t5['vaar_atual'])}. Manter compliance das condicionalidades e avanço nos indicadores.
</div>"""}

<div class="divider"></div>

<!-- PÁGINA 3: DETALHAMENTO -->
<h2 class="page-break">Detalhamento por Alavanca</h2>

{f"""<h3>T1 — Expansão VAAF: {t1['n_faltantes']} Categorias Não Captadas</h3>
<p style="font-size:8pt;color:#718096;margin-bottom:2mm">Cada categoria sem matrículas representa receita FUNDEB perdida. Simulação com 10 e 50 alunos novos:</p>
<table>
    <thead><tr><th>Categoria Faltante</th><th class="num">VAAF/aluno</th><th class="num">Ganho +10 alunos</th><th class="num">Ganho +50 alunos</th></tr></thead>
    <tbody>{t1_rows}</tbody>
</table>""" if t1_rows else '<h3>T1 — Expansão VAAF</h3><div class="success-box"><b>Excelente:</b> Já capta em todas as 15 categorias principais.</div>'}

{f"""<h3>T2 — Conversão Parcial → Integral</h3>
<p style="font-size:8pt;color:#718096;margin-bottom:2mm">Converter alunos de jornada parcial para integral aumenta o fator de ponderação VAAF:</p>
<table>
    <thead><tr><th>De (parcial)</th><th>Para (integral)</th><th class="num">Alunos</th><th class="num">Diferença/aluno</th><th class="num">Ganho Total</th></tr></thead>
    <tbody>{t2_rows}</tbody>
</table>
<div class="tier-bar" style="border-top:0.3mm solid #CBD5E0;padding-top:1mm">
    <div class="tier-label" style="font-weight:600">Subtotal T2</div>
    <div class="tier-value" style="color:#0D7377;font-weight:700">{fmt(t2['ganho_total'])}</div>
</div>""" if t2_rows else ""}

{f"""<h3>T3 — AEE Dupla Matrícula (Educação Especial)</h3>
<p style="font-size:8pt;color:#718096;margin-bottom:2mm">Aluno de Ed. Especial com AEE = dupla contagem no FUNDEB (fator 1,40 adicional por matrícula):</p>
<table>
    <thead><tr><th>Categoria</th><th class="num">Alunos Ed. Esp.</th><th class="num">VAAF AEE/aluno</th><th class="num">Ganho Adicional</th></tr></thead>
    <tbody>{t3_rows}</tbody>
</table>
<div class="tier-bar" style="border-top:0.3mm solid #CBD5E0;padding-top:1mm">
    <div class="tier-label" style="font-weight:600">Subtotal T3</div>
    <div class="tier-value" style="color:#0D7377;font-weight:700">{fmt(t3['ganho_total'])}</div>
</div>""" if t3_rows else ""}

<h3>T4 — Reclassificação de Localidade</h3>
<div class="two-col">
    <div class="info-row"><span class="il">Matrículas urbanas</span><span class="iv">{fmt_n(t4['mat_urbano_total'])}</span></div>
    <div class="info-row"><span class="il">Matrículas campo</span><span class="iv">{'Sim' if t4['has_campo'] else 'Não'}</span></div>
</div>
<div class="info-row"><span class="il">Ganho se 10% reclassificadas como Campo (+15%)</span><span class="iv" style="color:#0D7377">{fmt(t4['ganho_campo_10pct'])}</span></div>
<div class="info-row"><span class="il">Ganho se 5% reclassificadas como Ind/Quilomb (+40%)</span><span class="iv" style="color:#0D7377">{fmt(t4['ganho_ind_5pct'])}</span></div>

<h3>T5 — Complementação Federal (VAAR + VAAT)</h3>
<div class="two-col">
    <div class="info-row"><span class="il">VAAR atual</span><span class="iv">{'Recebe: ' + fmt(t5['vaar_atual']) if t5['recebe_vaar'] else '<span style="color:#D4553A;font-weight:700">Não recebe</span>'}</span></div>
    <div class="info-row"><span class="il">VAAT atual</span><span class="iv">{'Recebe: ' + fmt(t5['vaat_atual']) if t5['recebe_vaat'] else 'Não recebe'}</span></div>
    <div class="info-row"><span class="il">VAAR potencial</span><span class="iv" style="color:#0D7377">{fmt(t5['vaar_potencial']) if not t5['recebe_vaar'] else 'Já recebe'}</span></div>
    <div class="info-row"><span class="il">VAAT potencial</span><span class="iv">{fmt(t5['vaat_potencial']) if t5['vaat_potencial'] > 0 else 'N/A'}</span></div>
</div>

<h3>T6 — EC 135/2024 + BNCC Computação</h3>
<div class="two-col">
    <div class="info-row"><span class="il">4% FUNDEB (obrigatório p/ integral)</span><span class="iv" style="color:#E8A838;font-weight:700">{fmt(t6['valor_4pct'])}</span></div>
    <div class="info-row"><span class="il">Tempo integral atual</span><span class="iv">{fmt_n(t6['mat_integral_atual'])} ({fmt_pct(t6['pct_integral'])})</span></div>
    <div class="info-row"><span class="il">Novas vagas possíveis com 4%</span><span class="iv" style="color:#0D7377">~{fmt_n(t6['novas_mat_possiveis'])} alunos</span></div>
    <div class="info-row"><span class="il">PETI fomento federal/aluno</span><span class="iv">R$ {fmt_n(t6['peti_por_aluno'])}</span></div>
</div>

<!-- PÁGINA 4: COMPARAÇÃO + PLANO + CTA -->
<h2 class="page-break">Comparação com Municípios Similares</h2>
<p style="font-size:8pt;color:#718096;margin-bottom:2mm">Municípios com porte similar (número de matrículas próximo):</p>
<table>
    <thead><tr><th>Município</th><th class="num">Matrículas</th><th class="num">Receita FUNDEB</th><th class="num">Potencial</th><th class="num">% Ganho</th></tr></thead>
    <tbody>
        <tr style="background:rgba(13,115,119,0.08);font-weight:600">
            <td>{mun['nome']} (você)</td>
            <td class="num">{fmt_n(mun['tot_mat'])}</td>
            <td class="num">{fmt(rec_total)}</td>
            <td class="num" style="color:#0D7377">{fmt(pot_total)}</td>
            <td class="num">{fmt_pct(pct_total)}</td>
        </tr>
        {peers_rows}
    </tbody>
</table>

<h2>Recomendações Priorizadas</h2>
{strat_html}

<div class="divider"></div>

<h2>Plano de Ação Sugerido</h2>

<div class="action-phase">
    <div class="phase-title" style="background:rgba(13,115,119,0.1);color:#0D7377;border:0.3mm solid rgba(13,115,119,0.3)">Fase 1 · Curto Prazo (0–6 meses)</div>
    <ul>{action_list(action_short)}</ul>
</div>

<div class="action-phase">
    <div class="phase-title" style="background:rgba(17,153,142,0.1);color:#11998E;border:0.3mm solid rgba(17,153,142,0.3)">Fase 2 · Médio Prazo (6–12 meses)</div>
    <ul>{action_list(action_mid)}</ul>
</div>

<div class="action-phase">
    <div class="phase-title" style="background:rgba(232,168,56,0.1);color:#E8A838;border:0.3mm solid rgba(232,168,56,0.3)">Fase 3 · Longo Prazo (12–24 meses)</div>
    <ul>{action_list(action_long)}</ul>
</div>

<div class="cta">
    <h3>A APM e o Instituto i10 podem implementar este plano para {mun['nome']}</h3>
    <p>Consultoria especializada: Tecnologia · Dados · Suporte Jurídico · BNCC Computação</p>
    <div class="cta-items">
        <div class="cta-item">Diagnóstico Completo</div>
        <div class="cta-item">Compliance VAAR</div>
        <div class="cta-item">Busca Ativa AEE</div>
        <div class="cta-item">Suporte Jurídico</div>
        <div class="cta-item">BNCC Computação</div>
    </div>
</div>

</body>
</html>"""

    return html


def find_peers(mun, all_muns, n=5):
    target_mat = mun["tot_mat"]
    others = [m for m in all_muns if m["id"] != mun["id"] and m["tot_mat"] > 0]
    others.sort(key=lambda m: abs(m["tot_mat"] - target_mat))
    return others[:n]


def main():
    print("=" * 60)
    print("APM + Instituto i10 — Relatórios Completos FUNDEB 2026")
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

    print(f"\nGerando {total} relatórios PDF completos...")
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
            peers = find_peers(mun, muns, n=5)
            html = generate_full_html(mun, data, rank_pos, len(muns), peers)
            HTML(string=html).write_pdf(filepath)

            generated = i + 1 - skipped
            if generated % 20 == 0 or (i + 1) == total:
                print(f"  [{i+1}/{total}] {mun['nome']} → {filename}")
                gc.collect()
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
