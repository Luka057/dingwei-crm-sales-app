# 鼎伟 CRM 业务人员端

面向鼎伟织带工厂业务人员的移动端 CRM。它不是老板端，而是业务员每天打开用来安排拜访、沉淀客户、写周报、问 AI、找板样的工作应用。

当前仓库已经整理为：高保真原型 + 前端工程骨架 + 后端 mock API + 产品/技术/接口/数据文档 + agent 交接文档。

## 当前最重要的文件

- `frontend/prototype/crm-sales-timepage-prototype.html`：当前最新高保真交互原型，可直接双击打开。
- `frontend/public/prototype/crm-sales-timepage-prototype.html`：同一份原型，供 Vite / Docker 前端访问。
- `frontend/src/`：React + Vite 工程入口，当前用于承载原型和后续工程化开发。
- `backend/src/main.ts`：Express mock API，覆盖核心接口草案。
- `docs/agent/AGENT_HANDOFF.md`：下一位 agent 必读交接文档。
- `docs/原型交互说明.md`：当前原型已有交互与视觉决策。
- `docs/接口文档.md`、`docs/数据字典.md`：后端对接依据。

## 快速运行

### 直接看原型

打开：

```text
frontend/prototype/crm-sales-timepage-prototype.html
```

### 前端工程

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:5173
```

### 后端 mock API

```bash
cd backend
npm install
npm run dev
```

健康检查：

```text
http://localhost:3000/api/v1/health
```

### Docker Compose 草案

```bash
docker compose up -d
```

前端：`http://localhost:8080`

后端：`http://localhost:3000/api/v1`

## 产品现状

底部导航固定为四个入口：

- 日历
- 客户
- 周报
- AI

已经在原型中落地：

- 日程优先 / 月历优先双主题。
- 浅色 / 深色双显示模式。
- 暖纸、蓝调、绿调、紫调、石墨多配色，深色模式下各自有对应深色版本。
- 日程优先主题支持上下连续滚动日期。
- 左上角打开完整月历浮窗。
- 每一天模块内可直接新增拜访 / 计划，右下角加号也保留。
- 客户页筛选、客户详情、拜访时间线展开。
- 周报历史、录入、AI 草稿。
- AI 聊天、AI 找板入口和参数表单。
- 小模块选中态改为半透明毛玻璃，不再用纯白块盖住文字。

## 推荐下一步

1. 以 `frontend/prototype` 为 UI/交互基准拆 React 组件。
2. 以 `backend/src/main.ts` 和 `docs/接口文档.md` 为接口基准改成真实数据库。
3. 用 `docs/数据字典.md` 建 Prisma schema 或 SQL migration。
4. 接入登录与权限过滤，确保销售只能看自己的客户、计划、拜访、周报。
5. 接入 DeepSeek Function Calling，先实现 AI 摘要、AI 周报、客户问答，再做 AI 找板。

## Git 说明

本目录可以直接作为独立 Git 仓库。若还没有远程仓库，先在 Git 平台创建空仓库，再执行：

```bash
git remote add origin <你的仓库地址>
git push -u origin main
```
