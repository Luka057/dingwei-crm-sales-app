# 上下文切换交接文件

最后更新：2026-05-15

## 1. 目标

继续开发「鼎伟 CRM 业务人员端」。

这是销售/业务人员每天使用的手机端 CRM，不是老板端。核心目标是让业务员围绕日历完成客户拜访计划、拜访记录、客户沉淀、周报录入、AI 查询和 AI 找板，并把数据打通给老板端。

用户当前非常重视：

- 原型交互真实可点。
- 不要乱动没有要求改的交互。
- 底部导航只保留：日历、客户、周报、AI。
- 视觉风格要保留当前方向。
- 深浅模式、多色调、毛玻璃选中态要保留。
- 任何下一步 agent 都应能从本仓库文档继续接手。

## 2. 当前正在处理的状态文件

项目根目录：

```text
/Users/ywj/Desktop/鼎伟crm业务人员端
```

GitHub 仓库：

```text
https://github.com/Luka057/dingwei-crm-sales-app
```

当前本地分支：

```text
main
```

当前远程状态：

```text
main 已跟踪 origin/main
本地和远程当前对齐
远程最新提交：92a7839 chore: upload sales CRM project package
```

最重要的状态文件：

```text
frontend/prototype/crm-sales-timepage-prototype.html
frontend/public/prototype/crm-sales-timepage-prototype.html
docs/agent/AGENT_HANDOFF.md
docs/原型交互说明.md
docs/PRD.md
docs/需求文档.md
docs/接口文档.md
docs/数据字典.md
docs/GitHub上传说明.md
README.md
```

当前原型仍在用户浏览器中打开的文件：

```text
/Users/ywj/Desktop/数据采集介绍ppt/crm-sales-timepage-prototype.html
```

注意：项目包里的原型已经同步过上述文件。后续如果继续改桌面原型，记得同步回：

```text
/Users/ywj/Desktop/鼎伟crm业务人员端/frontend/prototype/crm-sales-timepage-prototype.html
/Users/ywj/Desktop/鼎伟crm业务人员端/frontend/public/prototype/crm-sales-timepage-prototype.html
```

## 3. 已经改变的事情

### 3.1 原型能力

已经完成的高保真原型能力：

- 底部导航固定为日历、客户、周报、AI。
- 日历页支持「日程优先 / 月历优先」双主题。
- 日程优先：默认显示日期时间线，左上角菜单打开完整月历浮窗。
- 月历优先：完整月历直接显示在日程上方。
- 日程优先支持上下连续滚动日期，能看昨天、前天、明天、后天以及更远日期。
- 每一天模块内有 `+ 拜访`、`+ 计划`。
- 原右下角全局 `+` 保留。
- 新增事项只保留拜访和自定义内容。
- 添加后的任务可查看、编辑、完成、删除。
- 拜访计划点进去后可以填写拜访内容，支持 AI 摘要。
- 客户页有筛选、客户卡片、客户详情、拜访时间线展开。
- 周报页有历史周报、录入入口、AI 草稿。
- AI 页有聊天、历史抽屉、AI 找板入口。
- AI 找板放在 AI 页右上角 `+`，支持图片、宽度、开力度、织带类型等参数。

### 3.2 视觉和主题

已经完成的主题能力：

- 浅色模式 / 深色模式。
- 暖纸原色、清爽蓝调、松绿色调、淡紫色调、石墨灰调。
- 深色模式下各色调都有各自深色版本，不是单一黑色。
- 配色切换、深浅模式、日程主题使用 localStorage 保存。
- 主题弹窗去掉了多余说明文字，只保留选择项。
- 小模块选中态改成半透明毛玻璃，避免深色模式下白色块盖住文字。
- 主操作按钮仍保持明确实底，例如搜索、保存、提交、查询。

localStorage key：

```text
dingwei-sales-tone
dingwei-sales-view-theme
dingwei-sales-appearance
```

### 3.3 工程和文档

已经整理为项目包：

- `frontend/`：React + Vite + TypeScript 工程入口。
- `frontend/prototype/`：当前最新 HTML 高保真原型。
- `frontend/public/prototype/`：同一份原型，用于 Vite/Nginx 部署访问。
- `backend/`：Express mock API。
- `docs/`：PRD、需求、技术栈、接口、数据字典、AI 功能、部署、开发计划、交接说明。
- `docker-compose.yml`：内网部署草案。
- `.env.example`：环境变量样例。

已验证：

```bash
cd /Users/ywj/Desktop/鼎伟crm业务人员端/frontend
npm run build

cd /Users/ywj/Desktop/鼎伟crm业务人员端/backend
npm run build
```

这两个 build 都成功过。

### 3.4 GitHub

已经完成：

- 本地 Git 初始化。
- GitHub CLI 登录账号：`Luka057`。
- 创建/关联远程仓库：`https://github.com/Luka057/dingwei-crm-sales-app`。
- 通过 GitHub API 上传完整项目和文档。
- 本地 `main` 已对齐 `origin/main`。

## 4. 尝试过但失败的事情

### 4.1 `gh auth login` 初次交互卡住

一开始 `gh auth login --web` 在 PTY 中卡住，没有显示完整设备码/浏览器提示。后来用户完成了 GitHub CLI 登录，`gh auth status` 显示成功。

### 4.2 普通 `git push` 失败

尝试：

```bash
git push -u origin main
```

失败原因：

```text
Failed to connect to github.com port 443
```

说明当时本机到 GitHub 的 Git HTTPS 通道不稳定。

### 4.3 远程仓库不是完全空仓库

用户要求建空仓库，但实际 GitHub 上的仓库 `dingwei-crm-sales-app` 已经有一个 GitHub 初始化的 `README.md` 提交：

```text
f1eb0bf Initial commit
```

处理方式：

- 没有强制覆盖远程历史。
- 使用 GitHub API 创建新提交，将完整项目树提交到远程 `main`。
- 远程现在包含初始 README 提交和项目包提交。

### 4.4 本地 commit 和远程 API commit 曾经不同步

本地原有提交：

```text
3387cc0 docs: add github upload guide
8278888 chore: package sales CRM prototype handoff
```

远程 API 上传后产生新提交：

```text
92a7839 chore: upload sales CRM project package
```

已用：

```bash
git reset --soft origin/main
git branch --set-upstream-to=origin/main main
```

让本地 `main` 对齐远程 `origin/main`。

## 5. 下一步建议

如果继续产品原型：

1. 优先改 `frontend/prototype/crm-sales-timepage-prototype.html`。
2. 改完同步到 `frontend/public/prototype/crm-sales-timepage-prototype.html`。
3. 用浏览器验证日历、客户、周报、AI 既有交互没坏。
4. 提交并推送。

如果开始工程化：

1. 按 `docs/原型交互说明.md` 拆 React 组件。
2. 用 `backend/src/main.ts` 的 mock API 做接口契约。
3. 根据 `docs/数据字典.md` 建真实数据库 schema。
4. 加登录和权限隔离，保证销售只能看自己的数据。
5. 再接 DeepSeek Function Calling。

## 6. 常用命令

```bash
cd /Users/ywj/Desktop/鼎伟crm业务人员端

git status --short --branch
git log --oneline --decorate -3
git push

cd frontend
npm install
npm run dev
npm run build

cd ../backend
npm install
npm run dev
npm run build
```

## 7. 接手时先读

下一位 agent 接手时建议按顺序读：

1. `CONTEXT_HANDOFF.md`
2. `docs/agent/AGENT_HANDOFF.md`
3. `docs/原型交互说明.md`
4. `README.md`
5. `frontend/prototype/crm-sales-timepage-prototype.html`
