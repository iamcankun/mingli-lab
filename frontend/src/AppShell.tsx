import { BrainCircuit, Database, Settings2, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

export type Page = "charts" | "inference" | "settings";

const items = [
  { id: "charts" as const, label: "命盘记录", icon: Database },
  { id: "inference" as const, label: "推理分析", icon: BrainCircuit },
  { id: "settings" as const, label: "模型设置", icon: Settings2 },
];

export function AppShell({
  page,
  onPage,
  children,
}: {
  page: Page;
  onPage: (page: Page) => void;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><Sparkles size={18} />命理 LAB</div>
        <nav>
          {items.map(({ id, label, icon: Icon }) => (
            <button className={page === id ? "nav-item active" : "nav-item"} key={id} onClick={() => onPage(id)}>
              <Icon size={17} />{label}
            </button>
          ))}
        </nav>
        <div className="local-note"><span />本地数据模式</div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div>
            <h1>{items.find((item) => item.id === page)?.label}</h1>
            <p>方法论调试与命盘验证工作台</p>
          </div>
          <div className="status"><span />本地服务</div>
        </header>
        {children}
      </main>
    </div>
  );
}

