# 人生K线图设计

## 背景

`mingli-lab` 当前已经完成命盘计算、命盘记录、结构化展示和大模型推理。命盘详情中保留了排盘引擎的 `raw` 数据和大运信息，但明确不生成未经验证的五行旺衰、流年、流月结果。

“人生K线图”要补上的是一个可复核的日级运势时间序列：围绕一个已保存命盘，生成近 3 年、精细到日的 K 线日历，用来观察趋势、波动、机会点和风险点。

第一版目标不是给出绝对吉凶断语，而是建立一个稳定、可解释、可测试的规则评分框架。大模型可以后续用于解释某一天或某个区间，但不能批量生成 1095 天结果。

## 目标

第一版交付范围：

- 在命盘详情中新增“人生K线图”模块。
- 对已保存命盘生成近 3 年的日级序列。
- 每天输出 `open/high/low/close` 四个分值，范围为 `0-100`。
- 每天输出流年、流月、流日干支，以及趋势、等级、标签、解释和规则证据。
- 支持综合运势 `overall` 维度。
- 不依赖大模型批量生成日级内容。
- 不修改已有命盘记录结构的兼容字段。

暂不纳入第一版：

- 事业、财运、感情、健康多维 K 线切换。
- AI 批量生成每日解释。
- 真太阳时修正。
- 用户自定义喜用神。
- 服务端持久化缓存表。
- 导出图片或报告。

## 产品形态

入口放在 `ChartDetail` 中，替换当前“流年、流月及旺衰强弱将在后续独立算法模块中接入”的占位模块。

界面由三部分组成：

- 趋势概览：展示 3 年均值、当前月均值、最高点、最低点、当前大运。
- 日历 K 线：按月分组，每天一个小蜡烛。红/绿或涨/跌色表达 `close` 相对 `open`，烛身长度表达当日变化，影线表达 `high/low` 波动。
- 日详情：点击某天后显示干支、四值、标签、解释和规则证据。

默认日期范围采用“今天起未来 3 年”，因为用户目标是分析接下来运势。后续可以增加范围切换，支持“过去 1 年 + 未来 2 年”的验证视角。

## K线语义

人生 K 线不是股票价格，而是把命理规则转成可比较的趋势分。

每一天的四个值定义如下：

- `open`：长期底盘分。来自原局基础、当前大运、流年、流月。
- `close`：当日收盘分。在 `open` 基础上叠加流日触发。
- `high`：机会上沿。来自有利十神、合会、生扶、贵人类信号。
- `low`：风险下沿。来自冲刑害破、忌神增强、结构失衡、日支受冲等信号。

输出示例：

```json
{
  "date": "2026-06-30",
  "ganzhi": {
    "year": "丙午",
    "month": "甲午",
    "day": "乙亥"
  },
  "kline": {
    "open": 58,
    "high": 67,
    "low": 49,
    "close": 62
  },
  "trend": "bullish",
  "level": "medium",
  "tags": ["财星触发", "日支有冲"],
  "explanation": "流日乙木触发财星，但与原局日支形成冲动，机会与波动并存。",
  "evidence": [
    {
      "rule": "day_stem_ten_god",
      "label": "流日天干为财星",
      "delta": 6,
      "polarity": "positive"
    }
  ]
}
```

## 数据生成

当前 `NodeBaziAdapter.calculate()` 每次只计算一个时间点。近 3 年约 1095 天，如果每天启动一次 Node 进程，会慢且不稳定。

需要扩展 `bazi-engine/bazi_local_node.mjs` 支持批量模式：

```json
{
  "mode": "batch",
  "items": [
    {
      "solarDatetime": "2026-06-30T12:00:00+08:00",
      "gender": 1,
      "eightCharProviderSect": 1
    }
  ]
}
```

返回：

```json
{
  "success": true,
  "data": [
    {
      "input": {
        "solarDatetime": "2026-06-30T12:00:00+08:00"
      },
      "chart": {
        "年柱": {},
        "月柱": {},
        "日柱": {},
        "时柱": {}
      }
    }
  ]
}
```

Python 侧新增：

- `NodeBaziAdapter.calculate_batch(arguments_list)`
- `build_daily_engine_arguments(start, end, gender)`
- `normalize_transit_day(raw)`

日级排盘统一用当天 `12:00:00+08:00`，避免时柱和跨日边界干扰流日判断。

## 后端模块

新增 `backend/app/services/life_kline.py`，拆成小函数：

- `build_life_kline(chart, start, end, dimension)`
- `normalize_dayun(chart)`
- `select_dayun_for_date(dayun_list, day)`
- `score_day(base_chart, transit_day, dayun, dimension)`
- `build_daily_explanation(evidence)`
- `clamp_score(value)`

新增 Pydantic 模型：

- `LifeKlineQuery`，用于校验 `start`、`end`、`dimension`。
- `LifeKlineResponse`
- `LifeKlineDay`
- `KlineValue`
- `KlineEvidence`

新增 API：

```text
GET /api/charts/{chart_id}/life-kline?start=2026-06-30&end=2029-06-29&dimension=overall
```

