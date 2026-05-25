#!/usr/bin/env python3
"""CATL 生态链日监控 — 数据采集模块 v1.2

新增: 60日K线 / 大盘指数 / MA5-20-60 / 行业涨跌 / 操作建议数据
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
        price, prev = float(p[3]), float(p[2])
        return {"price": price, "prev_close": prev,
                "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
    except: return None


def fetch_catl_pe():
    try:
        raw = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,1,qfq", headers=H_EM)
        d = json.loads(raw)
        qt = d.get("data", {}).get("sz300750", {}).get("qt", {}).get("sz300750", [])
        if len(qt) > 58 and qt[58]:
            return {"pe_ttm": float(qt[58])}
    except: pass
    return None


def fetch_catl_kline(days=60):
    """CATL K线 (腾讯复权) → 用于均线/连涨连跌"""
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


def fetch_market_indices():
    """大盘指数（上证/沪深300）"""
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
# 模块二: 上游原材料
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
    materials = {}
    ppi_map = {"碳酸锂": ("https://www.100ppi.com/price/detail-2928.html", 10000),
               "氢氧化锂": ("https://www.100ppi.com/price/detail-2858.html", 10000),
               "电解钴": ("https://www.100ppi.com/price/detail-2758.html", 10000),
               "硫酸镍": ("https://www.100ppi.com/price/detail-2481.html", 10000),
               "磷酸铁锂": ("https://www.100ppi.com/price/detail-2762.html", 10000),
               "六氟磷酸锂": ("https://www.100ppi.com/price/detail-3206.html", 10000)}
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
    for mat_name, ref in MATERIAL_REFERENCE.items():
        if mat_name not in materials:
            materials[mat_name] = {**ref, "source": "参考"}
            short = mat_name.split("(")[0].strip()
            if short not in materials: materials[short] = {**ref, "source": "参考"}
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
                 "date": (a.get("date", "") or "")[:10], "source": a.get("mediaName", ""),
                 "url": a.get("url", "")}
                for a in json.loads(m.group(1)).get("result", {}).get("cmsArticleWebOld", [])]
    except: return []


def fetch_all_news():
    return {kw: fetch_news(kw) for kw in NEWS_KEYWORDS}


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


# ═══════════════════════════════════════════
# 主采集
# ═══════════════════════════════════════════

def collect_all(verbose=True):
    if verbose: print("🔋 CATL 生态链数据采集 v1.2\n" + "=" * 50)

    data = {"date": get_date_str(), "datetime": get_datetime_str(), "mode": get_mode()}

    # 核心
    if verbose: print("📡 CATL核心 + K线 + 大盘...")
    data["catl_a"] = fetch_catl_a()
    data["catl_h"] = fetch_catl_h()
    data["catl_pe"] = fetch_catl_pe()
    data["catl_fund"] = fetch_catl_fund_flow()
    data["catl_kline"] = fetch_catl_kline(60)
    data["market"] = fetch_market_indices()
    if verbose:
        a = data["catl_a"]
        print(f"  A股: ¥{a['price']} ({a['change_pct']:+.1f}%)" if a else "  A股: ❌")
        print(f"  K线: {len(data['catl_kline'])}日")
        m = data["market"]
        if m:
            ss = m.get("上证指数", {})
            print(f"  上证: {ss['change_pct']:+.2f}%" if ss else "  上证: ❌")
            hs = m.get("沪深300", {})
            print(f"  沪深300: {hs['change_pct']:+.2f}%" if hs else "  沪深300: ❌")

    # 其他模块
    if verbose: print("⛏️ 原材料...")
    data["materials"] = fetch_material_prices()
    data["lithium_futures"] = fetch_lithium_futures()

    if verbose: print("🏭 上游..."); data["upstream"] = fetch_stock_batch(UPSTREAM_STOCKS)
    if verbose: print("⚔️ 竞争..."); data["competitors"] = fetch_stock_batch(COMPETITORS)
    if verbose: print("📊 板块..."); data["sectors"] = fetch_sector_indices()
    if verbose: print("📰 新闻..."); data["news"] = fetch_all_news()
    if verbose: print(f"  {sum(len(v) for v in data['news'].values())} 条")
    if verbose: print("💰 北向..."); data["north_flow"] = fetch_north_flow()
    if verbose: print("🚗 新能源车..."); data["nev_sector"] = fetch_nev_sector()

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
    s = {}  # summaries dict

    # ── 1. 均线系统 ──
    if kline and price:
        mas = {}
        for w in MA_WINDOWS:
            if len(kline) >= w:
                closes = [k["close"] for k in kline[-w:]]
                mas[f"MA{w}"] = round(statistics.mean(closes), 2)
        s["mas"] = mas

        # 距MA60
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
        streak, streak_pct, direction = calc_streak(kline, price)
        s["streak"] = {"days": streak, "pct": streak_pct, "direction": direction,
                       "text": f"连{direction}{streak}日 累计{'-' if direction=='跌' else '+'}{abs(streak_pct):.1f}%"}
        s["chg_5d"] = calc_period_change(kline, price, 5)
        s["chg_10d"] = calc_period_change(kline, price, 10)
        s["chg_20d"] = calc_period_change(kline, price, 20)
        # 量能
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

    # ── 3. 大盘对比 ──
    ss_index = market.get("上证指数", {})
    hs300 = market.get("沪深300", {})
    catl_chg = a.get("change_pct") if a else None
    market_chg = ss_index.get("change_pct") if ss_index else None

    if catl_chg is not None and market_chg is not None:
        diff = round(catl_chg - market_chg, 2)
        if catl_chg < 0 and market_chg > 0:
            s["vs_market"] = {"text": f"逆势下跌{catl_chg:.1f}% (大盘{'+' if market_chg>0 else ''}{market_chg:.2f}%)",
                              "type": "diverge_down", "diff": diff}
        elif catl_chg > 0 and market_chg < 0:
            s["vs_market"] = {"text": f"逆势上涨{catl_chg:.1f}% (大盘{market_chg:.2f}%)",
                              "type": "diverge_up", "diff": diff}
        elif catl_chg < market_chg:
            s["vs_market"] = {"text": f"跑输大盘 ({catl_chg:.1f}% vs {market_chg:+.2f}%)",
                              "type": "underperform", "diff": diff}
        else:
            s["vs_market"] = {"text": f"跑赢大盘 ({catl_chg:+.1f}% vs {market_chg:+.2f}%)",
                              "type": "outperform", "diff": diff}
    else:
        s["vs_market"] = {"text": "", "type": "unknown", "diff": 0}

    # ── 4. AH溢价 ──
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

    # ── 5. PEG + 目标价 ──
    if pe_ttm and pe_ttm > 0 and price:
        peg = round(pe_ttm / GROWTH_ASSUMPTION, 2)
        data["peg"] = peg
        eps = price / pe_ttm
        target_pe_peg1 = GROWTH_ASSUMPTION
        target_price_peg1 = round(target_pe_peg1 * eps, 2)
        dist_to_buy = round((target_price_peg1 - price) / price * 100, 2)

        s["peg"] = {"value": peg, "target_price": target_price_peg1, "distance_pct": dist_to_buy}

        if peg < PEG_UNDERVALUE:
            s["peg"]["signal"] = "buy"
            s["peg"]["text"] = f"PEG={peg:.2f} < 1.0 买入区间"
            data["peg_signal"] = {"text": "低估区间 ✅", "color": "#3fb950", "level": "buy"}
        elif peg > PEG_OVERVALUE:
            s["peg"]["signal"] = "sell"
            s["peg"]["text"] = f"PEG={peg:.2f} 偏高 距买点差{dist_to_buy:.1f}%"
            data["peg_signal"] = {"text": "偏高区间 ⚠️", "color": "#f85149", "level": "sell"}
        else:
            s["peg"]["signal"] = "hold"
            s["peg"]["text"] = f"PEG={peg:.2f} 合理"
            data["peg_signal"] = {"text": "合理区间 📊", "color": "#d29922", "level": "hold"}

        # 目标价（基于PE合理区间）
        target_low = round(s["peg"]["target_price"], 0)
        target_high = round(TRADING["target_pe_range"][1] * eps, 0)
        target_mid = round(statistics.mean([target_low, target_high]), 0)
        s["target_prices"] = {"low": target_low, "mid": target_mid, "high": target_high}
    else:
        data["peg"] = None
        data["peg_signal"] = {"text": "--", "color": "#8b949e", "level": "unknown"}
        s["peg"] = {"value": None, "target_price": None, "distance_pct": None,
                    "signal": "unknown", "text": "—"}
        s["target_prices"] = {"low": 0, "mid": 0, "high": 0}

    # ── 6. PE ──
    if pe_ttm:
        pe_level = "偏低" if pe_ttm < 25 else "合理" if pe_ttm < 40 else "偏高" if pe_ttm < 60 else "高"
        s["pe"] = {"value": pe_ttm, "level": pe_level,
                   "text": f"PE={pe_ttm:.1f}x {pe_level}"}
    else:
        s["pe"] = {"value": None, "level": "unknown", "text": "—"}

    # ── 7. 资金面 ──
    if fund:
        mn = fund.get("main_net", 0) / 1e4
        d3 = fund.get("three_day", 0) / 1e4
        d5 = fund.get("five_day", 0) / 1e4
        parts = []
        if abs(mn) > 0.5:
            parts.append(f"主力今日{'净流入' if mn>0 else '净流出'}{abs(mn):.1f}亿")
        if abs(d5) > 1:
            parts.append(f"近5日{'累计流入' if d5>0 else '累计流出'}{abs(d5):.1f}亿")
        s["fund"] = {"text": "，".join(parts) if parts else "资金平稳", "main_net": mn, "five_day": d5}
    else:
        s["fund"] = {"text": "数据暂缺", "main_net": 0, "five_day": 0}

    # ── 8. 碳酸锂 ──
    if lf and lf.get("price"):
        li_price = lf["price"]
        li_cur = li_price / 10000
        ref_li = 7.5
        delta = li_cur - ref_li
        impact = "成本利好" if delta < -0.5 else "成本压力" if delta > 0.5 else "成本稳定"
        s["lithium"] = {"price": li_price, "price_wan": round(li_cur, 2), "delta_wan": round(delta, 2),
                        "impact": impact,
                        "text": f"碳酸锂{li_cur:.1f}万/吨 {impact}" if abs(delta) > 0.3 else f"碳酸锂{li_cur:.1f}万/吨 稳定"}
    else:
        s["lithium"] = {"text": "碳酸锂数据暂缺"}

    # ── 9. 上游异动 ──
    upstream_alerts = []
    for name, st in upstream.items():
        if abs(st["change_pct"]) > 5:
            upstream_alerts.append({"name": name, "change": st["change_pct"],
                                    "text": f"{name} {st['change_pct']:+.1f}%"})
    s["upstream_alerts"] = upstream_alerts

    # ── 10. 成交额 ──
    if a and a.get("amount"):
        amt_yi = a["amount"] / 1e8
        amt_level = "放量明显" if amt_yi > 100 else "交投活跃" if amt_yi > 50 else "正常" if amt_yi > 20 else "缩量"
        s["amount"] = {"value": amt_yi, "level": amt_level, "text": f"成交额{amt_yi:.0f}亿 {amt_level}"}
    else:
        s["amount"] = {"text": "—"}

    # ── 11. 行业涨跌 ──
    ind_name = CATL_INDUSTRY_INDEX
    ind_data = sectors.get(ind_name)
    if ind_data:
        s["industry"] = {"name": ind_name, "change_pct": ind_data["change_pct"],
                         "text": f"{ind_name} {ind_data['change_pct']:+.1f}%"}
    else:
        # fallback to first available sector
        for sn, sd in sectors.items():
            s["industry"] = {"name": sn, "change_pct": sd["change_pct"],
                             "text": f"{sn} {sd['change_pct']:+.1f}%"}
            break
        else:
            s["industry"] = {"name": "—", "change_pct": 0, "text": "—"}

    # ── 12. 成本盈亏 ──
    if price and COST_PRICE:
        cost_chg = round((price - COST_PRICE) / COST_PRICE * 100, 2)
        s["cost"] = {"cost_price": COST_PRICE, "current": price, "change_pct": cost_chg,
                     "text": f"成本¥{COST_PRICE} 浮{'盈' if cost_chg>0 else '亏'}{abs(cost_chg):.1f}%"}
    else:
        s["cost"] = {"text": "—"}

    # ── 核心总结句 ──
    core_summary_parts = []
    peg_sig = s.get("peg", {})
    if peg_sig.get("signal") == "buy":
        core_summary_parts.append(f"PEG {peg_sig['value']:.2f} 买入区间")
    elif peg_sig.get("signal") == "sell":
        core_summary_parts.append(f"PEG {peg_sig['value']:.2f} 偏高")
    else:
        core_summary_parts.append(f"PEG {peg_sig.get('value','—')}")

    streak_sig = s.get("streak", {})
    if streak_sig.get("days", 0) >= 3:
        core_summary_parts.append(f"连{streak_sig['direction']}{streak_sig['days']}日{'累计'}{abs(streak_sig['pct']):.1f}%")

    li_sig = s.get("lithium", {})
    if li_sig.get("impact"):
        core_summary_parts.append(f"碳酸锂{li_sig.get('price_wan','')}万/吨 {li_sig.get('impact','')}")

    ah_sig = s.get("ah", {})
    ah = data.get("ah_premium")
    if ah is not None and ah < 0:
        core_summary_parts.append(f"AH溢价{ah:.1f}% 折价")

    vs_market = s.get("vs_market", {})
    if vs_market.get("type") == "diverge_down":
        core_summary_parts.append("逆势下跌 分化延续")

    s["core_summary"] = " · ".join(core_summary_parts) if core_summary_parts else "数据采集中"

    # ── 行业对比总结 ──
    ind = s.get("industry", {})
    if catl_chg is not None and ind.get("change_pct") is not None:
        ind_diff = round(catl_chg - ind["change_pct"], 2)
        if ind_diff < -1:
            s["vs_industry"] = f"弱于行业{abs(ind_diff):.1f}%"
        elif ind_diff > 1:
            s["vs_industry"] = f"强于行业{ind_diff:.1f}%"
        else:
            s["vs_industry"] = "与行业同步"
    else:
        s["vs_industry"] = ""

    # 上游/竞争平均
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
    return data


# ═══════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════

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

    streak = 1
    prev = current_price
    for i in range(len(closes) - 1, -1, -1):
        if direction == "up" and closes[i] < prev:
            streak += 1; prev = closes[i]
        elif direction == "down" and closes[i] > prev:
            streak += 1; prev = closes[i]
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


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == "__main__":
    data = collect_all()
    with open(os.path.join(REPO_DIR, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 saved → {REPO_DIR}/data.json")
