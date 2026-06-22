import { Search, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { api, type ChartRecord } from "./api";
import { ChartDetail } from "./ChartDetail";

export function ChartWorkspace({ onChartsChange }: { onChartsChange: (items: ChartRecord[]) => void }) {
  const [items, setItems] = useState<ChartRecord[]>([]);
  const [selected, setSelected] = useState<ChartRecord>();
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async (search = "") => {
    try {
      const result = await api.listCharts(search);
      setItems(result.items);
      onChartsChange(result.items);
      setSelected((current) => current || result.items[0]);
    } catch {
      setItems([]);
    }
  };
  useEffect(() => { void load(); }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setBusy(true); setError("");
    const form = new FormData(formElement);
    try {
      const result = await api.calculateChart({
        name: form.get("name"), gender: form.get("gender"),
        birth_date: form.get("birth_date"), birth_time: form.get("birth_time"),
        province: form.get("province"), city: form.get("city"), persist: true,
      });
      setSelected(result.record);
      formElement.reset();
      await load(query);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "排盘失败");
    } finally { setBusy(false); }
  }

  async function remove(id: number) {
    await api.deleteChart(id);
    if (selected?.id === id) setSelected(undefined);
    await load(query);
  }

  return (
    <div className="charts-layout">
      <section className="panel chart-rail">
        <div className="section-heading"><div><h2>命盘记录</h2><p>{items.length} 条本地记录</p></div></div>
        <form className="chart-form" onSubmit={submit}>
          <div className="form-grid">
            <label>姓名<input name="name" required placeholder="命主姓名" /></label>
            <label>性别<select name="gender"><option value="male">男</option><option value="female">女</option></select></label>
            <label>出生日期<input name="birth_date" type="date" required /></label>
            <label>出生时间<input name="birth_time" type="time" required /></label>
            <label>省份<input name="province" placeholder="仅记录" /></label>
            <label>城市<input name="city" placeholder="不校正真太阳时" /></label>
          </div>
          <button className="primary" disabled={busy}>{busy ? "计算中…" : "计算并保存命盘"}</button>
          {error ? <p className="error">{error}</p> : null}
        </form>
        <div className="search"><Search size={15}/><input placeholder="搜索姓名" value={query} onChange={(e) => { setQuery(e.target.value); void load(e.target.value); }}/></div>
        <div className="record-list">
          {items.map((item) => (
            <button className={selected?.id === item.id ? "record active" : "record"} key={item.id} onClick={() => setSelected(item)}>
              <div><strong>{item.name}</strong><span>{item.gender === "male" ? "男" : "女"} · {item.birth_date}</span></div>
              <code>{item.bazi}</code>
              <span className="delete" role="button" aria-label={`删除 ${item.name}`} onClick={(event) => { event.stopPropagation(); void remove(item.id); }}><Trash2 size={14}/></span>
            </button>
          ))}
        </div>
      </section>
      <section className="panel chart-canvas">
        <div className="section-heading"><div><h2>{selected?.name || "命盘详情"}</h2><p>{selected ? `${selected.birth_place || "出生地未记录"} · 创建于 ${selected.created_at.slice(0, 10)}` : "结构化排盘事实"}</p></div></div>
        <ChartDetail chart={selected?.chart}/>
      </section>
    </div>
  );
}
