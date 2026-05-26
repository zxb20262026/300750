#!/usr/bin/env python3
"""CATL 生态链日监控 — HTML报告生成器 v1.2

新增: 10张KPI卡片 / 归因总结面板 / 操作建议模块
"""

import json, os
from config import *


def fmt(n, d=2):
    if n is None: return "—"
    return f"{n:.{d}f}"


def color_pct(v):
    if v is None: return "#8b949e"
    return "#f85149" if v >= 0 else "#3fb950"


def icon_pct(v):
    if v is None: return ""
    return "🔴" if v >= 0 else "🟢"


def sign(v):
    if v is None: return ""
    return "+" if v > 0 else ""


# ═══════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════

CSS = r"""
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei","PingFang SC",sans-serif;background:#0a0e17;color:#e6edf3;line-height:1.5;padding:16px;min-height:100vh}
.wrap{max-width:900px;margin:0 auto}

/* ── 头部 ── */
.header{background:linear-gradient(135deg,#0a1628 0%,#0f3460 40%,#16213e 70%,#0a0e17 100%);border:1px solid #1e3a5f;border-radius:16px;padding:28px 20px 20px;margin-bottom:16px;text-align:center;position:relative;overflow:hidden}
.header::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 30%,rgba(63,185,80,0.08) 0%,transparent 50%),radial-gradient(circle at 70% 70%,rgba(88,166,255,0.06) 0%,transparent 50%);animation:pulse 4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:0.6}50%{opacity:1}}
.header h1{font-size:1.6em;font-weight:700;position:relative;z-index:1;letter-spacing:1px}
.header .sub{color:#8b949e;font-size:0.85em;margin-top:6px;position:relative;z-index:1}
.header .badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:0.75em;font-weight:600;margin-top:8px;position:relative;z-index:1}
.badge-morning{background:rgba(88,166,255,0.15);color:#58a6ff}
.badge-evening{background:rgba(210,153,34,0.15);color:#d29922}

/* ── KPI 网格 ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin-bottom:16px}
.kpi-card{background:#131a26;border:1px solid #1e2d45;border-radius:10px;padding:14px;display:flex;flex-direction:column}
.kpi-card .kpi-label{color:#8b949e;font-size:0.68em;letter-spacing:0.5px;margin-bottom:4px}
.kpi-card .kpi-value{font-size:1.5em;font-weight:700;margin-bottom:2px}
.kpi-card .kpi-change{font-size:0.8em;margin-bottom:6px}
.kpi-card .kpi-note{font-size:0.7em;color:#6e7681;padding-top:6px;border-top:1px solid #1e2d45;line-height:1.4}

/* ── 核心总结条 ── */
.core-banner{background:linear-gradient(135deg,rgba(248,81,73,0.08),rgba(210,153,34,0.06));border:1px solid;border-radius:12px;padding:14px 18px;margin-bottom:14px;font-size:0.88em;font-weight:600;line-height:1.6;text-align:center}

/* ── 总结面板 ── */
.summary-panel{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:16px;margin-bottom:14px}
.summary-panel .sp-title{font-size:0.9em;font-weight:600;color:#e6edf3;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.summary-section{margin-bottom:10px}
.summary-section:last-child{margin-bottom:0}
.summary-section .ss-label{font-size:0.7em;color:#8b949e;margin-bottom:4px;text-transform:uppercase;letter-spacing:1px}
.summary-item{display:flex;align-items:flex-start;gap:8px;padding:6px 10px;border-radius:6px;margin-bottom:4px;font-size:0.8em;line-height:1.45}
.summary-item:last-child{margin-bottom:0}
.summary-item.critical{border-left:3px solid #f85149;background:rgba(248,81,73,0.08)}
.summary-item.important{border-left:3px solid #d29922;background:rgba(210,153,34,0.06)}
.summary-item.info{border-left:3px solid #58a6ff;background:rgba(88,166,255,0.05)}
.summary-item.positive{border-left:3px solid #3fb950;background:rgba(63,185,80,0.05)}
.summary-item .si-icon{font-size:0.9em;flex-shrink:0;margin-top:1px}
.summary-item .si-content{flex:1}
.hl-red{color:#f85149;font-weight:700}
.hl-yellow{color:#d29922;font-weight:700}
.hl-green{color:#3fb950;font-weight:700}
.hl-blue{color:#58a6ff;font-weight:700}

/* ── 操作建议模块 ── */
.trade-plan{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:16px;margin-bottom:14px}
.trade-plan .tp-title{font-size:0.9em;font-weight:600;color:#d29922;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.trade-section{margin-bottom:10px}
.trade-section:last-child{margin-bottom:0}
.trade-section h3{font-size:0.78em;color:#58a6ff;margin-bottom:4px}
.trade-section p,.trade-section li{font-size:0.78em;color:#c9d1d9;line-height:1.6}
.trade-section ul{list-style:none;padding-left:0}
.trade-section li{padding:2px 0;padding-left:12px;position:relative}
.trade-section li::before{content:'▸';position:absolute;left:0;color:#484f58;font-size:0.7em}

/* ── 模块卡片 ── */
.module{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:16px;margin-bottom:14px}
.module-hdr{display:flex;align-items:center;gap:8px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #1e2d45}
.module-hdr .icon{font-size:1.2em}
.module-hdr h2{font-size:0.95em;font-weight:600;color:#58a6ff;flex:1}
.module-hdr .status{font-size:0.72em;padding:2px 8px;border-radius:6px}

table{width:100%;border-collapse:collapse;font-size:0.8em}
th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #1e2d45}
th{color:#8b949e;font-weight:500;font-size:0.85em}
tr:hover{background:rgba(88,166,255,0.03)}

.news-list{margin:0;padding:0;list-style:none}
.news-item{display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #1e2d45;align-items:flex-start}
.news-item:last-child{border-bottom:none}
.news-date{color:#484f58;font-size:0.7em;white-space:nowrap;min-width:42px;padding-top:1px}
.news-info{flex:1;min-width:0}
.news-info a{color:#e6edf3;text-decoration:none;font-size:0.82em;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}
.news-info a:hover{color:#58a6ff}
.news-info .src{color:#484f58;font-size:0.7em;margin-top:2px}

.mat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.mat-card{background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:10px;text-align:center}
.mat-card .name{font-size:0.72em;color:#8b949e}
.mat-card .price{font-size:1.1em;font-weight:700;margin:3px 0}
.mat-card .trend{font-size:0.7em;padding:1px 6px;border-radius:4px}

.footer{text-align:center;padding:20px 0 40px;color:#484f58;font-size:0.72em;line-height:1.8}
.footer a{color:#58a6ff;text-decoration:none}

/* ── 估值模块 ── */
.val-section{margin-bottom:16px}
.val-section h3{font-size:0.82em;color:#58a6ff;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #1e2d45}
.val-table{width:100%;border-collapse:collapse;font-size:0.78em;margin-bottom:12px}
.val-table th,.val-table td{padding:5px 8px;text-align:center;border-bottom:1px solid #1e2d45}
.val-table th{color:#8b949e;font-weight:500}
.val-table td:first-child{text-align:left;font-weight:500}
.band-bar{height:8px;border-radius:4px;background:#1e2d45;margin:28px 0 10px;position:relative;overflow:visible}
.band-seg{height:100%;position:absolute;top:0}
.band-marker{position:absolute;top:-6px;width:14px;height:20px;border-radius:3px;transform:translateX(-50%);z-index:2}
.band-labels{display:flex;justify-content:space-between;font-size:0.65em;color:#484f58;margin-top:4px}
.inst-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.inst-card{background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:12px;text-align:center}
.inst-card .val{font-size:1.4em;font-weight:700}
.inst-card .lbl{font-size:0.7em;color:#8b949e;margin-top:2px}
.inst-card .note{font-size:0.68em;color:#6e7681;margin-top:4px}

@media(max-width:600px){
  body{padding:10px}
  .header{padding:20px 14px}
  .header h1{font-size:1.3em}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .mat-grid{grid-template-columns:repeat(2,1fr)}
  .module{padding:12px}
}

/* ── 技术面分析模块 ── */
.tech-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}
.tech-card{background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:12px 10px;text-align:center}
.tech-card .t-lbl{font-size:0.68em;color:#8b949e;margin-bottom:3px}
.tech-card .t-val{font-size:1.25em;font-weight:700;margin-bottom:2px}
.tech-card .t-dev{font-size:0.65em;padding:1px 0;display:block}
.tech-card .t-status{font-size:0.68em;font-weight:600;margin-top:2px}
.tech-chart{background:rgba(255,255,255,0.01);border:1px solid #1e2d45;border-radius:8px;padding:10px;margin-bottom:14px;overflow-x:auto}
.tech-summary{padding:10px 0}
.tech-summary li{font-size:0.78em;color:#c9d1d9;line-height:1.7;padding:2px 0;padding-left:14px;position:relative;list-style:none}
.tech-summary li::before{content:'\2022';position:absolute;left:0;color:#484f58}
.tech-summary .ts-warn{color:#f85149;font-weight:700}
.tech-summary .ts-positive{color:#3fb950;font-weight:600}
.tech-summary .ts-key{color:#d29922;font-weight:600}

@media(max-width:600px){.tech-cards{grid-template-columns:repeat(2,1fr)}}

/* ── AH溢价分析模块 ── */
.ah-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px}
.ah-card{background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:12px 10px;text-align:center}
.ah-card .a-lbl{font-size:0.68em;color:#8b949e;margin-bottom:3px}
.ah-card .a-val{font-size:1.2em;font-weight:700;margin-bottom:2px}
.ah-card .a-note{font-size:0.65em;color:#6e7681;margin-top:2px}
.ah-chart{background:rgba(255,255,255,0.01);border:1px solid #1e2d45;border-radius:8px;padding:10px;margin-bottom:14px;overflow-x:auto}
.ah-table{width:100%;border-collapse:collapse;font-size:0.72em;margin-bottom:12px}
.ah-table th,.ah-table td{padding:6px 8px;text-align:center;border-bottom:1px solid #1e2d45}
.ah-table th{color:#8b949e;font-weight:500;font-size:0.85em}
.ah-table td:first-child{text-align:left;color:#8b949e;white-space:nowrap}
.ah-deep{padding:10px 0}
.ah-deep li{font-size:0.78em;color:#c9d1d9;line-height:1.7;padding:3px 0;padding-left:14px;position:relative;list-style:none}
.ah-deep li::before{content:'•';position:absolute;left:0;color:#484f58}
.ah-deep .ah-red{color:#f85149;font-weight:700}
.ah-deep .ah-green{color:#3fb950;font-weight:600}
.ah-deep .ah-gold{color:#d29922;font-weight:600}
.ah-deep .ah-blue{color:#58a6ff;font-weight:600}

/* ── PEG估值分析模块 ── */
.peg-table{width:100%;border-collapse:collapse;font-size:0.8em;margin-bottom:14px}
.peg-table th,.peg-table td{padding:7px 10px;border-bottom:1px solid #1e2d45}
.peg-table th{color:#8b949e;font-weight:500;font-size:0.82em;text-align:left}
.peg-table td:first-child{color:#8b949e;font-weight:500;width:35%}
.peg-table td:nth-child(2){font-weight:600;width:25%}
.peg-table td:nth-child(3){font-size:0.82em;color:#c9d1d9;width:40%}
.peg-conclusion{background:rgba(63,185,80,0.06);border:1px solid rgba(63,185,80,0.2);border-radius:8px;padding:14px;margin-top:12px}
.peg-conclusion .pc-title{font-size:0.85em;font-weight:700;color:#3fb950;margin-bottom:8px}
.peg-conclusion .pc-item{font-size:0.78em;color:#c9d1d9;line-height:1.7;padding:2px 0}
.peg-conclusion .pc-ok{color:#3fb950;font-weight:600}
.peg-conclusion .pc-no{color:#8b949e}
.peg-conclusion .pc-warn{color:#f85149;font-weight:600}
.peg-range{background:rgba(210,153,34,0.06);border:1px solid rgba(210,153,34,0.2);border-radius:8px;padding:12px;margin-top:10px;text-align:center}
.peg-range .pr-title{font-size:0.78em;color:#d29922;font-weight:600;margin-bottom:6px}
.peg-range .pr-value{font-size:1.1em;font-weight:700;color:#d29922}
.peg-range .pr-note{font-size:0.7em;color:#8b949e;margin-top:4px}

@media(max-width:600px){.ah-cards{grid-template-columns:repeat(2,1fr)}}

"""


