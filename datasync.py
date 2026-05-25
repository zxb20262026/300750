#!/usr/bin/env python3
"""CATL 生态链日监控 — 数据采集模块 v1.1

新增: K线历史 → 连涨连跌 / 距买点距离 / AH溢价趋势 / 节点总结话术
"""

import urllib.request, ssl, json, re, time
from config import *

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
H_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"}


def get(url, enc="utf-8", t=10, headers=None):
    h = headers or H_SINA
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=t, context=ssl_ctx).read().decode(enc, errors="replace")


def get_json(url, t=10):
    return json.loads(get(url, t=t, headers=H_EM))


# ═══════════════════════════════════════════
# 模块一: CATL 核心仪表盘
# ═══════════════════════════════════════════

def fetch_catl_a():
    """CATL A股实时行情"""
    try:
        raw = get("https://hq.sinajs.cn/list=sz300750", "gbk")
        m = re.search(r'"(.+?)"', raw)
        if not m: return None
        p = m.group(1).split(",")
        if len(p) < 10: return None
        price = float(p[3])
        prev_close = float(p[2])
        return {
            "name": p[0], "price": price, "prev_close": prev_close,
            "open": float(p[1]), "high": float(p[4]), "low": float(p[5]),
            "volume": int(p[8]) if p[8] else 0,
            "amount": float(p[9]) if p[9] else 0,
            "change": round(price - prev_close, 2),
            "change_pct": round((price - prev_close) / prev_close * 100, 2) if prev_close else 0,
        }
    except:
        return None


def fetch_catl_h():
    """CATL H股"""
    try:
        raw = get("https://hq.sinajs.cn/list=hk03750", "gbk")
        m = re.search(r'"(.+?)"', raw)
        if not m: return None
        p = m.group(1).split(",")
        if len(p) < 10: return None
        price = float(p[3])
        prev_close = float(p[2])
        return {
            "price": price, "prev_close": prev_close,
            "change_pct": round((price - prev_close) / prev_close * 100, 2) if prev_close else 0,
        }
    except:
        return None


def fetch_catl_pe():
    """CATL PE(TTM) 腾讯源"""
    try:
        raw = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,1,qfq", headers=H_EM)
        d = json.loads(raw)
        qt = d.get("data", {}).get("sz300750", {}).get("qt", {}).get("sz300750", [])
        if len(qt) > 58 and qt[58]:
            return {"pe_ttm": float(qt[58])}
    except:
        pass
    return None


def fetch_catl_kline(days=20):
    """CATL K线历史 (腾讯复权数据) → 用于连涨连跌/均线等"""
    try:
        raw = get(
            f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300750,day,,,{days},qfq",
            headers=H_EM)
        d = json.loads(raw)
        klines = d.get("data", {}).get("sz300750", {}).get("qfqday", [])
        if not klines:
            klines = d.get("data", {}).get("sz300750", {}).get("day", [])
        result = []
        for k in klines:
            parts = k.split(",") if isinstance(k, str) else k
            if len(parts) >= 6:
                result.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5]) if len(parts) > 5 else 0,
                })
        return result
    except:
        return []


def fetch_catl_fund_flow():
    """CATL 主力资金流向"""
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/stock/get?secid=0.300750&fields=f62,f64,f66,f184,f63,f65,f99,f100,f101")
        data = d.get("data", {})
        if not data or not data.get("f62"): return None
        return {
            "main_net": data.get("f62", 0), "huge_net": data.get("f64", 0),
            "big_net": data.get("f66", 0), "small_net": data.get("f184", 0),
            "main_pct": data.get("f63", 0), "today_in": data.get("f65", 0),
            "three_day": data.get("f99", 0), "five_day": data.get("f100", 0),
            "ten_day": data.get("f101", 0),
        }
    except:
        return None


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
            return {
                "price": float(p[3]),
                "prev_settle": float(p[4]) if p[4] else 0,
                "change_pct": round((float(p[3]) - float(p[4])) / float(p[4]) * 100, 2) if p[4] and float(p[4]) else 0,
                "name": p[0],
            }
    except:
        pass
    return None


