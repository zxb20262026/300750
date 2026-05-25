#!/usr/bin/env python3
"""CATL 生态链日监控 — 全局配置 v1.2"""

import os, re
from datetime import datetime

# ── GitHub ──
GITHUB_TOKEN = os.environ.get("CATL_GITHUB_TOKEN", "")
REPO_OWNER = "zxb20262026"
REPO_NAME = "catl-ecosystem-monitor"
PAGES_URL = f"https://{REPO_OWNER}.github.io/{REPO_NAME}/"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

if not GITHUB_TOKEN and os.path.exists(os.path.expanduser("~/catl-hermes-auto/catl_auto.py")):
    with open(os.path.expanduser("~/catl-hermes-auto/catl_auto.py")) as f:
        m = re.search(r'GITHUB_TOKEN\s*=\s*"([^"]+)"', f.read())
        if m: GITHUB_TOKEN = m.group(1)

# ── 持仓 ──
HOLDING_SHARES = 200
GROWTH_ASSUMPTION = 40
COST_PRICE = 350  # 用户持仓成本（需手动更新）

# ── PEG ──
PEG_UNDERVALUE = 1.0
PEG_OVERVALUE = 1.5

# ── 均线窗口 ──
MA_WINDOWS = [5, 20, 60]

# ── 大盘指数 ──
MARKET_INDICES = {
    "上证指数": "sh000001",
    "沪深300": "sh000300",
}

# ── 上游股票 ──
UPSTREAM_STOCKS = {
    "赣锋锂业": "sz002460", "天齐锂业": "sz002466",
    "华友钴业": "sh603799", "恩捷股份": "sz002812",
    "天赐材料": "sz002709", "当升科技": "sz300073",
}

# ── 竞争对手 ──
COMPETITORS = {
    "比亚迪": "sz002594", "亿纬锂能": "sz300014", "国轩高科": "sz002074",
}

# ── 板块指数 ──
SECTOR_INDICES = {
    "新能源车": "sz399417", "储能": "sh000688",
    "光伏产业": "sh000941", "锂电池": "sh000861",
}

# CATL归属行业（KPI卡片显示）
# 数据源: 新能源车指数(sz399417) — 与电池板块相关性>0.95
# 东财电池概念(BK0573)不可用时自动降级
CATL_INDUSTRY = "电池"         # 显示名称
CATL_INDUSTRY_SOURCE = "新能源车"  # 实际数据源 (SECTOR_INDICES的key)

# ── 新闻关键词 ──
NEWS_KEYWORDS = ["宁德时代", "固态电池", "储能", "钠离子电池", "换电"]

# ── 上游原材料参考价格 ──
MATERIAL_REFERENCE = {
    "碳酸锂(电池级)": {"price": 75000, "unit": "元/吨", "trend": "低位震荡"},
    "氢氧化锂": {"price": 78000, "unit": "元/吨", "trend": "跟随碳酸锂"},
    "电解钴": {"price": 195000, "unit": "元/吨", "trend": "偏弱"},
    "硫酸镍": {"price": 28500, "unit": "元/吨", "trend": "稳定"},
    "磷酸铁锂": {"price": 38000, "unit": "元/吨", "trend": "低位"},
    "六氟磷酸锂": {"price": 62000, "unit": "元/吨", "trend": "低位"},
}

# ── 操作建议参数 ──
TRADING = {
    "target_pe_range": (25, 27),      # 目标PE区间
    "stop_loss_price": 375,            # 止损位
    "ma60_tolerance": 2,               # MA60附近容差(元)
    "volume_threshold": 100,           # 放量阈值(亿)
}

# ── 时间 ──
def get_mode():
    return "早报 ☀️" if datetime.now().hour < 14 else "晚报 🌙"

def get_date_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_datetime_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
