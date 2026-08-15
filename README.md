# DataAgent Lite

一个可公开演示的简易 DataAgent：本地知识库检索 + OpenAI LLM + 浏览器聊天界面。

项目刻意不包含真实知识库数据、内部服务地址、业务提示词、账号或密钥。仓库中的 `knowledge_base/` 只有说明文件，运行后生成的本地索引也不会被 Git 提交。

## 功能

- 本地知识库：读取 `knowledge_base/` 中用户自行放入的 `.md` / `.txt` 文件。
- 检索机制：SQLite FTS5 全文索引、中文 Bigram/单字扩展、BM25 排序与归一化，采用“列出本地文件 → 建索引 → top-k 检索 → 读取原文”的简单流程。
- OpenAI 调用：只保留 OpenAI Responses API，不包含其他模型供应商。
- 缓存友好提示词：稳定系统规则和历史消息在前，本轮知识库结果与问题在后，并使用固定 `prompt_cache_key`。
- 简易前端：知识库状态、重建索引、检索预览和多轮问答。
- 隐私默认值：服务只监听 `127.0.0.1`，请求设置 `store=False`，日志不记录问题、知识库内容或 API Key。

## 快速开始

需要 Python 3.9+，并且本机 SQLite 支持 FTS5。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入你自己的 `OPENAI_API_KEY`。然后启动：

```bash
python run.py
```

浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

## 使用本地知识库

1. 把你自己的 `.md` 或 `.txt` 文件放进 `knowledge_base/`。不要提交私密文件。
2. 在页面点击“重建索引”。
3. 先用“检索预览”确认召回结果，再开始提问。

`knowledge_base/README.md` 只用于说明，不会被索引。索引保存在 `knowledge_base/.dataagent/index.db`，已在 `.gitignore` 中排除。

## 缓存说明

OpenAI 的提示词缓存依赖完全一致的前缀。这里保持系统规则、工具约束和历史消息顺序稳定，把每轮变化的知识库片段与用户问题放到末尾。`PROMPT_CACHE_KEY` 用于把共享长前缀的请求路由到同一缓存分组。

缓存只对达到平台门槛的请求生效，因此刚启动的短对话可能显示 `cached_tokens = 0`。接口响应会返回可用的缓存 token 统计，前端会展示该值。

参考：[OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching) 与 [Responses API](https://developers.openai.com/api/docs/guides/responses)。

## API

- `GET /api/status`：配置和知识库状态（不会返回密钥）。
- `POST /api/index`：重建本地 FTS5 索引。
- `POST /api/search`：预览知识库检索结果。
- `POST /api/chat`：检索后调用 LLM。

## 测试与公开前检查

```bash
python -m unittest discover -s tests -v
python scripts/check_sensitive.py
```

敏感信息检查只是最后一道防线，不能替代人工审查。发布前请确认 Git 暂存区中没有 `.env`、知识库文件、数据库、聊天记录或公司专属信息。

## 安全边界

本项目不会把知识库上传到专门的远程知识库服务，但被检索到的片段会随问题发送到 OpenAI API 以生成回答。请只放入你有权处理、且符合你所在组织数据政策的内容。详见 [SECURITY.md](SECURITY.md)。

