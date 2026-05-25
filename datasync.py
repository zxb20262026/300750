#!/usr/bin/env python3
"""CATL 生态链日监控 — 数据采集模块

采集范围: CATL核心 + 上游材料 + 上游龙头 + 下游需求 + 竞争格局 + 板块指数 + 资讯 + 期货
全部零依赖 (urllib only), 多源fallback
"""

import urllib.request, ssl, json, re, time
from config import *

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
H_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"}


def get(url, enc="utf-8", t=10, headers=None):
    """HTTP GET with encoding"""
    h = headers or H_SINA
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=t, context=ssl_ctx).read().decode(enc, errors="replace")


def get_json(url, t=10):
    """GET and parse JSON"""
    raw = get(url, t=t, headers=H_EM)
    return json.loads(raw)


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
            "name": p[0],
            "price": price,
            "prev_close": prev_close,
            "open": float(p[1]),
            "high": float(p[4]),
            "low": float(p[5]),
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
            "price": price,
            "prev_close": prev_close,
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


def fetch_catl_fund_flow():
    """CATL 主力资金流向"""
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get?secid=0.300750&fields=f62,f64,f66,f184,f63,f65,f99,f100,f101"
        d = get_json(url)
        data = d.get("data", {})
        if not data or not data.get("f62"):
            return None
        return {
            "main_net": data.get("f62", 0),
            "huge_net": data.get("f64", 0),
            "big_net": data.get("f66", 0),
            "small_net": data.get("f184", 0),
            "main_pct": data.get("f63", 0),
            "today_in": data.get("f65", 0),
            "three_day": data.get("f99", 0),
            "five_day": data.get("f100", 0),
            "ten_day": data.get("f101", 0),
        }
    except:
        return None


# ═══════════════════════════════════════════
# 模块二: 上游原材料
# ═══════════════════════════════════════════

def fetch_lithium_futures():
    """碳酸锂期货 (广期所)"""
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
    """原材料价格 (100ppi source, with fallback)"""
    # Try 100ppi first
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
            # Try multiple patterns
            for pat in [
                r'最新价.*?(\d[\d,]*\.?\d*)',
                r'价格.*?(\d[\d,]*\.?\d*)',
                r'>(\d[\d,]*\.?\d*)\s*<.*?元/吨',
                r'\b(\d[\d,]*\.?\d*)\s*元\s*/\s*吨\b',
            ]:
                m = re.search(pat, raw)
                if m:
                    v = m.group(1).replace(",", "")
                    vf = float(v)
                    price = round(vf / divisor, 2)
                    materials[name] = {"price": price, "unit": "万元/吨" if divisor > 100 else "元/吨", "source": "100ppi"}
                    break
        except:
            pass

    # Fallback to reference if not fetched
    for mat_name, ref in MATERIAL_REFERENCE.items():
        if mat_name not in materials:
            materials[mat_name] = {**ref, "source": "参考"}
            # Add simple 2-letter key
            short = mat_name.split("(")[0].strip()
            if short not in materials:
                materials[short] = {**ref, "source": "参考"}

    return materials


# ═══════════════════════════════════════════
# 模块三: 上游龙头股价
# ═══════════════════════════════════════════

def fetch_stock_batch(stock_map):
    """批量获取股票行情"""
    results = {}
    for name, code in stock_map.items():
        try:
            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
            m = re.search(r'"(.+?)"', raw)
            if not m: continue
            p = m.group(1).split(",")
            if len(p) < 10: continue
            price = float(p[3])
            prev = float(p[2])
            results[name] = {
                "code": code,
                "price": price,
                "change_pct": round((price - prev) / prev * 100, 2) if prev else 0,
            }
        except:
            pass
    return results


# ═══════════════════════════════════════════
# 模块四: 板块指数
# ═══════════════════════════════════════════

