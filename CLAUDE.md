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

## Git 工作流

- 永远不要直接往 main 分支提交或推送代码。
- 每次做改动前，先切到 main 拉取最新代码（git pull），然后创建 feature 分支：git checkout -b feat/<简短描述>。
- 在 feature 分支上完成开发并测试通过后，推送到远端：git push -u origin feat/<分支名>。
- 在 GitHub 上创建 Pull Request，但不要自己合并——合并由 GitHub 上的部署 agent 自动执行。
- PR 合入后，在本地切回 main，拉取最新代码（git pull），然后删除本地的 feature 分支。
- GitHub 仓库：git@github.com:shipitswq/guanlan.git
- 默认分支：main
## 自动提 PR 流程

- 当用户说"提交"或"提 PR"时，不再只做 git add + git commit，而是自动走完整流程：切到 main 拉取最新代码 -> 创建 feature 分支 -> commit -> push -> 在 GitHub 创建 PR。完成后告知用户 PR 链接。
## GitHub 凭证

- GitHub Token (classic PAT) 已存入 Windows Credential Manager（protocol=https, host=github.com），后续推送和 API 调用可直接复用。如需调用 GitHub REST API，从凭证管理器读取即可。
## PR 追踪

- 创建 PR 后，必须追踪 PR 最终是否被合并。使用 heartbeat automation 定期检查 PR 状态（合并/关闭/开放），一旦发现状态变更，告知用户。
