import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";


test("switches from chart workspace to inference workspace", async () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "命盘记录", level: 1 })).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "推理分析" }));
  expect(screen.getByRole("heading", { name: "推理分析", level: 1 })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "开始推理" })).toBeInTheDocument();
});


test("opens model settings without exposing an existing key", async () => {
  render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "模型设置" }));
  expect(screen.getByRole("heading", { name: "模型设置", level: 1 })).toBeInTheDocument();
  expect(screen.getByLabelText("API Key")).toHaveValue("");
});


test("keeps the chart form stable across an async calculation", async () => {
  const chart = {
    id: 1, name: "林默", gender: "male", birth_date: "1990-05-15", birth_time: "14:30",
    birth_place: "浙江 杭州", bazi: "庚午 辛巳 庚辰 癸未", day_master: "庚",
    created_at: "2026-06-22T00:00:00Z",
    chart: { bazi: "庚午 辛巳 庚辰 癸未", day_master: "庚", pillars: [] },
  };
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const url = String(input);
    const payload = url.includes("/calculate") ? { record: chart, chart: chart.chart }
      : url.includes("/api/charts") ? { items: [chart] } : { items: [] };
    return new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  render(<App />);
  await userEvent.type(screen.getByLabelText("姓名"), "林默");
  await userEvent.type(screen.getByLabelText("出生日期"), "1990-05-15");
  await userEvent.type(screen.getByLabelText("出生时间"), "14:30");
  await userEvent.click(screen.getByRole("button", { name: "计算并保存命盘" }));
  expect((await screen.findAllByText("庚午 辛巳 庚辰 癸未")).length).toBeGreaterThan(0);
  expect(screen.queryByText(/Cannot read properties/)).not.toBeInTheDocument();
});


test("renders life kline calendar and opens day evidence", async () => {
  const chart = {
    id: 1, name: "林默", gender: "male", birth_date: "1990-05-15", birth_time: "14:30",
    birth_place: "浙江 杭州", bazi: "庚午 辛巳 庚辰 癸未", day_master: "庚",
    created_at: "2026-06-22T00:00:00Z",
    chart: { bazi: "庚午 辛巳 庚辰 癸未", day_master: "庚", zodiac: "马", lunar: "四月廿一", pillars: [] },
  };
  const lifeKline = {
    chart_id: 1,
    range: { start: "2026-06-30", end: "2026-07-01", days: 2 },
    method: { version: "life-kline-v1", score_range: [0, 100], dimension: "overall" },
    series: [
      {
        date: "2026-06-30",
        ganzhi: { year: "丙午", month: "甲午", day: "乙亥" },
        kline: { open: 58, high: 67, low: 49, close: 62 },
        trend: "bullish",
        level: "medium",
        tags: ["财星触发"],
        explanation: "机会信号：流日天干为财星",
        evidence: [{ rule: "day_stem_ten_god", label: "流日天干为财星", delta: 6, polarity: "positive" }],
      },
      {
        date: "2026-07-01",
        ganzhi: { year: "丙午", month: "甲午", day: "丙子" },
        kline: { open: 56, high: 60, low: 45, close: 53 },
        trend: "bearish",
        level: "medium",
        tags: ["压力增强"],
        explanation: "波动信号：流日天干为七杀",
        evidence: [{ rule: "day_stem_ten_god", label: "流日天干为七杀", delta: -3, polarity: "negative" }],
      },
    ],
  };
  vi.mocked(fetch).mockImplementation(async (input) => {
    const url = String(input);
    const payload = url.includes("/life-kline") ? lifeKline
      : url.includes("/api/charts") ? { items: [chart] } : { items: [] };
    return new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } });
  });

  render(<App />);

  expect(await screen.findByText("人生K线图")).toBeInTheDocument();
  await userEvent.click(await screen.findByRole("button", { name: /2026-06-30/ }));
  expect(screen.getByText("乙亥")).toBeInTheDocument();
  expect(screen.getByText("流日天干为财星")).toBeInTheDocument();
});
