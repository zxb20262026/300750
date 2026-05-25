#!/usr/bin/env python3
"""CATL 生态链日监控 — HTML报告生成器

生成单页暗色科技风HTML报告，9大模块全覆盖。
移动端适配，适合微信阅读。
"""

import json, os
from config import *

# ── 工具函数 ──
def fmt_num(n, unit="", signed=False):
    """格式化数字"""
    if n is None: return "—"
    if abs(n) >= 10000:
        s = f"{n/10000:.2f}万{unit}"
    elif abs(n) >= 100:
        s = f"{n:.0f}{unit}"
    else:
        s = f"{n:.2f}{unit}"
    if signed and n > 0: return f"+{s}"
    return s

def color_pct(v):
    """涨跌颜色"""
    if v is None: return "#8b949e"
    return "#f85149" if v >= 0 else "#3fb950"

def icon_pct(v):
    """涨跌图标"""
    if v is None: return "—"
    return "🔴" if v >= 0 else "🟢"

def sign(v):
    """符号"""
    if v is None: return ""
    return "+" if v > 0 else ""

# ── CSS (外置以保持 clean) ──
CSS = r"""
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei","PingFang SC",sans-serif;
  background:#0a0e17; color:#e6edf3; line-height:1.5;
  padding:16px; min-height:100vh;
}
.wrap{max-width:900px;margin:0 auto}

/* ── 头部动画 ── */
.header{
  background:linear-gradient(135deg,#0a1628 0%,#0f3460 40%,#16213e 70%,#0a0e17 100%);
  border:1px solid #1e3a5f; border-radius:16px; padding:28px 20px 20px;
  margin-bottom:16px; text-align:center; position:relative; overflow:hidden;
}
.header::before{
  content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
  background:radial-gradient(circle at 30% 30%,rgba(63,185,80,0.08) 0%,transparent 50%),
             radial-gradient(circle at 70% 70%,rgba(88,166,255,0.06) 0%,transparent 50%);
  animation:pulse 4s ease-in-out infinite;
}
@keyframes pulse{0%,100%{opacity:0.6}50%{opacity:1}}
.header h1{font-size:1.6em;font-weight:700;position:relative;z-index:1;letter-spacing:1px}
.header .sub{color:#8b949e;font-size:0.85em;margin-top:6px;position:relative;z-index:1}
.header .badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:0.75em;font-weight:600;margin-top:8px;position:relative;z-index:1}
.badge-morning{background:rgba(88,166,255,0.15);color:#58a6ff}
.badge-evening{background:rgba(210,153,34,0.15);color:#d29922}

/* ── PEG 信号灯 ── */
.signal-box{
  background:#131a26; border:1px solid #1e2d45; border-radius:12px;
  padding:16px; margin-bottom:16px; text-align:center;
}
.signal-box .peg-v{font-size:1.4em;font-weight:700}
.signal-box .peg-label{font-size:0.82em;color:#8b949e;margin-top:4px}
.signal-box .peg-action{display:inline-block;padding:4px 16px;border-radius:8px;font-size:0.78em;font-weight:600;margin-top:6px}

/* ── KPI 网格 ── */
.kpi-grid{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
  gap:8px; margin-bottom:16px;
}
.kpi-card{
  background:#131a26; border:1px solid #1e2d45; border-radius:10px;
  padding:12px; text-align:center;
}
.kpi-card .label{color:#8b949e;font-size:0.7em;text-transform:uppercase;letter-spacing:1px}
.kpi-card .value{font-size:1.3em;font-weight:700;margin:4px 0 2px}
.kpi-card .sub{font-size:0.75em;color:#484f58}

/* ── 模块卡片 ── */
.module{
  background:#131a26; border:1px solid #1e2d45; border-radius:12px;
  padding:16px; margin-bottom:14px;
}
.module-hdr{display:flex;align-items:center;gap:8px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #1e2d45}
.module-hdr .icon{font-size:1.2em}
.module-hdr h2{font-size:0.95em;font-weight:600;color:#58a6ff;flex:1}
.module-hdr .status{font-size:0.72em;padding:2px 8px;border-radius:6px}

/* ── 表格 ── */
table{width:100%;border-collapse:collapse;font-size:0.8em}
th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #1e2d45}
th{color:#8b949e;font-weight:500;font-size:0.85em}
tr:hover{background:rgba(88,166,255,0.03)}

/* ── 新闻列表 ── */
.news-list{margin:0;padding:0;list-style:none}
.news-item{display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #1e2d45;align-items:flex-start}
.news-item:last-child{border-bottom:none}
.news-date{color:#484f58;font-size:0.7em;white-space:nowrap;min-width:42px;padding-top:1px}
.news-info{flex:1;min-width:0}
.news-info a{color:#e6edf3;text-decoration:none;font-size:0.82em;display:block;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}
.news-info a:hover{color:#58a6ff}
.news-info .src{color:#484f58;font-size:0.7em;margin-top:2px}

/* ── 原材料网格 ── */
.mat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.mat-card{background:rgba(255,255,255,0.02);border:1px solid #1e2d45;border-radius:8px;padding:10px;text-align:center}
.mat-card .name{font-size:0.72em;color:#8b949e}
.mat-card .price{font-size:1.1em;font-weight:700;margin:3px 0}
.mat-card .trend{font-size:0.7em;padding:1px 6px;border-radius:4px}

/* ── 预警栏 ── */
.alert{display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:8px;margin-bottom:14px;font-size:0.82em}
.alert-green{background:rgba(63,185,80,0.1);border:1px solid rgba(63,185,80,0.3);color:#3fb950}
.alert-yellow{background:rgba(210,153,34,0.1);border:1px solid rgba(210,153,34,0.3);color:#d29922}
.alert-red{background:rgba(248,81,73,0.1);border:1px solid rgba(248,81,73,0.3);color:#f85149}

/* ── Footer ── */
.footer{text-align:center;padding:20px 0 40px;color:#484f58;font-size:0.72em;line-height:1.8}
.footer a{color:#58a6ff;text-decoration:none}

/* ── 响应式 ── */
@media(max-width:600px){
  body{padding:10px}
  .header{padding:20px 14px}
  .header h1{font-size:1.3em}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .mat-grid{grid-template-columns:repeat(2,1fr)}
  .module{padding:12px}
}
"""


