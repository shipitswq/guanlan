# 观澜 · GuanLan

> **reading the waves.** — A 股模拟交易平台，支持 AI 驱动与规则驱动的量化交易 Agent。

观澜是一款面向 A 股的模拟交易平台，让你无需实盘资金就能体验量化交易的全流程。你可以创建多个交易 Agent，每个 Agent 关联一只股票，使用 **AI 策略**（基于 LLM 分析技术指标）或 **规则策略**（基于 RSI、MACD、布林带等经典指标）自动做出买卖决策，并实时查看收益曲线与交易记录。同时支持**回测模式**，用历史 K 线数据验证策略表现。

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 实时行情 | 接入 A 股实时行情，支持 K 线图（日线 / 60 分钟线） |
| AI Agent | 每个 Agent 绑定一只股票，自动执行交易策略 |
| 双策略引擎 | AI 驱动（调用 LLM 分析技术面）或 规则驱动（基于经典技术指标） |
| 技术指标 | RSI、MACD、均线、布林带、成交量等全覆盖 |
| 回测模式 | 基于历史数据的策略回测，计算收益率与胜率 |
| 模拟资金 | 初始资金 10 万元，实时计算持仓、盈亏、收益率 |
| 交易记录 | 完整的买卖记录与 Agent 操作日志 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js 15 (React 18, TypeScript, TailwindCSS) |
| **后端** | Python 3.12 + FastAPI |
| **数据库** | SQLite + SQLAlchemy ORM |
| **行情数据** | akshare（A 股数据接口），带本地缓存 |
| **图表** | lightweight-charts（K 线图）、recharts |
| **AI 引擎** | OpenAI API（可配置模型与 Base URL） |

---

## 项目结构

```
guanlan/
├── backend/                    # FastAPI 后端
│   └── app/
│       ├── main.py             # 应用入口，CORS、路由注册
│       ├── config.py           # 配置项（数据库、API Key、模型等）
│       ├── database.py         # SQLAlchemy 引擎与 Session
│       ├── models/             # 数据模型
│       │   ├── agent.py        # Agent、TradeRecord、AgentLog
│       │   └── stock.py        # Stock
│       ├── schemas/            # Pydantic 请求/响应模型
│       │   ├── agent.py
│       │   └── stock.py
│       ├── routers/            # API 路由
│       │   ├── agents.py       # Agent CRUD + 交易执行
│       │   └── stocks.py       # 股票搜索与行情
│       └── services/           # 核心业务逻辑
│           ├── agent_engine.py    # 交易引擎（策略编排）
│           ├── data_fetcher.py    # 行情数据获取（akshare + 缓存）
│           ├── technical_service.py  # 技术指标计算
│           ├── rule_engine.py    # 规则驱动策略
│           └── ai_analysis.py    # AI 驱动策略（LLM 决策）
├── frontend/                   # Next.js 前端
│   └── src/app/
│       ├── page.tsx            # Dashboard 首页
│       ├── layout.tsx          # 全局布局
│       ├── agents/
│       │   ├── page.tsx        # Agent 列表
│       │   ├── new/page.tsx    # 创建 Agent
│       │   └── [id]/page.tsx   # Agent 详情（持仓、交易、图表）
│       └── stocks/
│           └── [code]/page.tsx # 个股详情页
├── tests/
│   └── backend/
│       └── test_api.py         # 后端 API 测试
├── data_cache/                 # 行情数据缓存目录
├── stock_sim.db                # SQLite 数据库文件
├── .env.example                # 环境变量模板
├── start_all.bat               # 一键启动脚本
└── CLAUDE.md                   # 项目开发规则
```

---

## 快速开始

### 前置条件

- **Python 3.12+**
- **Node.js 18+**
- **OpenAI API Key**（使用 AI 策略时需要，只使用规则策略则不需要）

### 1. 克隆项目

```bash
git clone <repo-url>
cd guanlan
```

