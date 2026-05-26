     1|#!/usr/bin/env python3
     2|"""CATL 生态链日监控 — 数据采集模块 v1.3
     3|
     4|新增: 上游多周期涨跌+走势小结 / 原材料半年高低位 / 上游仅5大核心品种
     5|"""
     6|
     7|import urllib.request, ssl, json, re, time, statistics
     8|from config import *
     9|
    10|ssl_ctx = ssl.create_default_context()
    11|ssl_ctx.check_hostname = False
    12|ssl_ctx.verify_mode = ssl.CERT_NONE
    13|H_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    14|H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"}
    15|
    16|
    17|def get(url, enc="utf-8", t=10, headers=None):
    18|    req = urllib.request.Request(url, headers=headers or H_SINA)
    19|    return urllib.request.urlopen(req, timeout=t, context=ssl_ctx).read().decode(enc, errors="replace")
    20|
    21|
    22|def get_json(url, t=10):
    23|    return json.loads(get(url, t=t, headers=H_EM))
    24|
    25|
    26|# ═══════════════════════════════════════════
    27|# 模块一: CATL 核心 + K线 + 大盘
    28|# ═══════════════════════════════════════════
    29|
    30|def fetch_catl_a():
    31|    try:
    32|        raw = get("https://hq.sinajs.cn/list=sz300750", "gbk")
    33|        m = re.search(r'"(.+?)"', raw)
    34|        if not m: return None
    35|        p = m.group(1).split(",")
    36|        if len(p) < 10: return None
    37|        price, prev = float(p[3]), float(p[2])
    38|        return {
    39|            "name": p[0], "price": price, "prev_close": prev,
    40|            "open": float(p[1]), "high": float(p[4]), "low": float(p[5]),
    41|            "volume": int(p[8]) if p[8] else 0, "amount": float(p[9]) if p[9] else 0,
    42|            "change": round(price - prev, 2),
    43|            "change_pct": round((price - prev) / prev * 100, 2) if prev else 0,
    44|        }
    45|    except: return None
    46|
    47|
    48|def fetch_catl_h():
    49|    try:
    50|        raw = get("https://hq.sinajs.cn/list=hk03750", "gbk")
    51|        m = re.search(r'"(.+?)"', raw)
    52|        if not m: return None
    53|        p = m.group(1).split(",")
    54|        if len(p) < 10: return None
    55|        # 港股Sina格式: [0]英文名 [1]中文名 [2]今开 [3]昨收 [4]最高 [5]最低 [6]现价
    56|        price = float(p[6]) if len(p) > 6 else float(p[3])
    57|        prev = float(p[3])
    58|        return {"price": price, "prev_close": prev,
    59|                "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
    60|    except: return None
    61|
    62|
    63|def fetch_catl_pe():
    64|    """CATL PE(TTM) — 腾讯 qt[39] (已验证: 23.60, 非 qt[58]的72.5)"""
    65|    try:
    66|        raw = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,1,qfq", headers=H_EM)
    67|        d = json.loads(raw)
    68|        qt = d.get("data", {}).get("sz300750", {}).get("qt", {}).get("sz300750", [])
    69|        if len(qt) > 39 and qt[39]:
    70|            return {"pe_ttm": float(qt[39])}
    71|    except:
    72|        pass
    73|    return None
    74|
    75|
    76|def fetch_catl_kline(days=60):
    77|    try:
    78|        raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,{days},qfq", headers=H_EM)
    79|        d = json.loads(raw)
    80|        klines = d.get("data", {}).get("sz300750", {}).get("qfqday", []) or \
    81|                 d.get("data", {}).get("sz300750", {}).get("day", [])
    82|        result = []
    83|        for k in klines:
    84|            parts = k.split(",") if isinstance(k, str) else k
    85|            if len(parts) >= 6:
    86|                result.append({"date": parts[0], "open": float(parts[1]), "close": float(parts[2]),
    87|                               "high": float(parts[3]), "low": float(parts[4]),
    88|                               "volume": float(parts[5]) if parts[5] else 0})
    89|        return result
    90|    except: return []
    91|
    92|
    93|def fetch_hk_kline(days=750):
    94|    """CATL H股(00750)历史K线"""
    95|    try:
    96|        raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk03750,day,,,{days},qfq", headers=H_EM)
    97|        d = json.loads(raw)
    98|        klines = d.get("data", {}).get("hk03750", {}).get("qfqday", []) or \
    99|                 d.get("data", {}).get("hk03750", {}).get("day", [])
   100|        result = []
   101|        for k in klines:
   102|            parts = k.split(",") if isinstance(k, str) else k
   103|            if len(parts) >= 6:
   104|                result.append({"date": parts[0], "open": float(parts[1]), "close": float(parts[2]),
   105|                               "high": float(parts[3]), "low": float(parts[4]),
   106|                               "volume": float(parts[5]) if parts[5] else 0})
   107|        return result
   108|    except: return []
   109|
   110|
   111|def compute_ah_history(hk_kline, a_kline, fx_rate=0.92):
   112|    """计算AH溢价历史序列：按日期对齐A股和H股收盘价"""
   113|    if not hk_kline or not a_kline: return []
   114|    a_map = {k["date"]: k["close"] for k in a_kline}
   115|    result = []
   116|    for hk in hk_kline:
   117|        d = hk["date"]
   118|        if d in a_map:
   119|            h_cny = hk["close"] * fx_rate
   120|            if h_cny > 0:
   121|                premium = round((a_map[d] - h_cny) / h_cny * 100, 2)
   122|                result.append({"date": d, "a_close": a_map[d], "h_close": hk["close"],
   123|                               "h_cny": round(h_cny, 2), "premium": premium})
   124|    return result
   125|
   126|
   127|def fetch_ah_ranking(a_price, h_price, fx_rate=0.92):
   128|    """获取CATL在AH股中的溢价排名（约15只主流AH股）"""
   129|    AH_PEERS = [
   130|        ("招商银行", "sh600036", "hk03968"),
   131|        ("中国平安", "sh601318", "hk02318"),
   132|        ("比亚迪", "sz002594", "hk01211"),
   133|        ("海螺水泥", "sh600585", "hk00914"),
   134|        ("青岛啤酒", "sh600600", "hk00168"),
   135|        ("工商银行", "sh601398", "hk01398"),
   136|        ("建设银行", "sh601939", "hk00939"),
   137|        ("中国石油", "sh601857", "hk00857"),
   138|        ("中国神华", "sh601088", "hk01088"),
   139|        ("中芯国际", "sh688981", "hk00981"),
   140|        ("紫金矿业", "sh601899", "hk02899"),
   141|        ("潍柴动力", "sz000338", "hk02338"),
   142|        ("福耀玻璃", "sh600660", "hk03606"),
   143|        ("中国中车", "sh601766", "hk01766"),
   144|        ("中国中铁", "sh601390", "hk00390"),
   145|    ]
   146|    premiums = []
   147|    catl_h_cny = (h_price or 0) * fx_rate
   148|    catl_premium = round((a_price - catl_h_cny) / catl_h_cny * 100, 2) if catl_h_cny else 0
   149|
   150|    for name, a_code, h_code in AH_PEERS:
   151|        try:
   152|            a_raw = get(f"https://hq.sinajs.cn/list={a_code}", "gbk")
   153|            h_raw = get(f"https://hq.sinajs.cn/list={h_code}", "gbk")
   154|            a_m = re.search(r'"(.+?)"', a_raw)
   155|            h_m = re.search(r'"(.+?)"', h_raw)
   156|            if not a_m or not h_m: continue
   157|            a_p = float(a_m.group(1).split(",")[3])
   158|            h_p = float(h_m.group(1).split(",")[3])
   159|            if not a_p or not h_p: continue
   160|            h_cny = h_p * fx_rate
   161|            item_premium = round((a_p - h_cny) / h_cny * 100, 2)
   162|            premiums.append({"name": name, "a_price": a_p, "h_price": h_p,
   163|                             "premium": item_premium, "h_cny": round(h_cny, 2)})
   164|        except: continue
   165|
   166|    premiums.append({"name": "宁德时代", "a_price": a_price, "h_price": h_price,
   167|                     "premium": catl_premium, "h_cny": round(catl_h_cny, 2)})
   168|    premiums.sort(key=lambda x: x["premium"])
   169|    rank = next((i+1 for i, p in enumerate(premiums) if p["name"] == "宁德时代"), len(premiums))
   170|    return {"peers": premiums, "rank": rank, "total": len(premiums),
   171|            "catl_premium": catl_premium, "is_extreme": catl_premium < -25}
   172|
   173|
   174|def fetch_market_indices():
   175|    results = {}
   176|    for name, code in MARKET_INDICES.items():
   177|        try:
   178|            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
   179|            m = re.search(r'"(.+?)"', raw)
   180|            if not m: continue
   181|            p = m.group(1).split(",")
   182|            if len(p) < 10: continue
   183|            price, prev = float(p[3]), float(p[2])
   184|            results[name] = {"price": price,
   185|                             "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
   186|        except: pass
   187|    return results
   188|
   189|
   190|def fetch_catl_fund_flow():
   191|    try:
   192|        d = get_json("https://push2.eastmoney.com/api/qt/stock/get?secid=0.300750&fields=f62,f64,f66,f184,f63,f65,f99,f100,f101")
   193|        data = d.get("data", {})
   194|        if not data or not data.get("f62"): return None
   195|        return {"main_net": data.get("f62", 0), "huge_net": data.get("f64", 0),
   196|                "big_net": data.get("f66", 0), "small_net": data.get("f184", 0),
   197|                "main_pct": data.get("f63", 0), "today_in": data.get("f65", 0),
   198|                "three_day": data.get("f99", 0), "five_day": data.get("f100", 0),
   199|                "ten_day": data.get("f101", 0)}
   200|    except: return None
   201|
   202|
   203|# ═══════════════════════════════════════════
   204|# 模块二: 上游原材料 (仅5大核心)
   205|# ═══════════════════════════════════════════
   206|
   207|def fetch_lithium_futures():
   208|    try:
   209|        raw = get("https://hq.sinajs.cn/list=nf_LC0", "gbk")
   210|        m = re.search(r'"(.+?)"', raw)
   211|        if not m: return None
   212|        p = m.group(1).split(",")
   213|        if len(p) > 8:
   214|            return {"price": float(p[3]), "prev_settle": float(p[4]) if p[4] else 0,
   215|                    "change_pct": round((float(p[3]) - float(p[4])) / float(p[4]) * 100, 2) if p[4] and float(p[4]) else 0,
   216|                    "name": p[0]}
   217|    except: pass
   218|    return None
   219|
   220|
   221|def fetch_material_prices():
   222|    """原材料价格 — 仅5大核心品种，带半年高低位"""
   223|    materials = {}
   224|    ppi_map = {
   225|        "碳酸锂(电池级)": ("https://www.100ppi.com/price/detail-2928.html", 10000),
   226|        "氢氧化锂": ("https://www.100ppi.com/price/detail-2858.html", 10000),
   227|        "磷酸铁锂": ("https://www.100ppi.com/price/detail-2762.html", 10000),
   228|        "电解钴": ("https://www.100ppi.com/price/detail-2758.html", 10000),
   229|        "六氟磷酸锂": ("https://www.100ppi.com/price/detail-3206.html", 10000),
   230|    }
   231|    for name, (url, divisor) in ppi_map.items():
   232|        try:
   233|            raw = get(url, "gbk", t=8)
   234|            for pat in [r'最新价.*?(\d[\d,]*\.?\d*)', r'价格.*?(\d[\d,]*\.?\d*)',
   235|                        r'>(\d[\d,]*\.?\d*)\s*<.*?元/吨', r'\b(\d[\d,]*\.?\d*)\s*元\s*/\s*吨\b']:
   236|                m = re.search(pat, raw)
   237|                if m:
   238|                    v = m.group(1).replace(",", "")
   239|                    materials[name] = {"price": round(float(v) / divisor, 2),
   240|                                       "unit": "万元/吨" if divisor > 100 else "元/吨", "source": "100ppi"}
   241|                    break
   242|        except: pass
   243|
   244|    # Fallback: 用参考价格 + 半年高低位
   245|    for mat_name in MATERIAL_DISPLAY_ORDER:
   246|        ref = MATERIAL_REFERENCE.get(mat_name, {})
   247|        if mat_name not in materials:
   248|            price = ref.get("price", 0)
   249|            low, high = ref.get("low_6m", price), ref.get("high_6m", price)
   250|            materials[mat_name] = {"price": price, "unit": ref.get("unit", "元/吨"), "source": "参考"}
   251|        else:
   252|            price = materials[mat_name]["price"]
   253|            low, high = ref.get("low_6m", price), ref.get("high_6m", price)
   254|
   255|        # 计算半年区间位置
   256|        if high > low and price > 0:
   257|            pos = round((price - low) / (high - low) * 100, 1)
   258|            if pos < 15:
   259|                pos_text = f"距半年低点{price-low:.0f}元 · 低位"
   260|            elif pos < 35:
   261|                pos_text = f"半年P{pos:.0f}% · 偏低"
   262|            elif pos < 65:
   263|                pos_text = f"半年P{pos:.0f}% · 中部"
   264|            elif pos < 85:
   265|                pos_text = f"半年P{pos:.0f}% · 偏高"
   266|            else:
   267|                pos_text = f"距半年高点{high-price:.0f}元 · 高位"
   268|        else:
   269|            pos, pos_text = 50, "参考"
   270|        materials[mat_name]["pos_text"] = pos_text
   271|        materials[mat_name]["position"] = pos
   272|        materials[mat_name]["low_6m"] = low
   273|        materials[mat_name]["high_6m"] = high
   274|
   275|    return materials
   276|
   277|
   278|# ═══════════════════════════════════════════
   279|# 模块三-七: 股票批量 + 板块 + 新闻 + 北向
   280|# ═══════════════════════════════════════════
   281|
   282|def fetch_stock_batch(stock_map):
   283|    results = {}
   284|    for name, code in stock_map.items():
   285|        try:
   286|            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
   287|            m = re.search(r'"(.+?)"', raw)
   288|            if not m: continue
   289|            p = m.group(1).split(",")
   290|            if len(p) < 10: continue
   291|            price, prev = float(p[3]), float(p[2])
   292|            results[name] = {"code": code, "price": price,
   293|                             "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
   294|        except: pass
   295|    return results
   296|
   297|
   298|def enrich_stocks_period_changes(stocks, days=35):
   299|    """为上游/竞争股票补充多周期涨跌幅 (5/15/30日) + 走势小结"""
   300|    if not stocks: return stocks
   301|
   302|    for name, s in stocks.items():
   303|        code = s.get("code", "")
   304|        if not code: continue
   305|        try:
   306|            raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{days},qfq", headers=H_EM)
   307|            d = json.loads(raw)
   308|            klines = d.get("data", {}).get(code, {}).get("qfqday", []) or \
   309|                     d.get("data", {}).get(code, {}).get("day", [])
   310|            if not klines or len(klines) < 5: continue
   311|
   312|            closes = []
   313|            for k in klines:
   314|                if isinstance(k, str):
   315|                    closes.append(float(k.split(",")[2]))
   316|                elif isinstance(k, list):
   317|                    closes.append(float(k[2]))
   318|                elif isinstance(k, dict):
   319|                    closes.append(float(k.get("close", 0)))
   320|            current = s["price"]
   321|
   322|            periods = {}
   323|            for pname, pdays in [("5日", 5), ("15日", 15), ("30日", 30)]:
   324|                if len(closes) >= pdays:
   325|                    start = closes[-pdays]
   326|                    if start and start > 0:
   327|                        periods[pname] = round((current - start) / start * 100, 2)
   328|                    else:
   329|                        periods[pname] = None
   330|                else:
   331|                    periods[pname] = None
   332|            s["periods"] = periods
   333|
   334|            # 走势小结
   335|            chg_5 = periods.get("5日")
   336|            chg_15 = periods.get("15日")
   337|            chg_30 = periods.get("30日")
   338|
   339|            summary = ""
   340|            if chg_30 is not None and chg_15 is not None and chg_5 is not None:
   341|                if chg_30 < -10: summary = "深度回调"
   342|                elif chg_30 < -5: summary = "持续走弱"
   343|                elif chg_30 > 10: summary = "强势上涨"
   344|                elif chg_30 > 5: summary = "稳步上行"
   345|                else: summary = "横盘震荡"
   346|                if chg_5 < -5 and chg_15 < 0: summary += "，加速下跌"
   347|                elif chg_5 > 5 and chg_15 > 0: summary += "，加速上涨"
   348|                elif chg_5 * chg_15 < 0: summary += "，短期反转"
   349|            elif chg_5 is not None:
   350|                summary = "短期走弱" if chg_5 < -3 else "短期走强" if chg_5 > 3 else "横盘"
   351|            else:
   352|                summary = "数据不足"
   353|            s["trend_summary"] = summary
   354|        except:
   355|            s["periods"] = {}
   356|            s["trend_summary"] = "—"
   357|    return stocks
   358|
   359|
   360|def fetch_sector_indices():
   361|    results = {}
   362|    for name, code in SECTOR_INDICES.items():
   363|        try:
   364|            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
   365|            m = re.search(r'"(.+?)"', raw)
   366|            if not m: continue
   367|            p = m.group(1).split(",")
   368|            if len(p) < 10: continue
   369|            price, prev = float(p[3]), float(p[2])
   370|            results[name] = {"price": price,
   371|                             "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
   372|        except: pass
   373|    return results
   374|
   375|
   376|def fetch_news(keyword, count=5):
   377|    try:
   378|        params = {"cb": "jQ", "param": json.dumps({
   379|            "uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"],
   380|            "client": "web", "clientType": "web", "clientVersion": "curr",
   381|            "paramNum": 20, "pageNum": 1, "pageSize": count})}
   382|        raw = get("https://search-api-web.eastmoney.com/search/jsonp?" + urllib.parse.urlencode(params), headers=H_EM)
   383|        m = re.search(r'jQ\((.*)\)\s*$', raw.strip())
   384|        if not m: return []
   385|        return [{"title": a.get("title", "").replace("<em>", "").replace("</em>", ""),
   386|                 "date": (a.get("date", "") or "")[:10],
   387|                 "source": a.get("mediaName", ""),
   388|                 "url": a.get("url", ""),
   389|                 "content": (a.get("content", "") or "").replace("<em>", "").replace("</em>", "")[:120]}  # 正文摘要前120字，剥离东方财富高亮标签
   390|                for a in json.loads(m.group(1)).get("result", {}).get("cmsArticleWebOld", [])]
   391|    except: return []
   392|
   393|
   394|def fetch_all_news():
   395|    """批量获取所有维度新闻（含正文摘要）"""
   396|    results = {}
   397|    for category, keywords in NEWS_KEYWORDS.items():
   398|        all_articles = []
   399|        for kw in keywords:
   400|            articles = fetch_news(kw, count=3)
   401|            for a in articles:
   402|                # 去重
   403|                if a["url"] not in {x["url"] for x in all_articles}:
   404|                    all_articles.append(a)
   405|        results[category] = all_articles[:5]  # 每类最多5条
   406|    return results
   407|
   408|
   409|def fetch_north_flow():
   410|    try:
   411|        d = get_json("https://push2.eastmoney.com/api/qt/kamt.kline/get?fields1=f1,f3&fields2=f51,f52,f53,f54&klt=101&lmt=5")
   412|        klines = d.get("data", {}).get("klines", [])
   413|        if not klines: return None
   414|        today = klines[-1].split(",")
   415|        yesterday = klines[-2].split(",") if len(klines) > 1 else today
   416|        return {"today": {"date": today[0], "net": round(float(today[1]), 2)},
   417|                "yesterday": {"date": yesterday[0], "net": round(float(yesterday[1]), 2)} if yesterday != today else None}
   418|    except: return None
   419|
   420|
   421|def fetch_nev_sector():
   422|    try:
   423|        d = get_json("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&fields=f2,f3,f12,f14&fid=f3&fs=b:BK0493")
   424|        return {"total_stocks": d.get("data", {}).get("total", 0)}
   425|    except: return None
   426|
   427|
   428|def fetch_week_flow():
   429|    """CATL 近5日每日主力资金流向"""
   430|    try:
   431|        # 多试几个endpoint
   432|        for url in [
   433|            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=0.300750&fields1=f1,f3&fields2=f51,f52,f53&lmt=6",
   434|            "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=0.300750&fields1=f1,f3&fields2=f51,f52,f53&lmt=6",
   435|        ]:
   436|            try:
   437|                raw = urllib.request.urlopen(
   438|                    urllib.request.Request(url, headers=H_EM), timeout=5, context=ssl_ctx
   439|                ).read().decode()
   440|                d = json.loads(raw)
   441|                klines = d.get("data", {}).get("klines", [])
   442|                if klines:
   443|                    result = []
   444|                    for k in klines:
   445|                        parts = k.split(",")
   446|                        if len(parts) >= 3:
   447|                            result.append({
   448|                                "date": parts[0],
   449|                                "main_net": round(float(parts[1]) / 1e8, 2),
   450|                            })
   451|                    return result
   452|            except:
   453|                continue
   454|        return []
   455|    except:
   456|        return []
   457|
   458|
   459|# ═══════════════════════════════════════════
   460|# 模块七: P0/P1 新增 — 分析师预期 + 北向增强 + 财务 + 装机
   461|# ═══════════════════════════════════════════
   462|
   463|def fetch_analyst_consensus():
   464|    """分析师一致预期 — 东方财富 F10 ProfitForecast"""
   465|    try:
   466|        d = get_json("https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code=SZ300750")
   467|        pjtj = d.get("pjti", d.get("pjtj", []))
   468|        if not pjtj:
   469|            for k in d:
   470|                if isinstance(d[k], list) and len(d[k]) > 0:
   471|                    pjtj = d[k]; break
   472|        result = {"periods": [], "latest": None}
   473|        for p in pjtj:
   474|            period = {
   475|                "window": p.get("DATE_TYPE", ""),
   476|                "rating": p.get("COMPRE_RATING", ""),
   477|                "rating_num": p.get("COMPRE_RATING_NUM", 0),
   478|                "org_num": p.get("RATING_ORG_NUM", 0),
   479|                "buy_num": p.get("RATING_BUY_NUM", 0),
   480|                "add_num": p.get("RATING_ADD_NUM", 0),
   481|                "neutral_num": p.get("RATING_NEUTRAL_NUM", 0),
   482|                "reduce_num": p.get("RATING_REDUCE_NUM", 0),
   483|                "sale_num": p.get("RATING_SALE_NUM", 0),
   484|            }
   485|            result["periods"].append(period)
   486|        if result["periods"]:
   487|            result["latest"] = result["periods"][0]
   488|        return result if result["latest"] else None
   489|    except:
   490|        return None
   491|
   492|
   493|def fetch_analyst_eps():
   494|    """一致预期 EPS — 东财盈利预测 yctj_chart"""
   495|    try:
   496|        d = get_json("https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code=SZ300750")
   497|        chart = d.get("yctj_chart", [])
   498|        result = []
   499|        for y in chart:
   500|            eps = y.get("EPS"); pe = y.get("PE")
   501|