def build_header(data):
    """构建页面头部"""
    mode = data.get("mode", "日监控")
    badge_class = "badge-morning" if "早" in mode else "badge-evening"
    a = data.get("catl_a", {})
    price = a.get("price", "—") if a else "—"
    chg = a.get("change_pct") if a else None
    chg_str = f"{sign(chg)}{chg:.2f}%" if chg is not None else ""
    chg_clr = color_pct(chg)

    return f'''
<div class="header">
  <h1>🔋 宁德时代 · 生态链日监控</h1>
  <div class="sub">CATL Ecosystem Radar · {data["date"]} · 持仓{HOLDING_SHARES}股</div>
  <div class="sub" style="margin-top:2px">
    A股 <span style="color:{chg_clr};font-weight:600">¥{price} {chg_str}</span>
  </div>
  <span class="badge {badge_class}">{mode}</span>
</div>'''


def build_peg_signal(data):
    """PEG信号灯"""
    peg = data.get("peg")
    sig = data.get("peg_signal", {})
    pe = data.get("catl_pe", {})
    pe_val = pe.get("pe_ttm") if pe else None
    lf = data.get("lithium_futures", {})

    li_str = f"¥{lf['price']:.0f}/吨" if lf and lf.get("price") else "—"
    peg_str = f"{peg:.2f}" if peg else "—"
    pe_str = f"{pe_val:.1f}" if pe_val else "—"

    return f'''
<div class="signal-box" style="border-color:{sig.get('color','#1e2d45')}">
  <div class="peg-v" style="color:{sig.get('color','#8b949e')}">{sig.get('text','—')}</div>
  <div class="peg-label">
    PEG {peg_str} = PE {pe_str} / 增速 {GROWTH_ASSUMPTION}% ·
    碳酸锂期货 {li_str}
  </div>
  <span class="peg-action" style="background:rgba({sig.get('color','#8b949e').replace('#','')},0.12);color:{sig.get('color','#8b949e')}">
    {sig.get('level','—').upper()}
  </span>
</div>'''


