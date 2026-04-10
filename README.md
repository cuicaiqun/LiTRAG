# LLM Wiki RAG (No Vector DB)

这是一个参考 Karpathy「LLM Knowledge Base / LLM Wiki」思路的轻量项目：

- `raw/` 放原始资料（不需要先整理）
- `wiki/` 让 LLM 把资料“编译”为结构化知识
- `outputs/` 记录每次问答结果，可回灌到 `wiki/`

核心目标：先理解再问答，优先知识积累，不依赖向量数据库和 embedding。

## 1. 安装

```bash
# 方式 A（推荐）：使用 conda 环境 rag
conda activate rag
pip install -r requirements.txt

# 方式 B：使用 venv
# python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
# pip install -r requirements.txt
```

## 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写：

```bash
LLM_PROVIDER=openai
MODEL=gpt-5.4-mini
OPENAI_BASE_URL=https://code.rayinai.com/v1
OPENAI_API_KEY=your_key
TEMPERATURE_COMPILE=0.0
TEMPERATURE_QA=0.0
LLM_MAX_TOKENS=4096
VISION_MODEL=gpt-5.4-mini
ASR_MODEL=gpt-4o-mini-transcribe

TAVILY_BASE_URL=https://api.tavily.com
TAVILY_API_KEY=your_tavily_key
```

## 3. 使用方式

### 初始化目录（可重复执行）

```bash
python -m llm_wiki init
```

### 编译知识库

```bash
python -m llm_wiki compile
```

### 多模态摄取（重点）

```bash
# 从文件/目录/通配符摄取，统一转成 raw/ingested/*.md
python -m llm_wiki ingest "D:/data/knowledge/**/*"

# 摄取后立即编译进 wiki
python -m llm_wiki ingest "D:/data/knowledge/**/*" --compile
```

支持格式（当前）：

- 文本：`md markdown txt rst yaml yml csv json html htm`
- 文档：`pdf docx pptx`（`ppt` 需先转 `pptx`）
- 图像：`png jpg jpeg webp bmp gif tif tiff`
- 音频：`mp3 wav m4a aac flac ogg`
- 视频转写：`mp4 mov mkv webm avi`（提取音轨后转写）

### 提问

```bash
python -m llm_wiki ask "RAG 和 LLM Wiki 的关键差异是什么？"

# 回灌答案到 wiki/qa/
python -m llm_wiki ask "如何把这个方案用于客服知识库？" --promote
```

### Web 搜索接入（Tavily）

```bash
# 先搜并存入 raw/web/
python -m llm_wiki search "karpathy llm wiki"

# 搜索后立刻编译进 wiki
python -m llm_wiki search "agent memory design" --compile
```

### 仅重建索引与知识地图

```bash
python -m llm_wiki build-index
```

### Web 操作台（仪表盘）

```bash
# 默认: http://127.0.0.1:8787
python -m llm_wiki dashboard

# 开发模式热更新
python -m llm_wiki dashboard --reload
```

仪表盘包含：

- 运行概览（raw/wiki/outputs 统计、模型配置、索引时间）
- 趋势图（近 14 天 ingest / compile / output）
- 操作中心（init / ingest / search / compile / build-index / ask）
- 全局 + 任务双层进度条（总体状态 + 每个任务实时百分比与阶段文案）
- Ingest 路径输入 + 文件上传双模式（支持目录选择器，浏览器支持时）
- Ingest 严格失败模式（汇总后失败，返回完整错误列表）
- 文件预览（最近 outputs 与 wiki sources）
- 运行日志（前端实时记录操作结果）

### 中文测评（DuReader-Retrieval）

```bash
# 评测 dev（默认采样前 1000 条）
python -m llm_wiki eval-dureader --split dev

# 全量评测（可能较慢）
python -m llm_wiki eval-dureader --split dev --max-samples 0

# 指定本地数据文件（跳过下载）
python -m llm_wiki eval-dureader --dataset-path D:/datasets/dev.jsonl.gz
```

输出：
- `outputs/evals/dureader_retrieval/*.json`（结构化指标）
- `outputs/evals/dureader_retrieval/*.md`（可读报告）