def fetch_material_prices():
    materials = {}
    ppi_map = {
        "碳酸锂": ("https://www.100ppi.com/price/detail-2928.html", 10000),
        "氢氧化锂": ("https://www.100ppi.com/price/detail-2858.html", 10000),
        "电解钴": ("https://www.100ppi.com/price/detail-2758.html", 10000),
        "硫酸镍": ("https://www.100ppi.com/price/detail-2481.html", 10000),
        "磷酸铁锂": ("https://www.100ppi.com/price/detail-2762.html", 10000),
        "六氟磷酸锂": ("https://www.100ppi.com/price/detail-3206.html", 10000),
    }
    for name, (url, divisor) in ppi_map.items():
        try:
            raw = get(url, "gbk", t=8)
            for pat in [
                r'最新价.*?(\d[\d,]*\.?\d*)', r'价格.*?(\d[\d,]*\.?\d*)',
                r'>(\d[\d,]*\.?\d*)\s*<.*?元/吨', r'\b(\d[\d,]*\.?\d*)\s*元\s*/\s*吨\b',
            ]:
                m = re.search(pat, raw)
                if m:
                    v = m.group(1).replace(",", "")
                    materials[name] = {"price": round(float(v) / divisor, 2),
                                       "unit": "万元/吨" if divisor > 100 else "元/吨", "source": "100ppi"}
                    break
        except:
            pass
    for mat_name, ref in MATERIAL_REFERENCE.items():
        if mat_name not in materials:
            materials[mat_name] = {**ref, "source": "参考"}
            short = mat_name.split("(")[0].strip()
            if short not in materials:
                materials[short] = {**ref, "source": "参考"}
    return materials


# ═══════════════════════════════════════════
# 模块三/四/五: 股票批量 + 板块 + 新闻
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
        except:
            pass
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
        except:
            pass
    return results


def fetch_news(keyword, count=5):
    try:
        params = {"cb": "jQ", "param": json.dumps({
            "uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"],
            "client": "web", "clientType": "web", "clientVersion": "curr",
            "paramNum": 20, "pageNum": 1, "pageSize": count,
        })}
        url = "https://search-api-web.eastmoney.com/search/jsonp?" + urllib.parse.urlencode(params)
        raw = get(url, headers=H_EM)
        m = re.search(r'jQ\((.*)\)\s*$', raw.strip())
        if not m: return []
        return [{"title": a.get("title", "").replace("<em>", "").replace("</em>", ""),
                 "date": (a.get("date", "") or "")[:10],
                 "source": a.get("mediaName", ""), "url": a.get("url", "")}
                for a in json.loads(m.group(1)).get("result", {}).get("cmsArticleWebOld", [])]
    except:
        return []


def fetch_all_news():
    return {kw: fetch_news(kw) for kw in NEWS_KEYWORDS}


def fetch_north_flow():
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/kamt.kline/get?fields1=f1,f3&fields2=f51,f52,f53,f54&klt=101&lmt=5")
        klines = d.get("data", {}).get("klines", [])
        if not klines: return None
        today = klines[-1].split(",")
        yesterday = klines[-2].split(",") if len(klines) > 1 else today
        return {
            "today": {"date": today[0], "net": round(float(today[1]), 2)},
            "yesterday": {"date": yesterday[0], "net": round(float(yesterday[1]), 2)} if yesterday != today else None,
        }
    except:
        return None


def fetch_nev_sector():
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&fields=f2,f3,f12,f14&fid=f3&fs=b:BK0493")
        return {"total_stocks": d.get("data", {}).get("total", 0)}
    except:
        return None


# ═══════════════════════════════════════════
# 主采集函数
# ═══════════════════════════════════════════

