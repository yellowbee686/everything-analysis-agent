# Agent 分析 Markdown 知识库的高效方案调研

调研日期：2026-05-03  
材料对象：`/Users/bytedance/code/analysis-agent/data/md文件合集`

## 结论摘要

这个材料集不是普通 agent memory，而是一个大规模文献型 Markdown 语料库。本地统计显示它包含约 45,957 个 `.md` 文件，总字节约 2.37GB，单文件中位数约 22KB，P95 约 72KB，P99 约 858KB，超过 1MB 的文件有 313 个。它适合用“原始 Markdown 只读 + SQLite/FTS5 本地索引 + 可选 embedding/RAG + LLM 维护的研究 wiki”来处理，而不适合直接塞进 `MEMORY.md`、单个 `index.md` 或 agent 上下文。

推荐方案：

1. 原始 Markdown 文件系统保留为 source of truth，不把 SQLite 当唯一事实源。
2. SQLite 存元数据、文件 hash、chunk、FTS5 全文索引、任务日志和分析产物索引。
3. FTS5 使用 `trigram` 或“标题/作者/关键词字段 + 正文 trigram”做中文精确召回。
4. 对需要“概念相近但词不相同”的问题，再叠加 embedding 向量检索，形成 openclaw 风格的 hybrid RAG。
5. 对高频主题、专题研究和跨文献综合，采用 Karpathy LLM Wiki 思路：让 agent 把检索后的结论沉淀为结构化 wiki，而不是每次从 2.3GB 原始材料重新推理。

## 1. SQLite + FTS5 怎么工作

SQLite + FTS5 的常见工作流是：

1. 遍历 Markdown 文件，记录 path、mtime、size、sha256、标题、作者、关键词等元数据。
2. 将正文按标题或 token/字符窗口切成 chunk，保留 `path`、`start_line`、`end_line`、`heading_path`。
3. 把 chunk 文本写入普通 SQLite 表。
4. 同步写入 FTS5 虚拟表，建立倒排索引。
5. 查询时使用 `MATCH` 做全文匹配，通过 `rank` 或 `bm25()` 排序。
6. 返回 top-K chunk 后，再让 agent 用 `path#line` 读取原文上下文并综合回答。

FTS5 是 SQLite 的 full-text search 虚拟表模块。它不是向量数据库，而是本地全文检索引擎：把文本拆成 token，建立 token 到文档/chunk 的倒排索引，查询时快速找出包含词项、短语、前缀、NEAR 或布尔组合的结果。SQLite 官方文档说明 FTS5 支持 `MATCH` 查询、hidden `rank` 列、`bm25()` 排名函数，以及 `unicode61`、`trigram` 等 tokenizer。

### FTS5 适合存 Markdown 吗

适合，但应准确理解“存”的边界：

- 适合：把 Markdown 的文本内容、标题、路径、行号和 chunk 写入 SQLite，并为正文建 FTS5 索引。
- 更推荐：Markdown 原文件仍保留在文件系统，SQLite 作为可重建的索引和元数据库。
- 不推荐：把所有 Markdown 只存进 FTS5 虚拟表后丢掉原文件。这样会损失人类可读性、版本管理、图片/附件关系和原始排版线索。

对这个中文/古汉语/文献学语料库，FTS5 的优点很明显：

- 精确词项、书名、人名、术语、异文、短语检索很强。
- SQLite 单文件部署简单，agent 可以直接用 CLI 或 Python 查询。
- 可记录 `path#line`，引用和复核成本低。
- 可以用 hash 做增量索引，避免每次重扫 2.3GB。

局限也必须正视：

- FTS5 不懂语义。检索“离合词的构式特征”和检索“动宾离析的主观性”可能召回不同结果，需要 embedding 或 LLM query expansion 补足。
- 中文分词是关键。`unicode61` 对中文不够理想；`trigram` 对中文子串检索友好，但索引体积更大，且对 1-2 字查询不如自定义 bigram/unigram 或普通字段查询稳定。
- OCR 文本质量参差时，FTS 只能匹配已有字符，不能自动理解错字、断词和乱码。
- 大文件需要 chunking。P99 接近 858KB、最大约 9.75MB，不能整篇作为一个检索单元。

因此，FTS5 是这个材料库的基础设施级选择，但不是完整分析系统。它解决“快速找证据”，不解决“自动形成研究结论”。

## 2. hermes 的 8 个 provider 方案

参考 `/Users/bytedance/code/ttlive_strategy_agent_docs/hermes-agent/memory.md`，hermes 是“双层记忆”：内置 `MEMORY.md`/`USER.md` 始终注入，外部 MemoryProvider 按需预取或同步。8 个 provider 的定位如下：

