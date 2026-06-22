import type { ChartData } from "./api";

export function ChartDetail({ chart }: { chart?: ChartData }) {
  if (!chart) return <div className="empty-state">选择一条命盘，或在左侧创建新命盘。</div>;
  return (
    <div className="chart-detail">
      <div className="chart-summary">
        <div><span>八字</span><strong className="bazi-text">{chart.bazi}</strong></div>
        <div><span>日主</span><strong>{chart.day_master || "—"}</strong></div>
        <div><span>生肖</span><strong>{chart.zodiac || "—"}</strong></div>
        <div><span>农历</span><strong>{chart.lunar || "—"}</strong></div>
      </div>
      <div className="pillars">
        {(chart.pillars || []).map((pillar) => (
          <article className="pillar" key={pillar.label}>
            <small>{pillar.label}</small>
            <div className="pillar-glyphs"><b>{pillar.stem.char}</b><b>{pillar.branch.char}</b></div>
            <dl>
              <div><dt>十神</dt><dd>{pillar.stem.ten_god || "日主"}</dd></div>
              <div><dt>纳音</dt><dd>{pillar.nayin || "—"}</dd></div>
              <div><dt>星运</dt><dd>{pillar.xingyun || "—"}</dd></div>
            </dl>
            {(pillar.branch.hidden_stems || []).map((hidden) => (
              <p className="hidden-stem" key={`${hidden.role}-${hidden.char}`}>{hidden.role} · {hidden.char} · {hidden.ten_god}</p>
            ))}
          </article>
        ))}
      </div>
      <section className="future-module">
        <div><span>大运</span><b>排盘引擎数据已保留</b></div>
        <p>流年、流月及旺衰强弱将在后续独立算法模块中接入，当前不生成推测性结果。</p>
      </section>
    </div>
  );
}

