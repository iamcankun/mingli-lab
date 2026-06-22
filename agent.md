# 命理 LAB Agent 项目指南

## 1. 项目定位

`mingli-lab` 是一个面向命理研究者、算法验证人员和提示词工程人员的本地 Web 工作台。

当前交付范围是 P0，核心闭环为：

1. 输入公历出生资料。
2. 调用本地八字排盘引擎生成结构化命盘。
3. 将命盘保存到 SQLite，并支持搜索、查看和删除。
4. 选择已保存命盘或输入临时八字。
5. 调用 OpenAI 兼容模型进行单次命理分析。
6. 展示 Markdown 结果、实际 Prompt 和 Token 用量。

产品完整规划位于工作区根目录的 `PD.MD`。当前实现范围以本文件、`README.md` 和实际代码为准。

## 2. 当前已实现功能

### 命盘计算

- 输入姓名、性别、公历出生日期、出生时间、省份和城市。
- 出生地目前只记录，不参与真太阳时校正。
- 出生时间按东八区 `+08:00` 组装。
- 子时换日规则固定使用 `eightCharProviderSect: 1`。
- 支持输出公历、农历、八字、生肖、日主、四柱、藏干、十神、纳音、星运、神煞、大运、刑冲合会等引擎数据。
- 同时保留排盘引擎的完整原始响应。

### 命盘记录

- SQLite 本地持久化。
- 按姓名模糊搜索。
- 查看结构化命盘详情。
- 删除命盘记录。
- 列表按创建时间和 ID 倒序排列。

### 模型推理

- 维护一套当前 OpenAI 兼容模型配置。
- 支持 Base URL、模型 ID、API Key、Temperature、Max Tokens、Top P。
- 支持测试模型连接。
- 支持已保存命盘和临时八字两种输入。
- 内置全局、背景、性格、事业、财运、自定义六类 Prompt。
- 保存推理结果、完整 System/User Prompt、Token 用量和 Provider 可选 reasoning 字段。

### 安全

- API Key 使用 Fernet 加密后存入 SQLite。
- Fernet 主密钥默认保存在 `data/.secret_key`。
- 获取模型配置的接口只返回 `api_key_configured`，不会返回明文密钥。
- 前端不会把已保存的明文密钥加载到表单状态。

## 3. 技术架构

```text
React 19 + TypeScript + Vite
            │
            │ /api JSON
            ▼
FastAPI + Pydantic
  ├─ Chart API
  ├─ Model Settings API
  ├─ Prompt API
  └─ Inference API
            │
            ├─ SQLite repositories
            ├─ NodeBaziAdapter
            │      └─ Node.js 子进程 → bazi-mcp@0.1.0
            └─ OpenAICompatibleAdapter
                   └─ /chat/completions
```

技术栈：

- 后端：Python 3.11、FastAPI、Pydantic、SQLite、httpx、cryptography。
- 前端：React 19、TypeScript、Vite、react-markdown、lucide-react。
- 排盘：Node.js 22、`bazi-mcp@0.1.0`。
- 测试：pytest、Vitest、Testing Library。

## 4. 目录说明

