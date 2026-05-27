#!/bin/bash
# 300750 监控 — 启动脚本 (供cron使用)
# Token 由环境变量 CATL_GITHUB_TOKEN 提供

cd /home/ubuntu/300750
exec python3 run.py
