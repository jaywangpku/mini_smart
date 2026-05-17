# mini_smart

一个用于研究的 Longbridge 分钟级 K 线同步工具：后端通过 Longbridge OpenAPI 下载数据并写入 SQLite，前端用 Vue 展示同步任务和 K 线图。

## 功能

- 同步 `1min` K 线，兼容日/周/月等周期参数
- SQLite 幂等写入，按 `symbol + period + adjust_type + timestamp` 去重
- Vue 页面下发同步任务、查看状态、展示 K 线
- CLI 初始化数据库和启动 API

## 后端启动

```bash
cp .env.example .env
# 填入 LONGBRIDGE_APP_KEY / LONGBRIDGE_APP_SECRET / LONGBRIDGE_ACCESS_TOKEN
python -m venv .venv
source .venv/bin/activate
pip install -e .
mini-smart init-db
mini-smart api
```

API 默认运行在 `http://127.0.0.1:8000`。

## 前端启动

```bash
cd web
npm install
npm run dev
```

页面默认代理到后端 `/api`。

## 一键重启开发服务

```bash
./scripts/restart-dev.sh
```

脚本会重启后端 `http://127.0.0.1:8000` 和前端 `http://127.0.0.1:5173`，日志写入 `.run/backend.log` 和 `.run/frontend.log`。

## 常用 CLI

```bash
mini-smart init-db
mini-smart add-symbol AAPL.US
mini-smart sync AAPL.US --period 1min --start 2024-01-01 --end 2024-01-31
```

## 注意

Longbridge 行情权限会影响可下载的市场、周期和历史范围。同步失败时可以在页面任务状态或 `sync_tasks.error` 中查看原始错误。
