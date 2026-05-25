#!/usr/bin/env python3
"""CATL 生态链日监控 — HTML报告生成器 v1.1

新增: KPI卡片带节点总结 / 数据变化总结面板 / 预警合并
"""

import json, os
from config import *


def fmt_yi(n):
    """格式化(亿)"""
    if n is None: return "—"
    return f"{n:.2f}亿"


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

/* ── 模块卡片 ── */
.module{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:16px;margin-bottom:14px}
.module-hdr{display:flex;align-items:center;gap:8px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #1e2d45}
.module-hdr .icon{font-size:1.2em}
.module-hdr h2{font-size:0.95em;font-weight:600;color:#58a6ff;flex:1}
.module-hdr .status{font-size:0.72em;padding:2px 8px;border-radius:6px}

/* ── KPI 大卡片网格 ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin-bottom:16px}
.kpi-card{background:#131a26;border:1px solid #1e2d45;border-radius:10px;padding:14px;display:flex;flex-direction:column}
.kpi-card .kpi-label{color:#8b949e;font-size:0.68em;letter-spacing:0.5px;margin-bottom:4px}
.kpi-card .kpi-value{font-size:1.5em;font-weight:700;margin-bottom:2px}
.kpi-card .kpi-change{font-size:0.8em;margin-bottom:6px}
.kpi-card .kpi-note{font-size:0.7em;color:#6e7681;padding-top:6px;border-top:1px solid #1e2d45;line-height:1.4}

/* ── 总结面板 ── */
.summary-panel{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:16px;margin-bottom:14px}
.summary-panel .sp-title{font-size:0.9em;font-weight:600;color:#e6edf3;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.summary-section{margin-bottom:10px}
.summary-section:last-child{margin-bottom:0}
.summary-section .ss-label{font-size:0.7em;color:#8b949e;margin-bottom:4px;text-transform:uppercase;letter-spacing:1px}
.summary-item{display:flex;align-items:flex-start;gap:8px;padding:6px 10px;border-radius:6px;margin-bottom:4px;font-size:0.8em;line-height:1.4}
.summary-item:last-child{margin-bottom:0}
.summary-item.critical{border-left:3px solid #f85149;background:rgba(248,81,73,0.08)}
.summary-item.important{border-left:3px solid #d29922;background:rgba(210,153,34,0.06)}
.summary-item.info{border-left:3px solid #58a6ff;background:rgba(88,166,255,0.05)}
.summary-item.positive{border-left:3px solid #3fb950;background:rgba(63,185,80,0.05)}
.summary-item .si-icon{font-size:0.9em;flex-shrink:0;margin-top:1px}
.summary-item .si-content{flex:1}
.summary-item .si-content .highlight{font-weight:700}
.highlight-red{color:#f85149}
.highlight-yellow{color:#d29922}
.highlight-green{color:#3fb950}
.highlight-blue{color:#58a6ff}

/* ── 表格 ── */
table{width:100%;border-collapse:collapse;font-size:0.8em}
th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #1e2d45}
th{color:#8b949e;font-weight:500;font-size:0.85em}
tr:hover{background:rgba(88,166,255,0.03)}

/* ── 新闻 ── */
.news-list{margin:0;padding:0;list-style:none}
.news-item{display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #1e2d45;align-items:flex-start}
.news-item:last-child{border-bottom:none}
.news-date{color:#484f58;font-size:0.7em;white-space:nowrap;min-width:42px;padding-top:1px}
.news-info{flex:1;min-width:0}
.news-info a{color:#e6edf3;text-decoration:none;font-size:0.82em;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}
.news-info a:hover{color:#58a6ff}
.news-info .src{color:#484f58;font-size:0.7em;margin-top:2px}

/* ── 原材料 ── */
.mat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.mat-card{background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:10px;text-align:center}
.mat-card .name{font-size:0.72em;color:#8b949e}
.mat-card .price{font-size:1.1em;font-weight:700;margin:3px 0}
.mat-card .trend{font-size:0.7em;padding:1px 6px;border-radius:4px}

/* ── Footer ── */
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
# 模块构建函数
# ═══════════════════════════════════════════

def build_header(data):
    a = data.get("catl_a", {})
    price = a.get("price", "—") if a else "—"
    chg = a.get("change_pct") if a else None
    chg_str = f"{sign(chg)}{chg:.2f}%" if chg is not None else ""
    mode = data.get("mode", "日监控")
    badge_class = "badge-morning" if "早" in mode else "badge-evening"

    return f'''<div class="header">
  <h1>🔋 宁德时代 · 生态链日监控</h1>
  <div class="sub">CATL Ecosystem Radar · {data["date"]} · 持仓{HOLDING_SHARES}股</div>
  <div class="sub" style="margin-top:2px">A股 <span style="color:{color_pct(chg)};font-weight:700">¥{price} {chg_str}</span></div>
  <span class="badge {badge_class}">{mode}</span>
</div>'''


def build_kpi_dashboard(data):
    """重写的KPI仪表盘 — 每个卡片带节点总结"""
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    peg = data.get("peg")
    sig = data.get("peg_signal", {})
    ah = data.get("ah_premium")
    fund = data.get("catl_fund") or {}
    pe = data.get("catl_pe", {})
    s = data.get("summaries", {})

    cards = []

    # ── 1. CATL A股 ──
    price = a.get("price") if a else None
    chg = a.get("change_pct") if a else None
    streak = s.get("streak", {})
    chg_5d = s.get("chg_5d")

    a_streak_note = streak.get("text", "")
    if chg_5d is not None:
        a_streak_note += f" · 5日{'涨' if chg_5d>=0 else '跌'}{abs(chg_5d):.1f}%"

    cards.append({
        "label": "CATL A股", "value": f"¥{price:.2f}" if price else "—",
        "change": f"{icon_pct(chg)} {sign(chg)}{chg:.1f}%" if chg is not None else "",
        "note": a_streak_note,
        "value_clr": color_pct(chg),
    })

    # ── 2. H股 ──
    hp = h.get("price") if h else None
    hchg = h.get("change_pct") if h else None
    cards.append({
        "label": "H股", "value": f"HK${hp:.2f}" if hp else "—",
        "change": f"{sign(hchg)}{hchg:.1f}%" if hchg is not None else "",
        "note": f"≈ ¥{hp*0.92:.1f}" if hp else "",
        "value_clr": color_pct(hchg),
    })

    # ── 3. PE(TTM) ──
    pe_val = pe.get("pe_ttm") if pe else None
    pe_note = s.get("pe", {}).get("text", "")
    pe_clr = "#d29922" if pe_val and pe_val > 40 else "#58a6ff"
    cards.append({
        "label": "PE(TTM)", "value": f"{pe_val:.1f}x" if pe_val else "—",
        "change": "",
        "note": pe_note,
        "value_clr": pe_clr,
    })

    # ── 4. PEG ──
    peg_note = s.get("peg", {}).get("text", "")
    peg_target = s.get("peg", {}).get("target_price")
    peg_dist = s.get("peg", {}).get("distance_pct")
    if peg_target and peg_dist:
        peg_note += f"\n买入线 ¥{peg_target:.0f} (差{abs(peg_dist):.1f}%)"

    cards.append({
        "label": "PEG", "value": f"{peg:.2f}" if peg else "—",
        "change": sig.get("text", ""),
        "note": peg_note,
        "value_clr": sig.get("color", "#8b949e"),
    })

    # ── 5. AH溢价 ──
    ah_note = s.get("ah", {}).get("text", "")
    ah_clr = "#3fb950" if ah is not None and ah < 0 else "#f85149"
    cards.append({
        "label": "AH溢价", "value": f"{sign(ah)}{ah:.1f}%" if ah is not None else "—",
        "change": "",
        "note": ah_note,
        "value_clr": ah_clr,
    })

    # ── 6. 成交额 ──
    amt = a.get("amount", 0) / 1e8 if a else 0
    amt_note = s.get("amount", {}).get("text", "")
    vol_r = s.get("volume_ratio", {}).get("text", "")
    if vol_r and vol_r != "—":
        amt_note += f" · {vol_r}"

    cards.append({
        "label": "成交额", "value": f"{amt:.0f}亿" if amt else "—",
        "change": "",
        "note": amt_note,
        "value_clr": "#8b949e",
    })

    # ── 7. 主力资金 ──
    mn = fund.get("main_net", 0) / 1e4 if fund else 0
    mn_clr = "#f85149" if mn > 0 else "#3fb950" if mn < 0 else "#8b949e"
    fund_note = s.get("fund", {}).get("text", "")
    cards.append({
        "label": "主力净流入", "value": f"{sign(mn)}{mn:.2f}亿" if mn else "—",
        "change": "",
        "note": fund_note,
        "value_clr": mn_clr,
    })

    # ── 8. 碳酸锂 ──
    li_note = s.get("lithium", {}).get("text", "参考价~7.5万/吨")
    lf = data.get("lithium_futures", {})
    li_impact = s.get("lithium", {}).get("impact", "")
    li_clr = "#3fb950" if "利好" in li_impact else "#f85149" if "压力" in li_impact else "#8b949e"
    li_price_str = f"{lf.get('price',0)/10000:.1f}万" if lf and lf.get("price") else "—"

    cards.append({
        "label": "碳酸锂期货", "value": li_price_str,
        "change": lf.get("change_pct") and f"{sign(lf['change_pct'])}{lf['change_pct']:.1f}%" or "",
        "note": li_note,
        "value_clr": li_clr,
    })

    # 渲染
    rows = ""
    for c in cards:
        rows += f'''<div class="kpi-card">
  <div class="kpi-label">{c["label"]}</div>
  <div class="kpi-value" style="color:{c["value_clr"]}">{c["value"]}</div>
  {f'<div class="kpi-change" style="color:{c["value_clr"]}">{c["change"]}</div>' if c["change"] else ''}
  <div class="kpi-note">{c["note"]}</div>
</div>'''

    return f'<div class="kpi-grid">{rows}</div>'


def build_summary_panel(data):
    """数据变化总结面板 — 合并预警 + 关键信号"""
    s = data.get("summaries", {})
    peg_sig = s.get("peg", {})
    ah_sig = s.get("ah", {})
    streak = s.get("streak", {})
    amount_sig = s.get("amount", {})
    fund_sig = s.get("fund", {})
    li_sig = s.get("lithium", {})
    upstream_alerts = s.get("upstream_alerts", [])
    a = data.get("catl_a", {})
    pe = data.get("catl_pe", {})

    items = []

    # ── 核心信号 (critical) ── 最重要
    peg_v = peg_sig.get("value")
    peg_dist = peg_sig.get("distance_pct")

    if peg_v and peg_v > PEG_OVERVALUE:
        items.append({
            "level": "critical", "icon": "⚠️",
            "html": f'<span class="highlight highlight-red">PEG={peg_v:.2f} 偏高</span>，距买入区间还需跌<span class="highlight highlight-red">{abs(peg_dist):.1f}%</span>至 ¥{peg_sig.get("target_price","—"):.0f}，当前不宜追高'
        })
    elif peg_v and peg_v < PEG_UNDERVALUE:
        items.append({
            "level": "positive", "icon": "✅",
            "html": f'<span class="highlight highlight-green">PEG={peg_v:.2f} 低估</span>，已进入买入区间，可分批建仓'
        })

    # AH折溢价
    ah = data.get("ah_premium")
    if ah is not None and ah < -30:
        items.append({
            "level": "important", "icon": "💡",
            "html": f'<span class="highlight highlight-yellow">A股折价港股{abs(ah):.0f}%</span>，再创新低，<span class="highlight highlight-green">成本利好</span>，H股相对更贵'
        })
    elif ah is not None and ah < 0:
        items.append({
            "level": "info", "icon": "📌",
            "html": f'A股折价港股{abs(ah):.0f}%，成本端利好'
        })
    elif ah is not None and ah > 30:
        items.append({
            "level": "important", "icon": "⚠️",
            "html": f'<span class="highlight highlight-yellow">A股溢价{ah:.0f}%</span>，溢价偏高'
        })

    # 连涨连跌
    if streak and streak.get("days", 0) >= 3:
        if streak.get("direction") == "跌":
            items.append({
                "level": "important", "icon": "📉",
                "html": f'<span class="highlight highlight-yellow">连跌{streak["days"]}日累计{-abs(streak["pct"]):.1f}%</span>，短期超卖'
            })
        elif streak.get("direction") == "涨":
            items.append({
                "level": "info", "icon": "📈",
                "html": f'连涨{streak["days"]}日累计+{streak["pct"]:.1f}%，短期超买注意回调'
            })

    # 上游异动
    if upstream_alerts:
        alert_texts = [f'<span class="highlight highlight-yellow">{ua["name"]} {ua["change"]:+.1f}%</span>' for ua in upstream_alerts]
        items.append({
            "level": "important", "icon": "⛏️",
            "html": "上游异动: " + " · ".join(alert_texts)
        })

    # 放量
    amt_val = a.get("amount", 0) / 1e8 if a else 0
    if amt_val > 100:
        items.append({
            "level": "info", "icon": "📊",
            "html": f'<span class="highlight highlight-blue">成交额{amt_val:.0f}亿 放量明显</span>，关注资金方向'
        })

    # 碳酸锂
    li_text = li_sig.get("text", "")
    li_impact = li_sig.get("impact", "")
    if "利好" in li_impact:
        items.append({
            "level": "positive", "icon": "✅",
            "html": f'<span class="highlight highlight-green">{li_text}</span>'
        })
    elif "压力" in li_impact:
        items.append({
            "level": "important", "icon": "⚠️",
            "html": f'<span class="highlight highlight-yellow">{li_text}</span>'
        })
    elif li_text and "暂缺" not in li_text:
        items.append({
            "level": "info", "icon": "ℹ️",
            "html": li_text
        })

    # 主力资金
    mn = fund_sig.get("main_net", 0)
    d5 = fund_sig.get("five_day", 0)
    if mn and abs(mn) > 0.5:
        items.append({
            "level": "info", "icon": "💰",
            "html": f'主力今日{"净流入" if mn>0 else "净流出"}<span class="highlight">{abs(mn):.1f}亿</span>' +
                    (f'，近5日{"累计流入" if d5>0 else "累计流出"}{abs(d5):.1f}亿' if abs(d5) > 1 else '')
        })

    # PE
    pe_sig = s.get("pe", {})
    pe_level = pe_sig.get("level", "")
    if pe_level == "高":
        items.append({
            "level": "important", "icon": "📊",
            "html": f'PE(TTM) <span class="highlight highlight-yellow">{pe_sig.get("value",""):.1f}x 偏高</span>，估值端有压力'
        })

    # 渲染
    if not items:
        return ''

    html_parts = []
    for item in items:
        html_parts.append(f'<div class="summary-item {item["level"]}"><span class="si-icon">{item["icon"]}</span><span class="si-content">{item["html"]}</span></div>')

    # 按优先级排序: critical first, important second, info third, positive last
    # (already in that order from the code above)

    return f'''<div class="summary-panel">
  <div class="sp-title">📋 数据变化总结</div>
  {"".join(html_parts)}
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
            display_name = name.replace("碳酸锂(电池级)", "碳酸锂")
            mat_cards += f'<div class="mat-card"><div class="name">{display_name}</div><div class="price">{m.get("price","—")}{m.get("unit","")}</div><div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{m.get("trend",m.get("source",""))}</div></div>'
    for name, m in mats.items():
        if name not in shown:
            shown.add(name)
            mat_cards += f'<div class="mat-card"><div class="name">{name}</div><div class="price">{m.get("price","—")}{m.get("unit","")}</div><div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{m.get("trend",m.get("source",""))}</div></div>'

    upstream_rows = ""
    for name, s in upstream.items():
        clr = color_pct(s["change_pct"])
        upstream_rows += f'<tr><td>{name}</td><td style="color:{clr}">¥{s["price"]}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">⛏️</span><h2>上游原材料雷达</h2><span class="status" style="background:rgba(88,166,255,0.1);color:#58a6ff">平均 {sign(avg)}{avg:.1f}%</span></div>
  <div class="mat-grid">{mat_cards}</div>
  <table style="margin-top:12px"><tr><th>上游龙头</th><th>价格</th><th>涨跌幅</th></tr>{upstream_rows}</table>
</div>'''


def build_competitors(data):
    comps = data.get("competitors", {})
    rows = ""
    catl_a = data.get("catl_a", {})
    catl_chg = catl_a.get("change_pct") if catl_a else None
    catl_clr = color_pct(catl_chg)
    rows += f'<tr style="font-weight:600"><td>宁德时代 (CATL)</td><td style="color:{catl_clr}">¥{catl_a.get("price","—") if catl_a else "—"}</td><td style="color:{catl_clr}">{sign(catl_chg)}{catl_chg:.1f}%</td></tr>'
    for name, s in comps.items():
        clr = color_pct(s["change_pct"])
        rows += f'<tr><td>{name}</td><td style="color:{clr}">¥{s["price"]}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">⚔️</span><h2>竞争格局</h2><span class="status" style="background:rgba(210,153,34,0.1);color:#d29922">CATL vs 同行</span></div>
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
    fund_rows = ""
    for label, val in [
        ("主力净流入(今)", fund.get("main_net")), ("超大单", fund.get("huge_net")),
        ("大单", fund.get("big_net")), ("散户(小单)", fund.get("small_net")),
        ("3日主力", fund.get("three_day")), ("5日主力", fund.get("five_day")),
        ("10日主力", fund.get("ten_day")),
    ]:
        if val is not None:
            clr = "#f85149" if val > 0 else "#3fb950"
            fund_rows += f'<tr><td>{label}</td><td style="color:{clr}">{sign(val)}{val/1e4:.2f}亿</td></tr>'

    nf_html = ""
    if nf:
        net = nf["today"]["net"]
        nf_html = f'<div style="margin-top:12px;padding:10px;background:rgba(88,166,255,0.05);border-radius:8px"><span style="color:#8b949e;font-size:0.78em">北向资金 · {nf["today"]["date"]}</span><span style="color:{"#f85149" if net>0 else "#3fb950"};font-size:1.1em;font-weight:700;margin-left:8px">{sign(net)}{net:.1f}亿</span></div>'

    if not fund_rows and not nf_html:
        return ""
    return f'<div class="module"><div class="module-hdr"><span class="icon">💰</span><h2>资金面</h2></div>{"<table>"+fund_rows+"</table>" if fund_rows else ""}{nf_html}</div>'


def build_news_module(data):
    all_news = data.get("news", {})
    catl_html = ""
    for n in all_news.get("宁德时代", [])[:3]:
        catl_html += f'<li class="news-item"><span class="news-date">{n["date"]}</span><span class="news-info"><a href="{n["url"]}" target="_blank">{n["title"]}</a><span class="src">{n["source"]}</span></span></li>'

    tech_html = ""
    for kw in ["固态电池", "储能", "钠离子电池", "换电"]:
        kw_news = all_news.get(kw, [])[:2]
        if kw_news:
            tech_html += f'<div style="margin-bottom:10px"><span style="color:#58a6ff;font-size:0.78em;font-weight:600">{kw}</span>'
            for n in kw_news:
                tech_html += f'<li class="news-item"><span class="news-date">{n["date"]}</span><span class="news-info"><a href="{n["url"]}" target="_blank">{n["title"]}</a><span class="src">{n["source"]}</span></span></li>'
            tech_html += '</div>'

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📰</span><h2>资讯中心</h2></div>
  <div style="margin-bottom:12px"><span style="color:#f85149;font-size:0.8em;font-weight:600">🔥 CATL 头条</span>
  <ul class="news-list" style="margin-top:4px">{catl_html}</ul></div>
  {tech_html}
</div>'''


def build_footer(data):
    return f'''<div class="footer">
  🤖 Hermes · CATL Ecosystem Monitor v1.1<br>
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
  {build_summary_panel(data)}
  {build_upstream(data)}
  {build_competitors(data)}
  {build_sectors(data)}
  {build_fund_flow(data)}
  {build_news_module(data)}
  {build_footer(data)}
</div>
</body>
</html>'''


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == "__main__":
    data_path = os.path.join(REPO_DIR, "data.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    html = generate(data)
    out_path = os.path.join(REPO_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 报告已生成 → {out_path} ({len(html)} bytes)")
