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
        # 港股Sina格式: [0]英文名 [1]中文名 [2]今开 [3]昨收 [4]最高 [5]最低 [6]现价
        price = float(p[6]) if len(p) > 6 else float(p[3])
        prev = float(p[3])
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

