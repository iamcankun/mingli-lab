# 命理 LAB

面向命理研究者与提示词工程调试的本地工作台。P0 已实现：

- 公历出生资料排盘
- 四柱、藏干、十神、纳音、神煞、大运等结构化展示
- SQLite 命盘记录、姓名搜索、查看和删除
- 单栏 OpenAI 兼容推理
- Markdown 结果、完整 Prompt 和 Token 用量诊断
- 模型 API Key 本地加密存储

## 环境

- Python 3.11+
- Node.js 22+

## 安装

```powershell
cd bazi-engine
npm install

cd ..\backend
python -m pip install -r requirements.txt

cd ..\frontend
npm install
```

## 启动

Windows PowerShell：

```powershell
cd C:\path\to\mingli-lab
.\scripts\dev.ps1
```

macOS / Linux：

```bash
cd /path/to/mingli-lab
chmod +x scripts/dev.sh
./scripts/dev.sh
```

浏览器访问 [http://localhost:5173](http://localhost:5173)。

## 模型设置

进入“模型设置”，填写：

- API Base URL，例如 `https://api.deepseek.com/v1`
- 模型 ID
- API Key
- Temperature、Max Tokens、Top P

密钥经 Fernet 加密后写入 SQLite，加密主密钥保存在 `data/.secret_key`。接口不会回传明文密钥。

本地验收可启动 mock 模型：

```powershell
cd backend
python -m uvicorn scripts.mock_model:app --app-dir .. --port 8010
```

模型设置填写 `http://127.0.0.1:8010/v1`、任意非空 API Key 和模型 ID。

## 验证

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm test -- --run
npm run build

cd ..
python scripts\smoke_bazi.py
```

## 数据位置

- SQLite：`data/mingli.sqlite3`
- 本地加密主密钥：`data/.secret_key`

## 明确延期

P0 不生成未经实现验证的五行旺衰、日主强弱、流年和流月结果。Wiki、Raw 文件提炼、提示词版本管理和四栏对比按 `PD.MD` 的 P1/P2 阶段继续开发。

## 复用来源

排盘子进程协议和 `bazi-mcp` 调用方式来自工作区 `AI-MingLi-main`，已隔离为 `bazi-engine`，未引入原项目的登录、记忆、紫微、六爻、奇门等单体逻辑。

