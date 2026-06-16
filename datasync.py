#!/usr/bin/env python3
"""CATL 生态链日监控 — 数据采集模块 v1.3

新增: 上游多周期涨跌+走势小结 / 原材料半年高低位 / 上游仅5大核心品种
"""

import urllib.request, ssl, json, re, time, statistics
from config import *

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
H_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"}


def fetch_analyst_eps(code="300750"):
    """一致预期EPS — 东财F10 ProfitForecast (实时更新)"""
    try:
        prefix = "SZ" if (code.startswith("0") or code.startswith("3")) else "SH"
        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code={prefix}{code}"
        d = get_json(url)
        chart = d.get("yctj_chart", [])
        result = []
        for y in chart:
            eps = y.get("EPS")
            result.append({
                "year": y.get("YEAR", ""),
                "mark": y.get("YEAR_MARK", ""),  # A=实际 E=预测
                "eps": float(eps) if eps else None,
                "pe": float(y["PE"]) if y.get("PE") else None,
                "roe": float(y["ROE"]) if y.get("ROE") else None,
            })
        return result if result else None
    except Exception:
        return None


def calc_peg_from_analyst(analyst_eps, current_pe):
    """从分析师一致预期计算PEG和增长率"""
    if not analyst_eps or len(analyst_eps) < 2 or not current_pe:
        return None
    actual_eps = forecast_eps = None
    for item in analyst_eps:
        eps = item.get("eps")
        if not eps or eps <= 0:
            continue
        if item.get("mark") == "A":
            actual_eps = eps
        elif item.get("mark") == "E" and forecast_eps is None:
            forecast_eps = eps
    if not actual_eps or not forecast_eps:
        valid = [i for i in analyst_eps if i.get("eps") and i["eps"] > 0]
        if len(valid) >= 2:
            actual_eps, forecast_eps = valid[0]["eps"], valid[1]["eps"]
        else:
            return None
    growth = (forecast_eps - actual_eps) / actual_eps * 100
    peg = round(current_pe / growth, 2) if growth > 0 else None
    return {"growth": round(growth, 1), "peg": peg, "actual_eps": actual_eps, "forecast_eps": forecast_eps}


def get(url, enc="utf-8", t=10, headers=None):
    req = urllib.request.Request(url, headers=headers or H_SINA)
    return urllib.request.urlopen(req, timeout=t, context=ssl_ctx).read().decode(enc, errors="replace")


def get_json(url, t=10):
    return json.loads(get(url, t=t, headers=H_EM))


# ═══════════════════════════════════════════
# 模块一: CATL 核心 + K线 + 大盘
# ═══════════════════════════════════════════

def fetch_catl_a():
    try:
        raw = get("https://hq.sinajs.cn/list=sz300750", "gbk")
        m = re.search(r'"(.+?)"', raw)
        if not m: return None
        p = m.group(1).split(",")
        if len(p) < 10: return None
        price, prev = float(p[3]), float(p[2])
        return {
            "name": p[0], "price": price, "prev_close": prev,
            "open": float(p[1]), "high": float(p[4]), "low": float(p[5]),
            "volume": int(p[8]) if p[8] else 0, "amount": float(p[9]) if p[9] else 0,
            "change": round(price - prev, 2),
            "change_pct": round((price - prev) / prev * 100, 2) if prev else 0,
        }
    except: return None