def collect_all(verbose=True):
    if verbose: print("🔋 CATL 生态链数据采集\n" + "=" * 50)

    data = {"date": get_date_str(), "datetime": get_datetime_str(), "mode": get_mode()}

    # 1. CATL核心 + K线
    if verbose: print("📡 CATL核心 + K线...")
    data["catl_a"] = fetch_catl_a()
    data["catl_h"] = fetch_catl_h()
    data["catl_pe"] = fetch_catl_pe()
    data["catl_fund"] = fetch_catl_fund_flow()
    data["catl_kline"] = fetch_catl_kline(20)
    if verbose:
        a = data["catl_a"]
        print(f"  A股: ¥{a['price']} ({a['change_pct']:+.1f}%)" if a else "  A股: ❌")
        print(f"  K线: {len(data['catl_kline'])}日")

    # 2-8. 其他模块
    if verbose: print("⛏️ 原材料...")
    data["materials"] = fetch_material_prices()
    data["lithium_futures"] = fetch_lithium_futures()

    if verbose: print("🏭 上游龙头...")
    data["upstream"] = fetch_stock_batch(UPSTREAM_STOCKS)

    if verbose: print("⚔️ 竞争对手...")
    data["competitors"] = fetch_stock_batch(COMPETITORS)

    if verbose: print("📊 板块指数...")
    data["sectors"] = fetch_sector_indices()

    if verbose: print("📰 新闻...")
    data["news"] = fetch_all_news()
    if verbose: print(f"  {sum(len(v) for v in data['news'].values())} 条")

    if verbose: print("💰 北向资金...")
    data["north_flow"] = fetch_north_flow()

    if verbose: print("🚗 新能源车...")
    data["nev_sector"] = fetch_nev_sector()

    # 计算衍生指标
    compute_derived(data)

    if verbose: print("=" * 50 + "\n✅ 采集完成")
    return data


