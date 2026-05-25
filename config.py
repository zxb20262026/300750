#!/usr/bin/env python3
"""CATL 生态链日监控 — 全局配置"""

import os
from datetime import datetime

# ── GitHub ──
GITHUB_TOKEN = os.environ.get("CATL_GITHUB_TOKEN", "")
REPO_OWNER = "zxb20262026"
REPO_NAME = "catl-ecosystem-monitor"
PAGES_URL = f"https://{REPO_OWNER}.github.io/{REPO_NAME}/"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

# 如果环境变量未设置，尝试从旧repo的脚本读取（开发环境）
if not GITHUB_TOKEN and os.path.exists(os.path.expanduser("~/catl-hermes-auto/catl_auto.py")):
    import re
    with open(os.path.expanduser("~/catl-hermes-auto/catl_auto.py")) as f:
        m = re.search(r'GITHUB_TOKEN\s*=\s*"([^"]+)"', f.read())
        if m:
            GITHUB_TOKEN = m.group(1)

# ── 持仓 ──
HOLDING_SHARES = 200  # CATL持股
GROWTH_ASSUMPTION = 40  # PEG计算默认增速%

# ── PEG 信号 ──
PEG_UNDERVALUE = 1.0
PEG_OVERVALUE = 1.5

# ── 上游股票代码 ──
UPSTREAM_STOCKS = {
    "赣锋锂业": "sz002460",
    "天齐锂业": "sz002466",
    "华友钴业": "sh603799",
    "恩捷股份": "sz002812",
    "天赐材料": "sz002709",
    "当升科技": "sz300073",
}

# ── 竞争对手 ──
COMPETITORS = {
    "比亚迪": "sz002594",
    "亿纬锂能": "sz300014",
    "国轩高科": "sz002074",
}

# ── 板块指数 ──
SECTOR_INDICES = {
    "新能源车": "sz399417",
    "储能": "sh000688",
    "光伏产业": "sh000941",
    "锂电池": "sh000861",
}

# ── 新闻关键词 ──
NEWS_KEYWORDS = ["宁德时代", "固态电池", "储能", "钠离子电池", "换电"]

# ── 上游原材料参考价格（元/吨，定期手动更新） ──
MATERIAL_REFERENCE = {
    "碳酸锂(电池级)": {"price": 75000, "unit": "元/吨", "trend": "低位震荡"},
    "氢氧化锂": {"price": 78000, "unit": "元/吨", "trend": "跟随碳酸锂"},
    "电解钴": {"price": 195000, "unit": "元/吨", "trend": "偏弱"},
    "硫酸镍": {"price": 28500, "unit": "元/吨", "trend": "稳定"},
    "磷酸铁锂": {"price": 38000, "unit": "元/吨", "trend": "低位"},
    "六氟磷酸锂": {"price": 62000, "unit": "元/吨", "trend": "低位"},
}

# ── 时间模式 ──
def get_mode():
    """早报/晚报判断"""
    h = datetime.now().hour
    return "早报 ☀️" if h < 14 else "晚报 🌙"

def get_date_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_datetime_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