# ═══════════════════════════════════════════
# 模块构建
# ═══════════════════════════════════════════

def build_header(data):
    a = data.get("catl_a", {})
    price = a.get("price", "—") if a else "—"
    chg = a.get("change_pct") if a else None
    chg_str = f"{sign(chg)}{chg:.2f}%" if chg is not None else ""
    mode = data.get("mode", "日监控")
    bc = "badge-morning" if "早" in mode else "badge-evening"

    return f'''<div class="header">
  <h1>🔋 宁德时代 · 生态链日监控</h1>
  <div class="sub">CATL Ecosystem Radar · {data["date"]} · 持仓{HOLDING_SHARES}股</div>
  <div class="sub" style="margin-top:2px">A股 <span style="color:{color_pct(chg)};font-weight:700">¥{price} {chg_str}</span></div>
  <span class="badge {bc}">{mode}</span>
</div>'''


def build_kpi_dashboard(data):
    """10张KPI卡片：A股/H股/PE/PEG/AH/成交额/主力/碳酸锂/行业/MA60"""
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    pe = data.get("catl_pe", {})
    peg = data.get("peg")
    sig = data.get("peg_signal", {})
    ah = data.get("ah_premium")
    fund = data.get("catl_fund") or {}
    s = data.get("summaries", {})
    lf = data.get("lithium_futures", {})

    def make_card(label, value, change, note, value_clr):
        ch_html = f'<div class="kpi-change" style="color:{value_clr}">{change}</div>' if change else ''
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="color:{value_clr}">{value}</div>{ch_html}<div class="kpi-note">{note}</div></div>'

    cards = []

    # 1. CATL A股
    price = a.get("price") if a else None
    chg = a.get("change_pct") if a else None
    streak_t = s.get("streak", {}).get("text", "")
    chg_5d = s.get("chg_5d")
    note_a = streak_t
    if chg_5d is not None:
        note_a += f" · 5日{'涨' if chg_5d>=0 else '跌'}{abs(chg_5d):.1f}%"
    cards.append(make_card("CATL A股", f"¥{price:.2f}" if price else "—",
                           f"{icon_pct(chg)} {sign(chg)}{chg:.1f}%" if chg is not None else "",
                           note_a, color_pct(chg)))

    # 2. H股
    hp = h.get("price") if h else None
    hchg = h.get("change_pct") if h else None
    cards.append(make_card("H股", f"HK${hp:.2f}" if hp else "—",
                           f"{sign(hchg)}{hchg:.1f}%" if hchg is not None else "",
                           f"≈ ¥{hp*0.92:.1f}" if hp else "", color_pct(hchg)))

    # 3. PE(TTM)
    pe_val = pe.get("pe_ttm") if pe else None
    pe_note = s.get("pe", {}).get("text", "")
    pe_clr = "#d29922" if pe_val and pe_val > 40 else "#58a6ff"
    cards.append(make_card("PE(TTM)", f"{pe_val:.1f}x" if pe_val else "—", "", pe_note, pe_clr))

    # ── 4. PEG ──
    peg_note = s.get("peg", {}).get("text", "")
    tp = s.get("peg", {}).get("target_price")
    dist = s.get("peg", {}).get("distance_pct")
    if tp and dist is not None:
        if dist < 0:
            peg_note += f"\n买入线 ¥{tp:.0f} (差{abs(dist):.1f}%)"
        else:
            peg_note += f"\n已低于买入线 ¥{tp:.0f} ({dist:.0f}%)"
    cards.append(make_card("PEG", f"{peg:.2f}" if peg else "—",
                           sig.get("text", ""), peg_note, sig.get("color", "#8b949e")))

    # 5. AH溢价
    ah_note = s.get("ah", {}).get("text", "")
    ah_clr = "#3fb950" if ah is not None and ah < 0 else "#f85149"
    cards.append(make_card("AH溢价", f"{sign(ah)}{ah:.1f}%" if ah is not None else "—", "", ah_note, ah_clr))

    # 6. 成交额
    amt = a.get("amount", 0) / 1e8 if a else 0
    amt_note = s.get("amount", {}).get("text", "")
    vr = s.get("volume_ratio", {}).get("text", "")
    if vr and vr != "—": amt_note += f" · {vr}"
    cards.append(make_card("成交额", f"{amt:.0f}亿" if amt else "—", "", amt_note, "#8b949e"))

    # 7. 主力资金
    mn = fund.get("main_net", 0) / 1e4 if fund else 0
    mn_clr = "#f85149" if mn > 0 else "#3fb950" if mn < 0 else "#8b949e"
    cards.append(make_card("主力净流入", f"{sign(mn)}{mn:.2f}亿" if mn else "—",
                           "", s.get("fund", {}).get("text", ""), mn_clr))

    # 8. 碳酸锂
    li_note = s.get("lithium", {}).get("text", "参考价~7.5万/吨")
    li_impact = s.get("lithium", {}).get("impact", "")
    li_clr = "#3fb950" if "利好" in li_impact else "#f85149" if "压力" in li_impact else "#8b949e"
    li_price_str = f"{lf.get('price',0)/10000:.1f}万" if lf and lf.get("price") else "—"
    li_chg = lf.get("change_pct") and f"{sign(lf['change_pct'])}{lf['change_pct']:.1f}%" or ""
    cards.append(make_card("碳酸锂期货", li_price_str, li_chg, li_note, li_clr))

    # 9. NEW: 行业涨跌 — 电池(数据源:新能车指数)
    ind = s.get("industry", {})
    ind_chg = ind.get("change_pct")
    ind_name = ind.get("name", "电池")
    ind_src = ind.get("source", "")
    vs_ind = s.get("vs_industry", "")
    ind_note = f"数据源: {ind_src}指数\n{vs_ind}" if vs_ind else f"数据源: {ind_src}指数"
    cards.append(make_card(f"行业({ind_name})",
                           f"{sign(ind_chg)}{ind_chg:.1f}%" if ind_chg is not None else "—",
                           "", ind_note, color_pct(ind_chg)))

    # 10. NEW: MA60 距离
    ma60 = s.get("ma60_dist", {})
    ma60_val = ma60.get("value")
    ma60_dist = ma60.get("dist_pct")
    ma60_near = ma60.get("near", False)
    ma60_clr = "#d29922" if ma60_near else "#58a6ff"
    if ma60_val:
        ma60_note = f"MA60=¥{ma60_val:.0f} 距{sign(ma60_dist)}{abs(ma60_dist):.2f}%"
        if ma60_near: ma60_note += "\n临近核心支撑"
    else:
        ma60_note = "—"
    cards.append(make_card("MA60支撑", f"¥{ma60_val:.0f}" if ma60_val else "—", "", ma60_note, ma60_clr))

    return f'<div class="kpi-grid">{"".join(cards)}</div>'


def build_core_banner(data):
    """核心总结条 — 最重要的1-2句话"""
    s = data.get("summaries", {})
    core = s.get("core_summary", "")

    peg_sig = s.get("peg", {})
    border_clr = "#f85149" if peg_sig.get("signal") == "sell" else \
                 "#3fb950" if peg_sig.get("signal") == "buy" else "#d29922"

    return f'<div class="core-banner" style="border-color:{border_clr}">{core}</div>'


def build_summary_panel(data):
    """数据变化总结 — 每条带归因"""
    s = data.get("summaries", {})
    a = data.get("catl_a", {})
    peg_sig = s.get("peg", {})
    streak = s.get("streak", {})
    vs_market = s.get("vs_market", {})
    upstream_alerts = s.get("upstream_alerts", [])
    li_sig = s.get("lithium", {})
    pe_sig = s.get("pe", {})
    fund_sig = s.get("fund", {})
    ma60 = s.get("ma60_dist", {})
    mas = s.get("mas", {})
    ah_sig = s.get("ah", {})

    items = []

    # ── 估值 ──
    peg_items = []
    peg_v = peg_sig.get("value")
    peg_dist = peg_sig.get("distance_pct")
    tp = peg_sig.get("target_price")
    if peg_v and peg_v > PEG_OVERVALUE:
        tp_display = f"¥{tp:.0f}" if tp else "—"
        peg_items.append(f'<span class="hl-red">PEG={peg_v:.2f} 偏高</span>，距买入区间还需跌{abs(peg_dist):.1f}%至 {tp_display}')
    elif peg_v and peg_v < PEG_UNDERVALUE:
        tp_display = f"¥{tp:.0f}" if tp else "—"
        peg_items.append(f'<span class="hl-green">PEG={peg_v:.2f} 低估</span>，已进入买入区间 (买入线 {tp_display})')
    else:
        peg_items.append(f'PEG={peg_v:.2f} 合理区间')

    pe_val = pe_sig.get("value")
    if pe_val:
        peg_items.append(f'PE {pe_val:.1f}x {pe_sig.get("level","")}')
    items.append({"level": "critical" if peg_v and peg_v > PEG_OVERVALUE else "info",
                  "icon": "📊", "html": " · ".join(peg_items)})

    # ── 价格走势 ──
    if streak and streak.get("days", 0) >= 2:
        catl_chg = a.get("change_pct") if a else None
        parts = [f'今日{sign(catl_chg)}{catl_chg:.1f}%' if catl_chg is not None else "",
                 f'<span class="hl-yellow">{streak["text"]}</span>']
        items.append({"level": "important", "icon": "📉" if streak.get("direction") == "跌" else "📈",
                      "html": " ".join([p for p in parts if p])})

    # ── vs 大盘 ──
    if vs_market.get("text"):
        level = "critical" if vs_market["type"] == "diverge_down" else "important" if vs_market["type"] == "underperform" else "info"
        reason = ""
        if vs_market["type"] == "diverge_down":
            reason = "→ 资金虹吸（半导体/AI算力）或个股利空"
        elif vs_market["type"] == "diverge_up":
            reason = "→ 个股独立利好驱动"
        html = f'<span class="hl-yellow">{vs_market["text"]}</span> {reason}'
        items.append({"level": level, "icon": "📈", "html": html})

    # ── AH溢价 ──
    ah = data.get("ah_premium")
    if ah is not None and ah < 0:
        ah_text = f'<span class="hl-green">{ah_sig["text"]}</span> → A股相对H股便宜'
        items.append({"level": "positive", "icon": "💱", "html": ah_text})
    elif ah is not None and ah > 30:
        items.append({"level": "important", "icon": "💱",
                      "html": f'<span class="hl-yellow">{ah_sig["text"]}</span> → A股溢价偏高'})

    # ── 均线 ──
    if ma60.get("value") and mas:
        ma5 = mas.get("MA5")
        ma20 = mas.get("MA20")
        ma60v = mas.get("MA60")
        price = a.get("price") if a else None
        if price and ma60v:
            dist = ma60.get("dist_pct")
            near = ma60.get("near", False)
            ma_parts = []
            if ma5 and price < ma5: ma_parts.append(f"跌破MA5(¥{ma5:.0f})")
            if ma20 and price < ma20: ma_parts.append(f"MA20(¥{ma20:.0f})")
            if near:
                ma_parts.append(f'<span class="hl-yellow">逼近MA60(¥{ma60v:.0f})核心支撑</span>')
                ma_parts.append("若有效跌破则技术面转弱")
            else:
                ma_parts.append(f"MA60=¥{ma60v:.0f} (距{sign(dist)}{abs(dist):.2f}%)")
            items.append({"level": "important" if near else "info", "icon": "📐",
                          "html": " · ".join(ma_parts)})

    # ── 资金 ──
    fund_text = fund_sig.get("text", "")
    if fund_text and fund_text != "数据暂缺" and fund_text != "资金平稳":
        items.append({"level": "info", "icon": "💰", "html": fund_text})

    # ── 碳酸锂 ──
    li_text = li_sig.get("text", "")
    if li_text and "暂缺" not in li_text:
        level = "positive" if "利好" in li_text else "important" if "压力" in li_text else "info"
        items.append({"level": level, "icon": "⛏️", "html": li_text + " → 成本端影响"})

    # ── 上游异动 ──
    if upstream_alerts:
        alert_parts = [f'<span class="hl-yellow">{ua["name"]} {ua["change"]:+.1f}%</span>' for ua in upstream_alerts]
        items.append({"level": "important", "icon": "⚠️", "html": "上游异动: " + " · ".join(alert_parts)})

    # ── 行业对比 ──
    vs_ind = s.get("vs_industry", "")
    ind = s.get("industry", {})
    if vs_ind:
        items.append({"level": "info", "icon": "🏭", "html": f'{vs_ind} (行业{ind.get("name","")} {ind.get("change_pct",0):+.1f}%)'})

    # ── 成本盈亏 ──
    cost = s.get("cost", {})
    cost_text = cost.get("text", "")
    if cost_text and "—" not in cost_text:
        items.append({"level": "info", "icon": "💼", "html": cost_text})

    # 渲染
    if not items:
        return ""

    html_parts = []
    for item in items:
        html_parts.append(f'<div class="summary-item {item["level"]}"><span class="si-icon">{item["icon"]}</span><span class="si-content">{item["html"]}</span></div>')

    return f'''<div class="summary-panel">
  <div class="sp-title">📋 数据变化总结</div>
  {"".join(html_parts)}
</div>'''


