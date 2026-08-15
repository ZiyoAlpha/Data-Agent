# Local knowledge base structure

这个目录刻意不包含任何真实知识数据。它只保留一套 `common` 公共知识结构，供本地演示时填入你自己的非敏感资料。

## 目录结构

```text
knowledge_base/
├── README.md
└── common/
    ├── metrics/                  # 指标定义与统计口径
    ├── tables/                   # 数据实体、字段、粒度和关系
    ├── patterns/                 # 可复用的查询或处理模式
    ├── contracts/                # 机器可读的事实、约束和契约
    ├── queries/                  # 单次查询需求与查询模板
    ├── cases/                    # 端到端案例与复盘
    ├── rules/                    # 跨任务共享的规则与约定
    ├── skills/                   # 某类任务的执行步骤和检查清单
    └── precedents/               # 可复用的历史证据
        ├── fields/               # 字段含义、类型和枚举的历史证据
        ├── schema-changes/       # 数据结构变更记录
        └── decisions/            # 尚未升级为强制规则的历史决策
```

各目录目前只有 `.gitkeep` 占位文件，所以初始知识库文档数为 `0`。

## 各目录的详细契约

| 目录 | 回答的核心问题 | 建议正文至少包含 | 不应该放入 |
| --- | --- | --- | --- |
| `metrics/` | 一个指标到底怎么算？ | 定义、公式、粒度、时间口径、去重口径、来源、不适用场景、待确认项 | 只服务某一次查询的临时计算 |
| `tables/` | 一个数据实体客观上是什么？ | 用途、粒度、主键、字段、时间语义、关系、已知限制 | 指标口径、任务步骤或猜测性业务解释 |
| `patterns/` | 哪种处理方法可以重复使用？ | 适用条件、输入、步骤、输出、失败模式、验证方法 | 某一次任务的完整上下文 |
| `contracts/` | 哪些事实或约束需要机器和人共同遵守？ | 约束对象、约束内容、状态、置信度、证据引用、冲突处理 | 没有证据的推断或长篇案例 |
| `queries/` | 一个单段查询或模板怎样复用？ | 目标、参数、依赖知识、查询模板、校验方式、限制 | 多阶段落盘链路或完整项目复盘 |
| `cases/` | 一个端到端问题曾经怎样解决？ | 背景、目标、输入、关键决策、步骤、验证、结果、可复用与不可复用部分 | 已经抽象成公共规则但仍重复粘贴的正文 |
| `rules/` | 所有相关任务必须遵守什么？ | 规则、原因、适用范围、反例、例外、验证方法 | 可选建议或未经确认的历史判断 |
| `skills/` | 某类任务应该按什么流程执行？ | 触发条件、前置检查、步骤、停止条件、输出格式 | 表字段、指标公式等事实正文 |
| `precedents/fields/` | 某字段历史上如何被解释？ | 对象、历史结论、证据、日期、置信度、当前状态 | 已确认且长期有效的正式表定义 |
| `precedents/schema-changes/` | 数据结构何时发生过什么变化？ | 变更前后、影响、迁移建议、证据、时间 | 没有发生时间或证据的传闻 |
| `precedents/decisions/` | 哪个历史决策可能再次有用？ | 决策、背景、备选方案、理由、后果、适用边界 | 已升级为强制规则的内容 |

目录之间的关系可以概括为：`tables` 和 `metrics` 保存事实，`rules` 和 `contracts` 保存约束，`patterns` 和 `skills` 保存复用方法，`queries` 和 `cases` 保存任务实例，`precedents` 保存尚需上下文解释的历史证据。

## 通用文档外壳

通过写入接口创建的 Markdown 会自动带上以下元数据。直接手写文件时也建议保持相同字段：

```yaml
---
title: "清晰且唯一的标题"
section: "metrics"
status: "draft"             # draft | verified | deprecated
summary: "一到两句话说明本文档解决什么问题"
source_ref: "可公开的来源引用；没有则留空"
created_at: "ISO-8601 时间"
updated_at: "ISO-8601 时间"
---
```

状态含义：

- `draft`：结构完整但仍需复核，回答时不能当作强事实。
- `verified`：已经过人工或自动校验，可以作为主要依据。
- `deprecated`：保留用于解释历史，但不应继续指导新任务。

文件名统一采用小写英文、数字和连字符，例如 `example-task-completion-rate.md`。路径负责表达分类，文件名负责表达主题，不要在文件名中放日期、姓名、账号或环境标识。

## 放置原则

