# Agent 交接文档：鼎伟 CRM 业务人员端

最后更新：2026-05-15

## 1. 当前工作目标

用户正在设计「鼎伟 CRM 业务人员端」，不是老板端。老板端已有，业务人员端要和老板端数据打通，但交互、视角、首页重点完全不同。

业务人员端的核心是：让销售每天基于日历安排拜访、记录拜访、沉淀客户信息、写周报，并用 AI 查询客户/订单/样板/拜访记录。

## 2. 用户明确偏好

- 不要做老板端视角。
- 底部导航只保留：日历、客户、周报、AI。
- 用户很在意「没让你动的不要乱动」。
- 改视觉时必须保留已有配色体系，除非明确要求调整。
- 新交互必须真的能点，不能只是静态样子。
- 原型先在 `frontend/prototype/crm-sales-timepage-prototype.html` 里试，效果好再工程化。
- 用户喜欢 Timepage / Apple Calendar 的日历气质，但不能直接照抄配色。
- 选择项不要有说明小作文，显得廉价。
- 深色模式要像苹果深色模式：整体深色，但不同色调仍有各自的深色版本。
- 选中的小模块不能纯白块盖住文字，要半透明毛玻璃。

## 3. 当前原型入口

最新原型有两份相同文件：

- `frontend/prototype/crm-sales-timepage-prototype.html`
- `frontend/public/prototype/crm-sales-timepage-prototype.html`

第一份便于直接打开，第二份用于 Vite 构建后访问。

## 4. 当前原型关键能力

### 日历页

- 日程优先主题：默认全屏日期时间线，左上角按钮打开完整月历浮窗。
- 月历优先主题：完整月历直接显示在日程页上方。
- 日程优先支持上下连续滚动日期，可滚到昨天、前天、明天、后天以及更远日期。
- 左上角完整月历入口必须保留。
- 右上角主题/配色按钮必须保留。
- 右下角 `+` 必须保留。
- 每一天模块内也有 `+ 拜访` 和 `+ 计划`，用于按日期直接新增。
- 新增只保留两类：拜访、自定义内容。
- 添加后的任务可编辑、完成、删除。
- 拜访计划点进去后填写拜访内容和 AI 摘要。

### 客户页

- 展示自己的客户。
- 筛选：全部、超期、A 类、样板中、本周拜访。
- 客户卡片可点击进入客户 360。
- 客户详情包含基本信息、KPI、拜访时间线。
- 拜访时间线支持「点击查看详情」就地展开。

### 周报页

- 有历史周报。
- 有录入入口。
- 格式固定为：本周工作总结、下周工作计划、备注事项、附件。
- AI 可根据一周拜访记录摘要一键生成周报草稿。

### AI 页

- 聊天界面参考现代 AI 聊天软件。
- 中间 logo 和土味欢迎语已经删除。
- AI 找板入口放在右上角 `+`。
- AI 找板支持输入图片、客户场景、宽度、开力度、织带类型、要求。

## 5. 主题和本地状态

localStorage key：

- `dingwei-sales-tone`：`warm` / `ocean` / `forest` / `grape` / `graphite`
- `dingwei-sales-view-theme`：`agenda` / `calendar`
- `dingwei-sales-appearance`：`light` / `dark`

CSS 变量：

- 基础色调在 `:root` 和 `html[data-tone=...]`。
- 深色模式在 `html[data-appearance="dark"]`。
- 深色 + 色调组合在 `html[data-appearance="dark"][data-tone="..."]`。
- 选中毛玻璃态变量：`--glass-active`、`--glass-active-border`、`--glass-active-shadow`。

## 6. 工程状态

### 前端

- 技术栈：React + Vite + TypeScript。
- 当前 `frontend/src/App.tsx` 是工程入口页，主要承载原型 iframe 和项目说明。
- 真正高保真交互仍在单 HTML 原型中。
- 下一步应把单 HTML 中的状态、数据、页面拆成 React 组件。

### 后端

- 技术栈暂定：Node.js + Express mock，后续可升级 NestJS 或继续 Express。
- 当前 `backend/src/main.ts` 提供 mock API：
  - `/api/v1/health`
  - `/api/v1/auth/login`
  - `/api/v1/plans/calendar`
  - `/api/v1/plans`
  - `/api/v1/customers`
  - `/api/v1/customers/:id`
  - `/api/v1/visit-records`
  - `/api/v1/weekly-reports`
  - `/api/v1/weekly-reports/generate-ai-draft`
  - `/api/v1/ai/chat`
  - `/api/v1/ai/board-search`

### 文档

重要文档：

- `docs/PRD.md`
- `docs/需求文档.md`
- `docs/技术栈选型.md`
- `docs/接口文档.md`
- `docs/数据字典.md`
- `docs/AI功能设计.md`
- `docs/原型交互说明.md`
- `docs/开发计划.md`
- `docs/部署说明.md`

## 7. 不要轻易改的东西

- 不要恢复底部多余菜单，底部只要四项。
- 不要把 AI 找板放回聊天框中间。
- 不要删除左上大月历入口。
- 不要删除右下角 `+`。
- 不要把日历优先/月历优先合并。
- 不要用大段说明文字解释主题/配色选项。
- 不要把选中态改回纯白或纯黑实心块。

## 8. 建议下一位 agent 的工作方式

1. 先打开 `frontend/prototype/crm-sales-timepage-prototype.html` 看当前状态。
2. 若用户继续调视觉，直接改这个原型文件。
3. 若用户说“可以更新代码文件夹/工程化”，再同步到 React 组件。
4. 每次修改交互后，用 Playwright 检查：
   - 日历按钮还在。
   - 主题按钮还在。
   - 右下角加号还在。
   - 客户/周报/AI 的既有按钮还能点击。
   - 深色和各色调组合不出现白字白底。