def fetch_sector_indices():
    """板块指数行情"""
    results = {}
    for name, code in SECTOR_INDICES.items():
        try:
            raw = get(f"https://hq.sinajs.cn/list={code}", "gbk")
            m = re.search(r'"(.+?)"', raw)
            if not m: continue
            p = m.group(1).split(",")
            if len(p) < 10: continue
            price = float(p[3])
            prev = float(p[2])
            results[name] = {
                "price": price,
                "change_pct": round((price - prev) / prev * 100, 2) if prev else 0,
            }
        except:
            pass
    return results


# ═══════════════════════════════════════════
# 模块五: 新闻资讯
# ═══════════════════════════════════════════

def fetch_news(keyword, count=5):
    """东方财富新闻搜索"""
    try:
        params = {
            "cb": "jQ",
            "param": json.dumps({
                "uid": "",
                "keyword": keyword,
                "type": ["cmsArticleWebOld"],
                "client": "web",
                "clientType": "web",
                "clientVersion": "curr",
                "paramNum": 20,
                "pageNum": 1,
                "pageSize": count,
            })
        }
        url = "https://search-api-web.eastmoney.com/search/jsonp?" + urllib.parse.urlencode(params)
        raw = get(url, headers=H_EM)
        m = re.search(r'jQ\((.*)\)\s*$', raw.strip())
        if not m: return []
        articles = json.loads(m.group(1)).get("result", {}).get("cmsArticleWebOld", [])
        return [
            {
                "title": a.get("title", "").replace("<em>", "").replace("</em>", ""),
                "date": (a.get("date", "") or "")[:10],
                "source": a.get("mediaName", ""),
                "url": a.get("url", ""),
            }
            for a in articles
        ]
    except:
        return []


def fetch_all_news():
    """批量获取所有关键词新闻"""
    results = {}
    for kw in NEWS_KEYWORDS:
        results[kw] = fetch_news(kw)
    return results


# ═══════════════════════════════════════════
# 模块六: 北向资金
# ═══════════════════════════════════════════

def fetch_north_flow():
    """北向资金净流入"""
    try:
        url = "https://push2.eastmoney.com/api/qt/kamt.kline/get?fields1=f1,f3&fields2=f51,f52,f53,f54&klt=101&lmt=5"
        d = get_json(url)
        klines = d.get("data", {}).get("klines", [])
        if not klines:
            return None
        today = klines[-1].split(",")
        yesterday = klines[-2].split(",") if len(klines) > 1 else today
        return {
            "today": {"date": today[0], "net": round(float(today[1]), 2)},
            "yesterday": {"date": yesterday[0], "net": round(float(yesterday[1]), 2)} if yesterday != today else None,
        }
    except:
        return None


# ═══════════════════════════════════════════
# 模块七: 新能源车板块数据
# ═══════════════════════════════════════════

def fetch_nev_sector():
    """新能源车板块行情"""
    try:
        d = get_json("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&fields=f2,f3,f12,f14&fid=f3&fs=b:BK0493")
        data = d.get("data", {})
        return {"total_stocks": data.get("total", 0)}
    except:
        return None


# ═══════════════════════════════════════════
# 主采集函数
# ═══════════════════════════════════════════

