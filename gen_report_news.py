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

    impact_cards = _gen_impact_cards(all_news, s, data)

    return f'''<div class="module">
  <div class="module-hdr"><span class="icon">📰</span><h2>本周重大资讯 (5/19-5/25)</h2></div>
  {sections_html}
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #1e2d45">
    <div style="font-size:0.82em;font-weight:600;color:#d29922;margin-bottom:10px">📋 本周资讯对宁德时代的影响评估</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:8px">{impact_cards}</div>
  </div>
</div>'''


def _gen_impact_cards(all_news, s, data):
    """生成6张影响评估卡片"""
    peg_sig = s.get("peg", {})
    streak = s.get("streak", {})
    li = s.get("lithium", {})
    ma60 = s.get("ma60_dist", {})
    a = data.get("catl_a", {})

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
