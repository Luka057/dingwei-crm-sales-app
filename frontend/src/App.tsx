import { CalendarDays, FileText, Github, Server, Smartphone } from "lucide-react";
import "./styles.css";

const prototypeUrl = "/prototype/crm-sales-timepage-prototype.html";

export default function App() {
  return (
    <main className="home">
      <section className="hero">
        <div>
          <p className="eyebrow">Dingwei CRM Sales App</p>
          <h1>鼎伟 CRM 业务人员端</h1>
          <p className="lead">
            当前仓库已整理为前端工程、后端 mock API、Docker 部署草案、产品与交接文档。高保真交互原型是下一阶段开发的 UI 与交互基准。
          </p>
          <div className="actions">
            <a className="primary" href={prototypeUrl}>
              <Smartphone size={18} />
              打开手机原型
            </a>
            <a href="/api/v1/health">
              <Server size={18} />
              后端健康检查
            </a>
          </div>
        </div>
        <iframe title="鼎伟 CRM 业务人员端原型" src={prototypeUrl} />
      </section>

      <section className="grid">
        <article>
          <CalendarDays />
          <h2>日历驱动</h2>
          <p>支持日程优先、月历优先、无限日程流、月历浮窗、拜访与自定义事项。</p>
        </article>
        <article>
          <FileText />
          <h2>业务沉淀</h2>
          <p>客户 360、拜访时间线、周报结构化录入、AI 摘要和 AI 周报草稿。</p>
        </article>
        <article>
          <Github />
          <h2>Agent 交接</h2>
          <p>关键决策、文件路径、localStorage key、接口草案、数据字典都已沉淀在 docs。</p>
        </article>
      </section>
    </main>
  );
}