def compute_derived(data):
    """计算所有衍生指标 + 节点总结话术"""
    a = data.get("catl_a", {})
    h = data.get("catl_h", {})
    pe = data.get("catl_pe", {})
    fund = data.get("catl_fund") or {}
    kline = data.get("catl_kline", [])
    upstream = data.get("upstream", {})
    lf = data.get("lithium_futures", {})

    price = a.get("price") if a else None
    pe_ttm = pe.get("pe_ttm") if pe else None
    summaries = {}

    # ── 1. 连涨/连跌分析 ──
    if kline and len(kline) >= 3 and price:
        streak, streak_pct, streak_direction = calc_streak(kline, price)
        summaries["streak"] = {
            "days": streak, "pct": streak_pct,
            "direction": streak_direction,  # "up" or "down"
            "text": f"连{streak_direction}{streak}日 累计{'-' if streak_direction=='跌' else '+'}{abs(streak_pct):.1f}%"
        }
        # 5日/10日/20日涨跌
        summaries["chg_5d"] = calc_period_change(kline, price, 5)
        summaries["chg_10d"] = calc_period_change(kline, price, 10)
        summaries["chg_20d"] = calc_period_change(kline, price, 20)

        # 5日均量 vs 今日量 (判断放量/缩量)
        avg_vol_5d = calc_avg_volume(kline, 5)
        today_vol = a.get("volume", 0) if a else 0
        if avg_vol_5d and today_vol:
            vol_ratio = today_vol / avg_vol_5d
            summaries["volume_ratio"] = {"ratio": round(vol_ratio, 2),
                "text": f"量能{vol_ratio:.1f}x 均量" if vol_ratio >= 1 else f"缩量 {vol_ratio:.1f}x"}
        else:
            summaries["volume_ratio"] = {"ratio": 0, "text": "—"}

    else:
        summaries["streak"] = {"days": 0, "pct": 0, "direction": "—", "text": "—"}
        summaries["chg_5d"] = summaries["chg_10d"] = summaries["chg_20d"] = None
        summaries["volume_ratio"] = {"ratio": 0, "text": "—"}

    # ── 2. AH溢价 ──
    if a and h and h.get("price") and price:
        h_cny = h["price"] * 0.92
        ah = round((price - h_cny) / h_cny * 100, 2) if h_cny else None
        data["ah_premium"] = ah
        if ah is not None:
            if ah < -30:
                summaries["ah"] = {"level": "extreme_discount", "text": f"A股折价港股{ah:.0f}%，再创新低"}
            elif ah < 0:
                summaries["ah"] = {"level": "discount", "text": f"A股折价港股{abs(ah):.0f}%，成本利好"}
            elif ah > 30:
                summaries["ah"] = {"level": "extreme_premium", "text": f"A股溢价港股{ah:.0f}%，溢价偏高"}
            else:
                summaries["ah"] = {"level": "normal", "text": f"A股溢价{ah:.0f}%，合理区间"}
        else:
            summaries["ah"] = {"level": "unknown", "text": "—"}
    else:
        data["ah_premium"] = None
        summaries["ah"] = {"level": "unknown", "text": "—"}

    # ── 3. PEG + 距离买点 ──
    if pe_ttm and pe_ttm > 0 and price:
        peg = round(pe_ttm / GROWTH_ASSUMPTION, 2)
        data["peg"] = peg

        # 计算 PEG=1.0 对应的目标价
        # PEG=PE/增速 → PE@PEG=1 = 增速 → 目标价 = PE目标 * EPS
        # EPS ≈ price / pe_ttm
        eps = price / pe_ttm
        target_pe_for_peg1 = GROWTH_ASSUMPTION  # PEG=1 → PE=增速
        target_price_peg1 = round(target_pe_for_peg1 * eps, 2)
        distance_to_buy = round((target_price_peg1 - price) / price * 100, 2) if price else None

        summaries["peg"] = {
            "value": peg,
            "target_price": target_price_peg1,
            "distance_pct": distance_to_buy,
        }

        if peg < PEG_UNDERVALUE:
            summaries["peg"]["signal"] = "buy"
            summaries["peg"]["text"] = f"PEG={peg:.2f} < 1.0 买入区间"
            data["peg_signal"] = {"text": "低估区间 ✅", "color": "#3fb950", "level": "buy"}
        elif peg > PEG_OVERVALUE:
            summaries["peg"]["signal"] = "sell"
            summaries["peg"]["text"] = f"PEG={peg:.2f} > 1.5 偏高，距买入线还需跌{distance_to_buy:.1f}%"
            data["peg_signal"] = {"text": "偏高区间 ⚠️", "color": "#f85149", "level": "sell"}
        else:
            summaries["peg"]["signal"] = "hold"
            summaries["peg"]["text"] = f"PEG={peg:.2f} 合理区间"
            data["peg_signal"] = {"text": "合理区间 📊", "color": "#d29922", "level": "hold"}
    else:
        data["peg"] = None
        data["peg_signal"] = {"text": "--", "color": "#8b949e", "level": "unknown"}
        summaries["peg"] = {"value": None, "target_price": None, "distance_pct": None,
                            "signal": "unknown", "text": "—"}

    # ── 4. PE分析 ──
    if pe_ttm:
        # 粗略PE判断 (基于行业经验)
        if pe_ttm < 25:
            pe_level = "偏低"
        elif pe_ttm < 40:
            pe_level = "合理"
        elif pe_ttm < 60:
            pe_level = "偏高"
        else:
            pe_level = "高"
        summaries["pe"] = {"value": pe_ttm, "level": pe_level,
                           "text": f"PE={pe_ttm:.1f}x {pe_level}"}
    else:
        summaries["pe"] = {"value": None, "level": "unknown", "text": "—"}

    # ── 5. 资金面总结 ──
    if fund:
        mn = fund.get("main_net", 0) / 1e4
        d3 = fund.get("three_day", 0) / 1e4
        d5 = fund.get("five_day", 0) / 1e4
        d10 = fund.get("ten_day", 0) / 1e4

        fund_summary_parts = []
        if mn > 0.5:
            fund_summary_parts.append(f"今日主力净流入{mn:.1f}亿")
        elif mn < -0.5:
            fund_summary_parts.append(f"今日主力净流出{abs(mn):.1f}亿")

        if d5 > 1:
            fund_summary_parts.append(f"近5日累计流入{d5:.1f}亿")
        elif d5 < -1:
            fund_summary_parts.append(f"近5日累计流出{abs(d5):.1f}亿")

        summaries["fund"] = {"text": "，".join(fund_summary_parts) if fund_summary_parts else "资金平稳",
                             "main_net": mn, "five_day": d5}
    else:
        summaries["fund"] = {"text": "数据暂缺", "main_net": 0, "five_day": 0}

    # ── 6. 碳酸锂影响 ──
    if lf and lf.get("price"):
        li_price = lf["price"]
        # 粗略估算：碳酸锂每降1万/吨，CATL毛利率提升约0.5-1%
        # 参考价假设7.5万/吨为基准
        ref_li = 7.5  # 万元/吨基准
        li_cur = li_price / 10000  # 转万元
        delta = li_cur - ref_li
        if delta < -0.5:
            impact = "成本利好"
        elif delta > 0.5:
            impact = "成本压力"
        else:
            impact = "成本稳定"
        summaries["lithium"] = {
            "price": li_price, "price_wan": round(li_cur, 2),
            "delta_wan": round(delta, 2),
            "impact": impact,
            "text": f"碳酸锂{li_cur:.1f}万/吨 {impact}" if abs(delta) > 0.3 else f"碳酸锂{li_cur:.1f}万/吨 稳定"
        }
    else:
        summaries["lithium"] = {"text": "碳酸锂数据暂缺"}

    # ── 7. 上游异动 ──
    upstream_alerts = []
    for name, s in upstream.items():
        if abs(s["change_pct"]) > 5:
            upstream_alerts.append({
                "name": name, "change": s["change_pct"],
                "text": f"{name} {s['change_pct']:+.1f}%"
            })
    summaries["upstream_alerts"] = upstream_alerts

    # ── 8. 成交额判断 ──
    if a and a.get("amount"):
        amt_yi = a["amount"] / 1e8
        if amt_yi > 100:
            amt_level = "放量明显"
        elif amt_yi > 50:
            amt_level = "交投活跃"
        elif amt_yi > 20:
            amt_level = "正常"
        else:
            amt_level = "缩量"
        summaries["amount"] = {"value": amt_yi, "level": amt_level,
                               "text": f"成交额{amt_yi:.0f}亿 {amt_level}"}
    else:
        summaries["amount"] = {"text": "—"}

    # ── 9. 上游平均涨跌 ──
    if upstream:
        changes = [v["change_pct"] for v in upstream.values()]
        data["upstream_avg_change"] = round(sum(changes) / len(changes), 2) if changes else 0
    else:
        data["upstream_avg_change"] = 0

    # ── 10. 竞争平均涨跌 ──
    comps = data.get("competitors", {})
    if comps:
        changes = [v["change_pct"] for v in comps.values()]
        data["competitor_avg_change"] = round(sum(changes) / len(changes), 2) if changes else 0
    else:
        data["competitor_avg_change"] = 0

    # ── 组装 summaries ──
    data["summaries"] = summaries

    return data


