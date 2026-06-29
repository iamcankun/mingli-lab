import { FormEvent, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ChartRecord, InferenceResult } from "./api";
import { api } from "./api";
import { ChartDetail } from "./ChartDetail";

const types = ["全局分析", "背景分析", "性格分析", "事业分析", "财运分析", "自定义"];

export function InferenceWorkspace({ charts }: { charts: ChartRecord[] }) {
  const [chartId, setChartId] = useState(charts[0]?.id || 0);
  const [temporaryBazi, setTemporaryBazi] = useState("");
  const [analysisType, setAnalysisType] = useState("事业分析");
  const [customRequest, setCustomRequest] = useState("");
  const [result, setResult] = useState<InferenceResult>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const selected = charts.find((chart) => chart.id === chartId);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      setResult(await api.infer(selected ? { chart_id: selected.id, analysis_type: analysisType, custom_request: customRequest } : {
        temporary_chart: { bazi: temporaryBazi, day_master: "", chart: {} }, analysis_type: analysisType, custom_request: customRequest,
      }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "推理失败"); }
    finally { setBusy(false); }
  }
  return (
    <form className="inference-layout" onSubmit={submit}>
      <section className="panel inference-chart">
        <div className="section-heading"><div><h2>命盘</h2><p>本次推理固定对象</p></div></div>
        <label>选择记录<select value={chartId} onChange={(e)=>setChartId(Number(e.target.value))}><option value={0}>临时八字</option>{charts.map((chart)=><option value={chart.id} key={chart.id}>{chart.name} · {chart.bazi}</option>)}</select></label>
        {!selected ? <label>临时八字<textarea value={temporaryBazi} onChange={(e)=>setTemporaryBazi(e.target.value)} placeholder="甲戌 丁丑 乙卯 甲申" required/></label> : <ChartDetail chart={selected.chart} chartId={selected.id}/>}
      </section>
      <section className="panel inference-config">
        <div className="section-heading"><div><h2>推理配置</h2><p>自由组合分析任务</p></div></div>
        <label>分析类型<select value={analysisType} onChange={(e)=>setAnalysisType(e.target.value)}>{types.map((type)=><option key={type}>{type}</option>)}</select></label>
        <label>补充要求<textarea value={customRequest} onChange={(e)=>setCustomRequest(e.target.value)} placeholder="例如：关注未来三年的职业转型验证点"/></label>
        <div className="method-note"><b>默认方法</b><p>按“事实 → 推导 → 风险 → 验证点”组织结果。提示词和模型参数可在调试信息中复核。</p></div>
        <button className="primary" disabled={busy}>{busy ? "推理中…" : "开始推理"}</button>
        {error ? <p className="error">{error}</p> : null}
      </section>
      <section className="panel inference-result">
        <div className="section-heading"><div><h2>推理结果</h2><p>{result ? `${result.token_usage.total_tokens || 0} tokens` : "等待执行"}</p></div></div>
        {result ? <>
          <div className="markdown"><ReactMarkdown>{result.response}</ReactMarkdown></div>
          <details><summary>调试信息</summary><div className="debug"><b>System Prompt</b><pre>{result.system_prompt}</pre><b>User Prompt</b><pre>{result.user_prompt}</pre><b>Token 用量</b><pre>{JSON.stringify(result.token_usage, null, 2)}</pre></div></details>
        </> : <div className="empty-state">选择命盘并执行推理后，结果与完整诊断信息将在这里显示。</div>}
      </section>
    </form>
  );
}