def build_kpi_grid(data):
    """KPI指标卡片"""
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    peg = data.get("peg")
    sig = data.get("peg_signal", {})
    ah = data.get("ah_premium")
    fund = data.get("catl_fund", {}) or {}

    cards = []

    # A股
    chg = a.get("change_pct") if a else None
    cards.append(("CATL A股", f"¥{a['price']}" if a else "—",
                  f"{icon_pct(chg)} {sign(chg)}{chg:.1f}%" if chg is not None else "",
                  color_pct(chg)))

    # H股
    hchg = h.get("change_pct") if h else None
    cards.append(("H股", f"HK${h['price']}" if h else "—",
                  f"{f'{sign(hchg)}{hchg:.1f}%' if hchg else ''}",
                  color_pct(hchg)))

    # AH溢价
    ah_clr = "#f85149" if ah is not None and ah >= 0 else "#3fb950"
    cards.append(("AH溢价", f"{sign(ah)}{ah:.1f}%" if ah is not None else "—", "", ah_clr))

    # PEG
    cards.append(("PEG", f"{peg:.2f}" if peg is not None else "—", "", sig.get("color", "#8b949e")))

    # 成交额
    amt = a.get("amount", 0) / 1e8 if a else 0
    cards.append(("成交额", f"{amt:.1f}亿" if amt else "—", "", "#8b949e"))

    # 主力资金
    mn = fund.get("main_net", 0) / 1e4 if fund else 0
    mn_clr = "#f85149" if mn > 0 else "#3fb950" if mn < 0 else "#8b949e"
    cards.append(("主力净流入", f"{sign(mn)}{mn:.2f}亿" if mn else "—", "", mn_clr))

    rows = ""
    for label, value, sub, clr in cards:
        rows += f'<div class="kpi-card"><div class="label">{label}</div><div class="value" style="color:{clr}">{value}</div><div class="sub" style="color:{clr}">{sub}</div></div>'

    return f'<div class="kpi-grid">{rows}</div>'


def build_upstream(data):
    """模块二: 上游原材料"""
    mats = data.get("materials", {})
    upstream = data.get("upstream", {})
    avg = data.get("upstream_avg_change", 0)

    # 原材料卡片
    mat_cards = ""
    mat_order = ["碳酸锂(电池级)", "碳酸锂", "氢氧化锂", "电解钴", "硫酸镍", "磷酸铁锂", "六氟磷酸锂"]
    shown = set()
    for name in mat_order:
        if name in mats and name not in shown:
            m = mats[name]
            shown.add(name)
            display_name = name.replace("碳酸锂(电池级)", "碳酸锂")
            mat_cards += f'''
            <div class="mat-card">
              <div class="name">{display_name}</div>
              <div class="price">{m.get("price","—")}{m.get("unit","")}</div>
              <div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{m.get("trend",m.get("source",""))}</div>
            </div>'''
    # Add any remaining
    for name, m in mats.items():
        if name not in shown:
            shown.add(name)
            mat_cards += f'''
            <div class="mat-card">
              <div class="name">{name}</div>
              <div class="price">{m.get("price","—")}{m.get("unit","")}</div>
              <div class="trend" style="background:rgba(88,166,255,0.1);color:#58a6ff">{m.get("trend",m.get("source",""))}</div>
            </div>'''

    # 上游龙头表格
    upstream_rows = ""
    for name, s in upstream.items():
        clr = color_pct(s["change_pct"])
        upstream_rows += f'<tr><td>{name}</td><td style="color:{clr}">¥{s["price"]}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'

    avg_clr = color_pct(avg)

    return f'''
<div class="module">
  <div class="module-hdr"><span class="icon">⛏️</span><h2>上游原材料雷达</h2><span class="status" style="background:rgba(88,166,255,0.1);color:#58a6ff">平均 {sign(avg)}{avg:.1f}%</span></div>
  <div class="mat-grid">{mat_cards}</div>
  <table style="margin-top:12px">
    <tr><th>上游龙头</th><th>价格</th><th>涨跌幅</th></tr>
    {upstream_rows}
  </table>
</div>'''


