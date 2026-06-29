import { type CSSProperties, useEffect, useState } from "react";

import { api, type LifeKlineDay, type LifeKlineResponse } from "./api";
import "./life-kline.css";

function groupByMonth(series: LifeKlineDay[]) {
  return series.reduce<Record<string, LifeKlineDay[]>>((groups, day) => {
    const month = day.date.slice(0, 7);
    groups[month] = [...(groups[month] || []), day];
    return groups;
  }, {});
}

function averageClose(series: LifeKlineDay[]) {
  if (!series.length) return 0;
  return Math.round(series.reduce((sum, day) => sum + day.kline.close, 0) / series.length);
}

function candleStyle(day: LifeKlineDay) {
  const range = Math.max(1, day.kline.high - day.kline.low);
  const body = Math.max(18, Math.abs(day.kline.close - day.kline.open) * 3);
  return {
    "--candle-body": `${Math.min(46, body)}px`,
    "--candle-range": `${Math.min(56, Math.max(24, range * 2))}px`,
  } as CSSProperties;
}

export function LifeKlinePanel({ chartId }: { chartId?: number }) {
  const [data, setData] = useState<LifeKlineResponse>();
  const [selected, setSelected] = useState<LifeKlineDay>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!chartId) return;
    let active = true;
    setBusy(true); setError("");
    api.getLifeKline(chartId)
      .then((result) => {
        if (!active) return;
        if (Array.isArray(result.series)) {
          setData(result);
          setSelected(result.series[0]);
        }
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "人生K线图加载失败");
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => { active = false; };
  }, [chartId]);

  if (!chartId) return null;

  const series = data?.series || [];
  const groups = groupByMonth(series);
  const strongest = series.reduce<LifeKlineDay | undefined>((best, day) => !best || day.kline.close > best.kline.close ? day : best, undefined);
  const weakest = series.reduce<LifeKlineDay | undefined>((best, day) => !best || day.kline.close < best.kline.close ? day : best, undefined);

  return (
    <section className="life-kline">
      <div className="section-heading">
        <div><h2>人生K线图</h2><p>{data?.range ? `${data.range.start} 至 ${data.range.end} · ${data.range.days} 天` : "近三年日级趋势"}</p></div>
        <span className="kline-version">{data?.method?.version || "life-kline-v1"}</span>
      </div>
      {busy ? <div className="kline-state">正在生成日级K线…</div> : null}
      {error ? <p className="error">{error}</p> : null}
      {series.length ? (
        <>
          <div className="kline-summary">
            <div><span>均值</span><b>{averageClose(series)}</b></div>
            <div><span>高点</span><b>{strongest ? `${strongest.date} · ${strongest.kline.close}` : "—"}</b></div>
            <div><span>低点</span><b>{weakest ? `${weakest.date} · ${weakest.kline.close}` : "—"}</b></div>
          </div>
          <div className="kline-grid">
            <div className="kline-months">
              {Object.entries(groups).map(([month, days]) => (
                <article className="kline-month" key={month}>
                  <h3>{month}</h3>
                  <div className="kline-days">
                    {days.map((day) => (
                      <button
                        className={`kline-day ${day.trend} ${selected?.date === day.date ? "selected" : ""}`}
                        key={day.date}
                        type="button"
                        style={candleStyle(day)}
                        aria-label={`${day.date} ${day.ganzhi.day} ${day.trend}`}
                        onClick={() => setSelected(day)}
                        title={`${day.date} ${day.ganzhi.day} 收盘 ${day.kline.close}`}
                      >
                        <span className="wick" />
                        <span className="body" />
                        <small>{day.date.slice(8)}</small>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
            <aside className="kline-detail">
              {selected ? (
                <>
                  <div className="kline-detail-head">
                    <span>{selected.date}</span>
                    <strong>{selected.ganzhi.day}</strong>
                  </div>
                  <div className="ohlc">
                    <span>开 {selected.kline.open}</span><span>高 {selected.kline.high}</span>
                    <span>低 {selected.kline.low}</span><span>收 {selected.kline.close}</span>
                  </div>
                  <p>{selected.explanation}</p>
                  <div className="kline-tags">{selected.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
                  <ul>
                    {selected.evidence.map((item) => (
                      <li className={item.polarity} key={`${item.rule}-${item.label}`}>
                        <b>{item.delta > 0 ? "+" : ""}{item.delta}</b>{item.label}
                      </li>
                    ))}
                  </ul>
                </>
              ) : <div className="kline-state">选择一天查看证据。</div>}
            </aside>
          </div>
        </>
      ) : null}
    </section>
  );
}