说明：
- 当前评测是 **候选集重排序**（每个 query 的正负样本集合内排序），
- 指标含 `MRR@10`、`Recall@1/5/10/20/50`，
- 适合快速迭代检索算法，不是全库召回评测。
- 若你的网络无法直连镜像下载，可先手动准备 `dev.jsonl(.gz)`，再用 `--dataset-path` 指定本地文件。

## 4. 目录结构

```text
.
├─ raw/
├─ wiki/
│  ├─ sources/
│  ├─ qa/
│  ├─ index.md
│  └─ knowledge_map.md
├─ outputs/
├─ llm_wiki/
│  ├─ cli.py
│  ├─ compiler.py
│  ├─ qa.py
│  ├─ retrieve.py
│  └─ ...
└─ CLAUDE.md
```

## 5. 设计说明（为什么不是传统 RAG）

- 不做向量检索链路：使用可解释的关键词检索，先小规模跑通
- 不直接拼原文回答：先“编译”为 wiki，再围绕 wiki 回答
- 把答案当资产：高质量回答可回灌 wiki 形成增量知识
- Web 搜索作为“新资料入口”：先进入 `raw/`，再统一走编译流程
- 多模态入口统一：所有格式先摄取为结构化 markdown，再进入编译与问答

适用规模：

- 推荐：几十到几百篇文档
- 超大规模（万级以上）建议再引入传统 RAG 组件

## Retrieval Profiles (2026-04 Update)

### New env vars

```bash
EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=
EMBEDDING_DIMENSIONS=0

RERANK_BASE_URL=
RERANK_API_KEY=
RERANK_MODEL=

RETRIEVAL_PROFILE=baseline
RETRIEVAL_LEXICAL_TOP_K=80
RETRIEVAL_VECTOR_TOP_K=80
RETRIEVAL_CANDIDATE_MAX=120
RETRIEVAL_RERANK_TOP_N=50
RETRIEVAL_EMBED_BATCH=16
RETRIEVAL_EMBED_TEXT_MAX_CHARS=1800
```

### Ask with profile override

```bash
python -m llm_wiki ask "你的问题" --retrieval-profile hybrid_rerank
```

### Evaluate with profile override and ablation

```bash
python -m llm_wiki eval-dureader --dataset-path D:/datasets/dev.jsonl.gz --retrieval-profile hybrid_rerank
python -m llm_wiki eval-dureader --dataset-path D:/datasets/dev.jsonl.gz --ablation
```

Notes:
- `baseline`: lexical only.
- `hybrid_no_rerank`: lexical + vector fusion.
- `hybrid_rerank`: lexical + vector fusion + rerank.
- If embedding/rerank is unavailable, the pipeline auto-degrades and records the reason in outputs/reports.

## Compile Incremental + Chunk Index (2026-04 Update)

- `compile` now supports incremental skip via fingerprint:
  `file_hash + extractor_version + compile_prompt_version`.
- Fingerprints are stored in `wiki/.compile_manifest.json`.
- `build-index` now also writes retrieval chunk files:
  - `wiki/chunk_index.jsonl`
  - `wiki/chunk_index.meta.json`

## QA Eval With RAGAS (2026-04 Update)

Use `eval-dureader-qa` to score answer quality on DuReader candidate sets:

```bash
# recommended quick run (dev subset)
python -m llm_wiki eval-dureader-qa \
  --dataset-path datasets/dev.jsonl/dev.jsonl \
  --max-samples 200 \
  --retrieval-profile hybrid_rerank \
  --seed 42
```

Optional:
- `--judge-model <model_name>` to override the RAGAS judge model only.
- `--sample-retry-times <int>` retries answer generation for each sample before skipping.
- `--score-retry-times <int>` retries per-sample scoring before falling back / skipping.
- `--retry-backoff-base-sec <float>` base seconds for exponential retry backoff.
- If all scoring attempts fail, the run falls back to the latest successful QA report scores and records the source in the output JSON/MD.

Reported metrics:
- `Faithfulness`
- `Answer Relevance` (RAGAS `answer_relevancy`)

Default quality gates:
- `Faithfulness >= 0.85`
- `Answer Relevance >= 0.80`

Outputs:
- `outputs/evals/dureader_qa/*.json`
- `outputs/evals/dureader_qa/*.md`