def collect_all(verbose=True):
    """采集所有数据"""
    if verbose:
        print("🔋 CATL 生态链数据采集")
        print("=" * 50)

    data = {
        "date": get_date_str(),
        "datetime": get_datetime_str(),
        "mode": get_mode(),
    }

    # 1. CATL核心
    if verbose: print("📡 CATL核心...")
    data["catl_a"] = fetch_catl_a()
    data["catl_h"] = fetch_catl_h()
    data["catl_pe"] = fetch_catl_pe()
    data["catl_fund"] = fetch_catl_fund_flow()
    if verbose:
        a = data["catl_a"]
        print(f"  A股: ¥{a['price']} ({a['change_pct']:+.1f}%)" if a else "  A股: ❌")
        h = data["catl_h"]
        print(f"  H股: HK${h['price']} ({h['change_pct']:+.1f}%)" if h else "  H股: ❌")

    # 2. 上游原材料
    if verbose: print("⛏️ 原材料...")
    data["materials"] = fetch_material_prices()
    data["lithium_futures"] = fetch_lithium_futures()
    if verbose:
        lf = data["lithium_futures"]
        print(f"  碳酸锂期货: ¥{lf['price']}" if lf else "  碳酸锂期货: ❌")

    # 3. 上游龙头
    if verbose: print("🏭 上游龙头...")
    data["upstream"] = fetch_stock_batch(UPSTREAM_STOCKS)
    if verbose: print(f"  获取: {len(data['upstream'])}/{len(UPSTREAM_STOCKS)}")

    # 4. 竞争格局
    if verbose: print("⚔️ 竞争对手...")
    data["competitors"] = fetch_stock_batch(COMPETITORS)
    if verbose: print(f"  获取: {len(data['competitors'])}/{len(COMPETITORS)}")

    # 5. 板块指数
    if verbose: print("📊 板块指数...")
    data["sectors"] = fetch_sector_indices()
    if verbose: print(f"  获取: {len(data['sectors'])}/{len(SECTOR_INDICES)}")

    # 6. 新闻
    if verbose: print("📰 新闻资讯...")
    data["news"] = fetch_all_news()
    total_news = sum(len(v) for v in data["news"].values())
    if verbose: print(f"  获取: {total_news} 条")

    # 7. 北向资金
    if verbose: print("💰 北向资金...")
    nf = fetch_north_flow()
    data["north_flow"] = nf
    if verbose: print(f"  今日: {nf['today']['net']:+.1f}亿" if nf else "  ❌")

    # 8. 新能源车板块
    if verbose: print("🚗 新能源车...")
    data["nev_sector"] = fetch_nev_sector()

    # 计算衍生指标
    compute_derived(data)

    if verbose: print("=" * 50)
    if verbose: print("✅ 采集完成")
    return data


def compute_derived(data):
    """计算衍生指标"""
    a = data["catl_a"]
    pe = data["catl_pe"]
    h = data["catl_h"]

    # AH溢价
    if a and h and h.get("price"):
        h_cny = h["price"] * 0.92  # 港币→人民币
        data["ah_premium"] = round((a["price"] - h_cny) / h_cny * 100, 2) if h_cny else None
    else:
        data["ah_premium"] = None

    # PEG
    pe_ttm = pe["pe_ttm"] if pe else None
    if pe_ttm and pe_ttm > 0:
        peg = round(pe_ttm / GROWTH_ASSUMPTION, 2)
        data["peg"] = peg
        if peg < PEG_UNDERVALUE:
            data["peg_signal"] = {"text": "低估区间 ✅", "color": "#3fb950", "level": "buy"}
        elif peg > PEG_OVERVALUE:
            data["peg_signal"] = {"text": "偏高区间 ⚠️", "color": "#f85149", "level": "sell"}
        else:
            data["peg_signal"] = {"text": "合理区间 📊", "color": "#d29922", "level": "hold"}
    else:
        data["peg"] = None
        data["peg_signal"] = {"text": "--", "color": "#8b949e", "level": "unknown"}

    # 上游平均涨跌
    if data["upstream"]:
        changes = [v["change_pct"] for v in data["upstream"].values()]
        data["upstream_avg_change"] = round(sum(changes) / len(changes), 2) if changes else 0
    else:
        data["upstream_avg_change"] = 0

    # 竞争平均涨跌
    if data["competitors"]:
        changes = [v["change_pct"] for v in data["competitors"].values()]
        data["competitor_avg_change"] = round(sum(changes) / len(changes), 2) if changes else 0
    else:
        data["competitor_avg_change"] = 0

    return data


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == "__main__":
    data = collect_all()
    out_path = os.path.join(REPO_DIR, "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 saved → {out_path}")