| Provider | 核心方案 | 是否像 openclaw 的 RAG |
| --- | --- | --- |
| Honcho | 跨会话用户建模、语义搜索、dialectic reasoning、用户表征 | 部分像。它有语义搜索，但更偏用户/会话 memory，不是面向大文档库的文件 RAG |
| OpenViking | 分层知识库，L0/L1/L2 三级加载 | 部分像。更像层级摘要/渐进加载，不是标准 chunk + embedding + BM25 hybrid |
| Mem0 | 自动事实提取、server-side LLM 处理、语义搜索、重排、去重 | 像。它是外部长期记忆/RAG 服务风格，但关注事实记忆而非原始文献库 |
| Hindsight | 知识图谱、实体关系、多策略检索、reflect 合成 | 部分像。它更偏 graph memory 和反射合成 |
| Holographic | 本地结构化知识库、实体解析、信任评分、HRR 组合查询 | 部分像。强调结构化知识和组合推理，不是普通文档 RAG |
| RetainDB | 云端混合搜索、7 种记忆类型、delta 压缩 | 像。它有 hybrid search 和记忆压缩，接近 RAG 型外部后端 |
| ByteRover | 层级知识树、预压缩提取、CLI 管理 | 部分像。更像知识树/摘要索引 |
| Supermemory | 语义长期记忆、上下文围栏、会话图构建 | 像。它提供语义长期记忆召回，但仍偏 agent memory |

结论：hermes 的 provider 生态里确实有 RAG-like 方案，尤其是 Mem0、RetainDB、Supermemory；Hindsight/Holographic 更偏 knowledge graph；OpenViking/ByteRover 更偏层级摘要与渐进加载。它们适合 agent 的长期记忆和跨会话知识，但不一定适合直接承载 45,957 篇中文 Markdown 文献。对这个场景，openclaw 的 SQLite+FTS5+vector hybrid RAG 更贴近需求。

## 3. LLM Wiki 方案是否合适

Karpathy 的 LLM Wiki gist 主张三层结构：

- Raw sources：原始材料只读，是 source of truth。
- Wiki：LLM 维护的 Markdown 页面，包括摘要、实体页、概念页、比较页和综合页。
- Schema：`AGENTS.md`/`CLAUDE.md` 一类规则文件，约束 wiki 结构和维护流程。

它还建议维护两个特殊文件：

- `index.md`：按内容组织的 wiki 目录，每页一行摘要。
- `log.md`：按时间追加的 ingest/query/lint 记录。

这个思路对当前任务“合适，但不能单独使用”。

合适之处：

- 非常适合沉淀跨文献综合，例如“离合词研究脉络”“敦煌文献整理体例”“中古汉语语法研究专题”。
- 让分析结果复利增长。agent 不必每次重新从原始文献里拼接同一个专题。
- Markdown + git 易读、易审查、易回滚，适合人机协作。
- `index.md` 和 `log.md` 对 agent 导航很友好。

不适合单独承担全库检索的原因：

- gist 中提到中等规模约 100 sources、数百页 wiki 时 `index.md` 效果不错；当前是 45,957 个源文件、2.37GB，超出“人工/LLM 读 index 再钻取”的舒适区。
- 如果让 LLM 批量维护所有文献的 wiki 页面，成本和污染风险都高。
- 原始 OCR 文献需要精确定位和引用，wiki 摘要不能替代原文证据。

所以，LLM Wiki 应作为“分析产物层”，不是“检索底座”。底座仍应是 FTS5/hybrid RAG。

## 4. 通用 agent 的推荐架构

我会采用四层架构：

```text
raw_md/                  # 原始 Markdown，只读
  *.md

index.sqlite             # 可重建索引
  files                  # path, hash, title, author, size, mtime
  chunks                 # path, line range, heading path, text
  chunks_fts             # FTS5 index, trigram for CJK
  embeddings             # optional vector table/cache
  analyses               # analysis artifact metadata

wiki/                    # LLM 维护的研究 wiki
  index.md
  log.md
  topics/*.md
  entities/*.md
  comparisons/*.md

AGENTS.md / schema.md    # agent 操作协议
```

### 查询路径

1. 先读 wiki `index.md`，确认是否已有成熟专题结论。
2. 用 SQLite FTS5 检索标题、关键词、正文 chunk。
3. 如果问题是语义型、综述型或同义改写明显，使用 embedding 检索补召回。
4. 合并 FTS 和 vector 结果，做去重和 rerank。
5. 读取原文 `path#line`，回答时引用证据。
6. 如果本次问题形成了可复用结论，写入 wiki，并追加 `log.md`。

### 为什么不是单纯 SQLite+FTS5

单纯 FTS5 很适合“找包含某个词/书名/人名的文献”，但弱于：

- 同义概念召回；
- 跨文献主题聚类；
- 综述型问题；
- 用户不断追问后的知识沉淀。

因此最好叠加两件事：

- embedding/hybrid RAG：解决语义召回；
- LLM Wiki：解决长期综合与复用。

### 为什么不是单纯 openclaw 式 RAG

openclaw 风格的 RAG 很强，但如果只有 RAG，每次复杂分析都会重新检索、重新读、重新综合。对研究型任务，更高效的是把高价值综合写回 wiki，让知识库逐步形成“二级知识”：原始材料提供证据，wiki 提供结构化理解。