接口行为：

- `chart_id` 不存在返回 `404`。
- `start/end` 缺省时默认未来 3 年。
- 最大范围限制为 1100 天，避免误请求过大。
- `dimension` 第一版只允许 `overall`。
- 排盘引擎失败返回 `503 BAZI_ENGINE_UNAVAILABLE`。

## 评分模型

第一版使用可解释规则，不声称等同传统完整旺衰判定。

总分从 `50` 开始，所有规则产生 `delta`，最后 clamp 到 `0-100`。

长期底盘：

- 当前大运天干十神：`-8` 到 `+8`
- 当前大运地支十神：`-6` 到 `+6`
- 流年天干十神：`-6` 到 `+6`
- 流年地支与原局关系：`-8` 到 `+8`
- 流月天干十神：`-4` 到 `+4`
- 流月地支与原局关系：`-6` 到 `+6`

当日触发：

- 流日天干十神：`-5` 到 `+5`
- 流日地支十神：`-5` 到 `+5`
- 流日与日支冲刑害破：风险下沿增加，`low` 下探 `4-12`
- 流日与原局形成合会：机会上沿增加，`high` 上探 `3-10`
- 流日触发神煞：第一版只记录标签，不直接加大分，避免过度断言。

十神基础倾向第一版先采用中性业务解释：

- 印星：稳定、学习、资质、支持。
- 官杀：责任、压力、规则、职位。
- 财星：资源、交易、机会、消耗。
- 食伤：表达、产出、变动、泄秀。
- 比劫：竞争、同伴、自主、分夺。

不同日主、喜忌、格局会影响正负，这部分第一版不做强断。第一版规则以“触发强弱和波动”优先，正负只做温和权重。后续可加入人工配置的喜用神或模型辅助判定。

## 前端接口和组件

`frontend/src/api.ts` 新增：

- `LifeKlineResponse`
- `LifeKlineDay`
- `api.getLifeKline(chartId, params)`

新增组件：

- `LifeKlinePanel.tsx`
- `LifeKlineCalendar.tsx`
- `LifeKlineDayDetail.tsx`

`ChartDetail` 接收可选 `chartId`，有 `chartId` 时加载 K 线；临时命盘或无记录时不显示。

前端状态：

- `loading`
- `error`
- `series`
- `selectedDate`
- `range`

显示原则：

- 日历必须能一次浏览 3 年，但默认只展开当前年，其他年份折叠或横向切换。
- 每天小蜡烛必须有 tooltip 或点击详情，避免只给颜色不给解释。
- 颜色不能只依赖红绿，需配合图形方向和标签，照顾色弱用户。

## 缓存策略

第一版可以先不建数据库缓存，使用前端请求时即时计算。为了性能稳定，后端服务内部可以按请求过程一次性批量计算。

后续如果性能不够，再新增 SQLite 表：

```text
life_kline_cache
- id
- chart_id
- range_start
- range_end
- dimension
- method_version
- payload_json
- created_at
```

缓存失效条件：

- 命盘记录变化。
- `method_version` 改变。
- 请求范围或维度改变。

## 测试计划

后端测试：

- 批量 Node 输入输出协议。
- `select_dayun_for_date()` 使用精确起运日期边界。
- `score_day()` 固定命盘和固定流日输出稳定 evidence。
- API 默认日期范围不超过 1100 天。
- chart 不存在返回 404。
- 引擎异常返回 503。

前端测试：

- 命盘详情加载后请求 life-kline。
- loading、error、empty、success 状态。
- 日历渲染月份和日单元。
- 点击日单元显示详情。

手工验证：

- 创建命盘后进入详情，能看到人生K线图。
- 3 年日历可滚动或切换。
- 点击某天能看到干支、K线值、标签和解释。

## 分阶段实施

阶段 1：后端规则核心

- 新增批量排盘协议。
- 新增 `life_kline` 服务。
- 新增 API 和后端测试。

阶段 2：前端可视化

- 新增 API 类型。
- 新增 K 线日历组件。
- 接入 `ChartDetail`。
- 增加基础样式和前端测试。

阶段 3：解释增强

- 增加按月汇总。
- 增加点击某天的 AI 解读按钮。
- 增加事业、财运、感情、健康维度。

## 风险和约束

- 评分不是传统命理完整断法，只是可解释趋势指标，UI 文案必须避免绝对化。
- 不应伪造 `bazi-mcp` 没有提供的数据；所有日级干支必须来自排盘引擎或明确规则。
- 1095 天数据量不大，但逐日启动 Node 不可接受，必须批量化。
- 评分规则要版本化，避免以后规则变化导致旧截图或旧解释无法追踪。
- 第一版不引入数据库迁移，降低实现风险。

## 已定决策

默认时间范围采用“今天起未来 3 年”。如果产品更偏验证历史走势，可以改为“过去 1 年 + 未来 2 年”。

第一版只做 `overall` 综合运势。多维度切换放到第二版，避免评分规则尚未稳定时同时扩散到多个语义。