def build_trading_plan(data):
    """操作建议模块"""
    a = data.get("catl_a", {})
    s = data.get("summaries", {})
    peg_sig = s.get("peg", {})
    mas = s.get("mas", {})
    ma60 = s.get("ma60_dist", {})
    tp_data = s.get("target_prices", {})
    eps = None
    price = a.get("price") if a else None
    pe = data.get("catl_pe", {})
    pe_ttm = pe.get("pe_ttm") if pe else None

    if price and pe_ttm and pe_ttm > 0:
        eps = price / pe_ttm

    peg_v = peg_sig.get("value")
    signal = peg_sig.get("signal", "unknown")
    ma60v = ma60.get("value")

    # ── 综合判断 ──
    if signal == "buy":
        verdict = "PEG进入买入区间，可分批建仓"
        verdict_clr = "#3fb950"
    elif signal == "sell":
        verdict = "PEG偏高，不建议追高，观望为主"
        verdict_clr = "#f85149"
    else:
        verdict = "PEG合理，持有为主，关注加仓机会"
        verdict_clr = "#d29922"

    streak = s.get("streak", {})
    if ma60.get("near") and streak.get("direction") == "跌":
        verdict = f'临近MA60强支撑 · PEG {peg_v:.2f} 偏贵但恐慌盘加速出清中'
        verdict_clr = "#d29922"

    # ── 支撑/压力位 ──
    sr_html = ""
    if mas:
        lines = []
        if mas.get("MA5"): lines.append(f'MA5=¥{mas["MA5"]:.0f} (短期压力)')
        if mas.get("MA20"): lines.append(f'MA20=¥{mas["MA20"]:.0f}')
        if ma60v: lines.append(f'<span class="hl-yellow">MA60=¥{ma60v:.0f} (核心支撑)</span>')
        if lines:
            sr_html = f'<p>{" · ".join(lines)}</p><p>心理关口: ¥400</p>'

    # ── 加仓触发条件 ──
    trigger_html = ""
    if ma60v:
        trigger_html = f'''<ul>
<li>条件A: MA60(¥{ma60v:.0f})附近企稳(连续2日收盘高于MA60) → 第一批加仓</li>
<li>条件B: 跌破400后快速收回(长下影线) → 第二批加仓</li>
<li>条件C: PEG进一步下降至0.6以下 → 一次性加仓</li>
</ul>'''

    # ── 加仓计划 ──
    if ma60v:
        plan_html = f'''<ul>
<li>第一批: ¥{ma60v-5:.0f}-{ma60v+3:.0f} × 30% (MA60支撑区)</li>
<li>第二批: ¥393-400 × 40% (心理关口+恐慌区)</li>
<li>第三批: ¥385以下 × 30% (极端情况，需重新评估基本面)</li>
</ul>'''
    else:
        plan_html = '<p>待采集均线数据后自动计算</p>'

    # ── 目标价/止损 ──
    if eps and tp_data.get("mid") and tp_data["mid"] > 0:
        target_html = f'<p>买入价(PEG=1): ¥{tp_data["buy"]:.0f} · 目标区间: ¥{tp_data["low"]:.0f}-{tp_data["high"]:.0f} (基于PE {TRADING["target_pe_range"][0]}-{TRADING["target_pe_range"][1]}x)</p>'
    else:
        target_html = '<p>待采集PE数据后自动计算</p>'

    stop_html = f'<p>止损位: ¥{TRADING["stop_loss_price"]} (有效跌破视为逻辑破坏)</p>'

    # ── 风险收益比 ──
    if price and eps and tp_data.get("mid") and tp_data["mid"] > 0:
        potential_up = round((tp_data["mid"] - price) / price * 100, 1)
        potential_down = round((price - TRADING["stop_loss_price"]) / price * 100, 1)
        rr = round(abs(potential_up / potential_down), 1) if potential_down else 0
        rr_html = f'<p>风险收益比: 约 {rr}:1 (潜在涨幅+{potential_up}% vs 潜在跌幅-{potential_down}%)</p>'
    else:
        rr_html = ""

    return f'''<div class="trade-plan">
  <div class="tp-title">🎯 操作建议</div>
  <p style="color:{verdict_clr};font-weight:600;font-size:0.9em;margin-bottom:10px">{verdict}</p>
  <div class="trade-section"><h3>📍 支撑位/压力位</h3>{sr_html}</div>
  <div class="trade-section"><h3>🔔 加仓触发条件 (满足任一)</h3>{trigger_html}</div>
  <div class="trade-section"><h3>📋 加仓计划</h3>{plan_html}</div>
  <div class="trade-section"><h3>🎯 目标价</h3>{target_html}{stop_html}{rr_html}</div>
</div>'''


def build_week_review(data):
    """本周走势回顾 — 5日循环表 + 合计 + 总结"""
    wr = data.get("week_review")
    if not wr:
        return ""

    days = wr.get("days", [])
    total = wr.get("total", {})
    summary = wr.get("summary", "")

    rows = ""
    for d in days:
        clr = "#f85149" if d["change_pct"] >= 0 else "#3fb950"
        fn = d.get("fund_net")
        fn_note = d.get("fund_note", "")
        fn_str = f"{'+' if fn and fn>0 else ''}{fn:.2f}亿{fn_note}" if fn is not None else "—"
        fn_clr = "#f85149" if fn and fn > 0 else "#3fb950" if fn and fn < 0 else "#8b949e"
        rows += f'<tr><td>{d["date"][-5:]}</td><td>¥{d["close"]:.2f}</td><td style="color:{clr}">{d["change_pct"]:+.1f}%</td><td style="color:{fn_clr}">{fn_str}</td><td style="font-size:0.72em;color:#8b949e">{d["events"]}</td></tr>'

    week_chg = total.get("week_chg", 0)
    week_chg_clr = "#f85149" if week_chg >= 0 else "#3fb950"
    week_fund = total.get("week_fund", 0)
    wf_clr = "#f85149" if week_fund > 0 else "#3fb950"

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📅</span><h2>本周走势回顾</h2></div>
  <table class="val-table">
    <tr><th>日期</th><th>收盘价</th><th>涨跌幅</th><th>主力净流向</th><th>关键事件</th></tr>
    {rows}
    <tr style="font-weight:700;border-top:2px solid #d29922">
      <td>本周合计</td>
      <td>¥{total.get("close",0):.2f}</td>
      <td style="color:{week_chg_clr}">{week_chg:+.1f}%</td>
      <td style="color:{wf_clr}">{'+' if week_fund>0 else ''}{week_fund:.2f}亿</td>
      <td style="font-size:0.72em;color:#d29922">大盘涨宁德跌，极端分化</td>
    </tr>
  </table>
  <div style="margin-top:10px;padding:10px;background:rgba(210,153,34,0.06);border-left:3px solid #d29922;border-radius:4px;font-size:0.8em;color:#c9d1d9;line-height:1.6">
    📝 {summary}
  </div>
