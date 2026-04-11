window.INTERVIEW_KIT_DATA = {
  meta: {
    projectName: "LLM Wiki RAG Interview Kit",
    repoName: "rag-skill",
    position: "AI 应用 / Agent 工程师",
    headline: "把当前项目压缩成一套能复述、能深挖、也能守住边界的面试作战包",
    summary:
      "项目本质是 compile-first 的本地多模态知识库：先把原始资料抽取并编译成结构化 wiki，再围绕 wiki 做检索、问答、评测和 dashboard，而不是直接走向量库拼片段回答。",
    truthBoundary: "已实现和 roadmap 必须分开讲；QA 最新报告的 fallback 必须主动说明。",
    generatedDate: "2026-04-11",
    tone: "Editorial War Room"
  },
  pages: [
    { id: "index", href: "index.html", nav: "项目总览", title: "一眼看清项目主线与面试卖点", summary: "先理解定位、主流程、最强证据和边界。" },
    { id: "resume", href: "resume.html", nav: "简历写法", title: "把项目写成可投递、可口述、可举证的版本", summary: "解决项目标题、简历 bullet、STAR 与口述稿。" },
    { id: "architecture", href: "architecture.html", nav: "架构拆解", title: "从层次、数据流、目录、命令四个维度拆解系统", summary: "重点讲清为什么它不是普通 RAG demo。" },
    { id: "modules", href: "modules.html", nav: "模块细节", title: "逐模块掌握职责、输入输出、关键实现与追问点", summary: "二面最容易问到的细节都在这一页。" },
    { id: "evidence", href: "evidence.html", nav: "亮点证据", title: "所有亮点都带证据，所有风险都带边界", summary: "优先讲 retrieval 报告，其次讲工程亮点和 QA 辅助证据。" },
    { id: "graph", href: "graph.html", nav: "知识图谱", title: "用关系图串起主流程、证据、风险和 roadmap", summary: "点击节点可查看该部分的讲法与引用。" },
    { id: "qa", href: "qa.html", nav: "面试问答", title: "按定位、架构、实现、评测、风险准备标准答案", summary: "每题都给压缩版、完整回答、追问和坑点。" },
    { id: "drills", href: "drills.html", nav: "速记与模拟", title: "面试前 10 分钟速记卡", summary: "压缩成 30 秒、1 分钟、3 分钟三档口述稿。" }
  ],
  quickPitch: {
    resumeProjectName: "LLM Wiki / Compile-First 本地多模态知识库系统",
    oneLine:
      "我做了一个 compile-first 的本地 RAG/知识库系统，先把多源资料抽取和编译成 wiki，再基于 lexical、hybrid、rerank 检索做问答，并配了评测与 dashboard 闭环。",
    bullets: [
      "设计并实现 raw -> ingest -> compile -> index/map -> retrieve -> ask 的文件化知识工作流，强调可解释性与知识沉淀，而不是直接拼接原文回答。",
      "实现多模态 ingest，统一把 pdf/docx/pptx/image/audio/video/html/json 等输入抽取为 markdown；编译阶段引入 fingerprint 增量跳过机制，降低重复构建成本。",
      "实现 baseline、hybrid_no_rerank、hybrid_rerank 三档检索 profile，并加入 embedding cache、降级容错和评测闭环；DuReader candidate-set ranking 中 MRR@10 从 0.4121 提升到 0.7097。"
    ],
    star: {
      situation: "很多小型 RAG demo 只做向量检索和 prompt 拼接，长期难沉淀结构化知识，也不容易解释回答链路。",
      task: "目标是做一个 compile-first 的本地知识库，既能 ingest 多模态资料，也能把知识编译成 wiki，再围绕 wiki 做问答、评测和操作界面。",
      action: "我把系统拆成 ingest、compile、index、retrieve、qa、eval、dashboard 七个模块，并让每个阶段都有清晰输入输出和落盘产物。",
      result: "形成了端到端可运行的本地知识库系统，检索优化有数据支撑，且能清楚说明适用场景、风险边界和后续演进路线。"
    },
    sixtySec: [
      "这个项目不是简单聊天 demo，而是一个 compile-first 的本地多模态知识库。",
      "链路是 ingest 多模态资料、compile 成 wiki、build-index 生成索引和 knowledge map，再用 retrieval profile 做问答。",
      "工程上我做了多模态 ingest、增量 compile、hybrid/rerank 检索、dashboard 和 DuReader 评测。",
      "最强证据是 hybrid_rerank 的 MRR@10 从 0.4121 提升到 0.7097。"
    ],
    threeMinute: [
      "先讲问题：传统 RAG 重检索、轻知识治理，回答依赖临时召回。",
      "再讲设计：项目采用 compile-first，先 raw -> ingest -> compile -> wiki，再 build-index、retrieve、ask。",
      "再讲关键实现：多模态 ingest、fingerprint 增量编译、三档 retrieval profile、embedding cache、dashboard 任务视图。",
      "最后讲结果与边界：检索报告明显提升；QA 框架已做，但最新报告用了 historical fallback，所以 retrieval 是主证据，QA 是辅助证据。"
    ]
  },
  home: {
    overviewCards: [
      { title: "项目定位", body: "compile-first 的本地多模态知识库，适合中小规模语料和高可解释性场景。" },
      { title: "核心主线", body: "ingest -> compile -> build-index -> retrieve -> ask -> eval/dashboard。" },
      { title: "最硬证据", body: "DuReader candidate-set retrieval：MRR@10 从 0.4121 提升到 0.7097。" },
      { title: "最重要边界", body: "QA 最新报告是 fallback；dashboard 任务是内存态线程模型。" }
    ],
    highlightCards: [
      { title: "Compile-First", body: "先将原始资料编译成 wiki，再基于 wiki 回答。" },
      { title: "多模态入口", body: "文本、HTML、JSON、PDF、Docx、PPTX、图片、音视频统一入库。" },
      { title: "可降级检索", body: "baseline / hybrid / rerank 三档检索 profile，服务缺失时自动降级。" },
      { title: "评测与操作台", body: "CLI、FastAPI dashboard、检索评测、QA gate 全部打通。" }
    ],
    studyPath: [
      "先记一句话定位，再看架构页主流程。",
      "把简历页的项目标题、3 条 bullet、1 分钟口述版背下来。",
      "把 retrieval profile、增量 compile、dashboard 任务流讲顺。",
      "证据页只挑 3 个最强卖点，不要每个都展开。",
      "最后用速记页做 30 秒、1 分钟、3 分钟三轮压缩。"
    ],
    mustKnow: [
      "compile-first 定位。",
      "主链路 7 步。",
      "三档 retrieval profile。",
      "DuReader retrieval 指标提升。",
      "QA fallback 与内存态任务模型边界。"
    ],
    niceToKnow: [
      "fingerprint = file_hash + extractor_version + compile_prompt_version。",
      "embedding cache 写入 outputs/cache。",
      "chunk_index 已生成但还没成为检索主路径。",
      "ask 可以 promote 到 wiki/qa。"
    ],
    dontOverclaim: [
      "不要说已经做了生产级任务队列或分布式调度。",
      "不要把 candidate-set ranking 说成全库线上召回。",
      "不要把 QA fallback 报告说成最近一次在线强证据。",
      "不要说已经有真正的图数据库知识图谱。"
    ]
  },
  architecture: {
    layers: [
      {
        title: "入口层",
        focus: "CLI + Dashboard",
        points: ["CLI 暴露 init、ingest、compile、build-index、ask、search、dashboard、两类 eval。", "Dashboard 基于 FastAPI，负责任务、日志、结果预览。", "这一层是用户入口，不承载核心知识处理。"],
        refs: ["llm_wiki/cli.py", "llm_wiki/dashboard_api.py"]
      },
      {
        title: "知识加工层",
        focus: "Ingest + Compiler + Index",
        points: ["Ingest 统一多格式输入。", "Compiler 把 raw source 转成 wiki/sources。", "Build-index 生成 index、knowledge_map、chunk_index。"],
        refs: ["llm_wiki/ingest.py", "llm_wiki/compiler.py"]
      },
      {
        title: "检索问答层",
        focus: "Retrieve + QA",
        points: ["Retrieve 支持 lexical、embedding 融合和 rerank。", "QA 基于 wiki 上下文生成答案，并强制引用支持页。", "结果落盘到 outputs/，必要时回灌到 wiki/qa。"],
        refs: ["llm_wiki/retrieve.py", "llm_wiki/qa.py"]
      },
      {
        title: "评测运营层",
        focus: "Eval + Observability",
        points: ["DuReader retrieval 评估检索 profile。", "DuReader QA 评估 Faithfulness 与 Answer Relevance。", "Dashboard 提供运行状态、最近结果、任务日志。"],
        refs: ["llm_wiki/eval_dureader.py", "outputs/evals/"]
      }
    ],
    flow: [
      { title: "raw 作为原始资料入口", body: "不要求预处理，后续统一由 ingest 和 compile 接管。", tags: ["raw/", "本地文件化"] },
      { title: "Ingest 统一转 markdown", body: "不同格式先抽取为 markdown，保证 compile 输入稳定。", tags: ["pdf/docx/pptx", "vision OCR", "ASR"] },
      { title: "Compile 生成 wiki 页", body: "固定结构输出 Summary、Claims、Concepts 等部分，并维护 manifest。", tags: ["wiki/sources", "fingerprint"] },
      { title: "Build-index 建索引和知识地图", body: "生成 wiki/index.md、knowledge_map.md 和 chunk_index。", tags: ["index", "knowledge map", "chunk index"] },
      { title: "Retrieve 召回候选页面", body: "根据 profile 执行 lexical、hybrid 或 rerank 检索，并记录 degraded_reason。", tags: ["baseline", "hybrid", "rerank"] },
      { title: "Ask 生成答案并留痕", body: "答案必须带页面引用，输出落到 outputs/，可选回灌 wiki/qa。", tags: ["outputs", "citations", "promote"] },
      { title: "Eval + Dashboard 闭环", body: "检索和 QA 都能评测，操作过程可视化。", tags: ["DuReader", "FastAPI", "可演示"] }
    ],
    directories: [
      { title: "raw/", body: "原始资料、ingested 结果、web capture、评测数据。" },
      { title: "wiki/", body: "编译后的知识页、问答回灌、索引和 knowledge map。" },
      { title: "outputs/", body: "问答输出、评测报告、缓存等运行产物。" },
      { title: "llm_wiki/", body: "核心代码目录，包含 CLI、dashboard、ingest、compiler、retrieve、qa、eval。" }
    ],
    commands: [
      { title: "主链路命令", items: ["python -m llm_wiki init", "python -m llm_wiki ingest \"D:/data/**/*\" --compile", "python -m llm_wiki build-index", "python -m llm_wiki ask \"你的问题\" --retrieval-profile hybrid_rerank"] },
      { title: "外部资料与界面", items: ["python -m llm_wiki search \"karpathy llm wiki\" --compile", "python -m llm_wiki dashboard"] },
      { title: "评测命令", items: ["python -m llm_wiki eval-dureader --split dev --ablation", "python -m llm_wiki eval-dureader-qa --dataset-path datasets/dev.jsonl/dev.jsonl --max-samples 200 --retrieval-profile hybrid_rerank"] }
    ],
    retrievalProfiles: [
      { name: "baseline", description: "只做 lexical 检索，依赖最少。", whenToSay: "默认、稳定、可解释。", caveat: "效果不是最强，但可用性最高。" },
      { name: "hybrid_no_rerank", description: "lexical + embedding 融合，补语义召回。", whenToSay: "说明项目并非完全没有语义检索。", caveat: "embedding 不可用时会退化。" },
      { name: "hybrid_rerank", description: "在 hybrid 基础上再做 rerank，效果最强。", whenToSay: "这是检索效果最好的主卖点。", caveat: "要强调结果来自 candidate-set ranking。" }
    ],
    compareTraditionalRag: [
      { axis: "知识组织", thisProject: "先 compile 成 wiki 再检索。", traditional: "先 chunk，再拼 prompt。" },
      { axis: "可解释性", thisProject: "页面结构固定、引用清晰。", traditional: "更多依赖召回和 prompt。" },
      { axis: "知识沉淀", thisProject: "回答可回灌 wiki/qa。", traditional: "多数只留日志。" },
      { axis: "适用规模", thisProject: "更适合中小规模与高治理场景。", traditional: "更适合海量语料检索平台。" }
    ]
  },
  modules: [
    {
      title: "config + llm client",
      purpose: "统一环境变量、模型配置、OpenAI 兼容接口、视觉和 ASR 调用入口。",
      inputsOutputs: ["输入：.env / 环境变量", "输出：AppConfig、LLMClient、EmbeddingClient、RerankClient"],
      implementation: ["load_config() 统一读取目录、模型、检索 profile 及参数。", "LLMClient.complete() 依次尝试 streaming chat、responses、non-stream chat。", "视觉抽取与音频转写也统一封装。"],
      interviewAngles: ["为什么要三重 fallback：兼容不同网关返回格式。", "为什么检索参数放配置：方便 ablation 和运行时调优。"],
      risks: ["依赖环境变量和外部服务。", "当前只支持 OpenAI 风格 provider。"],
      refs: ["llm_wiki/config.py", "llm_wiki/llm.py", "llm_wiki/retrieval_clients.py"]
    },
    {
      title: "ingest",
      purpose: "把多格式输入统一转成 raw/ingested/*.md。",
      inputsOutputs: ["输入：文件、目录、glob", "输出：raw/ingested/*.md、IngestSummary"],
      implementation: ["按扩展名路由 extractor。", "PDF 走 pdfplumber + Vision OCR fallback。", "音视频先 ffmpeg 归一化再走 ASR。", "所有入库文件都带 source_path、source_type、extractor 元数据。"],
      interviewAngles: ["为什么统一转 markdown。", "为什么 PDF 需要 OCR fallback。"],
      risks: ["依赖 markdownify、pdfplumber、ffmpeg 等外部能力。", ".ppt 不直接支持。"],
      refs: ["llm_wiki/ingest.py"]
    },
    {
      title: "compiler + build-index",
      purpose: "把 raw source 编译成 wiki 页，并生成 index、knowledge_map、chunk_index。",
      inputsOutputs: ["输入：raw 文本", "输出：wiki/sources、wiki/index.md、wiki/knowledge_map.md、wiki/chunk_index.jsonl"],
      implementation: ["固定结构输出 Summary / Claims / Concepts。", "fingerprint = file_hash + extractor_version + compile_prompt_version。", "build_chunk_index() 生成 chunk_id、page_id、char_start、char_end。"],
      interviewAngles: ["为什么需要 manifest。", "为什么 chunk_index 先生成但尚未接入主检索。"],
      risks: ["knowledge_map 目前是 synthesis，不是图数据库。", "compile 质量受 prompt 与领域知识影响。"],
      refs: ["llm_wiki/compiler.py", "wiki/chunk_index.meta.json"]
    },
    {
      title: "retrieve",
      purpose: "围绕 wiki page 做 lexical / hybrid / rerank 检索。",
      inputsOutputs: ["输入：query、pages、profile", "输出：RetrievalResult、RetrievalHit、degraded_reason"],
      implementation: ["baseline 走 token frequency + title boost。", "hybrid_no_rerank 用 RRF 融合 lexical 与 vector。", "hybrid_rerank 对候选集前 N 个结果做 rerank。", "embedding cache 减少重复嵌入。"],
      interviewAngles: ["为什么 normalize_query 有 alias rule。", "为什么保留 lexical 而不是纯向量。"],
      risks: ["当前主检索仍是 page-level。", "embedding/rerank 缺失时效果会回退。"],
      refs: ["llm_wiki/retrieve.py"]
    },
    {
      title: "qa",
      purpose: "基于 wiki context 生成答案，并把结果落盘或回灌。",
      inputsOutputs: ["输入：question、retrieval_profile、top_k", "输出：outputs/*.md、可选 wiki/qa/*.md"],
      implementation: ["只使用给定 wiki context 回答。", "输出记录 requested/applied profile、candidate_count、degraded_reason、used_pages。", "promote 模式把问答写回 wiki/qa。"],
      interviewAngles: ["为什么强制引用页面。", "为什么 output 单独落在 outputs/。"],
      risks: ["回答质量受 compile 和 retrieval 共同影响。", "上下文裁剪仍基于字符长度。"],
      refs: ["llm_wiki/qa.py", "outputs/"]
    },
    {
      title: "dashboard_api + dashboard_static",
      purpose: "把 CLI 工作流包装成浏览器可操作的任务中心。",
      inputsOutputs: ["输入：HTTP 请求", "输出：job group / job state、overview、前端任务视图"],
      implementation: ["FastAPI 提供 overview、jobs、job-groups 与各类操作接口。", "任务执行采用 Thread + 内存字典。", "前端轮询展示任务组、日志、最近结果和当前结果。"],
      interviewAngles: ["为什么没上 Celery：当前目标是 demo + tooling。", "为什么要 job group：一次操作可能串起多个步骤。"],
      risks: ["任务状态不持久化。", "轮询简单直接，但不如 websocket。"],
      refs: ["llm_wiki/dashboard_api.py", "llm_wiki/dashboard_static/app.js"]
    },
    {
      title: "eval",
      purpose: "给 retrieval 和 QA 提供可重复的评测口径。",
      inputsOutputs: ["输入：DuReader 数据集、本地配置、profile", "输出：outputs/evals/*.json|md"],
      implementation: ["eval-dureader 输出 MRR@10 和 Recall@K，支持 ablation。", "eval-dureader-qa 支持 faithfulness、answer relevance、retry 和 fallback。", "报告全部落盘，便于复盘。"],
      interviewAngles: ["为什么 retrieval 是主证据。", "为什么 QA 需要 fallback。"],
      risks: ["retrieval 不是 full-corpus online retrieval。", "QA 最新报告用了 historical_report_fallback。"],
      refs: ["llm_wiki/eval_dureader.py", "outputs/evals/"]
    }
  ],
  evidence: {
    retrievalMetrics: [
      { name: "MRR@10", baseline: 0.4121, hybridNoRerank: 0.5048, hybridRerank: 0.7097, takeaway: "hybrid_rerank 相比 baseline 提升约 72.2%。" },
      { name: "Recall@1", baseline: 0.2824, hybridNoRerank: 0.3396, hybridRerank: 0.5857, takeaway: "头部命中显著提升，说明 rerank 对前排排序帮助很大。" },
      { name: "Recall@10", baseline: 0.7637, hybridNoRerank: 0.8681, hybridRerank: 0.9505, takeaway: "前 10 覆盖率很高，适合支撑上层问答。" }
    ],
    qaMetrics: [
      { title: "历史有效 QA 报告", body: "2026-04-10 13:48:44 的报告完成了 183/200 个样本评分，Faithfulness=0.8745，Answer Relevance=0.8773。", status: "辅助证据", refs: ["outputs/evals/dureader_qa/20260410-134844-dureader-dev-qa.json"] },
      { title: "最新 QA 报告边界", body: "2026-04-10 15:15:06 的最新报告因为连接错误而全部跳过，最终使用 historical_report_fallback 回填分数。", status: "必须主动说明", refs: ["outputs/evals/dureader_qa/20260410-151506-dureader-dev-qa.json"] }
    ],
    proofCards: [
      { title: "Compile Manifest 增量编译", claim: "已实现真正的增量跳过。", proof: "compiler.py 中维护 .compile_manifest.json，fingerprint 由 file_hash、extractor_version、compile_prompt_version 组成。", whyItMatters: "体现了重复构建成本意识。", refs: ["llm_wiki/compiler.py", "wiki/.compile_manifest.json"] },
      { title: "多模态 Ingest", claim: "不是只有 md/txt，而是覆盖文档、图片、音视频。", proof: "ingest.py 对 pdf/docx/pptx/image/audio/video/html/json 都有 extractor 路由。", whyItMatters: "说明项目已经进入知识工程系统形态。", refs: ["llm_wiki/ingest.py"] },
      { title: "可降级检索策略", claim: "hybrid/rerank 不是脆弱的单一路径。", proof: "retrieve.py 中 embedding 或 rerank 不可用时会记录 degraded_reason 并自动降级。", whyItMatters: "体现系统鲁棒性。", refs: ["llm_wiki/retrieve.py", "llm_wiki/qa.py"] },
      { title: "Dashboard 是可用的操作台", claim: "任务、日志、结果都能在浏览器里看到。", proof: "dashboard_api.py 提供 job-group 与 operation 接口，前端围绕轮询和当前结果视图组织。", whyItMatters: "项目不是只靠命令行演示。", refs: ["llm_wiki/dashboard_api.py", "llm_wiki/dashboard_static/app.js"] }
    ],
    risks: [
      { title: "评测口径不是 full-corpus", body: "DuReader retrieval 是 positives + negatives 的 candidate-set ranking，用于快速比较 profile。" },
      { title: "Dashboard 任务状态是内存态", body: "Thread + 内存字典适合 demo 与 tooling，不适合生产级任务恢复。" },
      { title: "QA 最新报告用了 fallback", body: "可以讲评测框架与 gate，但不能把最新报告包装成在线跑分成功。" },
      { title: "knowledge_map 不是图数据库", body: "当前更像跨文档总结与浏览层，而不是严格实体关系存储。" }
    ],
    roadmap: [
      "让 chunk_index 真正接入检索主链路。",
      "把 dashboard 升级成持久化任务队列。",
      "让 QA 评测稳定在线跑分，并区分 RAGAS、LLM judge、fallback 来源。",
      "把 knowledge_map 升级成更清晰的实体、关系、证据结构。"
    ],
    refs: [
      "outputs/evals/dureader_retrieval/20260410-002623-dureader-dev.json",
      "outputs/evals/dureader_qa/20260410-134844-dureader-dev-qa.json",
      "outputs/evals/dureader_qa/20260410-151506-dureader-dev-qa.json",
      "README.md"
    ]
  },
  graph: {
    nodes: [
      { id: "goal", label: "项目目标", group: "goal", x: 17, y: 20, summary: "把原始资料沉淀成可读、可用、可追溯的本地知识资产。", talkingPoints: ["它解决的是知识工程问题，不只是聊天。", "主线是先沉淀知识，再回答问题。"], refs: ["README.md"] },
      { id: "raw", label: "raw 层", group: "pipeline", x: 30, y: 32, summary: "原始资料入口层。", talkingPoints: ["raw 保存原始输入，便于追溯。", "它是 compile-first 的起点。"], refs: ["raw/", "README.md"] },
      { id: "ingest", label: "Ingest", group: "pipeline", x: 42, y: 18, summary: "统一多格式输入，全部转成 markdown。", talkingPoints: ["多模态入口是项目的重要卖点。", "Vision OCR 和 ASR fallback 是常见追问点。"], refs: ["llm_wiki/ingest.py"] },
      { id: "compile", label: "Compile", group: "pipeline", x: 52, y: 39, summary: "把 raw source 编译成结构化 wiki 页面。", talkingPoints: ["这是与传统 chunk-first RAG 最大的差异点。", "manifest 机制体现工程优化意识。"], refs: ["llm_wiki/compiler.py"] },
      { id: "index", label: "Index & Map", group: "pipeline", x: 62, y: 20, summary: "生成 index、knowledge_map 与 chunk_index。", talkingPoints: ["knowledge_map 是 synthesis，不是图数据库。", "chunk_index 是后续扩展口。"], refs: ["wiki/index.md", "wiki/knowledge_map.md", "wiki/chunk_index.jsonl"] },
      { id: "retrieve", label: "Retrieve", group: "pipeline", x: 73, y: 37, summary: "按 profile 执行 lexical、hybrid 或 rerank 检索。", talkingPoints: ["回答为什么不用向量库时，这个节点最关键。", "自动降级体现鲁棒性。"], refs: ["llm_wiki/retrieve.py"] },
      { id: "ask", label: "Ask", group: "pipeline", x: 86, y: 20, summary: "根据 wiki context 生成带引用的答案。", talkingPoints: ["回答受 wiki context 约束。", "引用页面是降低幻觉的重要手段。"], refs: ["llm_wiki/qa.py", "outputs/"] },
      { id: "eval", label: "Eval", group: "ops", x: 67, y: 63, summary: "检索与 QA 都有评测输出。", talkingPoints: ["retrieval 是主证据，QA 是辅助证据。", "一定要主动说明 candidate-set ranking 和 fallback。"], refs: ["llm_wiki/eval_dureader.py", "outputs/evals/"] },
      { id: "dashboard", label: "Dashboard", group: "ops", x: 46, y: 63, summary: "FastAPI + 静态前端构成操作台。", talkingPoints: ["说明你考虑了操作闭环。", "也要承认当前不是持久化任务队列。"], refs: ["llm_wiki/dashboard_api.py", "llm_wiki/dashboard_static/"] },
      { id: "evidence", label: "检索指标", group: "evidence", x: 84, y: 58, summary: "hybrid_rerank 的 MRR@10=0.7097，是当前最强证据。", talkingPoints: ["要能讲清 baseline、hybrid、rerank 的对比。", "记住这是 candidate-set ranking。"], refs: ["outputs/evals/dureader_retrieval/20260410-002623-dureader-dev.json"] },
      { id: "risk", label: "风险边界", group: "risk", x: 26, y: 67, summary: "QA fallback、内存态任务、非 full-corpus 评测，是必须主动交代的边界。", talkingPoints: ["主动承认边界，比被指出更好。", "边界不削弱项目，反而说明你理解系统位置。"], refs: ["outputs/evals/dureader_qa/20260410-151506-dureader-dev-qa.json"] },
      { id: "roadmap", label: "下一步", group: "roadmap", x: 52, y: 82, summary: "chunk 检索、持久化任务、稳定 QA 跑分、真正图结构，是自然扩展路径。", talkingPoints: ["roadmap 要从现有代码自然延伸。", "不要跳成完全不同的系统。"], refs: ["README.md", "wiki/chunk_index.jsonl"] }
    ],
    edges: [
      { from: "goal", to: "raw", label: "先积累资料" },
      { from: "raw", to: "ingest", label: "抽取标准化" },
      { from: "ingest", to: "compile", label: "进入编译" },
      { from: "compile", to: "index", label: "建索引和知识地图" },
      { from: "index", to: "retrieve", label: "为检索提供语料" },
      { from: "retrieve", to: "ask", label: "生成回答上下文" },
      { from: "retrieve", to: "eval", label: "被检索评测" },
      { from: "ask", to: "eval", label: "被 QA 评测" },
      { from: "dashboard", to: "ingest", label: "可视化操作" },
      { from: "dashboard", to: "compile", label: "任务中心" },
      { from: "dashboard", to: "ask", label: "结果预览" },
      { from: "eval", to: "evidence", label: "形成主证据" },
      { from: "risk", to: "roadmap", label: "驱动演进" },
      { from: "evidence", to: "roadmap", label: "决定优化方向" }
    ]
  },
  qaBank: [
    {
      category: "项目定位",
      questions: [
        { q: "这个项目一句话怎么讲？", fast: "一个 compile-first 的本地多模态知识库系统。", full: ["先 ingest 多模态资料，再 compile 成 wiki，随后做检索、问答、评测和 dashboard。", "核心不是聊天，而是把知识沉淀成结构化资产。"], followUps: ["为什么不直接叫 RAG 平台？", "最适合什么场景？"], pitfalls: ["不要讲成生产级 AI 平台。"], refs: ["README.md", "llm_wiki/cli.py"] },
        { q: "它和传统 RAG 最大区别是什么？", fast: "传统 RAG 是 chunk-first，这个项目是 compile-first。", full: ["传统 RAG 常见链路是切 chunk、向量检索、拼 prompt。", "这个项目先把原始资料编译成 wiki，再围绕 wiki 做检索和回答。"], followUps: ["这样做的好处和代价是什么？"], pitfalls: ["不要说自己的方案全面优于传统 RAG。"], refs: ["README.md", "llm_wiki/compiler.py"] },
        { q: "为什么不用向量数据库？", fast: "当前目标是中小规模、高可解释性和本地知识治理。", full: ["项目不是没有语义检索，而是不把系统重心建立在向量库上。", "当前规模下 compile-first 的知识整理价值更高，后续可再引入更重的检索后端。"], followUps: ["那现在的 hybrid 是什么？"], pitfalls: ["不要表现成因为不会用向量库所以没上。"], refs: ["llm_wiki/retrieve.py", "README.md"] }
      ]
    },
    {
      category: "架构与实现",
      questions: [
        { q: "多模态 ingest 是怎么做的？", fast: "按扩展名路由 extractor，统一输出 markdown。", full: ["文本类直接读，JSON pretty print，HTML 转 markdown。", "PDF 用 pdfplumber + Vision OCR fallback，音视频用 ffmpeg + ASR。"], followUps: ["为什么统一转 markdown？"], pitfalls: ["不要只说支持多格式，要说统一输出和 fallback。"], refs: ["llm_wiki/ingest.py"] },
        { q: "增量编译怎么做的？", fast: "通过 compile manifest 和 fingerprint 跳过未变化文件。", full: ["fingerprint = file_hash + extractor_version + compile_prompt_version。", "manifest 记录目标页和更新时间，未变化时直接跳过。"], followUps: ["为什么 prompt 变更也要重编译？"], pitfalls: ["不要把它说成只判断目标文件是否存在。"], refs: ["llm_wiki/compiler.py"] },
        { q: "retrieval profile 的区别是什么？", fast: "baseline 只 lexical，hybrid 多 embedding，hybrid_rerank 再加 rerank。", full: ["baseline 最稳，hybrid 补语义召回，hybrid_rerank 进一步优化候选排序。", "服务不可用时会自动降级并记录原因。"], followUps: ["为什么要保留 lexical？"], pitfalls: ["要主动讲 degrade 逻辑。"], refs: ["llm_wiki/retrieve.py"] },
        { q: "Dashboard 的任务模型是什么？", fast: "FastAPI + 线程 + 内存态 job/group 状态 + 前端轮询。", full: ["一次操作创建 job group，再由线程执行具体 runner。", "状态和日志在内存里维护，前端通过 API 轮询。"], followUps: ["为什么没上 Celery？"], pitfalls: ["不要把它包装成生产级调度系统。"], refs: ["llm_wiki/dashboard_api.py", "llm_wiki/dashboard_static/app.js"] }
      ]
    },
    {
      category: "评测与风险",
      questions: [
        { q: "你用什么证明检索优化有效？", fast: "用 DuReader retrieval 的 candidate-set ranking 做 ablation。", full: ["同一数据集上比较 baseline、hybrid_no_rerank、hybrid_rerank。", "MRR@10 从 0.4121 提升到 0.7097，Recall@1 从 0.2824 提升到 0.5857。"], followUps: ["为什么说这不是 full-corpus retrieval？"], pitfalls: ["不能省略 candidate-set 这个限定词。"], refs: ["outputs/evals/dureader_retrieval/20260410-002623-dureader-dev.json"] },
        { q: "QA 质量评测怎么讲？", fast: "讲框架和 gate 可以，但最新报告 fallback 必须主动承认。", full: ["项目里有独立的 eval-dureader-qa，支持 Faithfulness 和 Answer Relevance。", "历史报告有 183 个样本完成评分并通过 gate，但最新一版因为连接错误而使用了 historical_report_fallback。"], followUps: ["为什么还保留 fallback？"], pitfalls: ["不要说 QA 已稳定达标。"], refs: ["outputs/evals/dureader_qa/20260410-134844-dureader-dev-qa.json", "outputs/evals/dureader_qa/20260410-151506-dureader-dev-qa.json"] },
        { q: "如果线上化你会怎么改？", fast: "先补任务持久化和 chunk 级检索，再升级 QA 评测和图结构。", full: ["任务层引入持久化队列。", "检索层把 chunk_index 接入主链路，必要时再引入更专业后端。", "评测层把 fallback 降为兜底，而不是主要结果来源。"], followUps: ["你会先改 retrieval 还是 dashboard？"], pitfalls: ["roadmap 必须从现有代码自然延伸。"], refs: ["wiki/chunk_index.jsonl", "llm_wiki/dashboard_api.py"] }
      ]
    }
  ],
  drills: {
    thirtySeconds: ["这是一个 compile-first 的本地多模态知识库项目。", "核心链路是 ingest -> compile -> index -> retrieve -> ask。", "它和传统 RAG 的区别是先沉淀知识，再基于 wiki 回答。"],
    sixtySeconds: ["我把项目定义成 compile-first 的本地知识库，而不是聊天 demo。", "系统支持多模态 ingest、增量 compile、三档 retrieval profile、问答回灌、DuReader 评测和 FastAPI dashboard。", "最强证据是 hybrid_rerank 的 MRR@10 从 0.4121 提升到 0.7097，同时我也会主动说明 QA fallback 和任务模型边界。"],
    threeMinutes: ["问题定义：传统 RAG 重检索、轻治理。", "设计选择：先 raw -> ingest -> compile -> wiki，再 build-index、retrieve、ask。", "关键实现：多模态 ingest、manifest、hybrid/rerank、dashboard。", "结果与边界：retrieval 指标显著提升，但 QA 最新报告用了 fallback。"],
    rememberNumbers: ["有效 retrieval 样本：910 / 1000。", "baseline MRR@10 = 0.4121。", "hybrid_no_rerank MRR@10 = 0.5048。", "hybrid_rerank MRR@10 = 0.7097。", "历史有效 QA 报告：183 / 200 样本，Faithfulness = 0.8745，Answer Relevance = 0.8773。"],
    checklist: ["能在 15 秒内说出 compile-first 定位。", "能按顺序讲主流程。", "能说明三档 retrieval profile 和降级逻辑。", "能解释 fingerprint 的组成。", "能主动承认 QA fallback 和内存态任务模型。", "能背出至少两个关键数字。"],
    pressureQuestions: [
      { title: "如果面试官说这只是 prompt 包装项目？", answer: "反击点是：不是只靠 prompt。项目有多模态 ingest、增量 compile、检索 profile、评测报告、dashboard 和文件化知识资产。" },
      { title: "如果面试官质疑为什么没有向量库？", answer: "回答要落在场景和阶段：当前目标是中小规模、高可解释性与本地知识治理；检索上已经有 embedding 融合和 rerank。" },
      { title: "如果面试官追问 QA 最新报告为什么是 fallback？", answer: "先承认，再转化：说明框架已支持 retry 和 fallback，这次是连接错误导致跳过，所以 retrieval ablation 才是主证据。" }
    ],
    finishLine: "最后只背五件事：定位、主流程、三档检索、两组关键数字、两个风险边界。"
  },
  sourceLegend: [
    "README.md",
    "llm_wiki/cli.py",
    "llm_wiki/ingest.py",
    "llm_wiki/compiler.py",
    "llm_wiki/retrieve.py",
    "llm_wiki/qa.py",
    "llm_wiki/dashboard_api.py",
    "outputs/evals/dureader_retrieval/20260410-002623-dureader-dev.json",
    "outputs/evals/dureader_qa/20260410-134844-dureader-dev-qa.json",
    "outputs/evals/dureader_qa/20260410-151506-dureader-dev-qa.json"
  ]
};
