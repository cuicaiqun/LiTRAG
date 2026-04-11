(function () {
  const data = window.INTERVIEW_KIT_DATA;
  const pageId = document.body.dataset.page || "index";
  const page = data.pages.find((item) => item.id === pageId) || data.pages[0];
  const chrome = document.getElementById("chrome");
  const content = document.getElementById("content");

  document.title = `${page.nav} | ${data.meta.projectName}`;

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
      element.className = className;
    }
    if (text !== undefined) {
      element.textContent = text;
    }
    return element;
  }

  function appendList(parent, items, ordered = false) {
    const list = node(ordered ? "ol" : "ul");
    items.forEach((item) => {
      const li = node("li");
      if (typeof item === "string") {
        li.textContent = item;
      } else {
        li.append(item);
      }
      list.append(li);
    });
    parent.append(list);
    return list;
  }

  function renderRefs(refs) {
    const wrap = node("div", "ref-strip");
    refs.forEach((ref) => wrap.append(node("span", "ref-pill", ref)));
    return wrap;
  }

  function renderTags(items) {
    const wrap = node("div", "tag-strip");
    items.forEach((item) => wrap.append(node("span", "tag", item)));
    return wrap;
  }

  function section(kicker, title, summary) {
    const panel = node("section", "section-panel fade-in");
    const head = node("div", "section-head");
    const left = node("div");
    left.append(node("p", "eyebrow", kicker));
    left.append(node("h2", "", title));
    if (summary) {
      left.append(node("p", "sub-copy", summary));
    }
    head.append(left);
    panel.append(head);
    return panel;
  }

  function renderChrome() {
    chrome.className = "chrome";

    const brand = node("section", "brand-stage fade-in");
    const brandGrid = node("div", "brand-grid");
    const copy = node("div", "brand-copy");
    copy.append(node("p", "eyebrow", `${data.meta.position} / ${data.meta.tone}`));
    copy.append(node("h1", "", data.meta.projectName));
    copy.append(node("p", "", data.meta.summary));
    const meta = node("div", "hero-meta");
    meta.append(node("span", "meta-pill", `边界：${data.meta.truthBoundary}`));
    meta.append(node("span", "meta-pill", `日期：${data.meta.generatedDate}`));
    meta.append(node("span", "meta-pill", `仓库：${data.meta.repoName}`));
    copy.append(meta);

    const mini = node("aside", "mini-board");
    mini.append(node("h3", "", "当前页面目标"));
    appendList(mini, [page.title, page.summary, "所有页面共用一份共享数据源，保证话术一致。"]);
    brandGrid.append(copy, mini);
    brand.append(brandGrid);

    const nav = node("nav", "chapter-nav fade-in");
    data.pages.forEach((item) => {
      const link = node("a", item.id === pageId ? "active" : "", item.nav);
      link.href = item.href;
      nav.append(link);
    });

    chrome.append(brand, nav);
  }

  function renderPageHero(title, summary, rightTitle, rightBullets) {
    const wrap = node("div", "page-intro fade-in");
    const left = node("article", "page-hero");
    left.append(node("p", "eyebrow", page.nav));
    left.append(node("h2", "", title));
    left.append(node("p", "", summary));

    const right = node("aside", "floating-card");
    right.append(node("h3", "", rightTitle));
    appendList(right, rightBullets);

    wrap.append(left, right);
    return wrap;
  }

  function renderIndex() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "先把项目讲对，再追求讲得漂亮",
        "首页的任务是锁定定位、主流程、最强证据和最危险边界。先把这四件事讲顺，后面页面才有价值。",
        "首页记忆法",
        ["先记一句话定位。", "再记主链路。", "再记三个最强卖点。", "最后记不能乱说的边界。"]
      )
    );

    const overview = section("Snapshot", "项目快照", "四张卡先钉住项目的基本判断。");
    const overviewGrid = node("div", "card-grid");
    data.home.overviewCards.forEach((item) => {
      const card = node("article", "summary-card");
      card.append(node("h3", "", item.title));
      card.append(node("p", "sub-copy", item.body));
      overviewGrid.append(card);
    });
    overview.append(overviewGrid);
    stack.append(overview);

    const pitch = section("Pitch", "一句话与三条主卖点", "首页只背能直接开口说的内容。");
    const pitchGrid = node("div", "double-grid");
    pitchGrid.style.gridTemplateColumns = "minmax(0, 1.1fr) minmax(320px, 0.9fr)";
    const left = node("article", "note-card");
    left.append(node("h3", "", data.quickPitch.resumeProjectName));
    left.append(node("div", "quote-block", data.quickPitch.oneLine));
    appendList(left, data.quickPitch.bullets);
    const right = node("article", "note-card");
    right.append(node("h3", "", "只讲三个亮点"));
    appendList(right, data.home.highlightCards.map((item) => `${item.title}：${item.body}`));
    pitchGrid.append(left, right);
    pitch.append(pitchGrid);
    stack.append(pitch);

    const flow = section("Flow", "主流程 7 步", "这套项目必须按链路讲。");
    const flowline = node("div", "flowline");
    data.architecture.flow.forEach((item, index) => {
      const row = node("div", "flow-step");
      row.append(node("div", "flow-index", `${index + 1}`));
      const body = node("div", "flow-body");
      body.append(node("h3", "", item.title));
      body.append(node("p", "", item.body));
      body.append(renderTags(item.tags));
      row.append(body);
      flowline.append(row);
    });
    flow.append(flowline);
    stack.append(flow);

    const learn = section("Path", "学习顺序与重点取舍", "先掌握主线，再补细节和问答。");
    const learnGrid = node("div", "path-grid");
    const study = node("article", "path-card");
    study.append(node("h3", "", "建议顺序"));
    appendList(study, data.home.studyPath, true);
    const must = node("article", "path-card");
    must.append(node("h3", "", "必须掌握"));
    appendList(must, data.home.mustKnow);
    const nice = node("article", "path-card");
    nice.append(node("h3", "", "知道更好"));
    appendList(nice, data.home.niceToKnow);
    learnGrid.append(study, must, nice);
    learn.append(learnGrid);
    stack.append(learn);

    const boundary = section("Boundary", "不能乱说的边界", "主动讲边界，风险最低。");
    const grid = node("div", "card-grid");
    [
      { title: "高风险表述", items: data.home.dontOverclaim },
      { title: "优先讲的证据", items: ["DuReader retrieval ablation", "Compile manifest", "多模态 ingest", "Dashboard 任务闭环"] },
      { title: "次级证据", items: ["QA 历史有效报告", "chunk_index 扩展口", "promote 回 wiki/qa"] }
    ].forEach((item) => {
      const card = node("article", "truth-card");
      card.append(node("h3", "", item.title));
      appendList(card, item.items);
      grid.append(card);
    });
    boundary.append(grid);
    boundary.append(node("div", "footer-note", "首页目标只有一个：把项目定位、主链路、证据和边界讲顺。"));
    stack.append(boundary);
    content.append(stack);
  }

  function renderResume() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "简历写法一定要短、硬、可追溯",
        "这一页解决项目标题怎么写、bullet 怎么压缩、口述怎么从简历自然展开。",
        "投递原则",
        ["项目名偏能力，不偏炫技。", "每条 bullet 至多两层信息。", "结果写指标，边界放到面试里说。"]
      )
    );

    const titles = section("Resume", "标题与一句话介绍", "项目标题不要写成论文名。");
    const titleGrid = node("div", "card-grid");
    [
      { title: "推荐标题 A", body: "LLM Wiki / Compile-First 本地多模态知识库系统" },
      { title: "推荐标题 B", body: "多模态本地 RAG 知识库与检索评测系统" },
      { title: "一句话介绍", body: data.quickPitch.oneLine }
    ].forEach((item) => {
      const card = node("article", "summary-card");
      card.append(node("h3", "", item.title));
      card.append(node("p", "sub-copy", item.body));
      titleGrid.append(card);
    });
    titles.append(titleGrid);
    stack.append(titles);

    const bullets = section("Bullets", "三条简历 Bullet", "每条 bullet 都要有动作、对象、结果。");
    const bulletCard = node("article", "note-card");
    appendList(bulletCard, data.quickPitch.bullets);
    bullets.append(bulletCard);
    stack.append(bullets);

    const star = section("STAR", "STAR 讲法", "从简历切到口述时最稳。");
    const starGrid = node("div", "card-grid");
    [
      ["S - 背景", data.quickPitch.star.situation],
      ["T - 任务", data.quickPitch.star.task],
      ["A - 行动", data.quickPitch.star.action],
      ["R - 结果", data.quickPitch.star.result]
    ].forEach(([title, body]) => {
      const card = node("article", "summary-card");
      card.append(node("h3", "", title));
      card.append(node("p", "sub-copy", body));
      starGrid.append(card);
    });
    star.append(starGrid);
    stack.append(star);

    const scripts = section("Scripts", "1 分钟与 3 分钟口述稿", "先用 1 分钟版起手，再按追问展开。");
    const grid = node("div", "drill-grid");
    const one = node("article", "script-card");
    one.append(node("h3", "", "1 分钟版"));
    appendList(one, data.quickPitch.sixtySec);
    const three = node("article", "script-card");
    three.append(node("h3", "", "3 分钟版"));
    appendList(three, data.quickPitch.threeMinute);
    grid.append(one, three);
    scripts.append(grid);
    stack.append(scripts);

    const avoid = section("Avoid", "简历与口述里的禁区", "很多项目不是做得不够，而是说得太虚。");
    const card = node("article", "risk-card");
    card.append(node("h3", "", "高风险表述"));
    appendList(card, data.home.dontOverclaim);
    card.append(renderRefs(data.sourceLegend.slice(0, 6)));
    avoid.append(card);
    stack.append(avoid);
    content.append(stack);
  }

  function renderArchitecture() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "把架构讲成一条完整的数据流，而不是一堆模块名",
        "这一页建立工程视角：入口层、知识加工层、检索问答层、评测运营层分别做什么，它们之间如何传数据。",
        "讲架构的顺序",
        ["先讲分层目的。", "再讲数据流和目录。", "然后讲 retrieval profile。", "最后讲为什么不是传统 RAG。"]
      )
    );

    const layers = section("Layers", "四层架构", "按职责分层讲，比按文件名堆叠更像工程师。");
    const layerGrid = node("div", "card-grid");
    data.architecture.layers.forEach((item) => {
      const card = node("article", "module-card");
      const labels = node("div", "label-row");
      labels.append(node("span", "label", item.focus));
      card.append(labels);
      card.append(node("h3", "", item.title));
      appendList(card, item.points);
      card.append(renderRefs(item.refs));
      layerGrid.append(card);
    });
    layers.append(layerGrid);
    stack.append(layers);

    const dirs = section("Dirs", "目录与命令面", "这部分适合回答代码组织和用户入口。");
    const dirGrid = node("div", "directory-grid");
    data.architecture.directories.forEach((item) => {
      const card = node("article", "directory-card");
      card.append(node("h3", "", item.title));
      card.append(node("p", "sub-copy", item.body));
      dirGrid.append(card);
    });
    dirs.append(dirGrid);

    const commandGrid = node("div", "command-grid");
    data.architecture.commands.forEach((item) => {
      const card = node("article", "command-card");
      card.append(node("h3", "", item.title));
      appendList(card, item.items.map((text) => node("span", "inline-code", text)));
      commandGrid.append(card);
    });
    dirs.append(commandGrid);
    stack.append(dirs);

    const retrieval = section("Profiles", "Retrieval Profile 讲法", "三档 profile 和降级逻辑是检索部分的核心。");
    const profileGrid = node("div", "card-grid");
    data.architecture.retrievalProfiles.forEach((item) => {
      const card = node("article", "summary-card");
      card.append(node("h3", "", item.name));
      card.append(node("p", "sub-copy", item.description));
      const box = node("div", "source-box");
      box.append(node("strong", "", "面试讲法"));
      box.append(node("p", "muted", item.whenToSay));
      box.append(node("strong", "", "注意"));
      box.append(node("p", "muted", item.caveat));
      card.append(box);
      profileGrid.append(card);
    });
    retrieval.append(profileGrid);
    stack.append(retrieval);

    const compare = section("Compare", "为什么它不是传统 RAG", "高频追问的稳定答案。");
    const table = node("table", "comparison-table");
    const head = node("thead");
    const headRow = node("tr");
    ["维度", "当前项目", "传统 RAG"].forEach((text) => headRow.append(node("th", "", text)));
    head.append(headRow);
    table.append(head);
    const body = node("tbody");
    data.architecture.compareTraditionalRag.forEach((item) => {
      const row = node("tr");
      row.append(node("td", "", item.axis));
      row.append(node("td", "", item.thisProject));
      row.append(node("td", "", item.traditional));
      body.append(row);
    });
    table.append(body);
    compare.append(table);
    compare.append(renderRefs(["README.md", "llm_wiki/compiler.py", "llm_wiki/retrieve.py"]));
    stack.append(compare);
    content.append(stack);
  }

  function renderModules() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "模块细节不是背源码，而是背职责、输入输出、关键实现和边界",
        "这一页适合二面或深挖环节。每个模块都按同一结构展开，回答时不容易乱。",
        "模块回答模板",
        ["先说职责。", "再说输入输出。", "再说关键实现。", "最后补一个边界或风险。"]
      )
    );

    const modules = section("Modules", "核心模块卡片", "下面每张卡都可以单独拿来回答追问。");
    const grid = node("div", "module-grid");
    data.modules.forEach((item) => {
      const card = node("article", "module-card");
      const labels = node("div", "label-row");
      labels.append(node("span", "label", "职责"));
      labels.append(node("span", "label secondary", "可追问"));
      card.append(labels);
      card.append(node("h3", "", item.title));

      const purpose = node("div", "source-box");
      purpose.append(node("strong", "", "模块职责"));
      purpose.append(node("p", "muted", item.purpose));
      card.append(purpose);

      const io = node("div", "source-box");
      io.append(node("strong", "", "输入 / 输出"));
      appendList(io, item.inputsOutputs);
      card.append(io);

      const impl = node("div", "source-box");
      impl.append(node("strong", "", "关键实现"));
      appendList(impl, item.implementation);
      card.append(impl);

      const angles = node("div", "source-box");
      angles.append(node("strong", "", "高频追问"));
      appendList(angles, item.interviewAngles);
      card.append(angles);

      const risk = node("div", "source-box");
      risk.append(node("strong", "", "边界 / 风险"));
      appendList(risk, item.risks);
      card.append(risk);
      card.append(renderRefs(item.refs));
      grid.append(card);
    });
    modules.append(grid);
    stack.append(modules);
    content.append(stack);
  }

  function renderEvidence() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "证据优先级必须分层：检索报告 > 工程亮点 > QA 辅助证据 > roadmap",
        "强证据和弱证据不能混在一起讲。这一页帮你决定什么先讲、什么后讲、什么只能讲边界。",
        "证据顺序",
        ["先讲 retrieval ablation。", "再讲工程实现。", "QA 只做辅助说明。", "roadmap 单独讲。"]
      )
    );

    const metrics = section("Metrics", "检索指标", "这些数字是当前最值得背的结果。");
    const grid = node("div", "stats-grid");
    data.evidence.retrievalMetrics.forEach((item) => {
      const card = node("article", "metric-card");
      card.append(node("h3", "", item.name));
      const table = node("div", "metric-table");
      [["baseline", item.baseline], ["hybrid_no_rerank", item.hybridNoRerank], ["hybrid_rerank", item.hybridRerank]].forEach(([label, value]) => {
        const row = node("div", "metric-row");
        row.append(node("div", "muted", `${label}: ${value.toFixed(4)}`));
        const track = node("div", "metric-track");
        const fill = node("div", "metric-fill");
        fill.style.width = `${Math.max(8, value * 100)}%`;
        track.append(fill);
        row.append(track);
        table.append(row);
      });
      card.append(table);
      card.append(node("p", "sub-copy", item.takeaway));
      grid.append(card);
    });
    metrics.append(grid);
    metrics.append(renderRefs(["outputs/evals/dureader_retrieval/20260410-002623-dureader-dev.json"]));
    stack.append(metrics);

    const qa = section("QA", "QA 评测怎么讲", "QA 不是不能讲，而是要准确讲。");
    const qaGrid = node("div", "card-grid");
    data.evidence.qaMetrics.forEach((item) => {
      const card = node("article", "risk-card");
      const labelRow = node("div", "label-row");
      labelRow.append(node("span", "label", item.status));
      card.append(labelRow);
      card.append(node("h3", "", item.title));
      card.append(node("p", "sub-copy", item.body));
      card.append(renderRefs(item.refs));
      qaGrid.append(card);
    });
    qa.append(qaGrid);
    stack.append(qa);

    const proofs = section("Proof", "工程亮点证据", "这些点能证明你做的是系统，而不是零散脚本。");
    const proofGrid = node("div", "proof-grid");
    data.evidence.proofCards.forEach((item) => {
      const card = node("article", "proof-card");
      card.append(node("h3", "", item.title));
      appendList(card, [`主张：${item.claim}`, `证据：${item.proof}`, `为什么重要：${item.whyItMatters}`]);
      card.append(renderRefs(item.refs));
      proofGrid.append(card);
    });
    proofs.append(proofGrid);
    stack.append(proofs);

    const risks = section("Risk", "风险与 Roadmap", "主动讲边界不会削弱项目。");
    const riskGrid = node("div", "risk-grid");
    data.evidence.risks.forEach((item) => {
      const card = node("article", "risk-card");
      card.append(node("h3", "", item.title));
      card.append(node("p", "sub-copy", item.body));
      riskGrid.append(card);
    });
    risks.append(riskGrid);
    const roadmap = node("article", "note-card");
    roadmap.append(node("h3", "", "下一步路线"));
    appendList(roadmap, data.evidence.roadmap);
    roadmap.append(renderRefs(data.evidence.refs));
    risks.append(roadmap);
    stack.append(risks);
    content.append(stack);
  }

  function renderGraph() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "知识图谱页不是炫图，而是帮你建立节点关联记忆",
        "点击图中的节点，右侧会显示这部分该怎么讲、关联什么证据、最容易被问什么。",
        "推荐顺序",
        ["项目目标", "raw -> ingest -> compile -> index -> retrieve -> ask", "Eval / Dashboard", "检索指标 / 风险边界 / 下一步"]
      )
    );

    const wrapper = section("Graph", "项目知识图谱", "主流程、证据、风险和 roadmap 在这里被串成一个整体。");
    const layout = node("div", "graph-layout");
    const stage = node("div", "graph-stage");
    const canvas = node("div", "graph-canvas");
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "graph-svg");
    canvas.append(svg);
    const detail = node("aside", "graph-detail");

    const colors = { goal: "#b24a35", pipeline: "#d1a245", ops: "#3e6487", evidence: "#4f6f5c", risk: "#7d4f7b", roadmap: "#8f2b18" };
    const getNode = (id) => data.graph.nodes.find((item) => item.id === id);

    function renderDetail(activeId) {
      const current = getNode(activeId) || data.graph.nodes[0];
      detail.innerHTML = "";
      detail.append(node("p", "eyebrow", "Graph Detail"));
      detail.append(node("h3", "", current.label));
      detail.append(node("p", "", current.summary));
      const points = node("div", "source-box");
      points.append(node("strong", "", "面试讲法"));
      appendList(points, current.talkingPoints);
      detail.append(points);
      const rel = node("div", "source-box");
      rel.append(node("strong", "", "关联关系"));
      const related = data.graph.edges
        .filter((edge) => edge.from === current.id || edge.to === current.id)
        .map((edge) => `${edge.label} -> ${edge.from === current.id ? getNode(edge.to).label : getNode(edge.from).label}`);
      appendList(rel, related.length ? related : ["当前节点没有额外关系。"]);
      detail.append(rel);
      detail.append(renderRefs(current.refs));
    }

    data.graph.edges.forEach((edge) => {
      const from = getNode(edge.from);
      const to = getNode(edge.to);
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("class", "edge-line");
      line.setAttribute("x1", `${from.x}%`);
      line.setAttribute("y1", `${from.y}%`);
      line.setAttribute("x2", `${to.x}%`);
      line.setAttribute("y2", `${to.y}%`);
      svg.append(line);
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("class", "edge-label");
      label.setAttribute("x", `${(from.x + to.x) / 2}%`);
      label.setAttribute("y", `${(from.y + to.y) / 2}%`);
      label.textContent = edge.label;
      svg.append(label);
    });

    data.graph.nodes.forEach((item, index) => {
      const button = node("button", "graph-node");
      button.type = "button";
      button.dataset.nodeId = item.id;
      button.style.left = `${item.x}%`;
      button.style.top = `${item.y}%`;
      button.style.setProperty("--node-color", colors[item.group] || "#b24a35");
      button.append(node("small", "", item.group));
      button.append(node("div", "graph-node-label", item.label));
      button.addEventListener("click", () => {
        canvas.querySelectorAll(".graph-node").forEach((n) => n.classList.remove("active"));
        button.classList.add("active");
        renderDetail(item.id);
      });
      if (index === 0) {
        button.classList.add("active");
      }
      canvas.append(button);
    });

    renderDetail(data.graph.nodes[0].id);
    stage.append(canvas);
    layout.append(stage, detail);
    wrapper.append(layout);
    stack.append(wrapper);
    content.append(stack);
  }

  function renderQa() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "面试问答页只做一件事：把你从知道内容，推进到能稳定开口",
        "建议先遮住完整回答，只看压缩版回答；能说出来后再补追问和坑点。",
        "练习方式",
        ["先读 fast。", "再补 full。", "最后用 pitfalls 检查过度包装。"]
      )
    );

    const qa = section("QA", "标准问答库", "优先练高频问题，不要试图一口气背完全部。");
    const grid = node("div", "qa-grid");
    data.qaBank.forEach((group, groupIndex) => {
      const card = node("article", "qa-category");
      const labels = node("div", "label-row");
      labels.append(node("span", "label", group.category));
      card.append(labels);
      card.append(node("h3", "", group.category));
      group.questions.forEach((item, index) => {
        const details = document.createElement("details");
        if (groupIndex === 0 && index === 0) {
          details.open = true;
        }
        const summary = document.createElement("summary");
        summary.append(node("span", "qa-question", item.q));
        summary.append(node("span", "tag", "点击展开"));
        details.append(summary);
        const answer = node("div", "qa-answer");
        answer.append(node("h4", "", "压缩版"));
        answer.append(node("p", "", item.fast));
        answer.append(node("h4", "", "标准回答"));
        appendList(answer, item.full);
        answer.append(node("h4", "", "深挖追问"));
        appendList(answer, item.followUps);
        answer.append(node("h4", "", "不要踩的坑"));
        appendList(answer, item.pitfalls);
        answer.append(renderRefs(item.refs));
        details.append(answer);
        card.append(details);
      });
      grid.append(card);
    });
    qa.append(grid);
    stack.append(qa);
    content.append(stack);
  }

  function renderDrills() {
    const stack = node("div", "page-stack");
    stack.append(
      renderPageHero(
        "最后一页负责压缩：把项目压成几套能在高压下开口的话术",
        "如果面试前只剩 10 分钟，按这页从上往下过一遍即可。所有内容都为稳定说出来服务。",
        "最后复习顺序",
        ["30 秒版", "1 分钟版", "关键数字", "检查清单", "高压问题"]
      )
    );

    const scripts = section("Drill", "三档口述稿", "不同时长用不同压缩率。");
    const grid = node("div", "drill-grid");
    [
      { title: "30 秒版", items: data.drills.thirtySeconds },
      { title: "1 分钟版", items: data.drills.sixtySeconds },
      { title: "3 分钟版", items: data.drills.threeMinutes }
    ].forEach((item) => {
      const card = node("article", "script-card");
      card.append(node("h3", "", item.title));
      appendList(card, item.items);
      grid.append(card);
    });
    scripts.append(grid);
    stack.append(scripts);

    const numbers = section("Numbers", "必须记住的数字", "不会背代码细节没关系，但关键数字必须开口就有。");
    const numCard = node("article", "check-card");
    appendList(numCard, data.drills.rememberNumbers);
    numbers.append(numCard);
    stack.append(numbers);

    const checklist = section("Checklist", "面试前 10 分钟检查单", "从头到尾过一遍。");
    const checkCard = node("article", "check-card");
    appendList(checkCard, data.drills.checklist);
    checklist.append(checkCard);
    stack.append(checklist);

    const pressure = section("Pressure", "高压问题应对", "越难的问题，越要缩回定位、取舍、边界。");
    const pressureGrid = node("div", "card-grid");
    data.drills.pressureQuestions.forEach((item) => {
      const card = node("article", "risk-card");
      card.append(node("h3", "", item.title));
      card.append(node("p", "sub-copy", item.answer));
      pressureGrid.append(card);
    });
    pressure.append(pressureGrid);
    pressure.append(node("div", "footer-note", data.drills.finishLine));
    stack.append(pressure);
    content.append(stack);
  }

  const renderers = {
    index: renderIndex,
    resume: renderResume,
    architecture: renderArchitecture,
    modules: renderModules,
    evidence: renderEvidence,
    graph: renderGraph,
    qa: renderQa,
    drills: renderDrills
  };

  renderChrome();
  (renderers[pageId] || renderIndex)();
})();