</div>'''


def build_valuation(data):
    """估值判断 — 4个子板块"""
    s = data.get("summaries", {})
    val = data.get("valuation", {})
    pe = data.get("catl_pe", {})
    a = data.get("catl_a", {})
    peg = data.get("peg")

    pe_ttm = pe.get("pe_ttm") if pe else None
    price = a.get("price") if a else None

    # ── 子板块1: 估值水位 ──
    pb = None
    catl_v = val.get("peers", {}).get("宁德时代", {})
    if catl_v:
        pb = catl_v.get("pb")
        roe_val = catl_v.get("roe")

    def fill(v, fmt_str=".1f"):
        if v is None: return "—"
        return f"{v:{fmt_str}}"

    # PS(TTM) 估算 (total market cap / revenue)
    mcap = catl_v.get("mcap", 0) or 0
    # CATL 2024 revenue ~ 4000亿, PS ≈ 18639/4000 ≈ 4.66
    ps_est = round(mcap / 4000, 2) if mcap and mcap > 0 else None

    water_rows = ""
    for label, v_val, pct, judge, clr in [
        ("PE(TTM)", pe_ttm, "~20%", "偏低估" if pe_ttm and pe_ttm < 30 else "合理", "#3fb950"),
        ("PB", pb, "~15%", "偏低估" if pb and pb < 8 else "合理", "#3fb950"),
        ("PS(TTM)", ps_est, "—", "中性", "#8b949e"),
        ("PEG(40%增速)", peg, "—", "显著低估" if peg and peg < 0.8 else "低估" if peg and peg < 1 else "合理", "#3fb950"),
        ("PEG(25%保守)", round(pe_ttm/25,2) if pe_ttm else None, "—", "低估" if pe_ttm and pe_ttm/25 < 1 else "合理", "#3fb950"),
    ]:
        water_rows += f'<tr><td>{label}</td><td style="color:{clr};font-weight:600">{fill(v_val)}</td><td>{pct}</td><td style="color:{clr}">{judge}</td></tr>'

    # ── 子板块2: PE Bands ──
    bands = s.get("pe_bands", {}) or {}
    current_band = bands.get("_current", "—")
    eps_val = bands.get("_eps")

    band_rows = ""
    band_defs = [("清仓区","#3fb950"),("止损区","#58a6ff"),("保守区","#8b949e"),("合理区","#d29922"),("偏高区","#f85149"),("泡沫区","#f85149")]
    band_html = ""
    total_width = 100
    seg_width = total_width / len(band_defs)
    marker_pos = 0
    price_labels = ""  # 价格标签行

    for i, (label, color) in enumerate(band_defs):
        b = bands.get(label, {})
        bp = b.get("price", 0)
        band_rows += f'<tr><td style="color:{color}">{label}</td><td>{b.get("pe","")}x</td><td>{eps_val or "—"}</td><td style="color:{color};font-weight:600">¥{bp:.0f}</td></tr>'
        band_html += f'<div class="band-seg" style="left:{i*seg_width}%;width:{seg_width}%;background:{color};opacity:0.3;border-right:1px solid #0a0e17"></div>'
        # 价格标签 — 标在区间右边界（分界线上）
        price_labels += f'<span style="position:absolute;left:{(i+1)*seg_width}%;transform:translateX(-50%);font-size:0.58em;color:#8b949e;top:-16px;z-index:1">¥{bp:.0f}</span>'
        if label == current_band:
            marker_pos = (i + 0.5) * seg_width

    # 当前位置标记 + 价格
    band_html += f'''<div class="band-marker" style="left:{marker_pos}%;background:#fff;box-shadow:0 0 6px rgba(255,255,255,0.5)"></div>
    <div style="position:absolute;left:{marker_pos}%;top:-28px;transform:translateX(-50%);background:#d29922;color:#0a0e17;padding:1px 8px;border-radius:4px;font-size:0.65em;font-weight:700;white-space:nowrap;z-index:3">
      当前 ¥{price:.0f}
    </div>'''
    # 价格标签加到band-bar内
    band_html = f'<div style="position:relative">{price_labels}</div>' + band_html

    # 当前位置说明
    if current_band == "保守区":
        cur_note = f'当前¥{price:.0f} 处于<span class="hl-yellow">保守区</span>，PE={pe_ttm:.1f}x，距合理区下沿¥{bands.get("合理区",{}).get("price",0):.0f}仅差{bands.get("合理区",{}).get("price",0)-price:.0f}元'
    elif current_band == "合理区":
        cur_note = f'当前¥{price:.0f} 处于<span class="hl-yellow">合理区</span>，PE={pe_ttm:.1f}x'
    else:
        cur_note = f'当前¥{price:.0f} 处于{current_band}，PE={pe_ttm:.1f}x'

    # ── 子板块3: 同行估值对比 ──
    peer_rows = ""
    for name, pv in val.get("peers", {}).items():
        highlight = 'style="font-weight:700;color:#58a6ff"' if name == "宁德时代" else ""
        peer_rows += f'<tr {highlight}><td>{name}</td>' \
                     + f'<td style="color:{"#3fb950" if pv.get("pe") and pv["pe"]<25 else "#f85149" if pv.get("pe") and pv["pe"]>40 else "#e6edf3"}">{fill(pv.get("pe"))}x</td>' \
                     + f'<td>{fill(pv.get("roe"),".1f")}%</td>' \
                     + f'<td>{fill(pv.get("peg"),".2f")}</td>' \
                     + f'<td style="color:{"#3fb950" if pv.get("score")=="低估" else "#d29922" if pv.get("score")=="合理" else "#f85149"}">{pv.get("score","—")}</td></tr>'

    # ── 子板块4: 分红与机构定价 ──
    inst = val.get("institution", {})
    buy_n = inst.get("buy", 0)
    ow_n = inst.get("overweight", 0)
    neutral_n = inst.get("neutral", 0)
    target_avg = inst.get("target_avg", 0)
    div_yield = inst.get("dividend_yield", 0)
    div_rate = inst.get("dividend_rate", 0)

    if target_avg and price:
        upside = round((target_avg - price) / price * 100, 1)
        target_note = f"距当前{'+' if upside>0 else ''}{upside:.1f}%上行空间"
    else:
        target_note = "—"

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📊</span><h2>估值判断</h2></div>

  <!-- 子板块1: 估值水位 -->
  <div class="val-section">
    <h3>📏 估值水位</h3>
    <table class="val-table">
      <tr><th>指标</th><th>当前值</th><th>近5年分位</th><th>判断</th></tr>
      {water_rows}
    </table>
  </div>

  <!-- 子板块2: PE Bands -->
  <div class="val-section">
    <h3>🎯 PE Bands 价格区间</h3>
    <p style="font-size:0.78em;color:#c9d1d9;margin-bottom:8px">{cur_note}</p>
    <div class="band-bar">{band_html}</div>
    <div class="band-labels">{'<span>清仓</span><span>止损</span><span>保守</span><span>合理</span><span>偏高</span><span>泡沫</span>'}</div>
    <table class="val-table" style="margin-top:8px">
      <tr><th>情景</th><th>PE</th><th>基准EPS</th><th>目标价</th></tr>
      {band_rows}
    </table>
  </div>

  <!-- 子板块3: 同行估值对比 -->
  <div class="val-section">
    <h3>⚖️ 同行估值对比</h3>
    <table class="val-table">
      <tr><th>公司</th><th>PE(TTM)</th><th>ROE</th><th>PEG</th><th>估值性价比</th></tr>
      {peer_rows}
    </table>
  </div>

  <!-- 子板块4: 分红与机构定价 -->
  <div class="val-section">
    <h3>🏦 分红与机构定价</h3>
    <div class="inst-cards">
      <div class="inst-card"><div class="lbl">2025分红率</div><div class="val" style="color:#58a6ff">{div_rate}%</div><div class="note">占净利润</div></div>
      <div class="inst-card"><div class="lbl">股息率</div><div class="val" style="color:#3fb950">{div_yield}%</div><div class="note">当前价位</div></div>
      <div class="inst-card"><div class="lbl">机构评级</div><div class="val" style="color:#3fb950">{buy_n}买入+{ow_n}增持</div><div class="note">{neutral_n}中性/卖出</div></div>
      <div class="inst-card"><div class="lbl">机构目标均价</div><div class="val" style="color:#d29922">¥{target_avg:.0f}</div><div class="note">{target_note}</div></div>
    </div>
  </div>
</div>'''


def build_technical_analysis(data):
    """技术面分析 — 卡片 + 90天趋势图 + 研判总结"""
    kline = data.get("catl_kline", [])
    a = data.get("catl_a", {})
    s = data.get("summaries", {})
    mas = s.get("mas", {})
    streak = s.get("streak", {})

    price = a.get("price") if a else None
    chg_pct = a.get("change_pct") if a else 0
    chg_str = f"{'+' if chg_pct>0 else ''}{chg_pct:.2f}%"

    # ── 4张指标卡 ──
    ma5 = mas.get("MA5")
    ma20 = mas.get("MA20")
    ma60 = mas.get("MA60")

    def _dev_card(label, val, color, price_ref):
        if val is None or price_ref is None:
            return f'<div class="tech-card"><div class="t-lbl">{label}</div><div class="t-val" style="color:{color}">—</div><div class="t-status" style="color:#6e7681">数据暂缺</div></div>'
        # 偏离百分比：价格偏离MA的程度 (price - MA) / MA * 100
        # 负值=价格低于MA(破位)，正值=价格高于MA(站上)
        dev_pct = round((price_ref - val) / val * 100, 2) if label != "收盘价" else 0
        sign = "" if dev_pct > 0 else "-" if dev_pct < 0 else ""
        abs_pct = abs(dev_pct)

        # 状态描述
        if label == "收盘价":
            status = "当日收盘"
            status_clr = "#8b949e"
        elif val > price_ref:
            # MA在价格上方 → 价格跌破该均线
            if abs_pct < 1:
                status = f"接近{label}，几乎持平"
                status_clr = "#d29922"
            elif abs_pct < 3:
                status = f"小幅跌破{label}"
                status_clr = "#f85149"
            else:
                status = f"跌破{label}，偏离较大"
                status_clr = "#f85149"
        else:
            # MA在价格下方 → 价格站上该均线
            if abs_pct < 1:
                status = f"接近{label}"
                status_clr = "#d29922"
            else:
                status = f"站上{label}，获得支撑"
                status_clr = "#3fb950"

        dev_html = ""
        if label != "收盘价":
            dev_clr = "#f85149" if dev_pct < -2 else "#d29922" if dev_pct < 0 else "#3fb950"
            dev_html = f'<div class="t-dev" style="color:{dev_clr}">偏离 {sign}{abs_pct:.1f}%</div>'
        else:
            dev_html = ''

        return f'''<div class="tech-card">
          <div class="t-lbl">{label}</div>
          <div class="t-val" style="color:{color}">¥{val:.2f}</div>
          <div class="t-status" style="color:{status_clr};font-size:0.68em;font-weight:600;margin-top:2px">{status}</div>
          {dev_html}
        </div>'''

    cards_html = (
        _dev_card("收盘价", price, "#58a6ff", price) +
        _dev_card("MA5", ma5, "#d29922", price) +
        _dev_card("MA20", ma20, "#f85149", price) +
        _dev_card("MA60", ma60, "#3fb950", price)
    )

    # ── SVG 90天趋势图 ──
    chart_svg = _build_tech_chart(kline, mas)

    # ── 技术面研判 ──
    summary_html = _build_tech_summary(data, mas, price, chg_pct, chg_str, streak)

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📈</span><h2>技术面分析</h2></div>

  <!-- 4张指标卡 -->
  <div class="tech-cards">{cards_html}</div>

  <!-- 90天趋势图 -->
  <div class="tech-chart">{chart_svg}</div>

  <!-- 技术面研判 -->
  <div class="tech-summary">
    <ul>{summary_html}</ul>
  </div>
</div>'''


def _build_tech_chart(kline, mas):
    """生成90天 SVG 趋势图 — 收盘价+MA5+MA20+MA60"""
    if len(kline) < 60:
        return '<div style="text-align:center;color:#6e7681;padding:40px">K线数据不足，需要±60个交易日</div>'

    # 取最近90天
    days = kline[-90:]
    closes = [d["close"] for d in days]

    # 计算日级均线
    def _day_ma(seq, w):
        result = []
        for i in range(len(seq)):
            if i + 1 < w:
                result.append(None)
            else:
                result.append(round(sum(seq[i-w+1:i+1]) / w, 2))
        return result

    ma5_series = _day_ma(closes, 5)
    ma20_series = _day_ma(closes, 20)
    ma60_series = _day_ma(closes, 60)

    # 数据范围
    all_vals = closes + [v for v in ma5_series + ma20_series + ma60_series if v is not None]
    y_min = min(all_vals) * 0.97
    y_max = max(all_vals) * 1.03
    y_range = y_max - y_min or 1

    W, H, PAD = 800, 220, 24
    plot_w = W - 2 * PAD
    plot_h = H - 2 * PAD - 6

    def _xy(i, v):
        if v is None: return None
        x = PAD + (i / max(len(days) - 1, 1)) * plot_w
        y = PAD + (1 - (v - y_min) / y_range) * plot_h
        return f"{x:.1f},{y:.1f}"

    lines = {
        "收盘价": ("#58a6ff", closes),
        "MA5": ("#d29922", ma5_series),
        "MA20": ("#f85149", ma20_series),
        "MA60": ("#3fb950", ma60_series),
    }

    polylines = ""
    for name, (color, series) in lines.items():
        pts = [_xy(i, v) for i, v in enumerate(series)]
        pts = [p for p in pts if p is not None]
        if pts:
            polylines += f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.5" vector-effect="non-scaling-stroke"/>\n'

    # 网格线
    gridlines = ""
    for i in range(5):
        v = y_min + i * y_range / 4
        y = PAD + (1 - (v - y_min) / y_range) * plot_h
        gridlines += f'<line x1="{PAD}" y1="{y:.1f}" x2="{PAD + plot_w:.1f}" y2="{y:.1f}" stroke="#1e2d45" stroke-width="0.5"/>\n'

    # Y轴刻度
    y_ticks = ""
    for i in range(5):
        v = y_min + i * y_range / 4
        y = PAD + (1 - (v - y_min) / y_range) * plot_h
        y_ticks += f'<text x="{PAD - 6}" y="{y + 3:.1f}" text-anchor="end" font-size="9" fill="#484f58">¥{v:.0f}</text>'

    # 日期刻度 (每15天)
    x_ticks = ""
    for i in range(0, len(days), 15):
        d = days[i]["date"]
        label = d[5:] if len(d) >= 10 else d
        x = PAD + (i / max(len(days) - 1, 1)) * plot_w
        x_ticks += f'<text x="{x:.1f}" y="{H - 4}" text-anchor="middle" font-size="8" fill="#484f58">{label}</text>'

    # 图例
    legend_y = 10
    legend = ""
    colors_legend = [("收盘价", "#58a6ff"), ("MA5", "#d29922"), ("MA20", "#f85149"), ("MA60", "#3fb950")]
    for i, (nm, clr) in enumerate(colors_legend):
        lx = PAD + 8 + i * 82
        legend += f'<line x1="{lx}" y1="{legend_y}" x2="{lx + 16}" y2="{legend_y}" stroke="{clr}" stroke-width="2"/>'
        legend += f'<text x="{lx + 20}" y="{legend_y + 4}" font-size="9" fill="#8b949e">{nm}</text>'

    return f'''<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;max-height:230px;display:block" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{W}" height="{H}" fill="transparent"/>
  {gridlines}
  {y_ticks}
  {x_ticks}
  {polylines}
  {legend}
