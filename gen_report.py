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
        # 价格标签
        price_labels += f'<span style="position:absolute;left:{i*seg_width}%;width:{seg_width}%;text-align:center;font-size:0.58em;color:#8b949e;top:-16px">¥{bp:.0f}</span>'
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
              <div style="font-size:0.7em;color:#6e7681;line-height:1.4">{content if content else "—"}</div>
              <div style="font-size:0.65em;color:#484f58;margin-top:3px">{n["date"]} · {n["source"]}</div>
            </div>'''
        sections_html += f'<div style="margin-bottom:10px"><span style="font-size:0.78em;font-weight:600;color:{color}">{icon} {label}</span>{items}</div>'

    impact_cards = _gen_impact_cards(data)

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📰</span><h2>本周重大资讯 (5/19-5/25)</h2></div>
  {sections_html}
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #1e2d45">
    <div style="font-size:0.82em;font-weight:600;color:#d29922;margin-bottom:10px">📋 本周资讯对宁德时代的影响评估</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:8px">{impact_cards}</div>
  </div>
</div>'''


def _gen_impact_cards(data):
    """生成6张影响评估卡片"""
    s = data.get("summaries", {})
    peg_sig = s.get("peg", {})
    streak = s.get("streak", {})
    li = s.get("lithium", {})

    cards = [
        {"icon": "📈", "title": "股价反应", "color": "#f85149",
         "text": f"本周{streak.get('direction','')}{streak.get('days',0)}日，累计{abs(streak.get('pct',0)):.1f}%。大盘涨宁德跌——资金被热门板块虹吸。"},
        {"icon": "💰", "title": "估值影响", "color": "#d29922",
         "text": f"PEG={peg_sig.get('value','—')}" +
                ("，低估加深，越跌越便宜。" if peg_sig.get('value') and peg_sig['value'] < 1 else "，估值合理。")},
        {"icon": "⛏️", "title": "成本端", "color": "#3fb950",
         "text": f"{li.get('text','碳酸锂平稳')}，" +
                ("对CATL毛利率正面贡献。" if "利好" in li.get('impact','') else "成本端稳定。" if "稳定" in li.get('impact','') else "短期压缩利润空间。")},
        {"icon": "🏭", "title": "行业竞争", "color": "#58a6ff",
         "text": "新能源车渗透率持续提升，CATL装机量稳居第一。固态/钠电等新技术推进中，短期不影响主流格局。"},
        {"icon": "📜", "title": "政策环境", "color": "#58a6ff",
         "text": "储能政策持续加码，电力市场化改革推进。欧盟电池法案等海外政策需持续跟踪。"},
        {"icon": "🎯", "title": "操作提示", "color": "#d29922",
         "text": "PEG低估+MA60强支撑，长期持有者可分批布局。短期趋势偏弱，等企稳信号。" if peg_sig.get('value') and peg_sig['value'] < 1 else "估值合理，持有为主。"},
    ]
    html = ""
    for c in cards:
        html += f'''<div style="background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:10px">
          <div style="font-size:0.72em;font-weight:600;color:{c['color']};margin-bottom:4px">{c['icon']} {c['title']}</div>
          <div style="font-size:0.7em;color:#8b949e;line-height:1.5">{c['text']}</div>
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