- 可跨任务稳定复用的内容才进入 `common/`。
- 同一个事实只保留一个权威位置，其他文档使用链接引用。
- `tables/` 记录客观结构；`metrics/` 记录计算口径；`rules/` 记录必须遵守的约束。
- 单段查询或模板进入 `queries/`；包含多个步骤的完整流程进入 `cases/`。
- `skills/` 只描述“如何完成任务”，不重复存放事实正文。
- 暂时性的历史证据进入 `precedents/`，确认成为长期规范后再升级到对应正式目录。
- 不要提交个人信息、账号、密钥、内部地址、真实业务数据或未获授权的文档。

## 完全虚构的示例

下面仅展示文档格式，不代表任何真实系统、公司、表或指标。需要试用时，可以自行创建 `common/metrics/example-task-completion-rate.md`：

```markdown
# 示例指标：任务完成率

- 状态：example
- 定义：在选定统计周期内，已完成的示例任务占已提交示例任务的比例。
- 公式：完成任务数 / 提交任务数
- 统计粒度：天
- 时间口径：使用示例任务的完成日期
- 去重口径：按虚构的 task_id 去重
- 来源：common/tables/example_tasks.md
- 必选过滤：排除标记为测试的虚构记录
- 不适用场景：不用于评价个人绩效
- 待确认项：跨日任务归属规则
```

如果还要演示表文档，可以自行创建 `common/tables/example_tasks.md`：

```markdown
# 示例实体：example_tasks

- 用途：只用于演示知识库文档格式
- 粒度：每个虚构任务一行
- 主键：task_id
- 时间字段：created_at、completed_at
- 状态字段：submitted、completed、cancelled
- 数据声明：本文档和字段均为虚构，不对应任何真实数据源
```

创建示例文件后，在前端点击 **重建知识库索引**。生成的 `common/.dataagent/` 索引包含文档的可检索派生内容，已被 Git 忽略，也不应手工提交。

## 写入决策逻辑

建议把一次知识写入拆成以下步骤：

1. **输入检查**：确认材料有权使用，先移除真实数据、个人信息、密钥、内部地址和不可公开标识。
2. **知识拆分**：一份材料可能同时包含表事实、指标口径和案例过程，应拆到多个目录，并通过相对路径互相引用。
3. **分类路由**：先判断它是事实、约束、方法、任务实例还是历史证据，再选择唯一主目录。
4. **字段校验**：检查目标目录要求的必填信息；缺少来源或关键定义时保持 `draft`，不要自动补猜。
5. **重复与冲突检查**：同主题已存在时先比较。完全重复则跳过；补充信息则合并；结论冲突则保留旧文档并将冲突记录到 `precedents/decisions/`，等待人工决定。
6. **安全落盘**：只允许白名单目录和安全 slug；默认不覆盖；先写临时文件，再原子替换，避免中途失败留下半篇文档。
7. **索引同步**：写入成功后只更新这一篇文档的 FTS5 记录，不必每次全量重建。
8. **可检索性验证**：使用标题关键词和一个正文关键词各检索一次，确认能够命中正确路径。
9. **结果回执**：返回创建或替换动作、相对路径、字节数和索引状态，不在日志中输出正文。

伪代码如下：

```text
write(candidate):
  assert candidate is authorized and sanitized
  pieces = split_by_knowledge_type(candidate)

  for piece in pieces:
    section = classify(piece)
    validate_required_fields(section, piece)
    existing = find_same_topic(section, piece.slug)

    if existing is identical:
      continue
    if existing conflicts and no explicit overwrite approval:
      write_precedent_for_review(piece, existing)
      continue

    path = resolve_from_allowlist(section, piece.slug)
    atomic_write(path, render_standard_markdown(piece))
    incremental_fts5_upsert(path)
    verify_search_hit(path, piece.title)
```

## 当前示例项目中的写入接口

`POST /api/knowledge/documents` 实现了上述流程的安全骨架：

- `section` 必须来自现有 common 白名单。
- `slug` 只能包含小写英文、数字和单连字符。
- 默认 `overwrite=false`，已有文档不会被静默覆盖。
- 写入前检查常见 API Key、GitHub token 和私钥格式。
- 写入采用排他创建或临时文件原子替换。
- 成功后立即增量更新 FTS5，并返回 `indexed` 状态。

完全虚构的调用示例：

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge/documents \
  -H 'Content-Type: application/json' \
  -d '{
    "section": "metrics",
    "slug": "example-task-completion-rate",
    "title": "示例任务完成率",
    "summary": "完全虚构的演示指标",
    "body": "完成任务数除以提交任务数，仅用于演示。",
    "sourceRef": "tables/example-tasks.md",
    "confidence": "draft",
    "overwrite": false
  }'
```

这个接口只解决安全落盘和索引同步。真实项目在调用它之前，仍应增加人工审批、来源真实性校验、语义去重和冲突评审。