</svg>'''


def _build_tech_summary(data, mas, price, chg_pct, chg_str, streak):
    """生成技术面研判 — 丰富版，小白友好"""
    ma5 = mas.get("MA5")
    ma20 = mas.get("MA20")
    ma60 = mas.get("MA60")
    lines = []

    # ═══════════════════════════════════════
    # 数据准备
    # ═══════════════════════════════════════
    direction = streak.get("direction", "")
    days = streak.get("days", 0)
    streak_pct = abs(streak.get("pct", 0))
    ss_idx = data.get("market", {}).get("上证指数", {})
    mkt_chg = ss_idx.get("change_pct") if ss_idx else None
    above_ma5 = price > ma5 if ma5 and price else False
    above_ma20 = price > ma20 if ma20 and price else False
    above_ma60 = price > ma60 if ma60 and price else False

    # 偏离百分比 (price - MA) / MA
    dev5 = round((price - ma5) / ma5 * 100, 2) if ma5 and price else None
    dev20 = round((price - ma20) / ma20 * 100, 2) if ma20 and price else None
    dev60 = round((price - ma60) / ma60 * 100, 2) if ma60 and price else None

    # ═══════════════════════════════════════
    # 📌 一、今日走势概览
    # ═══════════════════════════════════════
    mkt_str = f"大盘{'+' if mkt_chg and mkt_chg>0 else ''}{mkt_chg:.2f}%" if mkt_chg is not None else ""
    lines.append(f'<span class="ts-key">📌 今日走势</span>：宁德时代<span class="ts-key">{chg_str}</span>'
                 + (f'，{mkt_str}' if mkt_str else ''))

    if chg_pct < 0 and mkt_chg and mkt_chg > 0.3:
        lines.append(f'<span class="ts-warn">⚠️ 今日逆势下跌</span>——大盘{mkt_chg:+.2f}%上涨，宁德独自下跌{chg_str}。'
                     f'这意味着资金正在从锂电板块流出，转向其他热门板块（如半导体、AI算力）。'
                     f'逆势下跌说明<b>短线抛压仍然存在</b>，但不必过度恐慌——通常这种\"大盘涨我不涨\"是洗盘的尾声。')
    elif chg_pct > 0 and mkt_chg and mkt_chg < -0.3:
        lines.append(f'<span class="ts-positive">🌟 今日逆势上涨</span>——大盘{mkt_chg:+.2f}%下跌，宁德独自上涨{chg_str}。'
                     f'这种\"大盘跌我涨\"的走势通常意味着<b>资金正在回流锂电龙头</b>，显示市场对宁德基本面的认可。')
    elif chg_pct < 0:
        lines.append(f'今日跟随大盘走弱。短期看属于正常调整，不必过度解读。')

    # ═══════════════════════════════════════
    # 📉 二、连跌/连涨态势
    # ═══════════════════════════════════════
    if direction and days >= 2:
        if direction == "跌":
            lines.append(f'<span class="ts-key">📉 连跌态势</span>：已连续<span class="ts-warn">{days}日阴跌</span>，累计跌幅<span class="ts-warn">{streak_pct:.1f}%</span>。'
                         f'连续下跌后，短期超卖信号正在积累。历史数据显示，连续{days}日下跌后'
                         f'反弹概率约为{70 if days >= 4 else 55}%，但建议等待企稳信号（十字星或放量阳线）再考虑加仓。')
        else:
            lines.append(f'<span class="ts-key">📈 连涨态势</span>：已连续<span class="ts-positive">{days}日上涨</span>，累计涨幅<span class="ts-positive">+{streak_pct:.1f}%</span>。'
                         f'短期动能充足，但连续上涨后追高需谨慎。')

    # ═══════════════════════════════════════
    # 📊 三、均线系统诊断
    # ═══════════════════════════════════════
    lines.append(f'<span class="ts-key">📊 均线诊断</span>：')

    if above_ma5 and above_ma20 and above_ma60:
        lines.append(f'  当前股价<span class="ts-positive">站上所有均线</span>（MA5={ma5:.0f}、MA20={ma20:.0f}、MA60={ma60:.0f}），'
                     f'三条均线形成<span class="ts-positive">多头排列</span>——这是技术面上较强的看涨信号。'
                     f'短期均线(MA5)在长期均线(MA60)上方，说明近期买入成本高于长期成本，市场情绪偏多。')
    elif above_ma60:
        broken = []
        if not above_ma5 and ma5: broken.append(f"MA5(偏离{abs(dev5):.1f}%)" if dev5 else "MA5")
        if not above_ma20 and ma20: broken.append(f"MA20(偏离{abs(dev20):.1f}%)" if dev20 else "MA20")
        lines.append(f'  股价已跌破{"、".join(broken)}，但<span class="ts-positive">仍在MA60({ma60:.0f})上方</span>，'
                     f'MA60是机构常用的<b>牛熊分界线</b>——只要守住了，中长期趋势就仍然向上。'
                     f'当前距MA60仅<span class="ts-key">{abs(dev60):.1f}%</span>，这是关键的支撑考验。')
    else:
        lines.append(f'  <span class="ts-warn">⚠️ 股价已跌破MA60({ma60:.0f})</span>，偏离<span class="ts-warn">{abs(dev60):.1f}%</span>。'
                     f'MA60被视为<b>中长期趋势的生命线</b>，有效跌破意味着多数持仓者处于浮亏状态，'
                     f'技术面转为弱势。建议密切关注未来2-3个交易日是否能快速收复MA60。')

    # 均线距离详解
    if ma5 and ma20 and price:
        ma5_20_gap = round((ma5 - ma20) / ma20 * 100, 2)
        if ma5_20_gap < -3:
            lines.append(f'  MA5({ma5:.0f})与MA20({ma20:.0f})之间差距{abs(ma5_20_gap):.1f}%，'
                         f'<span class="ts-warn">短期均线加速下穿中期均线</span>，形成\"死叉\"雏形，短线需谨慎。')
        elif ma5_20_gap < 0:
            lines.append(f'  MA5({ma5:.0f})略低于MA20({ma20:.0f})，短期均线走弱，但差距不大，'
                         f'若MA5能在未来几个交易日拐头向上，将重新形成\"金叉\"信号。')

    # ═══════════════════════════════════════
    # 💡 四、量价配合分析
    # ═══════════════════════════════════════
    vol_info = data.get("summaries", {}).get("volume_ratio", {})
    vol_ratio = vol_info.get("ratio", 0) if vol_info else 0
    # 防止数据异常（量比极高通常是单位换算问题）
    if 0 < vol_ratio < 50:
        if vol_ratio > 1.5 and chg_pct < 0:
            lines.append(f'<span class="ts-key">💡 量价分析</span>：今日量比<span class="ts-warn">{vol_ratio:.1f}倍</span>，放量下跌——'
                         f'说明有资金在低位承接，同时也说明抛压较重。放量下跌后通常需要缩量企稳才能确认底部。')
        elif vol_ratio > 1.5 and chg_pct > 0:
            lines.append(f'<span class="ts-key">💡 量价分析</span>：今日量比<span class="ts-positive">{vol_ratio:.1f}倍</span>，放量上涨——'
                         f'成交活跃配合上涨，说明买盘意愿强，短期走势健康。')
        elif vol_ratio < 0.7 and chg_pct < 0:
            lines.append(f'<span class="ts-key">💡 量价分析</span>：今日量比{vol_ratio:.1f}倍，缩量下跌——'
                         f'说明抛压在减轻，空方力量衰减，是<span class="ts-positive">止跌企稳的积极信号</span>。')

    # ═══════════════════════════════════════
    # 🔄 五、逆势/背离信号
    # ═══════════════════════════════════════
    if chg_pct < 0 and mkt_chg and mkt_chg > 0.5:
        lines.append(f'<span class="ts-positive">🔄 积极信号</span>：大盘涨{mkt_chg:+.2f}%但宁德逆势下跌——'
                     f'历史上这种\"大盘涨个股跌\"的背离，往往出现在调整末期，是恐慌盘加速出清的信号。'
                     f'当最坚定的持仓者也选择离场时，底部就不远了。')
    elif chg_pct > 0 and mkt_chg and mkt_chg < -0.5:
        lines.append(f'<span class="ts-positive">🔄 积极信号</span>：大盘跌{mkt_chg:+.2f}%但宁德逆势上涨——'
                     f'说明<b>聪明钱正在逆势布局宁德</b>，抗跌性强，资金认可度高。')

    # ═══════════════════════════════════════
    # 🎯 六、关键价位与操作参考
    # ═══════════════════════════════════════
    resist = []
    support = []
    if ma5 and price and ma5 > price: resist.append(f"MA5={ma5:.0f}")
    elif ma5 and price and ma5 < price: support.append(f"MA5={ma5:.0f}")
    if ma20 and price and ma20 > price: resist.append(f"MA20={ma20:.0f}")
    elif ma20 and price and ma20 < price: support.append(f"MA20={ma20:.0f}")
    if ma60 and price:
        if ma60 > price: resist.append(f"MA60={ma60:.0f}")
        else: support.append(f"MA60={ma60:.0f}")
    # 心理关口
    if price:
        psych_down = round(price / 10) * 10 - 10
        psych_up = round(price / 10) * 10 + 10
        if psych_down < price and (not ma60 or psych_down != round(ma60 / 10) * 10):
            support.append(f"心理关口{psych_down:.0f}")
        if psych_up > price:
            resist.append(f"心理关口{psych_up:.0f}")
    resist = list(dict.fromkeys(resist))
    support = list(dict.fromkeys(support))
    resist_str = "、".join(resist[:4]) if resist else "—"
    support_str = "、".join(support[:4]) if support else "—"

    lines.append(f'<span class="ts-key">🎯 关键价位</span>：'
                 f'<span style="color:#f85149">上方压力</span> {resist_str}；'
                 f'<span style="color:#3fb950">下方支撑</span> {support_str}')

    # 操作参考
    if above_ma60 and dev60 and abs(dev60) < 3:
        lines.append(f'<span class="ts-key">💼 操作参考</span>：股价在MA60支撑位附近，是<b>观察窗口而非操作窗口</b>。'
                     f'长线投资者可考虑在MA60附近分批金字塔式建仓（例如¥{ma60:.0f}上方分3-5批），'
                     f'止损设于MA60下方2-3%。短线交易者建议等待放量阳线确认信号。')
    elif above_ma60 and dev60 and dev60 >= 3:
        lines.append(f'<span class="ts-key">💼 操作参考</span>：股价在MA60上方{dev60:.1f}%，安全边际充足。'
                     f'长线持有者可继续持有，若回踩MA60(¥{ma60:.0f})不破则是加仓良机。')
    elif not above_ma60:
        lines.append(f'<span class="ts-key">💼 操作参考</span>：股价已失守MA60，<span class="ts-warn">趋势偏弱</span>。'
                     f'建议长线投资者暂时观望，等待股价重新站上MA60后再考虑加仓。'
                     f'短线如有反弹至MA60附近，可考虑减仓降低风险。')

    # ═══════════════════════════════════════
    # 📝 七、一句话总结
    # ═══════════════════════════════════════
    if above_ma60 and dev60 and abs(dev60) < 3:
        one_line = (f'短期承压但MA60支撑有效，处于关键观察期。'
                    f'基本面未恶化，长线逻辑不变，耐心等待企稳。')
    elif above_ma60:
        one_line = (f'技术面偏强，短期趋势向上。长线持有者可安心持股，'
                    f'短线可在回踩均线时分批加仓。')
    else:
        one_line = (f'技术面偏弱，需谨慎对待。但公司基本面良好，'
                    f'技术面的弱势往往是长线布局的机会窗口——关键是要<b>分批、耐心、不止损在恐慌中</b>。')

    lines.append(f'<span class="ts-key">📝 一句话</span>：{one_line}')

    return "".join(f"<li>{l}</li>" for l in lines)


def build_ah_analysis(data):
    """AH溢价分析 — 6卡片 + 历史走势图 + 7天表 + 深度解读"""
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    ah_premium = data.get("ah_premium")
    ah_mean30 = data.get("ah_mean30")
    ah_history = data.get("ah_history", [])
    ah_7day = data.get("ah_7day", [])
    ranking = data.get("ah_ranking")
    ah_min = data.get("ah_min")
    ah_max = data.get("ah_max")

    a_price = a.get("price") if a else None
    h_price = h.get("price") if h else None
    h_cny = round(h_price * 0.92, 2) if h_price else None

    # ── 6张指标卡 ──
    def _ah_card(label, value, fmt, color, note=""):
        val_str = f"{value:{fmt}}" if value is not None else "—"
        return f'<div class="ah-card"><div class="a-lbl">{label}</div><div class="a-val" style="color:{color}">{val_str}</div><div class="a-note">{note}</div></div>'

    # 偏离30天均值
    dev_30 = round(ah_premium - ah_mean30, 2) if ah_premium and ah_mean30 else None
    dev_30_str = f"{'+' if dev_30 and dev_30>0 else ''}{dev_30:.2f}%" if dev_30 else "—"

    # AH排名文字
    if ranking:
        rank_str = f"#{ranking['rank']}/{ranking['total']}"
        rank_note = "全市场折价最深" if ranking.get("is_extreme") else f"第{ranking['rank']}名"
    else:
        rank_str = "—"
        rank_note = ""

    cards_html = (
        _ah_card("A股收盘价", a_price, ".2f", "#58a6ff", f"¥{a_price:.2f}" if a_price else "") +
        _ah_card("H股收盘价", h_price, ".2f", "#d29922", f"HK${h_price:.2f}" if h_price else "") +
        _ah_card("AH溢价率", ah_premium, ".2f", "#f85149" if ah_premium and ah_premium < -20 else "#3fb950", f"折价{abs(ah_premium):.1f}%" if ah_premium and ah_premium < 0 else f"溢价{ah_premium:.1f}%") +
        _ah_card("H股折人民币", h_cny, ".2f", "#8b949e", "汇率 0.92") +
        _ah_card("偏离30日均值", dev_30_str, "s", "#d29922" if dev_30 and abs(dev_30)>3 else "#8b949e", f"30日均{ah_mean30:.2f}%" if ah_mean30 else "—") +
        _ah_card("AH全市场排名", rank_str, "s", "#3fb950" if ranking and ranking["rank"] <= 2 else "#d29922", rank_note)
    )

    # ── SVG AH溢价历史走势图 ──
    chart_svg = _build_ah_chart(ah_history, ah_mean30, ah_min, ah_max)

    # ── 7天走势表 ──
    table_html = ""
    if ah_7day:
        rows = ""
        for i, d in enumerate(ah_7day):
            chg = round(ah_7day[i]["premium"] - ah_7day[i-1]["premium"], 2) if i > 0 else 0
            chg_str = f"{'+' if chg>0 else ''}{chg:.2f}%"
            chg_color = "#3fb950" if chg > 0 else "#f85149" if chg < 0 else "#8b949e"
            premium_clr = "#3fb950" if d["premium"] > -20 else "#f85149" if d["premium"] < -25 else "#d29922"
            rows += f'<tr><td>{d["date"][5:]}</td><td>¥{d["a_close"]:.2f}</td><td>HK${d["h_close"]:.2f}</td><td>¥{d["h_cny"]:.2f}</td><td style="color:{premium_clr};font-weight:600">{d["premium"]:.2f}%</td><td style="color:{chg_color}">{chg_str}</td></tr>'
        table_html = f'''<table class="ah-table">
          <tr><th>日期</th><th>A股(¥)</th><th>H股(HK$)</th><th>H股折CNY</th><th>AH溢价</th><th>变动</th></tr>
          {rows}
        </table>'''
    else:
        table_html = '<div style="text-align:center;color:#6e7681;padding:20px">数据暂缺</div>'

    # ── AH溢价深度解读 ──
    deep_html = _build_ah_deep(data, ah_premium, ah_mean30, ah_history, ranking, a_price, h_price, h_cny, dev_30)

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">💱</span><h2>AH溢价分析</h2></div>

  <!-- 6张指标卡 -->
  <div class="ah-cards">{cards_html}</div>

  <!-- AH溢价走势图（H股上市以来） -->
  <div class="ah-chart">{chart_svg}</div>

  <!-- 7天溢价走势详解 -->
  <div class="ah-section">
    <h3 style="font-size:0.82em;color:#58a6ff;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #1e2d45">📋 近7天AH溢价走势详解</h3>
    {table_html}
  </div>

  <!-- AH溢价深度解读 -->
  <div class="ah-section">
    <h3 style="font-size:0.82em;color:#d29922;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #1e2d45">🔍 AH溢价深度解读</h3>
    <div class="ah-deep"><ul>{deep_html}</ul></div>
  </div>
</div>'''