# ═══════════════════════════════════════════
# 辅助计算函数
# ═══════════════════════════════════════════

def calc_streak(kline, current_price):
    """计算连涨/连跌天数"""
    if len(kline) < 2:
        return 0, 0, "—"

    # 从最近的数据往前数
    closes = [k["close"] for k in kline]

    # 最后一个是今天（或者最近一个收盘价）
    # 判断方向：比较最新两天的收盘价
    if len(closes) >= 2:
        if current_price > closes[-1] if current_price != closes[-1] else closes[-1] > closes[-2]:
            direction, dir_cn = "up", "涨"
        elif current_price < closes[-1] if current_price != closes[-1] else closes[-1] < closes[-2]:
            direction, dir_cn = "down", "跌"
        else:
            return 0, 0, "平"
    else:
        return 0, 0, "—"

    # 往前数连续同向的K线
    streak = 1
    prev = current_price

    for i in range(len(closes) - 1, -1, -1):
        if direction == "up" and closes[i] > prev:
            streak += 1
            prev = closes[i]
        elif direction == "down" and closes[i] < prev:
            streak += 1
            prev = closes[i]
        else:
            break

    # 计算累计涨跌幅
    if len(closes) >= streak:
        start_price = closes[len(closes) - streak]
        total_pct = round((current_price - start_price) / start_price * 100, 2) if start_price else 0
    else:
        total_pct = 0

    return streak, total_pct, dir_cn


def calc_period_change(kline, current_price, days):
    """计算N日涨跌幅"""
    if not kline or len(kline) < days:
        return None
    start_close = kline[len(kline) - days]["close"]
    if not start_close:
        return None
    return round((current_price - start_close) / start_close * 100, 2)


def calc_avg_volume(kline, days):
    """计算N日均量"""
    if not kline:
        return None
    recent = kline[-days:]
    volumes = [k.get("volume", 0) for k in recent]
    valid = [v for v in volumes if v > 0]
    return sum(valid) / len(valid) if valid else None


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == "__main__":
    data = collect_all()
    out_path = os.path.join(REPO_DIR, "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 saved → {out_path}")