### 2. 后端配置与启动

```bash
cd backend
pip install -r requirements.txt

# 配置环境变量（AI 策略需要）
# 复制 .env.example 为 .env，填入你的 API Key
# OPENAI_API_KEY=sk-xxxx
# OPENAI_BASE_URL=https://api.openai.com/v1  （可选，可改为代理地址）
# OPENAI_MODEL=gpt-4o

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 前端配置与启动

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 **http://localhost:3000**，后端 API 在 **http://localhost:8000**。

### 4. 一键启动

项目根目录提供了 `start_all.bat`（Windows），会依次启动后端和前端：

```bash
.\start_all.bat
```

启动后访问：

- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs

---

## 使用指南

### 创建 Agent

1. 打开首页，点击"创建 Agent"
2. 输入 Agent 名称，搜索并选择要交易的股票
3. 设置初始资金（默认 10 万元）
4. 选择策略类型：**AI 策略** 或 **规则策略**
5. 选择交易模式：**实盘模式**（实时决策）或 **回测模式**（回放历史数据）

### AI 策略

AI 策略会调用 LLM（默认 GPT-4o），传入当前股票的技术指标和持仓信息，由 AI 判断买入/卖出/持有。你可以在 `.env` 中配置模型和 API 地址，支持 OpenAI 兼容接口（包括国内代理）。

### 规则策略

规则策略基于经典技术指标执行决策：

- **RSI**：超卖区域（< 35）倾向买入，超买区域（> 70）倾向卖出
- **MACD**：金叉买入信号，死叉卖出信号
- **均线**：价格站上均线看多，跌破看空
- **布林带**：下轨支撑买入，上轨压力卖出
- **成交量**：放量突破/跌破确认信号

综合评分决定最终操作。

### 实盘模式

Agent 在每日/每 60 分钟定时执行一次交易决策，根据当前行情做出买卖操作。资金、持仓、盈亏实时更新。

### 回测模式

选择历史日期范围，回放 K 线数据驱动策略决策。回测结束后展示累计收益率、交易次数、胜率等绩效指标。

---

## API 概览

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/agents` | GET | 获取所有 Agent 列表 |
| `/api/agents` | POST | 创建新 Agent |
| `/api/agents/{id}` | GET | 获取 Agent 详情（含持仓、交易记录） |
| `/api/agents/{id}` | PUT | 更新 Agent（名称、状态、策略） |
| `/api/agents/{id}` | DELETE | 删除 Agent |
| `/api/agents/{id}/execute` | POST | 执行一次交易决策（实盘） |
| `/api/agents/{id}/backtest` | POST | 运行回测 |
| `/api/stocks/search` | GET | 搜索股票 |
| `/api/stocks/{code}/kline` | GET | 获取 K 线数据 |
| `/api/stocks/{code}/realtime` | GET | 获取实时行情 |
| `/api/health` | GET | 健康检查 |

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API Key（AI 策略必填） | `""` |
| `OPENAI_BASE_URL` | API Base URL（可用于代理） | `""` |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o` |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./stock_sim.db` |
| `CACHE_TTL_HOURS` | 行情数据缓存有效期（小时） | `6` |

---

## 开发

### 运行测试

```bash
cd backend
python -m pytest ../tests/backend/ -v
```

### 代码风格

- 后端：遵循 PEP 8，使用 type hints
- 前端：使用 TypeScript strict 模式

---

## 设计理念

观澜的名字取自"观水有术，必观其澜"——观察水流的方法，在于看它的波澜。做交易也好，做策略也好，道理是相通的：不看表象，看波动背后的规律。

这个项目不是一个简单的 demo。它的目标是让学习量化交易的人有一个真正能用、能摆弄、能理解每个决策环节的 playground。每个 Agent 的决策链路都是透明的——数据怎么来、指标怎么算、规则怎么判断、AI 为什么这么选，每一步都可以追溯。

---

## License

MIT
