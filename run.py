#!/usr/bin/env python3
"""CATL 生态链日监控 — 主入口

流程: 数据采集 → 报告生成 → Git推送 → 通知
用法: python3 run.py [--skip-push] [--mode auto|morning|evening]
"""

import subprocess, json, os, sys, time, base64, urllib.request, ssl
from datetime import datetime
from config import *

# 导入采集和生成
from datasync import collect_all
from gen_report import generate

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def github_push(file_path, content, commit_msg):
    """通过GitHub Contents API推送文件"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Hermes-CATL-Monitor",
    }
    req = urllib.request.Request(url, headers=headers)

    # 获取现有SHA
    sha = None
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        sha = json.loads(resp.read()).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"  ⚠️ GET SHA: {e.code}")
    except Exception as e:
        print(f"  ⚠️ GET SHA error: {e}")

    # PUT
    body = {
        "message": commit_msg,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main",
    }
    if sha:
        body["sha"] = sha

    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="PUT", headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=ssl_ctx)
        result = json.loads(resp.read())
        return result.get("content", {}).get("html_url", "ok")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ❌ Push failed: {e.code} - {body[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ Push error: {e}")
        return None


def push_via_api(data, html):
    """通过API推送data.json和index.html"""
    print("\n📤 推送 GitHub Pages...")

    # Push index.html
    commit_msg = f"[{data['mode']}] CATL生态监控 {data['date']} {data['datetime']}"
    result = github_push("index.html", html, commit_msg)
    if result:
        print(f"  ✅ index.html → {result}")
    else:
        print("  ❌ index.html push failed")
        return False

    # Push data.json
    data["pushed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result2 = github_push("data.json", json.dumps(data, ensure_ascii=False, indent=2, default=str),
                          f"data: {data['date']}")
    if result2:
        print(f"  ✅ data.json pushed")
    else:
        print("  ⚠️ data.json push failed (non-critical)")

    return True


def push_via_git():
    """通过Git命令推送（备用方案）"""
    print("\n📤 尝试 Git push...")
    os.chdir(REPO_DIR)
    cmds = [
        "git add index.html data.json",
        f'git commit -m "CATL生态监控 {get_date_str()}" --allow-empty',
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)

    # 带重试的push
    for attempt in range(3):
        r = subprocess.run("timeout 20 git push origin main 2>&1", shell=True,
                          capture_output=True, text=True, timeout=25)
        out = (r.stdout + r.stderr).strip()
        if "fatal" not in out and "error" not in out.lower():
            if out:
                print(f"  ✅ {out[:200]}")
            return True
        print(f"  🔄 重试 {attempt+1}/3...")
        time.sleep(2)
    print("  ❌ Git push 全部失败")
    return False


def send_notification(data, pages_url):
    """生成通知摘要（供 cron 发送）"""
    a = data.get("catl_a", {})
    sig = data.get("peg_signal", {})
    peg = data.get("peg")
    ah = data.get("ah_premium")
    upstream_avg = data.get("upstream_avg_change", 0)
    sector = data.get("sectors", {})

    price = a.get("price", "—") if a else "—"
    chg = a.get("change_pct") if a else None

    chg_str = f"{'+' if chg and chg>0 else ''}{chg:.1f}%" if chg is not None else "—"
    peg_str = f"PEG {peg:.2f}" if peg else "PEG —"
    ah_str = f"AH溢价 {ah:+.1f}%" if ah is not None else ""

    # 板块摘要
    sector_summary = ""
    if sector:
        parts = []
        for name, s in sector.items():
            parts.append(f"{name} {s['change_pct']:+.1f}%")
        sector_summary = " | ".join(parts)

    msg = f"""🔋 CATL生态链{data['mode']} · {data['date']}

⚡ CATL A股 ¥{price} {chg_str}
📊 {peg_str} | {sig.get('text','—')} | {ah_str}

⛏️ 上游: 平均 {upstream_avg:+.1f}%
📊 板块: {sector_summary if sector_summary else '—'}

📰 📊 完整报告: {pages_url}"""

    return msg


def main():
    skip_push = "--skip-push" in sys.argv

    print("╔══════════════════════════════╗")
    print("║  🔋 CATL 生态链日监控     ║")
    print("║  CATL Ecosystem Monitor    ║")
    print("╚══════════════════════════════╝")
    print(f"  {get_datetime_str()} · {get_mode()}")
    print()

    # Step 1: 采集
    data = collect_all(verbose=True)

    # Step 2: 生成
    print("\n🎨 生成HTML报告...")
    html = generate(data)
    print(f"  报告大小: {len(html)} bytes")

    # 保存本地
    out_path = os.path.join(REPO_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    data_path = os.path.join(REPO_DIR, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"  💾 已保存 → {out_path}")

    # Step 3: 推送
    if not skip_push:
        # 先用API推送
        api_ok = push_via_api(data, html)
        if not api_ok:
            # API失败，用Git备用
            push_via_git()
    else:
        print("\n⏭️ 跳过推送 (--skip-push)")

    # Step 4: 输出通知摘要
    print("\n" + "=" * 50)
    notification = send_notification(data, PAGES_URL)
    print(notification)
    print("=" * 50)
    print(f"\n📊 Pages: {PAGES_URL}")
    print("✅ 完成")

    # 输出通知文本供 cron 读取
    return notification


if __name__ == "__main__":
    msg = main()
    # 输出最后的 NOTIFICATION: 标记，方便cron截取
    print(f"\nNOTIFICATION:{msg}")