def build_competitors(data):
    """模块四: 竞争格局"""
    comps = data.get("competitors", {})
    avg = data.get("competitor_avg_change", 0)

    rows = ""
    for name, s in comps.items():
        clr = color_pct(s["change_pct"])
        rows += f'<tr><td>{name}</td><td style="color:{clr}">¥{s["price"]}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'

    avg_clr = color_pct(avg)
    catl_a = data.get("catl_a", {})
    catl_chg = catl_a.get("change_pct") if catl_a else None
    catl_clr = color_pct(catl_chg)

    # 添加CATL自身到对比
    rows = f'<tr style="font-weight:600"><td>宁德时代 (CATL)</td><td style="color:{catl_clr}">¥{catl_a.get("price","—") if catl_a else "—"}</td><td style="color:{catl_clr}">{sign(catl_chg)}{catl_chg:.1f}%</td></tr>' + rows

    return f'''
<div class="module">
  <div class="module-hdr"><span class="icon">⚔️</span><h2>竞争格局</h2><span class="status" style="background:rgba(210,153,34,0.1);color:#d29922">CATL vs 同行</span></div>
  <table>
    <tr><th>公司</th><th>价格</th><th>涨跌幅</th></tr>
    {rows}
  </table>
</div>'''


def build_sectors(data):
    """模块五: 板块指数"""
    sectors = data.get("sectors", {})

    rows = ""
    for name, s in sectors.items():
        clr = color_pct(s["change_pct"])
        rows += f'<tr><td>{name}</td><td style="color:{clr}">{s["price"]:.2f}</td><td style="color:{clr}">{sign(s["change_pct"])}{s["change_pct"]:.1f}%</td></tr>'

    return f'''
<div class="module">
  <div class="module-hdr"><span class="icon">📊</span><h2>板块指数联动</h2></div>
  <table>
    <tr><th>板块</th><th>点位</th><th>涨跌幅</th></tr>
    {rows}
  </table>
</div>'''


def build_fund_flow(data):
    """资金流向"""
    fund = data.get("catl_fund") or {}
    nf = data.get("north_flow")

    # CATL资金
    fund_rows = ""
    fund_map = [
        ("主力净流入(今)", fund.get("main_net")),
        ("超大单", fund.get("huge_net")),
        ("大单", fund.get("big_net")),
        ("散户(小单)", fund.get("small_net")),
        ("3日主力", fund.get("three_day")),
        ("5日主力", fund.get("five_day")),
        ("10日主力", fund.get("ten_day")),
    ]
    for label, val in fund_map:
        if val is not None:
            clr = "#f85149" if val > 0 else "#3fb950"
            fund_rows += f'<tr><td>{label}</td><td style="color:{clr}">{sign(val)}{val/1e4:.2f}亿</td></tr>'

    # 北向资金
    nf_html = ""
    if nf:
        net = nf["today"]["net"]
        nf_clr = "#f85149" if net > 0 else "#3fb950"
        nf_html = f'''
        <div style="margin-top:12px;padding:10px;background:rgba(88,166,255,0.05);border-radius:8px">
          <span style="color:#8b949e;font-size:0.78em">北向资金 · {nf["today"]["date"]}</span>
          <span style="color:{nf_clr};font-size:1.1em;font-weight:700;margin-left:8px">{sign(net)}{net:.1f}亿</span>
        </div>'''

    if not fund_rows and not nf_html:
        return ""

    return f'''
<div class="module">
  <div class="module-hdr"><span class="icon">💰</span><h2>资金面</h2></div>
  {('<table>'+fund_rows+'</table>') if fund_rows else ''}
  {nf_html}
</div>'''