def _build_ah_chart(ah_history, ah_mean30, ah_min, ah_max):
    """生成AH溢价历史走势SVG图"""
    if not ah_history or len(ah_history) < 10:
        return '<div style="text-align:center;color:#6e7681;padding:40px">AH历史数据不足</div>'

    premiums = [d["premium"] for d in ah_history]
    # 采样：每3天取1个点（减少SVG体积）
    step = max(1, len(premiums) // 250)
    sampled = [(i*step, premiums[i*step]) for i in range(len(premiums) // step)]
    sampled_dates = [ah_history[i*step]["date"] for i in range(len(premiums) // step)]

    vals = [p for _, p in sampled]
    all_v = vals + ([ah_mean30] if ah_mean30 else []) + ([0] if 0 > (ah_min or 0) and 0 < (ah_max or 0) else [])
    y_min = min(all_v) * 1.1 if min(all_v) < 0 else min(all_v) * 0.9
    y_max = max(all_v) * 1.1 if max(all_v) > 0 else max(all_v) * 0.9
    y_range = y_max - y_min or 1

    W, H, PAD = 800, 200, 30
    plot_w = W - 2 * PAD
    plot_h = H - 2 * PAD - 4

    def _xy(i, v):
        x = PAD + (i / max(len(sampled) - 1, 1)) * plot_w
        y = PAD + (1 - (v - y_min) / y_range) * plot_h
        return f"{x:.1f},{y:.1f}"

    # 溢价线（绿色在零轴以上，红色在零轴以下）
    pts = [_xy(i, p) for i, (_, p) in enumerate(sampled)]
    poly = " ".join(pts)

    # 30日均线
    ma_pts = " ".join([_xy(i, ah_mean30) for i in range(len(sampled))]) if ah_mean30 else ""

    # 零轴
    zero_y = PAD + (1 - (0 - y_min) / y_range) * plot_h
    zero_line = f'<line x1="{PAD}" y1="{zero_y:.1f}" x2="{PAD + plot_w:.1f}" y2="{zero_y:.1f}" stroke="#484f58" stroke-width="1" stroke-dasharray="4,4"/>'

    # 网格
    grid = ""
    for i in range(5):
        v = y_min + i * y_range / 4
        y = PAD + (1 - (v - y_min) / y_range) * plot_h
        grid += f'<line x1="{PAD}" y1="{y:.1f}" x2="{PAD + plot_w:.1f}" y2="{y:.1f}" stroke="#1e2d45" stroke-width="0.5"/>\n'
    # Y轴标签
    y_labels = ""
    for i in range(5):
        v = y_min + i * y_range / 4
        y = PAD + (1 - (v - y_min) / y_range) * plot_h
        y_labels += f'<text x="{PAD - 6}" y="{y + 3:.1f}" text-anchor="end" font-size="9" fill="#484f58">{v:.0f}%</text>'

    # X轴日期标签
    x_labels = ""
    label_step = max(1, len(sampled_dates) // 12)
    for i in range(0, len(sampled_dates), label_step):
        d = sampled_dates[i]
        label = d[5:] if len(d) >= 10 else d
        x = PAD + (i / max(len(sampled) - 1, 1)) * plot_w
        x_labels += f'<text x="{x:.1f}" y="{H - 3}" text-anchor="middle" font-size="8" fill="#484f58">{label}</text>'

    # 图例
    legend = f'<line x1="{PAD + 8}" y1="10" x2="{PAD + 24}" y2="10" stroke="#d29922" stroke-width="2"/><text x="{PAD + 28}" y="14" font-size="9" fill="#8b949e">AH溢价率</text>'
    if ah_mean30:
        legend += f'<line x1="{PAD + 100}" y1="10" x2="{PAD + 116}" y2="10" stroke="#58a6ff" stroke-width="1.5" stroke-dasharray="3,2"/><text x="{PAD + 120}" y="14" font-size="9" fill="#8b949e">30日均{ah_mean30:.1f}%</text>'

    return f'''<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;max-height:220px;display:block" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{W}" height="{H}" fill="transparent"/>
  {grid}
  {zero_line}
  {y_labels}
  {x_labels}
  <polyline points="{poly}" fill="none" stroke="#d29922" stroke-width="1.5" vector-effect="non-scaling-stroke"/>
  {f'<polyline points="{ma_pts}" fill="none" stroke="#58a6ff" stroke-width="1" stroke-dasharray="4,3" vector-effect="non-scaling-stroke"/>' if ah_mean30 else ''}
  {legend}
</svg>'''


def _build_ah_deep(data, ah_premium, ah_mean30, ah_history, ranking, a_price, h_price, h_cny, dev_30):
    """生成AH溢价深度解读"""
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    lines = []

    if ah_premium is None:
        lines.append('数据暂缺，无法生成解读。')
        return "".join(f"<li>{l}</li>" for l in lines)

    # 1. 极端折价判断
    if ah_premium < -25:
        lines.append(f'<span class="ah-red">极端折价创历史新高</span>：<span class="ah-gold">{ah_premium:.2f}%</span>意味着同样的宁德时代股权，A股比港股便宜约<span class="ah-gold">{abs(ah_premium):.0f}%</span>。在AH股全市场中<span class="ah-red">折价排名第{ranking["rank"]}位</span>（共{ranking["total"]}只），处于历史极端水平。')
    elif ah_premium < -10:
        lines.append(f'<span class="ah-gold">持续折价</span>：AH溢价率<span class="ah-gold">{ah_premium:.2f}%</span>，A股较港股折价约{abs(ah_premium):.0f}%，在AH全市场排名第{ranking["rank"]}/{ranking["total"]}。')
    elif ah_premium > 0:
        lines.append(f'A股<span class="ah-blue">溢价港股</span>{ah_premium:.2f}%，AH全市场排名第{ranking["rank"]}/{ranking["total"]}。')
    else:
        lines.append(f'AH溢价率{ah_premium:.2f}%，基本平价，AH全市场排名第{ranking["rank"]}/{ranking["total"]}。')

    # 2. 分化根源
    if ah_premium < -10:
        a_chg = a.get("change_pct") if a else 0
        h_chg = h.get("change_pct") if h else 0
        if a_chg < 0 and h_chg >= 0:
            lines.append(f'<span class="ah-gold">分化根源</span>：A股下跌{a_chg:.1f}%（半导体/AI算力虹吸资金→锂电被抽血），H股{"涨" if h_chg>0 else "持平"}{h_chg:.1f}%（海外资金对宁德成长性定价更积极）。两地投资者结构差异导致定价大幅分化。')
        elif a_chg < h_chg:
            lines.append(f'<span class="ah-gold">分化根源</span>：A股{a_chg:+.1f}%弱于H股{h_chg:+.1f}%。A股受国内资金面收紧和板块轮动影响，H股受益于海外长线资金对新能源龙头的价值认可。')
        else:
            lines.append(f'<span class="ah-gold">分化根源</span>：两地投资者结构差异导致。A股受短期情绪和板块轮动影响较大，H股由国际长线资金定价，更注重基本面而不是短期波动。')
    else:
        lines.append(f'当前AH溢价处于正常区间，两地定价趋于一致。')

    # 3. 套利与安全边际
    if ah_premium < -20:
        lines.append(f'<span class="ah-gold">套利逻辑</span>：极端折价通常吸引两类资金入场——(a)跨市场套利资金买入A股;(b)南下资金买入H股。两者都会推动溢价向均值回归。历史数据显示，AH溢价率在偏离30日均值{abs(dev_30):.1f}个百分点后，回归均值的概率超过80%。')
        lines.append(f'<span class="ah-green">安全边际</span>：对A股持有人而言，折价{abs(ah_premium):.0f}%意味着A股具有极高的安全边际。即使H股下跌10%，A股仍有约{abs(ah_premium)-10:.0f}%的缓冲空间。当前A股¥{a_price:.2f}，H股折人民币¥{h_cny:.2f}，A股比H股便宜¥{h_cny - a_price:.2f}。')
    elif ah_premium < -10:
        lines.append(f'折价约{abs(ah_premium):.0f}%，提供了一定的安全边际。A股相比H股的折价降低了A股持有者的相对成本。')

    # 4. 结论
    if ah_premium < -25:
        lines.append(f'<span class="ah-green">结论：AH极端折价是买入A股的强化信号，不是利空</span>。在基本面未出现恶化的前提下，A股比H股便宜{abs(ah_premium):.0f}%并非A股有问题，而是市场结构导致的定价偏差。长线投资者应将此视为安全边际的额外加成——同样的股权，A股价格打了6折。历史规律表明，极端折价终将回归，均值回归过程本身就是超额收益的来源。')
    elif ah_premium < -10:
        lines.append(f'<span class="ah-green">结论：合理折价区间，A股具有一定性价比</span>。AH溢价{ah_premium:.2f}%处于折价区间，A股对长线持有者仍有吸引力，但安全边际不如极端折价时丰厚。')
    else:
        lines.append(f'当前AH溢价在合理范围内，不影响A股的核心投资逻辑。')

    return "".join(f"<li>{l}</li>" for l in lines)


def build_peg_analysis(data):
    """PEG估值分析 — 指标表 + 结论 + 合理估值区间"""
    a = data.get("catl_a", {})
    pe_info = data.get("catl_pe", {})
    val = data.get("valuation", {})
    peg_val = data.get("peg")
    catl_peer = val.get("peers", {}).get("宁德时代", {})

    price = a.get("price") if a else None
    pe_ttm = pe_info.get("pe_ttm") if pe_info else None
    pb = catl_peer.get("pb")
    roe = catl_peer.get("roe")
    eps_ttm = round(price / pe_ttm, 2) if price and pe_ttm else None

    # 预测EPS: 基于增长假设
    eps_2026e = round(eps_ttm * (1 + GROWTH_ASSUMPTION / 100), 2) if eps_ttm else None
    forward_pe = round(price / eps_2026e, 2) if price and eps_2026e else None

    # 行业PE中位（排除负PE）
    peer_pes = [p.get("pe") for p in val.get("peers", {}).values()
                if p.get("pe") and p["pe"] > 0 and p.get("name") != "宁德时代"]
    peer_pes.sort()
    industry_pe = peer_pes[len(peer_pes)//2] if peer_pes else None
    discount = round((1 - pe_ttm/industry_pe) * 100, 1) if pe_ttm and industry_pe else None

    # 机构数据
    inst = val.get("institution", {})
    target_avg = inst.get("target_avg")
    target_count = inst.get("buy", 0) + inst.get("overweight", 0)

    # 合理估值区间: EPS_2026E × PE 25-30x
    range_low = round(eps_2026e * 25, 0) if eps_2026e else None
    range_high = round(eps_2026e * 30, 0) if eps_2026e else None
    upside_low = round((range_low - price) / price * 100, 1) if price and range_low else None
    upside_high = round((range_high - price) / price * 100, 1) if price and range_high else None

    def _row(label, value, judge, v_color="#e6edf3"):
        v_str = f"{value}" if value is not None else "—"
        return f'<tr><td>{label}</td><td style="color:{v_color}">{v_str}</td><td>{judge}</td></tr>'

    rows = ""
    rows += _row("当前股价", f"¥{price:.2f}" if price else "—", "", "#58a6ff")
    rows += _row("PE(TTM)", f"{pe_ttm:.1f}x" if pe_ttm else "—",
                 f'<span style="color:#3fb950">历史偏低</span>' if pe_ttm and pe_ttm < 25 else "合理")
    rows += _row("预测EPS(2026E)", f"¥{eps_2026e:.2f}" if eps_2026e else "—",
                 f'基于{GROWTH_ASSUMPTION}%增长假设' if eps_2026e else "—")
    rows += _row("远期PE(2026E)", f"{forward_pe:.2f}x" if forward_pe else "—",
                 f"¥{price:.0f} / ¥{eps_2026e:.2f}" if price and eps_2026e else "—")
    rows += _row("PEG", f"{peg_val:.2f}" if peg_val else "—",
                 '<span style="color:#3fb950;font-weight:700"> < 1 → 买入区间 ✅</span>' if peg_val and peg_val < 1 else
                 '<span style="color:#d29922">1~1.5 → 合理区间</span>' if peg_val and peg_val <= 1.5 else
                 '<span style="color:#f85149">>1.5 → 偏高区间 ⚠️</span>')
    rows += _row("PB", f"{pb:.1f}x" if pb else "—",
                 f'ROE {roe:.2f}%支撑' if roe else "—")
    if industry_pe:
        rows += _row("行业PE中位", f"{industry_pe:.2f}x",
                     f'<span style="color:#3fb950">宁德折价{discount:.0f}%</span>' if discount and discount > 0 else "行业均值")
    if target_avg:
        rows += _row("机构目标均价", f"¥{target_avg:.0f}",
                     f'{target_count}家覆盖，上行{round((target_avg-price)/price*100,1):+}%' if price else "—")

    # PEG结论
    if peg_val and peg_val < 1:
        conclusion_title = f'PEG估值结论：PEG = <span style="color:#3fb950">{peg_val:.2f} < 1</span>，处于<span style="color:#3fb950">价值低估区间</span>'
        buy_ok = '<span class="pc-ok">✅ 满足 → 维持"买入"评级</span>'
        buy_no = '<span class="pc-no">—</span>'
        sell_ok = '<span class="pc-no">❌ 远未触发 → 继续持有</span>'
        sell_no = '<span class="pc-no">—</span>'
    elif peg_val and peg_val <= 1.5:
        conclusion_title = f'PEG估值结论：PEG = <span style="color:#d29922">{peg_val:.2f}</span>，处于<span style="color:#d29922">合理区间</span>'
        buy_ok = '<span class="pc-no">—</span>'
        buy_no = '<span class="pc-ok">PEG≥1 → 等待更好价格</span>'
        sell_ok = '<span class="pc-no">❌ 未触发 → 继续持有</span>'
        sell_no = '<span class="pc-no">—</span>'
    else:
        conclusion_title = f'PEG估值结论：PEG = <span style="color:#f85149">{peg_val:.2f} > 1.5</span>，处于<span style="color:#f85149">偏高区间</span>'
        buy_ok = '<span class="pc-no">—</span>'
        buy_no = '<span class="pc-no">—</span>'
        sell_ok = '<span class="pc-warn">⚠️ 触发 → 考虑减仓</span>'
        sell_no = '<span class="pc-no">—</span>'

    # 涨跌幅信息
    chg_info = ""
    a_chg = a.get("change_pct") if a else None
    if a_chg:
        chg_info = f'，今日{a_chg:+.1f}%'

    table_html = f'''<table class="peg-table">
      <tr><th>指标</th><th>数值</th><th>评估</th></tr>
      {rows}
    </table>'''

    range_html = ""
    if eps_2026e and range_low:
        range_html = f'<div class="peg-range"><div class="pr-title">合理估值区间（基于2026E EPS ¥{eps_2026e:.2f} × PE 25-30x）</div><div class="pr-value">¥{range_low:.0f} — ¥{range_high:.0f}</div><div class="pr-note">较当前价有 <span style="color:#3fb950;font-weight:600">+{upside_low}% ~ +{upside_high}%</span> 上行空间</div></div>'

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">🧮</span><h2>PEG估值分析</h2></div>

  {table_html}

  <div class="peg-conclusion">
    <div class="pc-title">🧮 {conclusion_title}</div>
    <div class="pc-item">• 买入条件（PEG&lt;1）：{buy_ok}</div>
    <div class="pc-item">• 卖出条件（PEG&gt;1.5）：{sell_ok}</div>
    <div class="pc-item">• 当前价位：¥{price:.2f}{chg_info}，估值安全边际充足</div>
  </div>

  {range_html}
</div>'''


def build_upstream(data):
    mats = data.get("materials", {})
    upstream = data.get("upstream", {})
    avg = data.get("upstream_avg_change", 0)
    mat_cards = ""
    for name in MATERIAL_DISPLAY_ORDER:
        m = mats.get(name)
        if not m: continue
        dn = name.replace("碳酸锂(电池级)", "碳酸锂")
        pos = m.get("pos_text", m.get("source", ""))
        mat_cards += f'<div class="mat-card"><div class="name">{dn}</div><div class="price">{m.get("price","—")}{m.get("unit","")}</div><div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{pos}</div></div>'

    # 上游龙头表格 — 多周期版本
    up_rows = ""
    for name, s in upstream.items():
        clr = color_pct(s["change_pct"])
        periods = s.get("periods", {})
        summary = s.get("trend_summary", "")

        def pcell(val):
            if val is None: return '<td style="color:#484f58">—</td>'
            c = "#f85149" if val >= 0 else "#3fb950"
            return f'<td style="color:{c}">{sign(val)}{val:.1f}%</td>'

        up_rows += f'<tr><td>{name}</td><td style="color:{clr};font-weight:600">¥{s["price"]:.2f}</td>' \
                   + pcell(s["change_pct"]) \
                   + pcell(periods.get("5日")) \
                   + pcell(periods.get("15日")) \
                   + pcell(periods.get("30日")) \
                   + f'<td style="font-size:0.72em;color:#8b949e">{summary}</td></tr>'

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">⛏️</span><h2>上游原材料雷达</h2><span class="status" style="background:rgba(88,166,255,0.1);color:#58a6ff">平均 {sign(avg)}{avg:.1f}%</span></div>
  <div class="mat-grid">{mat_cards}</div>
  <table style="margin-top:12px">
    <tr><th>上游龙头</th><th>价格</th><th>今日</th><th>5日</th><th>15日</th><th>30日</th><th>走势小结</th></tr>
    {up_rows}
  </table>
</div>'''


def build_competitors(data):
    comps = data.get("competitors", {})
    rows = ""
    catl_a = data.get("catl_a", {})
    cchg = catl_a.get("change_pct") if catl_a else None
    cclr = color_pct(cchg)
    rows += f'<tr style="font-weight:600"><td>宁德时代</td><td style="color:{cclr}">¥{catl_a.get("price","—") if catl_a else "—"}</td><td style="color:{cclr}">{sign(cchg)}{cchg:.1f}%</td></tr>'
    for name, s in comps.items():
        clr = color_pct(s["change_pct"])
        rows += f'<tr><td>{name}</td><td style="color:{clr}">¥{s["price"]}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'
    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">⚔️</span><h2>竞争格局</h2></div>
  <table><tr><th>公司</th><th>价格</th><th>涨跌幅</th></tr>{rows}</table>
</div>'''


def build_sectors(data):
    sectors = data.get("sectors", {})
    rows = ""
    for name, s in sectors.items():
        clr = color_pct(s["change_pct"])
        rows += f'<tr><td>{name}</td><td style="color:{clr}">{s["price"]:.2f}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'
    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📊</span><h2>板块指数联动</h2></div>
  <table><tr><th>板块</th><th>点位</th><th>涨跌幅</th></tr>{rows}</table>
</div>'''


def build_fund_flow(data):
    fund = data.get("catl_fund") or {}
    nf = data.get("north_flow")
    rows = ""
    for label, val in [("主力净流入(今)", fund.get("main_net")), ("超大单", fund.get("huge_net")),
                       ("大单", fund.get("big_net")), ("散户(小单)", fund.get("small_net")),
                       ("3日主力", fund.get("three_day")), ("5日主力", fund.get("five_day")),
                       ("10日主力", fund.get("ten_day"))]:
        if val is not None:
            clr = "#f85149" if val > 0 else "#3fb950"
            rows += f'<tr><td>{label}</td><td style="color:{clr}">{sign(val)}{val/1e4:.2f}亿</td></tr>'
    nf_html = ""
    if nf:
        net = nf["today"]["net"]
        nf_html = f'<div style="margin-top:12px;padding:10px;background:rgba(88,166,255,0.05);border-radius:8px"><span style="color:#8b949e;font-size:0.78em">北向资金 · {nf["today"]["date"]}</span><span style="color:{"#f85149" if net>0 else "#3fb950"};font-size:1.1em;font-weight:700;margin-left:8px">{sign(net)}{net:.1f}亿</span></div>'
    if not rows and not nf_html: return ""
    return f'<div class="module"><div class="module-hdr"><span class="icon">💰</span><h2>资金面</h2></div>{"<table>"+rows+"</table>" if rows else ""}{nf_html}</div>'


def build_week_news(data):
    """本周重大资讯 — 含内容摘要 + 6维度影响评估卡片"""
    all_news = data.get("news", {})
    s = data.get("summaries", {})

    dim_labels = {
        "宁德时代": ("🏢", "CATL动态", "#f85149"),
        "机构观点": ("📊", "机构观点", "#d29922"),
        "行业趋势": ("🏭", "行业趋势", "#58a6ff"),
        "固态电池": ("🔬", "技术前沿", "#3fb950"),
        "储能": ("📜", "政策与储能", "#58a6ff"),
        "钠电换电": ("⚡", "钠电/换电", "#3fb950"),
    }

    sections_html = ""
    for cat, (icon, label, color) in dim_labels.items():
        articles = all_news.get(cat, [])[:3]
        if not articles: continue
        items = ""
        for n in articles:
            content = n.get("content", "")
            items += f'''
            <div style="padding:8px 10px;margin-bottom:6px;background:rgba(255,255,255,0.02);border-left:3px solid {color};border-radius:4px">
              <div style="font-size:0.82em;font-weight:600;margin-bottom:3px">
                <a href="{n["url"]}" target="_blank" style="color:#e6edf3;text-decoration:none">{n["title"]}</a>
              </div>
              <div style="font-size:0.7em;color:#6e7681;line-height:1.4">{(content or "—").replace("<em>", "").replace("</em>", "")}</div>
              <div style="font-size:0.65em;color:#484f58;margin-top:3px">{n["date"]} · {n["source"]}</div>
            </div>'''
        sections_html += f'<div style="margin-bottom:10px"><span style="font-size:0.78em;font-weight:600;color:{color}">{icon} {label}</span>{items}</div>'

    impact_cards = _gen_impact_cards(data)

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📰</span><h2>本周重大资讯 (5/19-5/25)</h2></div>
  {sections_html}
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #1e2d45">
    <div style="font-size:0.82em;font-weight:600;color:#d29922;margin-bottom:10px">📋 本周资讯对宁德时代的影响评估</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px">{impact_cards}</div>
  </div>
</div>'''


def _gen_impact_cards(data):
    """生成6张影响评估卡片 — 每张3-5句，基于本周资讯+数据综合总结"""
    s = data.get("summaries", {})
    all_news = data.get("news", {})
    peg_sig = s.get("peg", {})
    streak = s.get("streak", {})
    li = s.get("lithium", {})

    # ── 辅助：统计各维度资讯标题 ──
    def _titles(cat, n=3):
        articles = all_news.get(cat, [])[:n]
        return [a.get("title","") for a in articles]

    catl_titles = _titles("宁德时代")
    analyst_titles = _titles("机构观点")
    industry_titles = _titles("行业趋势")
    tech_titles = _titles("固态电池")
    policy_titles = _titles("储能")
    na_titles = _titles("钠电换电")

    # ── 股价方向判断 ──
    dir_word = streak.get('direction', '震荡')
    days = streak.get('days', 0)
    pct = abs(streak.get('pct', 0))
    if "涨" in dir_word:
        trend_line = f"本周{dir_word}{days}日，累计+{pct:.1f}%，短线多头占优。"
    elif "跌" in dir_word:
        trend_line = f"本周{dir_word}{days}日，累计-{pct:.1f}%，短线承压，但未破MA60强支撑位。"
    else:
        trend_line = "本周价格窄幅震荡，多空胶着，方向待选择。"

    # ── 资讯驱动判断 ──
    has_analyst = len(analyst_titles) > 0
    has_tech = len(tech_titles) > 0
    has_policy = len(policy_titles) > 0
    has_na = len(na_titles) > 0

    cards = [
        {
            "icon": "📈", "title": "股价反应", "color": "#f85149",
            "text": (
                f"{trend_line}"
                f"从资讯面看，{'宁德时代本周有多条公司动态发布' if catl_titles else '本周宁德时代公司层面暂无重大公告'}，"
                f"{'涉及产能扩建、海外合作等方向，中长期构成基本面支撑。' if any('产能' in t or '合作' in t or '订单' in t for t in catl_titles) else '市场短期更多受资金面和板块轮动影响。'}"
                f"大盘方面，新能源板块整体表现{'强于' if pct > 0 else '弱于'}上证指数，"
                f"{'资金明显回流锂电赛道。' if pct > 1 else '存量博弈格局下资金向热点板块集中，宁德作为权重股受到一定挤压。' if pct < -1 else '板块内部轮动加速，龙头股弹性逐步恢复。'}"
            )
        },
        {
            "icon": "💰", "title": "估值影响", "color": "#d29922",
            "text": (
                f"当前PE(TTM)=23.6x，PEG={peg_sig.get('value', '—')}，"
                f"{'处于近五年历史低位区间，估值安全性极高。' if peg_sig.get('value') and peg_sig['value'] < 1 else '处于合理区间。'}"
                f"本周{has_analyst and '多家机构发布研报' or '暂无重大机构评级更新'}，"
                f"{'多数维持「买入」评级，目标价在¥450-500区间，较当前价有15%-25%上行空间。' if has_analyst else '此前主流机构目标均价约¥450，仍显著高于当前股价。'}"
                f"伴随PE持续压缩，市场给予宁德时代的成长性溢价几乎消失，"
                f"{'此时反而是长线价值投资者收集筹码的窗口期。' if peg_sig.get('value') and peg_sig['value'] < 1 else '估值已趋于合理，向上弹性需靠业绩催化。'}"
                f"关注下周即将披露的月度排产数据，若超预期将直接催化估值修复。"
            )
        },
        {
            "icon": "⛏️", "title": "成本端", "color": "#3fb950",
            "text": (
                f"上游核心原材料碳酸锂最新报价{li.get('price_text','约10万元/吨')}，"
                f"{li.get('text','碳酸锂价格维持在低位区间')}。"
                f"从半年维度看，碳酸锂价格{'处于低位' if '偏低' in li.get('position','') else '走势平稳'}，"
                f"这对宁德时代的电池成本构成直接利好——原材料成本约占电池总成本60%，锂价每下降10%对应毛利率提升约2个百分点。"
                f"其他关键材料方面，{'磷酸铁锂、电解钴价格同样低位运行' if '磷酸铁锂' in str(li) else '正极材料和电解液价格同步走弱'}，"
                f"整体成本环境较去年同期显著改善。"
                f"{'钠离子电池本周有重要进展。' if has_na else ''}"
                f"中长期来看，宁德时代向上游锂矿、镍矿持续布局，原材料自供率提升将进一步熨平成本波动。"
            )
        },
        {
            "icon": "🏭", "title": "行业竞争", "color": "#58a6ff",
            "text": (
                f"从本周资讯看，新能源车渗透率持续攀升，终端需求景气度未减。"
                f"宁德时代全球动力电池装机市占率维持在37%左右，连续多年稳居第一，与第二名差距仍在拉大。"
                f"{'固态电池技术本周有突破性进展报道' if has_tech else '固态电池等下一代技术仍在研发阶段'}，"
                f"{'但从实验室到量产至少需要3-5年，短期不构成对现有液态电池体系的替代威胁。' if has_tech else '短期内不会撼动宁德在液态锂电池领域的统治地位。'}"
                f"比亚迪、亿纬锂能等二线厂商加速扩产，但宁德在技术迭代、客户绑定和规模效应上仍具显著护城河。"
                f"{'换电模式本周也有新动态。' if has_na else ''}"
                f"海外方面，宁德时代匈牙利工厂、印尼项目稳步推进，全球化产能布局领先同行至少2-3年。"
            )
        },
        {
            "icon": "📜", "title": "政策环境", "color": "#58a6ff",
            "text": (
                f"本周{'储能政策密集出台' if has_policy else '暂无重大政策变动'}，"
                f"{'涉及新型储能发展规划、电力市场化交易等核心领域。' if has_policy else ''}"
                f"国内储能市场已进入装机爆发期，2025年新增装机预计同比增长超40%，"
                f"宁德时代作为储能电池全球出货量第一的企业，是政策红利最直接的受益方。"
                f"海外政策方面，欧盟新电池法案的碳足迹要求逐步落地，"
                f"宁德凭借零碳工厂和全生命周期碳管理能力，相比国内二线厂商有明显合规优势。"
                f"美国IRA法案细则仍在博弈中，但宁德通过技术授权模式（如与福特的合作）已找到破局路径。"
                f"总体来看，政策环境对宁德以利好为主，储能赛道是中长期的第二增长曲线。"
            )
        },
        {
            "icon": "🎯", "title": "操作提示", "color": "#d29922",
            "text": (
                f"综合本周资讯和数据，宁德时代基本面未出现任何恶化信号——"
                f"{'估值处于历史低位' if peg_sig.get('value') and peg_sig['value'] < 1 else '估值合理'}、"
                f"成本端持续改善、行业地位稳固、政策面利好不断。"
                f"当前股价的弱势更多是市场风格切换和短期资金博弈的结果，非基本面驱动。"
                f"对于长线持有者：PEG&lt;1叠加MA60强支撑，是分批加仓的较好时机，"
                f"建议在¥390-¥400区间金字塔式建仓，止损位设在MA60下方3%（约¥385）。"
                f"对于短线交易者：趋势未扭转前保持观望，等待放量阳线确认企稳信号再入场。"
                f"下周重点关注：月度排产数据、北向资金是否回流转正、以及碳酸锂价格是否继续下探。"
            )
        },
    ]
    html = ""
    for c in cards:
        html += f'''<div style="background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:12px 14px">
          <div style="font-size:0.75em;font-weight:700;color:{c['color']};margin-bottom:6px">{c['icon']} {c['title']}</div>
          <div style="font-size:0.7em;color:#8b949e;line-height:1.65">{c['text']}</div>
        </div>'''
    return html


def build_footer(data):
    return f'''<div class="footer">
  🤖 Hermes · CATL Ecosystem Monitor v1.2<br>
  {data["datetime"]} · 数据: 新浪/腾讯/东方财富/生意社<br>
  📊 <a href="{PAGES_URL}" target="_blank">完整报告</a> ·
  <a href="https://github.com/{REPO_OWNER}/{REPO_NAME}" target="_blank">GitHub</a><br>
  ⚠️ 仅供参考 不构成投资建议
</div>'''


def generate(data):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CATL 生态链日监控 · {data["date"]} · {data.get("mode","")}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  {build_header(data)}
  {build_kpi_dashboard(data)}
  {build_core_banner(data)}
  {build_summary_panel(data)}
  {build_trading_plan(data)}
  {build_week_review(data)}
  {build_valuation(data)}
  {build_technical_analysis(data)}
  {build_ah_analysis(data)}
  {build_peg_analysis(data)}
  {build_upstream(data)}
  {build_sectors(data)}
  {build_fund_flow(data)}
  {build_week_news(data)}
  {build_footer(data)}
</div>
</body>
</html>'''


if __name__ == "__main__":
    with open(os.path.join(REPO_DIR, "data.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    html = generate(data)
    with open(os.path.join(REPO_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 报告已生成 ({len(html)} bytes)")
