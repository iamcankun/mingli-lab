import { useEffect, useState } from "react";
import { api, type ChartRecord } from "./api";
import { AppShell, type Page } from "./AppShell";
import { ChartWorkspace } from "./ChartWorkspace";
import { InferenceWorkspace } from "./InferenceWorkspace";
import { ModelSettings } from "./ModelSettings";
import "./styles.css";

export default function App() {
  const [page, setPage] = useState<Page>("charts");
  const [charts, setCharts] = useState<ChartRecord[]>([]);
  useEffect(() => { api.listCharts().then((x)=>setCharts(x.items)).catch(()=>undefined); }, []);
  return (
    <AppShell page={page} onPage={setPage}>
      {page === "charts" ? <ChartWorkspace onChartsChange={setCharts}/> : null}
      {page === "inference" ? <InferenceWorkspace charts={charts}/> : null}
      {page === "settings" ? <ModelSettings/> : null}
    </AppShell>
  );
}