def build_news_module(data):
    """新闻资讯"""
    all_news = data.get("news", {})

    # CATL头条
    catl_news = all_news.get("宁德时代", [])[:3]
    catl_html = ""
    for n in catl_news:
        catl_html += f'''
        <li class="news-item">
          <span class="news-date">{n["date"]}</span>
          <span class="news-info">
            <a href="{n["url"]}" target="_blank">{n["title"]}</a>
            <span class="src">{n["source"]}</span>
          </span>
        </li>'''

    # 技术/行业新闻
    tech_news_html = ""
    for kw in ["固态电池", "储能", "钠离子电池", "换电"]:
        kw_news = all_news.get(kw, [])[:2]
        if kw_news:
            tech_news_html += f'<div style="margin-bottom:10px"><span style="color:#58a6ff;font-size:0.78em;font-weight:600">{kw}</span>'
            for n in kw_news:
                tech_news_html += f'''
                <li class="news-item">
                  <span class="news-date">{n["date"]}</span>
                  <span class="news-info">
                    <a href="{n["url"]}" target="_blank">{n["title"]}</a>
                    <span class="src">{n["source"]}</span>
                  </span>
                </li>'''
            tech_news_html += '</div>'

    return f'''
<div class="module">
  <div class="module-hdr"><span class="icon">📰</span><h2>资讯中心</h2></div>
  <div style="margin-bottom:12px">
    <span style="color:#f85149;font-size:0.8em;font-weight:600">🔥 CATL 头条</span>
    <ul class="news-list" style="margin-top:4px">{catl_html}</ul>
  </div>
  {tech_news_html}
</div>'''


def build_warnings(data):
    """预警信号"""
    warnings = []
    alerts = []

    # PEG预警
    peg = data.get("peg")
    if peg and peg < PEG_UNDERVALUE:
        alerts.append(("green", f"PEG={peg:.2f} < {PEG_UNDERVALUE}，处于低估区间，可关注加仓机会"))
    elif peg and peg > PEG_OVERVALUE:
        alerts.append(("red", f"PEG={peg:.2f} > {PEG_OVERVALUE}，偏高区间，注意风险控制"))

    # AH溢价
    ah = data.get("ah_premium")
    if ah is not None:
        if ah > 40:
            alerts.append(("yellow", f"AH溢价={ah:.1f}% > 40%，A股相对H股明显偏贵"))
        elif ah < 0:
            alerts.append(("green", f"AH溢价={ah:.1f}% < 0%，A股折价，可关注"))

    # 上游龙头异动
    upstream = data.get("upstream", {})
    for name, s in upstream.items():
        if abs(s["change_pct"]) > 5:
            alerts.append(("yellow", f"{name} {sign(s['change_pct'])}{s['change_pct']:.1f}%，上游异动"))

    # CATL放量
    a = data.get("catl_a", {})
    if a and a.get("amount", 0) > 10e8:  # >100亿
        alerts.append(("yellow", f"CATL成交额{a['amount']/1e8:.0f}亿，放量明显"))

    if not alerts:
        return '''<div class="alert alert-green">🟢 今日无异常预警信号，所有指标正常</div>'''

    html = ""
    for level, msg in alerts:
        html += f'<div class="alert alert-{level}">{msg}</div>'

    return html


def build_footer(data):
    """页脚"""
    return f'''
<div class="footer">
  🤖 Hermes · CATL Ecosystem Monitor v1.0<br>
  {data["datetime"]} · 数据来源: 新浪财经 / 腾讯 / 东方财富 / 生意社<br>
  📊 <a href="{PAGES_URL}" target="_blank">完整报告</a> ·
  <a href="https://github.com/{REPO_OWNER}/{REPO_NAME}" target="_blank">GitHub</a><br>
  ⚠️ 仅供参考，不构成投资建议
</div>'''


def generate(data):
    """生成完整HTML报告"""
    html = f'''<!DOCTYPE html>
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
  {build_peg_signal(data)}
  {build_kpi_grid(data)}
  {build_warnings(data)}
  {build_upstream(data)}
  {build_competitors(data)}
  {build_sectors(data)}
  {build_fund_flow(data)}
  {build_news_module(data)}
  {build_footer(data)}
</div>
</body>
</html>'''

    return html


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
