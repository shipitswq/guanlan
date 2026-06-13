# Guanlan 项目规则

## 项目结构

```
guanlan/
├── backend/app/           # FastAPI 后端
│   ├── main.py
│   ├── routers/           # agents.py, stocks.py
│   ├── models/            # agent.py, stock.py
│   ├── schemas/           # agent.py, stock.py
│   └── services/          # agent_engine.py, ai_analysis.py, data_fetcher.py, rule_engine.py, technical_service.py
├── frontend/              # Next.js 前端
├── tests/backend/         # 后端测试
│   └── test_api.py
└── data_cache/
```

## 任务委派规则

- 遇到多模块的任务，主动拆分并行处理（explorer 用于调研、worker 用于执行），不要一个人全包。
- 同一个模块的后续改动，尽量复用已有的 agent 上下文，而不是每次都从零开始。
- 调研类和改代码任务可以并行做，互不阻塞。

## 测试规则

- 修改 `backend/app/` 下的任何 Python 文件后，必须运行 `tests/backend/test_api.py`，确保测试通过。
- 修改数据库模型（`models/`）后，额外检查是否影响了已有的 API 行为。
- 修改前端代码后，确认 `npm run build` 无报错。

## 代码规范

- Python 使用 type hints。
- 配置优先用 pydantic-settings（参考 `backend/app/config.py`）。
- API 路由遵循 FastAPI 的 router 模式。
- 业务逻辑优先复用 `services/` 层的模块，不要在 router 里重复实现。