```text
mingli-lab/
├─ backend/
│  ├─ app/
│  │  ├─ adapters/
│  │  │  ├─ node_bazi.py             # Node 排盘子进程适配器
│  │  │  └─ openai_compatible.py     # OpenAI 兼容 HTTP 适配器
│  │  ├─ services/
│  │  │  ├─ bazi.py                  # 排盘参数构造与结果标准化
│  │  │  └─ inference.py             # Prompt 变量渲染
│  │  ├─ database.py                 # SQLite 建表与连接
│  │  ├─ repositories.py             # 命盘、设置、推理日志仓储
│  │  ├─ models.py                   # API 请求模型
│  │  ├─ prompts.py                  # 内置 Prompt
│  │  ├─ security.py                 # Fernet 加解密
│  │  └─ main.py                     # 应用装配和全部 API 路由
│  └─ tests/
├─ frontend/
│  └─ src/
│     ├─ App.tsx                     # 页面状态和入口
│     ├─ AppShell.tsx                # 导航与整体布局
│     ├─ ChartWorkspace.tsx          # 命盘创建、搜索和记录列表
│     ├─ ChartDetail.tsx             # 命盘结构化展示
│     ├─ InferenceWorkspace.tsx      # 三栏推理工作台
│     ├─ ModelSettings.tsx           # 当前模型配置
│     ├─ api.ts                      # 前端类型和 API 客户端
│     └─ styles.css                  # 全局视觉系统
├─ bazi-engine/
│  └─ bazi_local_node.mjs            # stdin/stdout JSON 排盘桥接
├─ scripts/
│  ├─ dev.ps1                        # Windows 开发启动
│  ├─ dev.sh                         # macOS/Linux 开发启动
│  ├─ mock_model.py                  # 本地 OpenAI 兼容 Mock
│  └─ smoke_bazi.py                  # 真实排盘引擎冒烟测试
├─ data/                              # 本地数据库和密钥，不应提交
└─ README.md
```

## 5. 核心业务链路

### 5.1 命盘计算链路

```text
ChartWorkspace 表单
  → POST /api/charts/calculate
  → build_engine_arguments()
  → NodeBaziAdapter.calculate()
  → bazi_local_node.mjs
  → bazi-mcp.getBaziDetail()
  → normalize_chart()
  → ChartRepository.create()
  → 返回稳定 chart 结构和 record
```

排盘引擎输入：

```json
{
  "solarDatetime": "1990-05-15T14:30:00+08:00",
  "gender": 1,
  "eightCharProviderSect": 1
}
```

其中男性映射为 `1`，女性映射为 `0`。

标准化命盘的主要字段：

- `solar`
- `lunar`
- `bazi`
- `zodiac`
- `day_master`
- `pillars`
- `fetal_origin`
- `fetal_breath`
- `life_palace`
- `body_palace`
- `shensha`
- `dayun`
- `relations`
- `raw`

修改命盘计算时，优先保持这些稳定字段兼容前端和历史 SQLite 数据。

### 5.2 推理链路

```text
InferenceWorkspace
  → POST /api/inferences
  → 读取保存命盘或临时八字
  → 选择内置 Prompt
  → render_prompt()
  → 解密当前模型 API Key
  → OpenAICompatibleAdapter.complete()
  → POST {base_url}/chat/completions
  → InferenceRepository.create()
  → 返回结果和诊断信息
```

支持的 Prompt 变量：

- `{{bazi}}`
- `{{day_master}}`
- `{{chart_json}}`
- `{{analysis_type}}`
- `{{custom_request}}`

未定义变量必须抛出 `PromptRenderError`，不要静默替换为空字符串。

## 6. API 清单

```text
GET    /api/health

POST   /api/charts/calculate
GET    /api/charts?query=
GET    /api/charts/{id}
DELETE /api/charts/{id}

GET    /api/settings/model
PUT    /api/settings/model
POST   /api/settings/model/test

GET    /api/prompts

POST   /api/inferences
GET    /api/inferences?chart_id=
```

接口约束：

- `POST /api/charts/calculate` 的 `persist` 默认为 `true`。
- 推理请求必须在 `chart_id` 和 `temporary_chart` 中二选一。
- API Key 更新时，空字符串表示保留原密钥。
- API 响应和日志中禁止输出明文 API Key。
- 排盘子进程异常统一映射为 `503 BAZI_ENGINE_UNAVAILABLE`。
- 模型连接或推理异常统一映射为 `502`，并返回稳定业务错误码。

## 7. SQLite 数据

数据库文件：`data/mingli.sqlite3`。

### `chart_records`

保存用户出生资料、八字摘要、日主和完整 `chart_json`。

### `model_settings`

只保存一条 `id = 1` 的当前模型配置。API Key 字段为加密文本。

### `inference_logs`

保存命盘 ID、分析类型、实际 Prompt、模型响应、可选 reasoning、Token 用量和创建时间。

