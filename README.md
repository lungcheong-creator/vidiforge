# VidiForge · 智選銀河

> AI 短視頻生成工作室。從主題到成片，一鍵完成。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

---

## 簡介

VidiForge 是 [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) 的現代化重構版：
- **前端**：Next.js 14 + Tailwind + shadcn/ui，煉瓦色 + 米白編輯式風格（Fraunces + Inter）
- **後端**：Python 3.11 + FastAPI + SQLModel + FFmpeg subprocess
- **部署**：Vercel（前端）+ Railway（後端）

支援中英雙語、暗色模式、BYOK（自備 API Key）、純 CPU FFmpeg 渲染。

---

## 工作流

```
輸入主題 → AI 生成腳本 → TTS 配音 → 素材匹配 → 字幕 → BGM → 1080p MP4
```

---

## 快速開始（本地）

```bash
# 1. 啟動後端（端口 8080）
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# 2. 啟動前端（端口 3000）
cd web
npm install
npm run dev

# 或一鍵啟動
docker compose up
```

訪問 [http://localhost:3000](http://localhost:3000)

---

## 文檔

- [部署到 Vercel + Railway](docs/DEPLOYMENT.md)
- [API 文檔](docs/API.md)（運行後端後訪問 `/docs`）
- [BYOK 配置說明](docs/BYOK.md)

---

## 授權

MIT © 2026