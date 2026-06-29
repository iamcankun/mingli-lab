export type ChartRecord = {
  id: number;
  name: string;
  gender: "male" | "female";
  birth_date: string;
  birth_time: string;
  birth_place: string;
  bazi: string;
  day_master: string;
  chart: ChartData;
  created_at: string;
};

export type ChartData = {
  solar?: string;
  lunar?: string;
  bazi: string;
  zodiac?: string;
  day_master: string;
  pillars?: Array<{
    label: string;
    stem: { char: string; element?: string; ten_god?: string };
    branch: {
      char: string;
      element?: string;
      hidden_stems?: Array<{ role: string; char: string; ten_god: string }>;
    };
    nayin?: string;
    xingyun?: string;
  }>;
  dayun?: Record<string, unknown>;
};

export type LifeKlineDay = {
  date: string;
  ganzhi: { year: string; month: string; day: string };
  kline: { open: number; high: number; low: number; close: number };
  trend: "bullish" | "bearish" | "neutral";
  level: "high" | "medium" | "low";
  tags: string[];
  explanation: string;
  evidence: Array<{ rule: string; label: string; delta: number; polarity: "positive" | "negative" | "neutral" }>;
};

export type LifeKlineResponse = {
  chart_id: number;
  range: { start: string; end: string; days: number };
  method: { version: string; score_range: [number, number]; dimension: string };
  series: LifeKlineDay[];
};

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload?.detail?.message || payload?.detail || "请求失败");
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  listCharts: (query = "") =>
    request<{ items: ChartRecord[] }>(`/api/charts?query=${encodeURIComponent(query)}`),
  calculateChart: (payload: Record<string, unknown>) =>
    request<{ chart: ChartData; record: ChartRecord }>("/api/charts/calculate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteChart: (id: number) => request<void>(`/api/charts/${id}`, { method: "DELETE" }),
  getLifeKline: (id: number, params: { start?: string; end?: string; dimension?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.start) query.set("start", params.start);
    if (params.end) query.set("end", params.end);
    if (params.dimension) query.set("dimension", params.dimension);
    const suffix = query.toString() ? `?${query}` : "";
    return request<LifeKlineResponse>(`/api/charts/${id}/life-kline${suffix}`);
  },
  getModel: () => request<ModelSettings>("/api/settings/model"),
  saveModel: (payload: ModelSettings & { api_key: string }) =>
    request<ModelSettings>("/api/settings/model", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  testModel: () => request<{ ok: boolean; message: string }>("/api/settings/model/test", { method: "POST" }),
  infer: (payload: Record<string, unknown>) =>
    request<InferenceResult>("/api/inferences", { method: "POST", body: JSON.stringify(payload) }),
};

export type ModelSettings = {
  base_url: string;
  model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  api_key_configured: boolean;
};

export type InferenceResult = {
  response: string;
  reasoning?: string;
  system_prompt: string;
  user_prompt: string;
  token_usage: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number };
};