def fetch_catl_h():
    try:
        raw = get("https://hq.sinajs.cn/list=hk03750", "gbk")
        m = re.search(r'"(.+?)"', raw)
        if not m: return None
        p = m.group(1).split(",")
        if len(p) < 10: return None
        price, prev = float(p[3]), float(p[2])
        return {"price": price, "prev_close": prev,
                "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
    except: return None


def fetch_catl_pe():
    """CATL PE(TTM) — 腾讯 qt[39] (已验证: 23.60, 非 qt[58]的72.5)"""
    try:
        raw = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,1,qfq", headers=H_EM)
        d = json.loads(raw)
        qt = d.get("data", {}).get("sz300750", {}).get("qt", {}).get("sz300750", [])
        if len(qt) > 39 and qt[39]:
            return {"pe_ttm": float(qt[39])}
    except:
        pass
    return None


def fetch_catl_kline(days=60):
    try:
        raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,{days},qfq", headers=H_EM)
        d = json.loads(raw)
        klines = d.get("data", {}).get("sz300750", {}).get("qfqday", []) or \
                 d.get("data", {}).get("sz300750", {}).get("day", [])
        result = []
        for k in klines:
            parts = k.split(",") if isinstance(k, str) else k
            if len(parts) >= 6:
                result.append({"date": parts[0], "open": float(parts[1]), "close": float(parts[2]),
                               "high": float(parts[3]), "low": float(parts[4]),
                               "volume": float(parts[5]) if parts[5] else 0})
        return result
    except: return []


def fetch_hk_kline(days=750):
    """CATL H股(00750)历史K线"""
    try:
        raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk03750,day,,,{days},qfq", headers=H_EM)
        d = json.loads(raw)
        klines = d.get("data", {}).get("hk03750", {}).get("qfqday", []) or \
                 d.get("data", {}).get("hk03750", {}).get("day", [])
        result = []
        for k in klines:
            parts = k.split(",") if isinstance(k, str) else k
            if len(parts) >= 6:
                result.append({"date": parts[0], "open": float(parts[1]), "close": float(parts[2]),
                               "high": float(parts[3]), "low": float(parts[4]),
                               "volume": float(parts[5]) if parts[5] else 0})
        return result
    except: return []


def compute_ah_history(hk_kline, a_kline, fx_rate=0.92):
    """计算AH溢价历史序列：按日期对齐A股和H股收盘价"""
    if not hk_kline or not a_kline: return []
    a_map = {k["date"]: k["close"] for k in a_kline}
    result = []
    for hk in hk_kline:
        d = hk["date"]
        if d in a_map:
            h_cny = hk["close"] * fx_rate
            if h_cny > 0:
                premium = round((a_map[d] - h_cny) / h_cny * 100, 2)
                result.append({"date": d, "a_close": a_map[d], "h_close": hk["close"],
                               "h_cny": round(h_cny, 2), "premium": premium})
    return result


def fetch_ah_ranking(a_price, h_price, fx_rate=0.92):
    """获取CATL在AH股中的溢价排名（约15只主流AH股）"""
    AH_PEERS = [
        ("招商银行", "sh600036", "hk03968"),
        ("中国平安", "sh601318", "hk02318"),
        ("比亚迪", "sz002594", "hk01211"),
        ("海螺水泥", "sh600585", "hk00914"),
        ("青岛啤酒", "sh600600", "hk00168"),
        ("工商银行", "sh601398", "hk01398"),
        ("建设银行", "sh601939", "hk00939"),
        ("中国石油", "sh601857", "hk00857"),
        ("中国神华", "sh601088", "hk01088"),
        ("中芯国际", "sh688981", "hk00981"),
        ("紫金矿业", "sh601899", "hk02899"),
        ("潍柴动力", "sz000338", "hk02338"),
        ("福耀玻璃", "sh600660", "hk03606"),
        ("中国中车", "sh601766", "hk01766"),
        ("中国中铁", "sh601390", "hk00390"),
    ]
    premiums = []
    catl_h_cny = (h_price or 0) * fx_rate
    catl_premium = round((a_price - catl_h_cny) / catl_h_cny * 100, 2) if catl_h_cny else 0

    for name, a_code, h_code in AH_PEERS:
        try:
            a_raw = get(f"https://hq.sinajs.cn/list={a_code}", "gbk")
            h_raw = get(f"https://hq.sinajs.cn/list={h_code}", "gbk")
            a_m = re.search(r'"(.+?)"', a_raw)
            h_m = re.search(r'"(.+?)"', h_raw)
            if not a_m or not h_m: continue
            a_p = float(a_m.group(1).split(",")[3])
            h_p = float(h_m.group(1).split(",")[3])
            if not a_p or not h_p: continue
            h_cny = h_p * fx_rate
            item_premium = round((a_p - h_cny) / h_cny * 100, 2)
            premiums.append({"name": name, "a_price": a_p, "h_price": h_p,
                             "premium": item_premium, "h_cny": round(h_cny, 2)})
        except: continue

    premiums.append({"name": "宁德时代", "a_price": a_price, "h_price": h_price,
                     "premium": catl_premium, "h_cny": round(catl_h_cny, 2)})
    premiums.sort(key=lambda x: x["premium"])
    rank = next((i+1 for i, p in enumerate(premiums) if p["name"] == "宁德时代"), len(premiums))
    return {"peers": premiums, "rank": rank, "total": len(premiums),
            "catl_premium": catl_premium, "is_extreme": catl_premium < -25}


def fetch_market_indices():
    results = {}
    for name, code in MARKET_INDICES.items():
        try:
            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
            m = re.search(r'"(.+?)"', raw)
            if not m: continue
            p = m.group(1).split(",")
            if len(p) < 10: continue
            price, prev = float(p[3]), float(p[2])
            results[name] = {"price": price,
                             "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
        except: pass
    return results


def fetch_catl_fund_flow():
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/stock/get?secid=0.300750&fields=f62,f64,f66,f184,f63,f65,f99,f100,f101")
        data = d.get("data", {})
        if not data or not data.get("f62"): return None
        return {"main_net": data.get("f62", 0), "huge_net": data.get("f64", 0),
                "big_net": data.get("f66", 0), "small_net": data.get("f184", 0),
                "main_pct": data.get("f63", 0), "today_in": data.get("f65", 0),
                "three_day": data.get("f99", 0), "five_day": data.get("f100", 0),
                "ten_day": data.get("f101", 0)}
    except: return None


# ═══════════════════════════════════════════
# 模块二: 上游原材料 (仅5大核心)
# ═══════════════════════════════════════════

def fetch_lithium_futures():
    try:
        raw = get("https://hq.sinajs.cn/list=nf_LC0", "gbk")
        m = re.search(r'"(.+?)"', raw)
        if not m: return None
        p = m.group(1).split(",")
        if len(p) > 8:
            return {"price": float(p[3]), "prev_settle": float(p[4]) if p[4] else 0,
                    "change_pct": round((float(p[3]) - float(p[4])) / float(p[4]) * 100, 2) if p[4] and float(p[4]) else 0,
                    "name": p[0]}
    except: pass
    return None


def fetch_material_prices():
    """原材料价格 — 仅5大核心品种，带半年高低位"""
    materials = {}
    ppi_map = {
        "碳酸锂(电池级)": ("https://www.100ppi.com/price/detail-2928.html", 10000),
        "氢氧化锂": ("https://www.100ppi.com/price/detail-2858.html", 10000),
        "磷酸铁锂": ("https://www.100ppi.com/price/detail-2762.html", 10000),
        "电解钴": ("https://www.100ppi.com/price/detail-2758.html", 10000),
        "六氟磷酸锂": ("https://www.100ppi.com/price/detail-3206.html", 10000),
    }
    for name, (url, divisor) in ppi_map.items():
        try:
            raw = get(url, "gbk", t=8)
            for pat in [r'最新价.*?(\d[\d,]*\.?\d*)', r'价格.*?(\d[\d,]*\.?\d*)',
                        r'>(\d[\d,]*\.?\d*)\s*<.*?元/吨', r'\b(\d[\d,]*\.?\d*)\s*元\s*/\s*吨\b']:
                m = re.search(pat, raw)
                if m:
                    v = m.group(1).replace(",", "")
                    materials[name] = {"price": round(float(v) / divisor, 2),
                                       "unit": "万元/吨" if divisor > 100 else "元/吨", "source": "100ppi"}
                    break
        except: pass

    # Fallback: 用参考价格 + 半年高低位
    for mat_name in MATERIAL_DISPLAY_ORDER:
        ref = MATERIAL_REFERENCE.get(mat_name, {})
        if mat_name not in materials:
            price = ref.get("price", 0)
            low, high = ref.get("low_6m", price), ref.get("high_6m", price)
            materials[mat_name] = {"price": price, "unit": ref.get("unit", "元/吨"), "source": "参考"}
        else:
            price = materials[mat_name]["price"]
            low, high = ref.get("low_6m", price), ref.get("high_6m", price)

        # 计算半年区间位置
        if high > low and price > 0:
            pos = round((price - low) / (high - low) * 100, 1)
            if pos < 15:
                pos_text = f"距半年低点{price-low:.0f}元 · 低位"
            elif pos < 35:
                pos_text = f"半年P{pos:.0f}% · 偏低"
            elif pos < 65:
                pos_text = f"半年P{pos:.0f}% · 中部"
            elif pos < 85:
                pos_text = f"半年P{pos:.0f}% · 偏高"
            else:
                pos_text = f"距半年高点{high-price:.0f}元 · 高位"
        else:
            pos, pos_text = 50, "参考"
        materials[mat_name]["pos_text"] = pos_text
        materials[mat_name]["position"] = pos
        materials[mat_name]["low_6m"] = low
        materials[mat_name]["high_6m"] = high

    return materials


# ═══════════════════════════════════════════
# 模块三-七: 股票批量 + 板块 + 新闻 + 北向
# ═══════════════════════════════════════════

def fetch_stock_batch(stock_map):
    results = {}
    for name, code in stock_map.items():
        try:
            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
            m = re.search(r'"(.+?)"', raw)
            if not m: continue
            p = m.group(1).split(",")
            if len(p) < 10: continue
            price, prev = float(p[3]), float(p[2])
            results[name] = {"code": code, "price": price,
                             "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
        except: pass
    return results


def enrich_stocks_period_changes(stocks, days=35):
    """为上游/竞争股票补充多周期涨跌幅 (5/15/30日) + 走势小结"""
    if not stocks: return stocks

    for name, s in stocks.items():
        code = s.get("code", "")
        if not code: continue
        try:
            raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{days},qfq", headers=H_EM)
            d = json.loads(raw)
            klines = d.get("data", {}).get(code, {}).get("qfqday", []) or \
                     d.get("data", {}).get(code, {}).get("day", [])
            if not klines or len(klines) < 5: continue

            closes = []
            for k in klines:
                if isinstance(k, str):
                    closes.append(float(k.split(",")[2]))
                elif isinstance(k, list):
                    closes.append(float(k[2]))
                elif isinstance(k, dict):
                    closes.append(float(k.get("close", 0)))
            current = s["price"]

            periods = {}
            for pname, pdays in [("5日", 5), ("15日", 15), ("30日", 30)]:
                if len(closes) >= pdays:
                    start = closes[-pdays]
                    if start and start > 0:
                        periods[pname] = round((current - start) / start * 100, 2)
                    else:
                        periods[pname] = None
                else:
                    periods[pname] = None
            s["periods"] = periods

            # 走势小结
            chg_5 = periods.get("5日")
            chg_15 = periods.get("15日")
            chg_30 = periods.get("30日")

            summary = ""
            if chg_30 is not None and chg_15 is not None and chg_5 is not None:
                if chg_30 < -10: summary = "深度回调"
                elif chg_30 < -5: summary = "持续走弱"
                elif chg_30 > 10: summary = "强势上涨"
                elif chg_30 > 5: summary = "稳步上行"
                else: summary = "横盘震荡"
                if chg_5 < -5 and chg_15 < 0: summary += "，加速下跌"
                elif chg_5 > 5 and chg_15 > 0: summary += "，加速上涨"
                elif chg_5 * chg_15 < 0: summary += "，短期反转"
            elif chg_5 is not None:
                summary = "短期走弱" if chg_5 < -3 else "短期走强" if chg_5 > 3 else "横盘"
            else:
                summary = "数据不足"
            s["trend_summary"] = summary
        except:
            s["periods"] = {}
            s["trend_summary"] = "—"
    return stocks


def fetch_sector_indices():
    results = {}
    for name, code in SECTOR_INDICES.items():
        try:
            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
            m = re.search(r'"(.+?)"', raw)
            if not m: continue
            p = m.group(1).split(",")
            if len(p) < 10: continue
            price, prev = float(p[3]), float(p[2])
            results[name] = {"price": price,
                             "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
        except: pass
    return results


def fetch_news(keyword, count=5):
    try:
        params = {"cb": "jQ", "param": json.dumps({
            "uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"],
            "client": "web", "clientType": "web", "clientVersion": "curr",
            "paramNum": 20, "pageNum": 1, "pageSize": count})}
        raw = get("https://search-api-web.eastmoney.com/search/jsonp?" + urllib.parse.urlencode(params), headers=H_EM)
        m = re.search(r'jQ\((.*)\)\s*$', raw.strip())
        if not m: return []
        return [{"title": a.get("title", "").replace("<em>", "").replace("</em>", ""),
                 "date": (a.get("date", "") or "")[:10],
                 "source": a.get("mediaName", ""),
                 "url": a.get("url", ""),
                 "content": (a.get("content", "") or "").replace("<em>", "").replace("</em>", "")[:120]}  # 正文摘要前120字，剥离东方财富高亮标签
                for a in json.loads(m.group(1)).get("result", {}).get("cmsArticleWebOld", [])]
    except: return []


def fetch_all_news():
    """批量获取所有维度新闻（含正文摘要）"""
    results = {}
    for category, keywords in NEWS_KEYWORDS.items():
        all_articles = []
        for kw in keywords:
            articles = fetch_news(kw, count=3)
            for a in articles:
                # 去重
                if a["url"] not in {x["url"] for x in all_articles}:
                    all_articles.append(a)
        results[category] = all_articles[:5]  # 每类最多5条
    return results


def fetch_north_flow():
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/kamt.kline/get?fields1=f1,f3&fields2=f51,f52,f53,f54&klt=101&lmt=5")
        klines = d.get("data", {}).get("klines", [])
        if not klines: return None
        today = klines[-1].split(",")
        yesterday = klines[-2].split(",") if len(klines) > 1 else today
        return {"today": {"date": today[0], "net": round(float(today[1]), 2)},
                "yesterday": {"date": yesterday[0], "net": round(float(yesterday[1]), 2)} if yesterday != today else None}
    except: return None


def fetch_nev_sector():
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&fields=f2,f3,f12,f14&fid=f3&fs=b:BK0493")
        return {"total_stocks": d.get("data", {}).get("total", 0)}
    except: return None


def fetch_week_flow():
    """CATL 近5日每日主力资金流向"""
    try:
        # 多试几个endpoint
        for url in [
            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=0.300750&fields1=f1,f3&fields2=f51,f52,f53&lmt=6",
            "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=0.300750&fields1=f1,f3&fields2=f51,f52,f53&lmt=6",
        ]:
            try:
                raw = urllib.request.urlopen(
                    urllib.request.Request(url, headers=H_EM), timeout=5, context=ssl_ctx
                ).read().decode()
                d = json.loads(raw)
                klines = d.get("data", {}).get("klines", [])
                if klines:
                    result = []
                    for k in klines:
                        parts = k.split(",")
                        if len(parts) >= 3:
                            result.append({
                                "date": parts[0],
                                "main_net": round(float(parts[1]) / 1e8, 2),
                            })
                    return result
            except:
                continue
        return []
    except:
        return []


# ═══════════════════════════════════════════
# 模块七: P0/P1 新增 — 分析师预期 + 北向增强 + 财务 + 装机
# ═══════════════════════════════════════════

def fetch_analyst_consensus():
    """分析师一致预期 — 东方财富 F10 ProfitForecast"""
    try:
        d = get_json("https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code=SZ300750")
        pjtj = d.get("pjti", d.get("pjtj", []))
        if not pjtj:
            for k in d:
                if isinstance(d[k], list) and len(d[k]) > 0:
                    pjtj = d[k]; break
        result = {"periods": [], "latest": None}
        for p in pjtj:
            period = {
                "window": p.get("DATE_TYPE", ""),
                "rating": p.get("COMPRE_RATING", ""),
                "rating_num": p.get("COMPRE_RATING_NUM", 0),
                "org_num": p.get("RATING_ORG_NUM", 0),
                "buy_num": p.get("RATING_BUY_NUM", 0),
                "add_num": p.get("RATING_ADD_NUM", 0),
                "neutral_num": p.get("RATING_NEUTRAL_NUM", 0),
                "reduce_num": p.get("RATING_REDUCE_NUM", 0),
                "sale_num": p.get("RATING_SALE_NUM", 0),
            }
            result["periods"].append(period)
        if result["periods"]:
            result["latest"] = result["periods"][0]
        return result if result["latest"] else None
    except:
        return None


def fetch_analyst_eps():
    """一致预期 EPS — 东财盈利预测 yctj_chart"""
    try:
        d = get_json("https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code=SZ300750")
        chart = d.get("yctj_chart", [])
        result = []
        for y in chart:
            eps = y.get("EPS"); pe = y.get("PE")
            result.append({
                "year": y.get("YEAR", ""),
                "year_mark": y.get("YEAR_MARK", ""),  # A=实际, E=预测
                "eps": float(eps) if eps else None,
                "pe": float(pe) if pe else None,
                "roe": float(y["ROE"]) if y.get("ROE") else None,
                "net_profit": int(y["PARENT_NETPROFIT"]) if y.get("PARENT_NETPROFIT") else None,
                "revenue": int(y["TOTAL_OPERATE_INCOME"]) if y.get("TOTAL_OPERATE_INCOME") else None,
                "org_num": None,  # 统计值不限机构数
            })
        return result if result else None
    except:
        return None


def fetch_analyst_targets():
    """分析师目标价 — 从一致预期EPS反推 (EPS × 合理PE区间)"""
    try:
        d = get_json("https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code=SZ300750")
        jgyc = d.get("jgyc", [])
        if not jgyc:
            return None
        
        # 取近六月平均预测
        avg = jgyc[0]
        eps_curr = float(avg["EPS1"]) if avg.get("EPS1") else None  # 2025A
        eps_next = float(avg["EPS2"]) if avg.get("EPS2") else None  # 2026E
        eps_far = float(avg["EPS3"]) if avg.get("EPS3") else None   # 2027E
        
        # PE区间: 合理PE 20-30倍 (参考行业中枢)
        pe_low, pe_mid, pe_high = 20, 25, 30
        
        # 同时也从jgyc中提取近半年目标价 (EPS_next * PE_next)
        pe_next = float(avg["PE2"]) if avg.get("PE2") else 25
        
        result = {
            "eps_curr": eps_curr,
            "eps_next": eps_next,
            "eps_far": eps_far,
            "target_low": round(eps_next * pe_low, 0) if eps_next else None,
            "target_mid": round(eps_next * pe_mid, 0) if eps_next else None,
            "target_high": round(eps_next * pe_high, 0) if eps_next else None,
            "implied_pe": round(pe_next, 1) if pe_next else None,
            "avg": round(eps_next * pe_next, 0) if eps_next and pe_next else None,
            "high": round(eps_next * pe_high, 0) if eps_next else None,
            "low": round(eps_next * pe_low, 0) if eps_next else None,
            "count": len(jgyc),
        }
        return result
    except:
        return None


def fetch_financial_trends():
    """财务面追踪 — 从腾讯qt提取 + 行业参考"""
    import statistics
    result = {}
    try:
        raw = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,1,qfq", headers=H_EM)
        d = json.loads(raw)
        qt = d.get("data", {}).get("sz300750", {}).get("qt", {}).get("sz300750", [])
        if qt and len(qt) > 65:
            result["pe_ttm"] = float(qt[39]) if len(qt) > 39 and qt[39] else None
            result["pb"] = float(qt[46]) if len(qt) > 46 and qt[46] else None
            result["roe"] = float(qt[65]) if len(qt) > 65 and qt[65] else None
            result["mcap"] = float(qt[45]) if len(qt) > 45 and qt[45] else None
            result["price"] = float(qt[3]) if len(qt) > 3 and qt[3] else None
    except:
        pass

    # ── 参考财务数据（宁德时代2025年报 + 行业共识）──
    # 动态更新: 财报季手动刷新
    result["quarters"] = [
        {"period": "2024Q1", "revenue": 797, "net_profit": 105, "eps": 2.39, "roe": 24.0, "gross_margin": 26.4},
        {"period": "2024Q2", "revenue": 870, "net_profit": 123, "eps": 2.80, "roe": 25.4, "gross_margin": 27.1},
        {"period": "2024Q3", "revenue": 923, "net_profit": 131, "eps": 2.98, "roe": 25.8, "gross_margin": 27.8},
        {"period": "2024Q4", "revenue": 1050, "net_profit": 148, "eps": 3.36, "roe": 26.5, "gross_margin": 28.2},
        {"period": "2025Q1", "revenue": 980, "net_profit": 139, "eps": 3.16, "roe": 25.0, "gross_margin": 28.0},
    ]
    # 计算趋势
    if result["quarters"]:
        latest = result["quarters"][-1]
        prev = result["quarters"][-2]
        result["trends"] = {
            "revenue_qoq": round((latest["revenue"] - prev["revenue"]) / prev["revenue"] * 100, 1) if prev["revenue"] else None,
            "profit_qoq": round((latest["net_profit"] - prev["net_profit"]) / prev["net_profit"] * 100, 1) if prev["net_profit"] else None,
            "revenue_yoy": round((latest["revenue"] - result["quarters"][-5]["revenue"]) / result["quarters"][-5]["revenue"] * 100, 1) if len(result["quarters"]) >= 5 else None,
            "profit_yoy": round((latest["net_profit"] - result["quarters"][-5]["net_profit"]) / result["quarters"][-5]["net_profit"] * 100, 1) if len(result["quarters"]) >= 5 else None,
        }
    return result


def fetch_battery_install():
    """电池装机量 — 月度参考数据（来源：中国汽车动力电池产业联盟）"""
    # 月度数据，每次月度报告发布后手动更新
    return {
        "source": "中国汽车动力电池产业创新联盟",
        "source_url": "https://www.autobattery.org.cn/",
        "update_note": "每月11日左右发布上月数据，需手动更新",
        "monthly": [
            {"month": "2025-01", "total_gwh": 32.5, "catl_gwh": 14.6, "catl_share": 44.9},
            {"month": "2025-02", "total_gwh": 28.0, "catl_gwh": 12.8, "catl_share": 45.7},
            {"month": "2025-03", "total_gwh": 38.2, "catl_gwh": 17.1, "catl_share": 44.8},
            {"month": "2025-04", "total_gwh": 36.8, "catl_gwh": 16.3, "catl_share": 44.3},
        ],
        "yoy_global": "CATL 2025年全球市占率约 37-38% (SNE Research)",
        "trend": "国内市占率稳定在44-46%区间，全球龙头地位稳固",
    }


# ═══════════════════════════════════════════
# 主采集
# ═══════════════════════════════════════════

def collect_all(verbose=True):
    if verbose: print("🔋 CATL 生态链数据采集 v1.3\n" + "=" * 50)

    data = {"date": get_date_str(), "datetime": get_datetime_str(), "mode": get_mode()}

    if verbose: print("📡 CATL核心 + K线 + 大盘...")
    data["catl_a"] = fetch_catl_a()
    data["catl_h"] = fetch_catl_h()
    data["catl_pe"] = fetch_catl_pe()
    data["catl_fund"] = fetch_catl_fund_flow()
    data["catl_kline"] = fetch_catl_kline(90)  # 90天用于技术面分析
    data["catl_kline_long"] = fetch_catl_kline(750)  # 长周期用于AH溢价历史
    data["hk_kline"] = fetch_hk_kline(750)  # H股上市以来
    data["market"] = fetch_market_indices()
    if verbose:
        a = data["catl_a"]
        print(f"  A股: ¥{a['price']} ({a['change_pct']:+.1f}%)" if a else "  A股: ❌")
        print(f"  K线: {len(data['catl_kline'])}日")

    if verbose: print("⛏️ 原材料(5核心)...")
    data["materials"] = fetch_material_prices()
    data["lithium_futures"] = fetch_lithium_futures()

    if verbose: print("🏭 上游..."); data["upstream"] = fetch_stock_batch(UPSTREAM_STOCKS)
    data["upstream"] = enrich_stocks_period_changes(data["upstream"])
    if verbose: print("⚔️ 竞争..."); data["competitors"] = fetch_stock_batch(COMPETITORS)
    data["competitors"] = enrich_stocks_period_changes(data["competitors"])
    if verbose: print("📊 板块..."); data["sectors"] = fetch_sector_indices()
    if verbose: print("📰 新闻..."); data["news"] = fetch_all_news()
    if verbose: print(f"  {sum(len(v) for v in data['news'].values())} 条")
    if verbose: print("💰 北向..."); data["north_flow"] = fetch_north_flow()
    if verbose: print("🚗 新能源车..."); data["nev_sector"] = fetch_nev_sector()
    if verbose: print("📊 估值..."); data["valuation"] = fetch_valuation_data()
    if verbose: print("📅 周回顾..."); data["week_flow"] = fetch_week_flow()
    if verbose: print("🔮 分析师..."); data["analyst_consensus"] = fetch_analyst_consensus()
    if verbose: print("🎯 目标价..."); data["analyst_targets"] = fetch_analyst_targets()
    if verbose: print("🧠 一致预期EPS..."); data["analyst_eps"] = fetch_analyst_eps()
    if verbose: print("📈 财务..."); data["financials"] = fetch_financial_trends()
    if verbose: print("🔋 装机量..."); data["battery_install"] = fetch_battery_install()
    if verbose: print("💱 AH溢价...")
    if verbose and data.get("ah_history"):
        print(f"  AH历史: {len(data['ah_history'])}天 · 当前{data.get('ah_premium','—'):.1f}% · "
              f"30日均{data.get('ah_mean30', '—')}")
    if verbose and data.get("ah_ranking"):
        r = data["ah_ranking"]
        print(f"  AH排名: #{r['rank']}/{r['total']} {'极端' if r.get('is_extreme') else ''}")

    compute_derived(data)
    if verbose: print("=" * 50 + "\n✅ 采集完成")
    return data


# ═══════════════════════════════════════════
# 衍生计算 + 归因
# ═══════════════════════════════════════════

def _sign(v):
    if v is None: return ""
    return "+" if v > 0 else ""


def compute_derived(data):
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    pe = data.get("catl_pe", {})
    fund = data.get("catl_fund") or {}
    kline = data.get("catl_kline", [])
    market = data.get("market", {})
    upstream = data.get("upstream", {})
    sectors = data.get("sectors", {})
    lf = data.get("lithium_futures", {})

    price = a.get("price") if a else None
    pe_ttm = pe.get("pe_ttm") if pe else None
    s = {}

    # ── 1. 均线系统 ──
    if kline and price:
        mas = {}
        for w in MA_WINDOWS:
            if len(kline) >= w:
                closes = [k["close"] for k in kline[-w:]]
                mas[f"MA{w}"] = round(statistics.mean(closes), 2)
        s["mas"] = mas
        ma60 = mas.get("MA60")
        if ma60 and price:
            dist_ma60 = round((price - ma60) / ma60 * 100, 2)
            s["ma60_dist"] = {"value": ma60, "dist_pct": dist_ma60,
                              "text": f"距MA60 {_sign(dist_ma60)}{dist_ma60:.2f}%",
                              "near": abs(dist_ma60) < 3}
        else:
            s["ma60_dist"] = {"value": None, "dist_pct": None, "text": "—", "near": False}

    # ── 2. 连涨连跌 ──
    if kline and price and len(kline) >= 3:
        streak_v, streak_pct, direction = calc_streak(kline, price)
        s["streak"] = {"days": streak_v, "pct": streak_pct, "direction": direction,
                       "text": f"连{direction}{streak_v}日 累计{'-' if direction=='跌' else '+'}{abs(streak_pct):.1f}%"}
        s["chg_5d"] = calc_period_change(kline, price, 5)
        s["chg_10d"] = calc_period_change(kline, price, 10)
        s["chg_20d"] = calc_period_change(kline, price, 20)
        avg_vol_5d = calc_avg_volume(kline, 5)
        today_vol = a.get("volume", 0) if a else 0
        if avg_vol_5d and today_vol:
            vr = today_vol / avg_vol_5d
            s["volume_ratio"] = {"ratio": round(vr, 2),
                                 "text": f"量能{vr:.1f}x均量" if vr >= 1 else f"缩量{vr:.1f}x"}
        else:
            s["volume_ratio"] = {"ratio": 0, "text": "—"}
    else:
        s["streak"] = {"days": 0, "pct": 0, "direction": "—", "text": "—"}
        s["chg_5d"] = s["chg_10d"] = s["chg_20d"] = None
        s["volume_ratio"] = {"ratio": 0, "text": "—"}

    # ── 3-10: 大盘对比 / AH / PEG / PE / 资金 / 碳酸锂 / 上游异动 / 成交额 ──
    ss_index = market.get("上证指数", {})
    catl_chg = a.get("change_pct") if a else None
    market_chg = ss_index.get("change_pct") if ss_index else None
    if catl_chg is not None and market_chg is not None:
        diff = round(catl_chg - market_chg, 2)
        if catl_chg < 0 and market_chg > 0:
            s["vs_market"] = {"text": f"逆势下跌{catl_chg:.1f}% (大盘{'+' if market_chg>0 else ''}{market_chg:.2f}%)", "type": "diverge_down", "diff": diff}
        elif catl_chg > 0 and market_chg < 0:
            s["vs_market"] = {"text": f"逆势上涨{catl_chg:.1f}% (大盘{market_chg:.2f}%)", "type": "diverge_up", "diff": diff}
        elif catl_chg < market_chg:
            s["vs_market"] = {"text": f"跑输大盘 ({catl_chg:.1f}% vs {market_chg:+.2f}%)", "type": "underperform", "diff": diff}
        else:
            s["vs_market"] = {"text": f"跑赢大盘 ({catl_chg:+.1f}% vs {market_chg:+.2f}%)", "type": "outperform", "diff": diff}
    else:
        s["vs_market"] = {"text": "", "type": "unknown", "diff": 0}

    if a and h and h.get("price") and price:
        h_cny = h["price"] * 0.92
        ah = round((price - h_cny) / h_cny * 100, 2) if h_cny else None
        data["ah_premium"] = ah
        if ah is not None:
            if ah < -30: s["ah"] = {"level": "extreme_discount", "text": f"A股折价港股{abs(ah):.0f}% 再创新低"}
            elif ah < 0: s["ah"] = {"level": "discount", "text": f"A股折价港股{abs(ah):.0f}% 成本利好"}
            elif ah > 30: s["ah"] = {"level": "extreme_premium", "text": f"A股溢价港股{ah:.0f}% 偏高"}
            else: s["ah"] = {"level": "normal", "text": f"A股溢价{ah:.0f}%"}
        else: s["ah"] = {"level": "unknown", "text": "—"}
    else:
        data["ah_premium"] = None
        s["ah"] = {"level": "unknown", "text": "—"}

    # ── AH溢价历史序列 + 排名 ──
    hk_kline = data.get("hk_kline", [])
    a_long = data.get("catl_kline_long", [])
    if hk_kline and a_long:
        ah_history = compute_ah_history(hk_kline, a_long)
        data["ah_history"] = ah_history
        # 30天均值
        if len(ah_history) >= 30:
            recent_30 = [d["premium"] for d in ah_history[-30:]]
            data["ah_mean30"] = round(statistics.mean(recent_30), 2)
        else:
            data["ah_mean30"] = None
        # 7天详情
        data["ah_7day"] = ah_history[-7:] if len(ah_history) >= 7 else ah_history[-len(ah_history):]
        # 极值
        if ah_history:
            premiums_only = [d["premium"] for d in ah_history]
            data["ah_min"] = min(premiums_only)
            data["ah_max"] = max(premiums_only)
    else:
        data["ah_history"] = []
        data["ah_mean30"] = None
        data["ah_7day"] = []

    # ── AH排名（批量抓取，较慢）──
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    if a and h:
        data["ah_ranking"] = fetch_ah_ranking(a.get("price", 0), h.get("price", 0))
    else:
        data["ah_ranking"] = None

    if pe_ttm and pe_ttm > 0 and price:
        # ── PEG计算：优先用分析师一致预期，API不可用时降级为配置的固定增长率 ──
        analyst = fetch_analyst_eps("300750")
        peg_result = calc_peg_from_analyst(analyst, pe_ttm) if analyst else None
        
        if peg_result:
            peg = peg_result["peg"]
            growth_rate = peg_result["growth"]
            growth_source = f"分析师一致预期 ({growth_rate}%)"
            data["peg_growth_source"] = "analyst"
            data["peg_growth_rate"] = growth_rate
        else:
            # 降级：使用config.py中的固定增长率
            peg = round(pe_ttm / GROWTH_ASSUMPTION, 2)
            growth_rate = GROWTH_ASSUMPTION
            growth_source = f"固定假设 {growth_rate}%（API降级）"
            data["peg_growth_source"] = "fallback"
            data["peg_growth_rate"] = growth_rate
        
        data["peg"] = peg
        eps = price / pe_ttm
        target_pe_peg1 = growth_rate  # PEG=1时合理PE=增长率
        target_price_peg1 = round(target_pe_peg1 * eps, 2)
        dist_to_buy = round((target_price_peg1 - price) / price * 100, 2)
        s["peg"] = {"value": peg, "target_price": target_price_peg1, "distance_pct": dist_to_buy,
                     "growth_rate": growth_rate, "growth_source": growth_source}
        if peg < PEG_UNDERVALUE:
            s["peg"]["signal"] = "buy"; s["peg"]["text"] = f"PEG={peg:.2f} < 1.0 买入区间（增速{int(growth_rate)}%）"
            data["peg_signal"] = {"text": "低估区间 ✅", "color": "#3fb950", "level": "buy"}
        elif peg > PEG_OVERVALUE:
            s["peg"]["signal"] = "sell"; s["peg"]["text"] = f"PEG={peg:.2f} 偏高 距买点差{dist_to_buy:.1f}%"
            data["peg_signal"] = {"text": "偏高区间 ⚠️", "color": "#f85149", "level": "sell"}
        else:
            s["peg"]["signal"] = "hold"; s["peg"]["text"] = f"PEG={peg:.2f} 合理（增速{int(growth_rate)}%）"
            data["peg_signal"] = {"text": "合理区间 📊", "color": "#d29922", "level": "hold"}
        buy_price = round(target_pe_peg1 * eps, 0)
        # ── 动态目标PE：基于分析师一致预期增速（PEG=1推导）──
        dyn_target_pe = max(15, min(50, growth_rate))  # 限制在15-50倍
        dyn_pe_low = max(15, round(dyn_target_pe * 0.8))
        dyn_pe_high = min(50, round(dyn_target_pe * 1.2))
        s["target_pe"] = {"value": round(dyn_target_pe, 1), "low": dyn_pe_low, "high": dyn_pe_high,
                           "source": f"PEG=1推导（=分析师增速{int(growth_rate)}%）"}
        target_low = round(dyn_pe_low * eps, 0)
        target_high = round(dyn_pe_high * eps, 0)
        target_mid = round((target_low + target_high) / 2, 0)
        s["target_prices"] = {"buy": buy_price, "low": target_low, "mid": target_mid, "high": target_high}

        # ── 动态止损位 = MA60（均线系统已实时计算）──
        ma60_val = s.get("ma60_dist", {}).get("value")
        if ma60_val and ma60_val > 0:
            stop_loss_price = round(ma60_val * 0.97, 0)  # MA60下方3%
            s["stop_loss"] = {"price": stop_loss_price, "ma60": round(ma60_val, 0),
                               "source": "MA60均线×0.97", "note": "MA60为中长期趋势生命线，跌破3%视为逻辑破坏"}
        else:
            stop_loss_price = price * 0.85 if price else 0  # 降级：当前价-15%
            s["stop_loss"] = {"price": round(stop_loss_price, 0), "ma60": None,
                               "source": "当前价×0.85（降级）", "note": "MA60数据不可用"}

        # ── PE Bands ──
        if eps and eps > 0:
            bands = {}
            band_defs = [
                ("清仓区", 15, "#3fb950"),
                ("止损区", 18, "#58a6ff"),
                ("保守区", 21, "#8b949e"),
                ("合理区", 25, "#d29922"),
                ("偏高区", 30, "#f85149"),
                ("泡沫区", 35, "#f85149"),
            ]
            current_band = None
            for label, pe_band, color in band_defs:
                price_band = round(pe_band * eps, 0)
                bands[label] = {"pe": pe_band, "price": price_band, "color": color}
                if price and price_band and not current_band:
                    if price <= price_band:
                        current_band = label
            if not current_band:
                current_band = "泡沫区"
            bands["_current"] = current_band
            bands["_eps"] = round(eps, 2)
            data["valuation"]["pe_bands"] = bands
            s["pe_bands"] = bands
    else:
        data["peg"] = None
        data["peg_signal"] = {"text": "--", "color": "#8b949e", "level": "unknown"}
        s["peg"] = {"value": None, "target_price": None, "distance_pct": None, "signal": "unknown", "text": "—"}
        s["target_prices"] = {"buy": 0, "low": 0, "mid": 0, "high": 0}

    if pe_ttm:
        pe_level = "偏低" if pe_ttm < 25 else "合理" if pe_ttm < 40 else "偏高" if pe_ttm < 60 else "高"
        s["pe"] = {"value": pe_ttm, "level": pe_level, "text": f"PE={pe_ttm:.1f}x {pe_level}"}
    else:
        s["pe"] = {"value": None, "level": "unknown", "text": "—"}

    if fund:
        mn = fund.get("main_net", 0) / 1e4; d5 = fund.get("five_day", 0) / 1e4
        parts = []
        if abs(mn) > 0.5: parts.append(f"主力今日{'净流入' if mn>0 else '净流出'}{abs(mn):.1f}亿")
        if abs(d5) > 1: parts.append(f"近5日{'累计流入' if d5>0 else '累计流出'}{abs(d5):.1f}亿")
        s["fund"] = {"text": "，".join(parts) if parts else "资金平稳", "main_net": mn, "five_day": d5}
    else:
        s["fund"] = {"text": "数据暂缺", "main_net": 0, "five_day": 0}

    if lf and lf.get("price"):
        li_cur = lf["price"] / 10000; delta = li_cur - 7.5
        impact = "成本利好" if delta < -0.5 else "成本压力" if delta > 0.5 else "成本稳定"
        s["lithium"] = {"price": lf["price"], "price_wan": round(li_cur, 2), "delta_wan": round(delta, 2),
                        "impact": impact, "text": f"碳酸锂{li_cur:.1f}万/吨 {impact}" if abs(delta) > 0.3 else f"碳酸锂{li_cur:.1f}万/吨 稳定"}
    else:
        s["lithium"] = {"text": "碳酸锂数据暂缺"}

    upstream_alerts = []
    for name, st in upstream.items():
        if abs(st["change_pct"]) > 5:
            upstream_alerts.append({"name": name, "change": st["change_pct"], "text": f"{name} {st['change_pct']:+.1f}%"})
    s["upstream_alerts"] = upstream_alerts

    if a and a.get("amount"):
        amt_yi = a["amount"] / 1e8
        amt_level = "放量明显" if amt_yi > 100 else "交投活跃" if amt_yi > 50 else "正常" if amt_yi > 20 else "缩量"
        s["amount"] = {"value": amt_yi, "level": amt_level, "text": f"成交额{amt_yi:.0f}亿 {amt_level}"}
    else:
        s["amount"] = {"text": "—"}

    ind_key = CATL_INDUSTRY_SOURCE
    ind_data = sectors.get(ind_key)
    if ind_data:
        s["industry"] = {"name": CATL_INDUSTRY, "source": ind_key,
                         "change_pct": ind_data["change_pct"],
                         "text": f"{CATL_INDUSTRY}({ind_key}) {ind_data['change_pct']:+.1f}%"}
    else:
        for sn, sd in sectors.items():
            s["industry"] = {"name": sn, "change_pct": sd["change_pct"], "text": f"{sn} {sd['change_pct']:+.1f}%"}
            break
        else:
            s["industry"] = {"name": "—", "change_pct": 0, "text": "—"}

    if price and COST_PRICE:
        cost_chg = round((price - COST_PRICE) / COST_PRICE * 100, 2)
        s["cost"] = {"cost_price": COST_PRICE, "current": price, "change_pct": cost_chg,
                     "text": f"成本¥{COST_PRICE} 浮{'盈' if cost_chg>0 else '亏'}{abs(cost_chg):.1f}%"}
    else:
        s["cost"] = {"text": "—"}

    # ── 核心总结句 ──
    core_parts = []
    peg_sig = s.get("peg", {})
    if peg_sig.get("signal") == "buy": core_parts.append(f"PEG {peg_sig['value']:.2f} 买入区间")
    elif peg_sig.get("signal") == "sell": core_parts.append(f"PEG {peg_sig['value']:.2f} 偏高")
    else: core_parts.append(f"PEG {peg_sig.get('value','—')}")

    streak_sig = s.get("streak", {})
    if streak_sig.get("days", 0) >= 3:
        core_parts.append(f"连{streak_sig['direction']}{streak_sig['days']}日{'累计'}{abs(streak_sig['pct']):.1f}%")
    li_sig = s.get("lithium", {})
    if li_sig.get("impact"):
        core_parts.append(f"碳酸锂{li_sig.get('price_wan','')}万/吨 {li_sig.get('impact','')}")
    ah = data.get("ah_premium")
    if ah is not None and ah < 0: core_parts.append(f"AH溢价{ah:.1f}% 折价")
    vs_market = s.get("vs_market", {})
    if vs_market.get("type") == "diverge_down": core_parts.append("逆势下跌 分化延续")
    s["core_summary"] = " · ".join(core_parts) if core_parts else "数据采集中"

    # 行业对比
    ind = s.get("industry", {})
    if catl_chg is not None and ind.get("change_pct") is not None:
        ind_diff = round(catl_chg - ind["change_pct"], 2)
        s["vs_industry"] = f"弱于行业{abs(ind_diff):.1f}%" if ind_diff < -1 else f"强于行业{ind_diff:.1f}%" if ind_diff > 1 else "与行业同步"
    else:
        s["vs_industry"] = ""

    if upstream:
        changes = [v["change_pct"] for v in upstream.values()]
        data["upstream_avg_change"] = round(sum(changes) / len(changes), 2) if changes else 0
    else:
        data["upstream_avg_change"] = 0

    comps = data.get("competitors", {})
    if comps:
        changes = [v["change_pct"] for v in comps.values()]
        data["competitor_avg_change"] = round(sum(changes) / len(changes), 2) if changes else 0
    else:
        data["competitor_avg_change"] = 0

    data["summaries"] = s

    # ── 本周走势回顾 ──
    compute_week_review(data)

    return data


def compute_week_review(data):
    """生成本周5日走势表格 + 周总结"""
    kline = data.get("catl_kline", [])
    week_flow = data.get("week_flow", [])
    a = data.get("catl_a", {})
    s = data.get("summaries", {})

    if not kline or len(kline) < 6:
        data["week_review"] = None
        return

    # 取最近6个交易日 (6个才能算5天的涨跌幅)
    recent = kline[-6:]
    days = []
    for i in range(1, len(recent)):  # skip first, use as prev
        prev_close = recent[i-1]["close"]
        curr = recent[i]
        curr_close = curr["close"]
        chg = round((curr_close - prev_close) / prev_close * 100, 2) if prev_close else 0

        # 匹配当日主力资金
        date_str = curr["date"]
        fund_net = None
        for wf in week_flow:
            if wf.get("date") == date_str:
                fund_net = wf.get("main_net")
                break

        # 关键事件 (数据驱动)
        events = []
        if abs(chg) > 1.5:
            events.append("放量下跌" if chg < -1.5 else "强势上涨")
        elif abs(chg) < 0.3:
            events.append("窄幅横盘")
        if fund_net and fund_net < -5:
            events.append(f"主力净流出{abs(fund_net):.1f}亿")
        elif fund_net and fund_net > 5:
            events.append(f"主力净流入{fund_net:.1f}亿")
        if i == len(recent) - 1 and abs(chg) > 1:
            events.append("盘中触及关键位")

        days.append({
            "date": date_str,
            "close": curr_close,
            "change_pct": chg,
            "fund_net": fund_net,
            "events": "，".join(events) if events else "—"
        })

    # 本周合计
    if days:
        first_close = days[0]["close"]
        last_close = days[-1]["close"]
        week_chg = round((last_close - first_close) / first_close * 100, 2) if first_close else 0

        # 资金: 优先用每日明细，降级用5日累计
        daily_funds = [d["fund_net"] for d in days if d["fund_net"] is not None]
        if daily_funds:
            week_fund = round(sum(daily_funds), 2)
        else:
            # 降级: 用fetch_catl_fund_flow的5日累计
            fund_data = data.get("catl_fund") or {}
            d5 = fund_data.get("five_day")
            week_fund = round(d5 / 1e4, 2) if d5 else 0
            # 把5日累计均匀填入每一天
            if week_fund != 0 and len(days) > 0:
                per_day = round(week_fund / len(days), 2)
                for d in days:
                    if d["fund_net"] is None:
                        d["fund_net"] = per_day
                        d["fund_note"] = "（日均估算）"

        # 周总结
        chg_values = [d["change_pct"] for d in days]
        fund_values = [d["fund_net"] for d in days if d["fund_net"] is not None]

        # 判断趋势
        neg_count = sum(1 for c in chg_values if c < 0)
        pos_count = sum(1 for c in chg_values if c > 0)

        if neg_count >= 4:
            if chg_values[-1] > chg_values[0]:
                trend_desc = "跌多涨少，但跌幅逐日收窄，抛压接近衰竭"
            else:
                trend_desc = "连续阴跌，弱势不改"
        elif pos_count >= 4:
            trend_desc = "持续走强，多头掌控"
        elif neg_count >= 3:
            trend_desc = "偏弱震荡，卖压占优"
        elif pos_count >= 3:
            trend_desc = "偏强震荡，买盘积极"
        else:
            trend_desc = "涨跌互现，震荡整理"

        # 资金总结
        if week_fund < -10:
            fund_desc = f"主力持续净流出，全周累计{abs(week_fund):.1f}亿"
        elif week_fund < 0:
            fund_desc = f"主力资金偏空，全周净流出{abs(week_fund):.1f}亿"
        elif week_fund > 0:
            fund_desc = f"主力资金偏多，全周净流入{week_fund:.1f}亿"
        else:
            fund_desc = "主力资金基本平衡"

        # 大盘对比
        vs_m = s.get("vs_market", {})
        market_context = ""
        if vs_m.get("type") == "diverge_down":
            market_context = "大盘上涨但宁德逆跌，极端分化延续（半导体/AI算力虹吸资金）"
        elif vs_m.get("type") == "underperform":
            market_context = "跑输大盘，新能源板块整体承压"

        # 周总结 — 详细版，小白可读
        week_summary = _gen_week_summary(days, week_chg, week_fund, s, data)

        data["week_review"] = {
            "days": days,
            "total": {
                "close": last_close,
                "week_chg": week_chg,
                "week_fund": week_fund,
            },
            "summary": week_summary,
            "trend_desc": trend_desc,
            "fund_desc": fund_desc,
        }


# ═══════════════════════════════════════════
# 估值数据采集
# ═══════════════════════════════════════════

def fetch_valuation_data():
    """采集估值对比数据 + PE Bands + 机构评级"""
    result = {}

    # ── 1. 同行估值 ──
    peers_val = {}
    for name, code in VALUATION_PEERS.items():
        try:
            raw = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,1,qfq", headers=H_EM)
            d = json.loads(raw)
            qt = d.get("data", {}).get(code, {}).get("qt", {}).get(code, [])
            if qt and len(qt) > 65:
                pe = float(qt[39]) if len(qt) > 39 and qt[39] else None
                pb = float(qt[46]) if len(qt) > 46 and qt[46] else None
                roe = float(qt[65]) if len(qt) > 65 and qt[65] else None
                price = float(qt[3]) if len(qt) > 3 and qt[3] else None
                mcap = float(qt[45]) if len(qt) > 45 and qt[45] else None

                # PEG = PE / 增速 (粗略用行业平均增速25%)
                peg = round(pe / 25, 2) if pe and pe > 0 else None

                # 估值性价比: (1/PE) vs (1/行业PE) 简单比值
                score = "—"
                if pe and pe > 0:
                    if pe < 20: score = "低估"
                    elif pe < 30: score = "合理"
                    elif pe < 50: score = "偏高"
                    else: score = "高估"

                peers_val[name] = {
                    "code": code, "price": price, "pe": pe, "pb": pb,
                    "roe": roe, "peg": peg, "mcap": mcap, "score": score
                }
        except:
            pass
    result["peers"] = peers_val

    # ── 2. PE Bands (基于当前EPS) ──
    # 从已采集的PE和价格计算EPS，然后构建Bands
    result["pe_bands"] = None  # 后续在compute_derived中填充

    # ── 3. 机构评级 (静态参考，定期手动更新) ──
    result["institution"] = {
        "buy": 9, "overweight": 2, "neutral": 0, "sell": 0,
        "target_avg": 520.0,  # 机构目标均价
        "dividend_rate": 1.2,  # 2025分红率(% 占净利润)
        "dividend_yield": 0.38,  # 股息率(%)
    }

    return result

def _gen_week_summary(days, week_chg, week_fund, s, data):
    """生成本周详细总结 — 小白可读"""
    if not days:
        return "数据不足"

    a = data.get("catl_a", {})
    market = data.get("market", {})
    peg = data.get("peg")
    pe = data.get("catl_pe", {})
    pe_ttm = pe.get("pe_ttm") if pe else None
    mas = s.get("mas", {})
    ma60 = s.get("ma60_dist", {})
    streak = s.get("streak", {})
    vs_m = s.get("vs_market", {})
    ah = data.get("ah_premium")
    li = s.get("lithium", {})
    peg_sig = s.get("peg", {})

    lines = []

    # ── 第一段: 整体概况 ──
    trend = "下跌" if week_chg < 0 else "上涨"
    chg_vals = [d["change_pct"] for d in days]
    neg_days = sum(1 for c in chg_vals if c < 0)

    lines.append(f"本周CATL累计{trend}{abs(week_chg):.1f}%，{neg_days}天下跌。")

    # 每日细节
    daily_detail = " → ".join([f"{d['change_pct']:+.1f}%" for d in days])
    lines.append(f"每日涨跌: {daily_detail}")

    # 收窄/扩大判断
    if len(chg_vals) >= 3:
        first_half = chg_vals[:len(chg_vals)//2]
        second_half = chg_vals[len(chg_vals)//2:]
        avg1 = sum(first_half) / len(first_half)
        avg2 = sum(second_half) / len(second_half)
        if avg2 > avg1 and avg1 < 0:
            lines.append(f"📉 好消息是跌幅在收窄（前半周均值{avg1:+.1f}% → 后半周{avg2:+.1f}%），抛压可能接近尾声。")
        elif avg2 < avg1 and avg1 < 0:
            lines.append(f"⚠️ 跌幅仍在扩大（前半周{avg1:+.1f}% → 后半周{avg2:+.1f}%），抛压尚未释放完毕。")

    # ── 第二段: 市场环境 ──
    ss = market.get("上证指数", {})
    if ss:
        ss_chg = ss.get("change_pct")
        if ss_chg is not None:
            diff = round(week_chg - ss_chg, 2) if ss_chg else 0
            if week_chg < 0 and ss_chg > 0:
                lines.append(f"📊 大盘（上证）上涨{ss_chg:+.1f}%，但宁德逆势下跌{diff:.1f}个百分点——资金被半导体、AI算力等热门板块虹吸，新能源/锂电暂时失血。")
            elif week_chg < ss_chg:
                lines.append(f"📊 宁德跑输大盘（周跌{abs(week_chg):.1f}% vs 上证{ss_chg:+.1f}%），板块整体偏弱。")
            else:
                lines.append(f"📊 宁德跑赢大盘（周{'+' if week_chg>0 else ''}{week_chg:.1f}% vs 上证{ss_chg:+.1f}%），独立走强。")

    # ── 第三段: 资金面 ──
    if week_fund < -5:
        lines.append(f"💰 主力资金本周持续净流出，合计{abs(week_fund):.1f}亿元，机构在减仓。")
    elif week_fund < 0:
        lines.append(f"💰 主力资金小幅净流出{abs(week_fund):.1f}亿元，抛压有限。")
    elif week_fund > 0:
        lines.append(f"💰 主力资金净流入{week_fund:.1f}亿元，机构在吸筹。")
    else:
        lines.append("💰 主力资金本周基本平衡（东财数据暂缺，待恢复后更新）。")

    # ── 第四段: 估值与技术面 ──
    if pe_ttm:
        lines.append(f"📏 当前PE={pe_ttm:.1f}x，PEG={peg:.2f}，" +
                    ("处于低估区间（PEG<1），越跌越便宜。" if peg and peg < 1 else
                     "估值合理。" if peg and peg < 1.5 else "估值偏高，需注意风险。"))

    if ma60.get("value"):
        dist = ma60.get("dist_pct", 0)
        near = ma60.get("near", False)
        lines.append(f"📐 MA60=¥{ma60['value']:.0f}，" +
                    (f"当前价距MA60仅{abs(dist):.1f}%，已逼近核心支撑位——这是技术面的关键防线。" if near else
                     f"距MA60还有{abs(dist):.1f}%距离，下方有支撑。"))

    if streak and streak.get("days", 0) >= 3:
        lines.append(f"📉 连续{streak['direction']}{streak['days']}日，累计{abs(streak['pct']):.1f}%。" +
                    ("恐慌盘在加速出清，通常这是底部信号之一。" if streak.get("direction") == "跌" else "短线过热，注意回调风险。"))

    # ── 第五段: AH溢价 ──
    if ah is not None and ah < 0:
        lines.append(f"💱 AH溢价{ah:.1f}%（A股折价港股），意味着A股比港股便宜{abs(ah):.0f}%，对A股持有者是成本端利好。")

    # ── 第六段: 碳酸锂 ──
    li_text = li.get("text", "")
    if li_text and "暂缺" not in li_text:
        impact = li.get("impact", "")
        if "利好" in impact:
            lines.append(f"⛏️ {li_text}——原材料成本下行，对CATL毛利率是正面贡献。")
        elif "压力" in impact:
            lines.append(f"⛏️ {li_text}——原材料成本上行，短期压缩利润空间。")
        else:
            lines.append(f"⛏️ {li_text}，成本端稳定。")

    # ── 结尾: 操作提示 ──
    if peg and peg < 1 and ma60.get("near"):
        lines.append("💡 综合来看：估值已进入低估区间，技术面逼近强支撑。如果你是长期持有者，当前价位可能是分批加仓的窗口期。但短期趋势偏弱，建议等企稳信号出现后再动手。")
    elif peg and peg >= 1.5:
        lines.append("💡 估值偏高+趋势偏弱，建议观望为主，耐心等待PEG回到1.0以下的买入区间。")

    return "\n\n".join(lines)


def calc_streak(kline, current_price):
    if len(kline) < 2: return 0, 0, "—"
    closes = [k["close"] for k in kline]
    if len(closes) < 2: return 0, 0, "—"
    if current_price > closes[-1] if abs(current_price - closes[-1]) > 0.01 else closes[-1] > closes[-2]:
        direction, dir_cn = "up", "涨"
    elif current_price < closes[-1] if abs(current_price - closes[-1]) > 0.01 else closes[-1] < closes[-2]:
        direction, dir_cn = "down", "跌"
    else:
        return 0, 0, "平"
    streak = 1; prev = current_price
    for i in range(len(closes) - 1, -1, -1):
        if direction == "up" and closes[i] < prev: streak += 1; prev = closes[i]
        elif direction == "down" and closes[i] > prev: streak += 1; prev = closes[i]
        else: break
    if len(closes) >= streak:
        start_price = closes[len(closes) - streak]
        total_pct = round((current_price - start_price) / start_price * 100, 2) if start_price else 0
    else:
        total_pct = 0
    return streak, total_pct, dir_cn


def calc_period_change(kline, current_price, days):
    if not kline or len(kline) < days: return None
    start = kline[len(kline) - days]["close"]
    return round((current_price - start) / start * 100, 2) if start else None


def calc_avg_volume(kline, days):
    if not kline: return None
    recent = kline[-days:]
    vols = [k.get("volume", 0) for k in recent if k.get("volume", 0) > 0]
    return sum(vols) / len(vols) if vols else None


if __name__ == "__main__":
    data = collect_all()
    with open(os.path.join(REPO_DIR, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 saved → {REPO_DIR}/data.json")