### 为什么不是 agent memory

hermes、claude-code、codex 的 memory 主要解决“agent 跨会话记住用户偏好、项目约定、过去任务和经验教训”。当前材料库是外部文献库，不能当作 agent memory 全量注入。最多把操作规则、常用查询方式、已完成专题、索引位置写入 memory；文献本体应走检索系统。

## 5. 建议的落地阶段

### Phase 1：最小可用全文索引

- 建 `index.sqlite`。
- `files` 表记录 path、hash、title、author、size、mtime。
- `chunks` 表按标题/行号切分正文。
- `chunks_fts` 使用 FTS5 `trigram`。
- 提供 `search_md(query, limit)` 和 `read_chunk(chunk_id)` 两个 agent 可调用脚本。

这个阶段即可显著提升效率，尤其适合精确术语、书名、人名和关键词检索。

### Phase 2：混合检索

- 为 chunk 生成 embedding。
- 增加向量检索表或 sqlite-vec。
- 查询时并行跑 FTS 和 vector。
- 采用加权融合，初始权重可设为 FTS 0.4、vector 0.6；文献学精确查询可反过来。
- 做 MMR 去重，避免同一篇长文占满 top-K。

### Phase 3：研究 wiki

- 建 `wiki/index.md` 和 `wiki/log.md`。
- 按专题创建 `wiki/topics/*.md`。
- 每次完成可复用分析后，沉淀“结论 + 证据路径 + 未解决问题”。
- 周期性 lint：检查孤儿页面、重复专题、过期结论和缺少原文引用的断言。

### Phase 4：任务级分析流水线

为常见分析任务固化脚本：

- 专题综述：query expansion -> hybrid retrieval -> cluster -> evidence table -> synthesis page。
- 单篇精读：metadata -> outline -> key claims -> cited evidence -> related documents。
- 对比分析：多 query 检索 -> 表格化字段抽取 -> 差异/共性总结。
- 文献追踪：作者、术语、年代、期刊/书名维度统计。

## 6. 工程细节建议

- Chunk 粒度：普通论文按标题段落切；无标题 OCR 大文件按 800-1200 中文字符窗口切，重叠 100-200 字。
- 元数据抽取：从文件名和正文前 30 行抽标题、作者、OCR/可搜索标记、主题词。
- 中文检索：FTS5 `trigram` 作为主索引，同时为标题/作者保留普通 `LIKE` 或精确字段索引，处理 1-2 字查询。
- 引用格式：统一输出 `path:start_line-end_line`，分析 wiki 中每个关键断言都附证据路径。
- 增量索引：以 sha256 为准，mtime 只作为快速过滤。
- 数据库维护：批量事务写入，开启 WAL；大批导入后执行 FTS `optimize`。
- 安全边界：原始 Markdown 只读；wiki 和索引可重建；agent 不直接改原始文献。
- 质量控制：OCR 噪声高的文档标注 `ocr_quality`，召回后优先交叉验证。

## 7. 对四个问题的直接回答

1. SQLite+FTS5 是“SQLite 元数据/正文 chunk + FTS5 倒排索引 + MATCH/BM25 排名”的全文检索方案。FTS5 是 SQLite 官方全文搜索扩展，适合索引 Markdown 内容，但原始 Markdown 应继续留在文件系统。对中文库建议用 trigram 或自定义中文 tokenizer，并叠加 metadata 字段。
2. hermes 的 8 个 provider 分别是 Honcho、OpenViking、Mem0、Hindsight、Holographic、RetainDB、ByteRover、Supermemory。其中 Mem0、RetainDB、Supermemory 最像 RAG；Hindsight/Holographic 偏知识图谱；OpenViking/ByteRover 偏层级知识；Honcho 偏用户建模。
3. LLM Wiki 方案适合做分析产物层和研究综合层，不适合单独做 2.37GB、45,957 文件的底层检索。它应该接在 FTS5/hybrid RAG 后面。
4. 通用 agent 最合适的方案是“文件系统原文 + SQLite FTS5 基础索引 + 可选向量混合检索 + LLM Wiki 持久综合 + 明确 schema/AGENTS 约束”。这比单纯 memory、单纯 RAG 或单纯 wiki 更稳。

## 参考材料

- `/Users/bytedance/code/ttlive_strategy_agent_docs/comparative_analysis/memory.md`
- `/Users/bytedance/code/ttlive_strategy_agent_docs/hermes-agent/memory.md`
- `/Users/bytedance/code/ttlive_strategy_agent_docs/openclaw/memory.md`
- `/Users/bytedance/code/ttlive_strategy_agent_docs/claude-code/memory.md`
- `/Users/bytedance/code/ttlive_strategy_agent_docs/codex/memory.md`
- SQLite FTS5 官方文档：https://www.sqlite.org/fts5.html
- Karpathy LLM Wiki gist：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
