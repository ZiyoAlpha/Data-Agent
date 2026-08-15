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
