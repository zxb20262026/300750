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

    # 9. NEW: 行业涨跌
    ind = s.get("industry", {})
    ind_chg = ind.get("change_pct")
    ind_name = ind.get("name", "—")
    # 显示简称 "电池"
    ind_label = "电池" if "电池" in ind_name else ind_name
    vs_ind = s.get("vs_industry", "")
    cards.append(make_card(f"行业({ind_label})",
                           f"{sign(ind_chg)}{ind_chg:.1f}%" if ind_chg is not None else "—",
                           "", vs_ind or "", color_pct(ind_chg)))

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


def build_upstream(data):
    mats = data.get("materials", {})
    upstream = data.get("upstream", {})
    avg = data.get("upstream_avg_change", 0)
    mat_cards = ""
    mat_order = ["碳酸锂(电池级)", "碳酸锂", "氢氧化锂", "电解钴", "硫酸镍", "磷酸铁锂", "六氟磷酸锂"]
    shown = set()
    for name in mat_order:
        if name in mats and name not in shown:
            m = mats[name]; shown.add(name)
            dn = name.replace("碳酸锂(电池级)", "碳酸锂")
            mat_cards += f'<div class="mat-card"><div class="name">{dn}</div><div class="price">{m.get("price","—")}{m.get("unit","")}</div><div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{m.get("trend",m.get("source",""))}</div></div>'
    for name, m in mats.items():
        if name not in shown:
            shown.add(name)
            mat_cards += f'<div class="mat-card"><div class="name">{name}</div><div class="price">{m.get("price","—")}{m.get("unit","")}</div><div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{m.get("trend",m.get("source",""))}</div></div>'
    up_rows = ""
    for name, s in upstream.items():
        clr = color_pct(s["change_pct"])
        up_rows += f'<tr><td>{name}</td><td style="color:{clr}">¥{s["price"]}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'
    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">⛏️</span><h2>上游原材料雷达</h2><span class="status" style="background:rgba(88,166,255,0.1);color:#58a6ff">平均 {sign(avg)}{avg:.1f}%</span></div>
  <div class="mat-grid">{mat_cards}</div>
  <table style="margin-top:12px"><tr><th>上游龙头</th><th>价格</th><th>涨跌幅</th></tr>{up_rows}</table>
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


def build_news_module(data):
    all_news = data.get("news", {})
    ch = ""
    for n in all_news.get("宁德时代", [])[:3]:
        ch += f'<li class="news-item"><span class="news-date">{n["date"]}</span><span class="news-info"><a href="{n["url"]}" target="_blank">{n["title"]}</a><span class="src">{n["source"]}</span></span></li>'
    th = ""
    for kw in ["固态电池", "储能", "钠离子电池", "换电"]:
        kn = all_news.get(kw, [])[:2]
        if kn:
            th += f'<div style="margin-bottom:10px"><span style="color:#58a6ff;font-size:0.78em;font-weight:600">{kw}</span>'
            for n in kn:
                th += f'<li class="news-item"><span class="news-date">{n["date"]}</span><span class="news-info"><a href="{n["url"]}" target="_blank">{n["title"]}</a><span class="src">{n["source"]}</span></span></li>'
            th += '</div>'
    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📰</span><h2>资讯中心</h2></div>
  <div style="margin-bottom:12px"><span style="color:#f85149;font-size:0.8em;font-weight:600">🔥 CATL 头条</span>
  <ul class="news-list" style="margin-top:4px">{ch}</ul></div>{th}
</div>'''


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
  {build_upstream(data)}
  {build_competitors(data)}
  {build_sectors(data)}
  {build_fund_flow(data)}
  {build_news_module(data)}
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