变更数据库结构时必须考虑已有本地数据库。不能只修改 `CREATE TABLE IF NOT EXISTS`；新增字段需要显式迁移或兼容读取逻辑。

## 8. 本地开发

环境要求：

- Python 3.11+
- Node.js 22+

首次安装：

```powershell
cd bazi-engine
npm install

cd ..\backend
python -m pip install -r requirements.txt

cd ..\frontend
npm install
```

Windows 启动：

```powershell
cd C:\Users\aCan\Desktop\deemo\mingli-lab
.\scripts\dev.ps1
```

服务地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- Vite 将 `/api` 代理到后端。

本地 Mock 模型：

```powershell
cd C:\Users\aCan\Desktop\deemo\mingli-lab\backend
python -m uvicorn scripts.mock_model:app --app-dir .. --port 8010
```

模型 Base URL 使用 `http://127.0.0.1:8010/v1`。

## 9. 验证命令

后端测试：

```powershell
cd C:\Users\aCan\Desktop\deemo\mingli-lab\backend
python -m pytest -q
```

前端测试与构建：

```powershell
cd C:\Users\aCan\Desktop\deemo\mingli-lab\frontend
npm test -- --run
npm run build
```

真实排盘引擎冒烟测试：

```powershell
cd C:\Users\aCan\Desktop\deemo\mingli-lab
python scripts\smoke_bazi.py
```

涉及前端交互的修改还应在浏览器中验证目标页面、请求结果和控制台错误。

## 10. 开发约束

- 以测试驱动方式修改行为：先添加失败测试，再实现，再运行完整相关测试。
- 不直接把 `AI-MingLi-main` 的单体代码整体复制进来；只通过明确的适配层复用独立能力。
- 保持 Node 排盘引擎与 FastAPI 之间的 stdin/stdout JSON 协议。
- 不在 Python 后端重新实现一套未经验证的八字算法。
- 不伪造 `bazi-mcp@0.1.0` 未可靠提供的五行旺衰、日主强弱、流年和流月数据。
- 不修改或提交 `data/`、`.secret_key`、SQLite 数据库、`node_modules/`、`dist/` 和缓存文件。
- 不在测试、日志、截图或文档中写入真实 API Key。
- 修改前端 API 类型时，同步检查后端 Pydantic 模型、公开响应、SQLite 仓储和前端表单。
- 修改命盘标准化结构时，同步检查 `ChartData`、`ChartDetail`、历史记录读取和 API 测试。
- 当前工作区没有 Git 元数据，不要假设可以提交、切分支或创建 PR。

## 11. 当前已知差距

以下内容在产品规划中存在，但当前 P0 尚未实现：

- Raw 文件上传、解析和管理。
- Wiki 提炼、审核、发布和版本追踪。
- Prompt 模板持久化、版本管理和回滚。
- 多模型配置库与用途标记。
- 最多四栏的模型、Prompt、知识对比。
- 真太阳时修正。
- 流年、流月、五行旺衰和日主强弱算法。
- 桌面安装包和用户登录系统。

当前模型 HTTP 请求超时固定为后端适配器默认的 60 秒，模型设置页面尚未提供超时配置。若增加该功能，需要同时修改：

- `backend/app/models.py`
- `backend/app/database.py` 及已有数据库迁移
- `backend/app/repositories.py`
- `backend/app/main.py`
- `backend/app/adapters/openai_compatible.py`
- `frontend/src/api.ts`
- `frontend/src/ModelSettings.tsx`
- 后端与前端测试

## 12. 参考资料优先级

处理需求时按以下顺序判断：

1. 用户当前明确要求。
2. `mingli-lab` 实际代码和测试。
3. 本文件与 `mingli-lab/README.md`。
4. `docs/superpowers/specs/2026-06-22-mingli-lab-p0-design.md`。
5. 工作区根目录 `PD.MD` 的长期产品规划。
6. `AI-MingLi-main` 仅作为可复用实现参考，不作为当前架构规范。

