const els = {
  summaryMeta: document.getElementById("summaryMeta"),
  totalJobs: document.getElementById("summaryTotalJobs"),
  runningJobs: document.getElementById("summaryRunningJobs"),
  failedJobs: document.getElementById("summaryFailedJobs"),
  completedJobs: document.getElementById("summaryCompletedJobs"),
  progressFill: document.getElementById("globalProgressFill"),
  progressText: document.getElementById("globalProgressText"),
  jobGroupList: document.getElementById("jobGroupList"),
  recommendationList: document.getElementById("recommendationList"),
  recentResultList: document.getElementById("recentResultList"),
  logStream: document.getElementById("logStream"),
  clearLogBtn: document.getElementById("clearLogBtn"),
  askAnswer: document.getElementById("askAnswer"),
  previewPath: document.getElementById("previewPath"),
  filePreview: document.getElementById("filePreview"),
  refreshBtn: document.getElementById("refreshBtn"),
  lastRefresh: document.getElementById("lastRefresh"),
  modelPill: document.getElementById("modelPill"),
  workspacePill: document.getElementById("workspacePill"),
  taskDrawerContent: document.getElementById("taskDrawerContent"),
  currentResultTitle: document.getElementById("currentResultTitle"),
  currentResultStatus: document.getElementById("currentResultStatus"),
  currentResultSummary: document.getElementById("currentResultSummary"),
  currentResultMeta: document.getElementById("currentResultMeta"),
  currentResultPath: document.getElementById("currentResultPath"),
  currentResultBody: document.getElementById("currentResultBody"),
};

const state = {
  overview: null,
  jobGroups: [],
  activeGroupId: null,
  activeGroupDetail: null,
  polling: new Set(),
  logKeys: new Map(),
};

const operationLabels = {
  init: "初始化工作区",
  admin: "管理任务",
  ingest: "入库",
  compile: "编译索引",
  index: "索引任务",
  "build-index": "重建索引",
  search: "搜索资料",
  ask: "向知识库提问",
};

const statusLabels = {
  idle: "待命",
  queued: "排队中",
  running: "进行中",
  completed: "已完成",
  error: "失败",
};

const ACTION_REQUEST_TIMEOUT_MS = 15000;

/* helpers */

function safeText(element, value) {
  if (element) {
    element.textContent = value ?? "";
  }
}

function createNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  return node;
}

function clamp(value, min = 0, max = 100) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return min;
  }
  return Math.max(min, Math.min(max, number));
}

function stripWrappingQuotes(value) {
  const text = String(value ?? "").trim();
  if (text.length >= 2) {
    const first = text[0];
    const last = text[text.length - 1];
    if ((first === `"` || first === `'`) && first === last) {
      return text.slice(1, -1).trim();
    }
  }
  return text;
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function formatTime(value) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function formatClockNow() {
  return new Date().toLocaleTimeString("zh-CN", { hour12: false });
}

function formatBytes(size) {
  if (!Number.isFinite(Number(size))) {
    return "--";
  }
  const value = Number(size);
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function setStatusBadge(element, status) {
  if (!element) {
    return;
  }
  element.className = `status-badge ${status || "idle"}`;
  element.textContent = statusLabels[status] || status || "未知";
}

function setProgress(percent = 0, message = "等待任务", status = "idle") {
  const value = clamp(percent);
  if (els.progressFill) {
    els.progressFill.style.width = `${value}%`;
    els.progressFill.classList.remove("done", "error");
    if (status === "completed") {
      els.progressFill.classList.add("done");
    }
    if (status === "error") {
      els.progressFill.classList.add("error");
    }
  }
  if (els.progressText) {
    els.progressText.textContent = `${value}% · ${message}`;
  }
}

function pushLog(text, level = "info") {
  if (!els.logStream || !text) {
    return;
  }
  const item = createNode("div", `log-item ${level}`);
  const ts = createNode("time", "", formatClockNow());
  const body = createNode("div", "", text);
  item.append(ts, body);
  els.logStream.prepend(item);
  while (els.logStream.childElementCount > 80) {
    els.logStream.removeChild(els.logStream.lastElementChild);
  }
}

async function fetchJson(url, options = {}, timeoutMs = 0) {
  const requestOptions = { ...options };
  let timerId = null;

  if (timeoutMs > 0) {
    const controller = new AbortController();
    requestOptions.signal = controller.signal;
    timerId = window.setTimeout(() => controller.abort(), timeoutMs);
  }

  try {
    const response = await fetch(url, requestOptions);
    const raw = await response.text();
    let data = {};

    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch {
        data = { message: raw };
      }
    }

    if (!response.ok) {
      throw new Error(data.detail || data.message || `请求失败 (${response.status})`);
    }

    return data;
  } catch (error) {
    if (error?.name === "AbortError") {
      const seconds = Math.max(1, Math.round(timeoutMs / 1000));
      throw new Error(`请求超时（${seconds} 秒），服务在创建任务时没有及时响应。`);
    }
    throw error;
  } finally {
    if (timerId !== null) {
      window.clearTimeout(timerId);
    }
  }
}

function getOperationKey(source) {
  if (!source) {
    return "";
  }
  if (source.operation) {
    return source.operation;
  }
  if (source.kind) {
    return source.kind;
  }
  return "";
}

function getOperationLabel(source) {
  const key = getOperationKey(source);
  return operationLabels[key] || "任务";
}

function getStatusText(status) {
  return statusLabels[status] || status || "未知";
}

function resolveResultPath(job) {
  const result = job?.result || {};
  if (result.output_path) {
    return result.output_path;
  }
  if (result.capture_path) {
    return result.capture_path;
  }
  if (Array.isArray(result.updated_paths) && result.updated_paths.length) {
    return result.updated_paths[0];
  }
  if (Array.isArray(result.compiled_paths) && result.compiled_paths.length) {
    return result.compiled_paths[0];
  }
  if (Array.isArray(result.created) && result.created.length) {
    return result.created[0].output_path || result.created[0].source_path || "";
  }
  return "";
}

function describeCompleted(job) {
  const operation = getOperationKey(job);
  const result = job?.result || {};
  if (operation === "ask") {
    return "回答已生成，并已回填到主屏结果区。";
  }
  if (operation === "search") {
    return typeof result.result_count === "number" ? `已保存 ${result.result_count} 条搜索结果。` : "搜索结果已保存。";
  }
  if (operation === "ingest") {
    return typeof result.ingested_count === "number" ? `已新增 ${result.ingested_count} 条入库内容。` : "入库已完成。";
  }
  if (operation === "compile" || operation === "build-index" || operation === "index") {
    const count = Array.isArray(result.updated_paths) ? result.updated_paths.length : 0;
    return count ? `索引已更新，共 ${count} 个文件。` : "索引任务已完成。";
  }
  return "任务已完成。";
}

function describeRunning(group, job) {
  const operation = getOperationKey(job || group);
  const progress = clamp(group?.progress ?? job?.progress ?? 0);

  if (group?.status === "queued" || job?.status === "queued") {
    return `${getOperationLabel(job || group)}已提交，正在排队。`;
  }
  if (operation === "ask") {
    return `正在检索知识并生成回答，当前进度 ${progress}%。`;
  }
  if (operation === "search") {
    return `正在抓取和整理搜索资料，当前进度 ${progress}%。`;
  }
  if (operation === "ingest") {
    return `正在读取来源并写入知识库，当前进度 ${progress}%。`;
  }
  if (operation === "compile" || operation === "build-index" || operation === "index") {
    return `正在编译文档并更新索引，当前进度 ${progress}%。`;
  }
  return `任务执行中，当前进度 ${progress}%。`;
}

function rawErrorHint(error) {
  if (!error) {
    return "";
  }
  if (/[A-Za-z0-9_:\\/.-]/.test(error)) {
    return error;
  }
  return "";
}

function buildResultBody(job, group) {
  if (!job) {
    return "当前还没有可展示的任务结果。";
  }

  const result = job.result || {};
  const status = group?.status || job.status || "idle";
  const lines = [];

  if (status === "error") {
    lines.push("任务执行失败。");
    const hint = rawErrorHint(job.error);
    if (hint) {
      lines.push("", hint);
    }
    lines.push("", "请打开日志抽屉或任务详情查看失败原因。");
    return lines.join("\n");
  }

  if (status === "queued" || status === "running") {
    lines.push(describeRunning(group, job));
    lines.push("", "任务区会持续刷新。完成后会自动刷新最近结果，并打开当前详情。");
    return lines.join("\n");
  }

  if (result.answer) {
    lines.push(String(result.answer).trim());
    if (Array.isArray(result.used_pages) && result.used_pages.length) {
      lines.push("", "引用页面：");
      result.used_pages.slice(0, 8).forEach((path) => lines.push(`- ${path}`));
    }
    if (result.retrieval_applied_profile || result.retrieval_requested_profile) {
      lines.push("", `检索策略：${result.retrieval_applied_profile || result.retrieval_requested_profile}`);
    }
    if (result.retrieval_degraded_reason) {
      lines.push(`降级原因：${result.retrieval_degraded_reason}`);
    }
    if (result.output_path) {
      lines.push(`输出文件：${result.output_path}`);
    }
    return lines.join("\n");
  }

  if (result.capture_path || typeof result.result_count === "number") {
    lines.push("搜索流程已完成。");
    if (typeof result.result_count === "number") {
      lines.push(`命中结果：${result.result_count}`);
    }
    if (result.capture_path) {
      lines.push(`抓取文件：${result.capture_path}`);
    }
    if (typeof result.compiled_count === "number") {
      lines.push(`新增编译：${result.compiled_count}`);
    }
    if (Array.isArray(result.updated_paths) && result.updated_paths.length) {
      lines.push("", "更新索引：");
      result.updated_paths.slice(0, 6).forEach((path) => lines.push(`- ${path}`));
    }
    return lines.join("\n");
  }

  if (typeof result.ingested_count === "number" || Array.isArray(result.created)) {
    lines.push("入库流程已完成。");
    if (typeof result.ingested_count === "number") {
      lines.push(`新入库：${result.ingested_count}`);
    }
    if (typeof result.skipped_existing === "number") {
      lines.push(`跳过已有：${result.skipped_existing}`);
    }
    if (typeof result.skipped_unsupported === "number") {
      lines.push(`跳过不支持：${result.skipped_unsupported}`);
    }
    if (typeof result.compiled_count === "number") {
      lines.push(`后续编译：${result.compiled_count}`);
    }
    if (Array.isArray(result.errors) && result.errors.length) {
      lines.push(`错误数：${result.errors.length}`);
    }
    if (Array.isArray(result.created) && result.created.length) {
      lines.push("", "已生成：");
      result.created.slice(0, 6).forEach((item) => {
        lines.push(`- ${item.output_path || item.source_path || JSON.stringify(item)}`);
      });
    }
    return lines.join("\n");
  }

  if (typeof result.compiled_count === "number" || Array.isArray(result.compiled_paths) || Array.isArray(result.updated_paths)) {
    lines.push("索引任务已完成。");
    if (typeof result.compiled_count === "number") {
      lines.push(`编译文档：${result.compiled_count}`);
    }
    if (Array.isArray(result.compiled_paths) && result.compiled_paths.length) {
      lines.push("", "编译输出：");
      result.compiled_paths.slice(0, 6).forEach((path) => lines.push(`- ${path}`));
    }
    if (Array.isArray(result.updated_paths) && result.updated_paths.length) {
      lines.push("", "索引文件：");
      result.updated_paths.slice(0, 6).forEach((path) => lines.push(`- ${path}`));
    }
    return lines.join("\n");
  }

  return job.result_preview || job.message || describeCompleted(job);
}

/* rendering */

function buildCurrentViewFromGroup(payload, chosenJob) {
  const group = payload?.group || {};
  const job = chosenJob || payload?.jobs?.[0] || payload?.primary_job || null;
  const status = group.status || job?.status || "idle";
  const summary =
    status === "completed"
      ? describeCompleted(job)
      : status === "error"
        ? "任务执行失败，请查看日志或当前详情。"
        : describeRunning(group, job);

  const metaParts = [getStatusText(status)];
  if (group.progress !== undefined) {
    metaParts.push(`进度 ${clamp(group.progress)}%`);
  }
  if (group.counts?.total) {
    metaParts.push(`任务数 ${group.counts.total}`);
  }
  if (job?.updated_at || group.updated_at) {
    metaParts.push(`更新时间 ${formatTime(job?.updated_at || group.updated_at)}`);
  }

  return {
    title: getOperationLabel(job || group),
    status,
    summary,
    meta: metaParts.join(" / "),
    path: resolveResultPath(job),
    body: buildResultBody(job, group),
    answer: job?.result?.answer || "",
    raw: job?.result || {},
    group,
    job,
  };
}

function buildCurrentViewFromRecent(item) {
  return {
    title: item?.name || "最近结果",
    status: "completed",
    summary: "来自 outputs 目录的最近结果文件。",
    meta: `更新时间 ${item?.mtime || "--"} / 大小 ${formatBytes(item?.size)}`,
    path: item?.path || "",
    body: [
      `文件名：${item?.name || "--"}`,
      `更新时间：${item?.mtime || "--"}`,
      `文件大小：${formatBytes(item?.size)}`,
      "",
      "当前页面没有直接读取文件正文，如需完整内容请打开该文件。",
    ].join("\n"),
    answer: "",
    raw: item || {},
    group: null,
    job: null,
  };
}

function renderCurrentResult(view) {
  setStatusBadge(els.currentResultStatus, view?.status || "idle");
  safeText(els.currentResultTitle, view?.title || "提交任务后，这里会直接显示结果");
  safeText(els.currentResultSummary, view?.summary || "当前没有正在查看的任务。");
  safeText(els.currentResultMeta, view?.meta || "右侧任务区会保持最新任务组列表。");
  safeText(els.currentResultPath, view?.path ? `结果路径：${view.path}` : "还没有生成结果路径。");
  safeText(els.currentResultBody, view?.body || "当前还没有可展示的结果。");
}

function renderDetailDrawer(view, payload) {
  safeText(els.previewPath, view?.path ? `结果路径：${view.path}` : "当前任务还没有结果路径。");

  const lines = [];
  if (view?.group?.id) {
    lines.push(`任务组 ID：${view.group.id}`);
  }
  if (view?.job?.id) {
    lines.push(`任务 ID：${view.job.id}`);
  }
  if (view?.title) {
    lines.push(`任务名称：${view.title}`);
  }
  if (view?.status) {
    lines.push(`任务状态：${getStatusText(view.status)}`);
  }
  if (view?.group?.progress !== undefined) {
    lines.push(`任务进度：${clamp(view.group.progress)}%`);
  }
  if (view?.job?.duration_ms) {
    lines.push(`耗时：${view.job.duration_ms} ms`);
  }

  const raw = payload?.primary_job?.result || view?.raw || {};
  const rawText = raw && Object.keys(raw).length ? JSON.stringify(raw, null, 2) : "暂无结构化结果。";
  safeText(els.filePreview, `${lines.join("\n")}\n\n${rawText}`.trim());
  safeText(els.askAnswer, view?.answer || view?.body || "暂无回答。");
}

function renderEmptyCurrentResult() {
  renderCurrentResult({
    title: "提交任务后，这里会直接显示结果",
    status: "idle",
    summary: "当前没有正在查看的任务。",
    meta: "主屏结果区会跟随当前任务持续更新。",
    path: "",
    body: "回答、搜索结果、编译结果和入库摘要都会直接回填到这里。",
  });
  safeText(els.previewPath, "尚未选择内容");
  safeText(els.filePreview, "暂无结构化结果");
  safeText(els.askAnswer, "暂无回答");
}

function updateSummary(groups) {
  const total = groups.length;
  const running = groups.filter((item) => item.status === "running" || item.status === "queued").length;
  const failed = groups.filter((item) => item.status === "error").length;
  const completed = groups.filter((item) => item.status === "completed").length;

  safeText(els.totalJobs, total);
  safeText(els.runningJobs, running);
  safeText(els.failedJobs, failed);
  safeText(els.completedJobs, completed);

  const focusGroup =
    (state.activeGroupDetail?.group && groups.find((item) => item.id === state.activeGroupDetail.group.id)) ||
    groups.find((item) => item.id === state.activeGroupId) ||
    groups.find((item) => item.status === "running" || item.status === "queued") ||
    groups[0] ||
    null;

  safeText(
    els.summaryMeta,
    total
      ? `真实任务组统计 / 索引更新 ${state.overview?.status?.index_updated || "N/A"}`
      : `索引更新 ${state.overview?.status?.index_updated || "N/A"}`
  );

  if (!focusGroup) {
    setProgress(0, "暂无任务组，等待新的提交", "idle");
    return;
  }

  const label = getOperationLabel(focusGroup);
  const message =
    focusGroup.status === "completed"
      ? `${label} 已完成`
      : focusGroup.status === "error"
        ? `${label} 执行失败`
        : `${label} 正在执行`;
  setProgress(focusGroup.progress ?? 0, message, focusGroup.status || "idle");
}

function renderRecommendations(groups) {
  if (!els.recommendationList) {
    return;
  }

  const suggestions = [];
  const running = groups.filter((item) => item.status === "running" || item.status === "queued");
  const failed = groups.filter((item) => item.status === "error");

  if (running.length) {
    suggestions.push(`有 ${running.length} 个任务组正在执行，优先关注当前任务结果和右侧任务区。`);
  }
  if (failed.length) {
    suggestions.push(`有 ${failed.length} 个任务组失败，建议打开当前详情或日志抽屉定位问题。`);
  }
  if (state.overview?.recent?.outputs?.length) {
    suggestions.push("最近结果列表会在任务完成后自动刷新，可以直接点击查看最新输出。");
  }
  if (!groups.length) {
    suggestions.push("首次使用建议按“入库 → 编译索引 → 向知识库提问”的顺序执行。");
  }
  if (!suggestions.length) {
    suggestions.push("当前没有需要处理的阻塞项，可以继续提问或检查最近结果。");
  }

  els.recommendationList.innerHTML = "";
  suggestions.slice(0, 3).forEach((text) => {
    els.recommendationList.append(createNode("li", "", text));
  });
}

function renderRecentResults(items) {
  if (!els.recentResultList) {
    return;
  }

  els.recentResultList.innerHTML = "";
  if (!items?.length) {
    els.recentResultList.append(createNode("li", "empty-item", "暂无结果"));
    return;
  }

  items.forEach((item) => {
    const row = createNode("li", "clickable-item");
    const button = createNode("button", "list-button");
    button.append(
      createNode("span", "list-title", item.name || "未命名结果"),
      createNode("span", "list-meta", `${item.mtime || "--"} / ${formatBytes(item.size)}`)
    );
    button.addEventListener("click", () => {
      const view = buildCurrentViewFromRecent(item);
      renderCurrentResult(view);
      renderDetailDrawer(view, { primary_job: { result: item } });
      openDrawer("detailDrawer");
      activatePanel("command-center-panel");
    });
    row.append(button);
    els.recentResultList.append(row);
  });
}

function createTaskCard(group) {
  const button = createNode("button", `task-card${group.id === state.activeGroupId ? " active" : ""}`);
  button.type = "button";

  const head = createNode("div", "task-card-head");
  const badge = createNode("span", "status-badge");
  setStatusBadge(badge, group.status || "idle");
  head.append(createNode("strong", "", getOperationLabel(group)), badge);

  const summary =
    group.status === "completed"
      ? "已完成，可查看当前详情。"
      : group.status === "error"
        ? "执行失败，建议打开日志。"
        : group.status === "queued"
          ? "已提交，等待执行。"
          : `进行中，当前进度 ${clamp(group.progress)}%。`;

  button.append(
    head,
    createNode("p", "task-card-summary", summary),
    createNode("div", "task-card-foot", `${clamp(group.progress)}% / ${group.counts?.total || 0} 个任务 / ${group.counts?.running || 0} 进行中`)
  );

  button.addEventListener("click", async () => {
    await inspectGroup(group.id, { openTaskDrawer: true });
  });

  return button;
}

function renderJobGroups(groups) {
  if (!els.jobGroupList) {
    return;
  }

  els.jobGroupList.innerHTML = "";
  if (!groups.length) {
    els.jobGroupList.append(createNode("div", "task-empty", "当前还没有任务组"));
    return;
  }

  groups.forEach((group) => {
    els.jobGroupList.append(createTaskCard(group));
  });
}

function renderTaskDrawer(payload) {
  if (!els.taskDrawerContent) {
    return;
  }

  els.taskDrawerContent.innerHTML = "";

  const group = payload?.group;
  const jobs = payload?.jobs || [];
  if (!group) {
    els.taskDrawerContent.append(createNode("div", "task-empty", "选择右侧任务组查看详情"));
    return;
  }

  const view = buildCurrentViewFromGroup(payload);
  const summarySection = createNode("section", "drawer-section");
  const progressTrack = createNode("div", "progress-track");
  const progressFill = createNode("div", "progress-fill");
  progressFill.style.width = `${clamp(group.progress)}%`;
  if (group.status === "completed") {
    progressFill.classList.add("done");
  }
  if (group.status === "error") {
    progressFill.classList.add("error");
  }
  progressTrack.append(progressFill);
  summarySection.append(
    createNode("h4", "drawer-section-title", getOperationLabel(view.job || group)),
    createNode("p", "drawer-section-meta", `${getStatusText(group.status)} / 进度 ${clamp(group.progress)}% / 更新时间 ${formatTime(group.updated_at)}`),
    createNode("p", "drawer-section-summary", view.summary),
    progressTrack
  );

  const jobsSection = createNode("section", "drawer-section");
  jobsSection.append(createNode("h4", "drawer-section-title", "任务列表"));

  if (!jobs.length) {
    jobsSection.append(createNode("div", "task-empty", "当前任务组还没有子任务。"));
  } else {
    const list = createNode("div", "job-detail-list");
    jobs.forEach((job) => {
      const item = createNode("button", "job-detail-item");
      item.type = "button";
      const head = createNode("div", "job-detail-head");
      const badge = createNode("span", "status-badge");
      setStatusBadge(badge, job.status || "idle");
      head.append(createNode("strong", "", getOperationLabel(job)), badge);
      item.append(
        head,
        createNode("p", "job-detail-meta", `任务进度 ${clamp(job.progress)}% / 更新时间 ${formatTime(job.updated_at)}`),
        createNode("p", "job-detail-preview", buildCurrentViewFromGroup(payload, job).summary)
      );
      item.addEventListener("click", () => {
        const jobView = buildCurrentViewFromGroup(payload, job);
        renderCurrentResult(jobView);
        renderDetailDrawer(jobView, { primary_job: job });
        openDrawer("detailDrawer");
      });
      list.append(item);
    });
    jobsSection.append(list);
  }

  els.taskDrawerContent.append(summarySection, jobsSection);
}

/* data */

function syncGroupSummary(summary) {
  if (!summary?.id) {
    return;
  }
  const index = state.jobGroups.findIndex((item) => item.id === summary.id);
  if (index >= 0) {
    state.jobGroups[index] = { ...state.jobGroups[index], ...summary };
  } else {
    state.jobGroups.unshift(summary);
  }
}

function pushCleanGroupLog(payload) {
  const group = payload?.group;
  if (!group?.id) {
    return;
  }

  const bucket = Math.floor(clamp(group.progress) / 10);
  const key = `${group.status}|${bucket}`;
  if (state.logKeys.get(group.id) === key) {
    return;
  }
  state.logKeys.set(group.id, key);

  const label = getOperationLabel(payload.primary_job || group);
  const level = group.status === "error" ? "error" : group.status === "completed" ? "ok" : "info";
  const message =
    group.status === "completed"
      ? `${label}已完成。`
      : group.status === "error"
        ? `${label}执行失败。`
        : `${label}进行中，当前 ${clamp(group.progress)}%。`;
  pushLog(message, level);
}

async function inspectGroup(groupId, options = {}) {
  if (!groupId) {
    return null;
  }

  const payload = await fetchJson(`/api/job-groups/${groupId}`);
  state.activeGroupId = groupId;
  state.activeGroupDetail = payload;

  syncGroupSummary(payload.group);
  renderJobGroups(state.jobGroups);
  updateSummary(state.jobGroups);
  renderTaskDrawer(payload);

  const view = buildCurrentViewFromGroup(payload);
  renderCurrentResult(view);
  renderDetailDrawer(view, payload);

  if (options.openTaskDrawer) {
    openDrawer("taskDrawer");
  }
  if (options.openDetailDrawer) {
    openDrawer("detailDrawer");
  }

  return payload;
}

async function refreshAll(options = {}) {
  const [overview, groupPayload] = await Promise.all([
    fetchJson("/api/overview"),
    fetchJson("/api/job-groups?limit=200"),
  ]);

  state.overview = overview;
  state.jobGroups = groupPayload.items || [];

  safeText(els.modelPill, `模型 ${overview?.model || "--"}`);
  safeText(els.workspacePill, `工作区 ${overview?.workspace || "--"}`);
  safeText(els.lastRefresh, `最近刷新 ${formatClockNow()}`);

  renderRecentResults(overview?.recent?.outputs || []);
  renderRecommendations(state.jobGroups);
  renderJobGroups(state.jobGroups);
  updateSummary(state.jobGroups);

  const preferredId =
    options.preferredGroupId ||
    (state.activeGroupId && state.jobGroups.some((item) => item.id === state.activeGroupId) ? state.activeGroupId : null) ||
    state.jobGroups.find((item) => item.status === "running" || item.status === "queued")?.id ||
    state.jobGroups[0]?.id ||
    null;

  if (preferredId) {
    await inspectGroup(preferredId, {
      openTaskDrawer: Boolean(options.openTaskDrawer),
      openDetailDrawer: Boolean(options.openDetailDrawer),
    });
  } else if (overview?.recent?.outputs?.length) {
    const view = buildCurrentViewFromRecent(overview.recent.outputs[0]);
    renderCurrentResult(view);
    renderDetailDrawer(view, { primary_job: { result: overview.recent.outputs[0] } });
  } else {
    renderEmptyCurrentResult();
  }
}

async function pollGroup(groupId, label) {
  if (!groupId || state.polling.has(groupId)) {
    return;
  }

  state.polling.add(groupId);
  try {
    while (true) {
      const payload = await fetchJson(`/api/job-groups/${groupId}`);
      const group = payload.group;
      syncGroupSummary(group);
      renderJobGroups(state.jobGroups);
      updateSummary(state.jobGroups);
      pushCleanGroupLog(payload);

      if (state.activeGroupId === groupId || !state.activeGroupId) {
        state.activeGroupDetail = payload;
        renderTaskDrawer(payload);
        const view = buildCurrentViewFromGroup(payload);
        renderCurrentResult(view);
        renderDetailDrawer(view, payload);
      }

      if (group.status === "completed" || group.status === "error") {
        await refreshAll({
          preferredGroupId: groupId,
          openTaskDrawer: true,
          openDetailDrawer: true,
        });
        break;
      }

      await sleep(1500);
    }
  } catch (error) {
    pushLog(`${label || "任务"}轮询失败：${error.message}`, "error");
    setProgress(100, "轮询失败，请查看日志", "error");
  } finally {
    state.polling.delete(groupId);
  }
}

async function pollJob(jobId, label) {
  if (!jobId || state.polling.has(jobId)) {
    return;
  }

  state.polling.add(jobId);
  try {
    while (true) {
      const job = await fetchJson(`/api/jobs/${jobId}`);
      const payload = {
        group: {
          id: job.group_id || job.id,
          kind: job.kind,
          status: job.status,
          progress: job.progress,
          counts: {
            total: 1,
            running: job.status === "running" || job.status === "queued" ? 1 : 0,
            failed: job.status === "error" ? 1 : 0,
            completed: job.status === "completed" ? 1 : 0,
          },
          updated_at: job.updated_at,
        },
        primary_job: job,
        jobs: [job],
      };

      const view = buildCurrentViewFromGroup(payload);
      renderCurrentResult(view);
      renderDetailDrawer(view, payload);
      setProgress(job.progress ?? 0, view.summary, job.status);

      if (job.status === "completed" || job.status === "error") {
        pushLog(`${label || getOperationLabel(job)}${job.status === "completed" ? "已完成" : "失败"}`, job.status === "completed" ? "ok" : "error");
        await refreshAll();
        break;
      }

      await sleep(1500);
    }
  } catch (error) {
    pushLog(`${label || "任务"}轮询失败：${error.message}`, "error");
  } finally {
    state.polling.delete(jobId);
  }
}

/* forms and events */

function validatePayload(action, payload, label) {
  if (action === "ingest" && (!payload.inputs || !payload.inputs.length)) {
    pushLog(`${label}至少需要一条输入路径。`, "error");
    openDrawer("logDrawer");
    return false;
  }
  if (action === "search" && !payload.query) {
    pushLog("搜索问题不能为空。", "error");
    openDrawer("logDrawer");
    return false;
  }
  if (action === "ask" && !payload.question) {
    pushLog("提问内容不能为空。", "error");
    openDrawer("logDrawer");
    return false;
  }
  return true;
}

function submissionPreview(action, payload) {
  const lines = [`已提交 ${operationLabels[action] || action}。`, "", "本次参数："];
  lines.push(JSON.stringify(payload, null, 2));
  return lines.join("\n");
}

async function runAction(endpoint, payload, action) {
  const label = operationLabels[action] || endpoint;
  activatePanel("command-center-panel");

  renderCurrentResult({
    title: `${label}已提交`,
    status: "queued",
    summary: "任务已进入队列，主屏会持续回填进度与结果。",
    meta: "提交后会自动打开任务详情或日志视图。",
    path: "",
    body: submissionPreview(action, payload),
  });

  setProgress(3, `${label}已提交，正在创建任务组`, "running");
  pushLog(`${label}已提交。`, "info");
  openDrawer("logDrawer");

  try {
    const response = await fetchJson(`/api/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, ACTION_REQUEST_TIMEOUT_MS);

    if (response.job_group_id) {
      state.activeGroupId = response.job_group_id;
      await inspectGroup(response.job_group_id, { openTaskDrawer: true });
      pollGroup(response.job_group_id, label);
      return;
    }

    if (response.job_id) {
      openDrawer("logDrawer");
      pollJob(response.job_id, label);
      return;
    }

    pushLog(`${label}已提交，但没有返回任务标识。`, "error");
    openDrawer("logDrawer");
  } catch (error) {
    const isTimeout = /请求超时/.test(error.message || "");
    pushLog(`${label}提交失败：${error.message}`, "error");
    setProgress(100, isTimeout ? `${label}创建任务超时` : `${label}提交失败`, "error");
    renderCurrentResult({
      title: isTimeout ? `${label}创建任务超时` : `${label}提交失败`,
      status: "error",
      summary: isTimeout ? "服务在创建任务时卡住或没有及时返回。" : "任务没有成功创建。",
      meta: isTimeout ? "请检查后端服务状态或日志，然后重试。" : "请检查接口返回信息。",
      path: "",
      body: error.message,
    });
    openDrawer("logDrawer");
  }
}

function collectIngest(form) {
  const raw = form.elements.inputs?.value?.trim() || "";
  return {
    inputs: raw
      .split(/\r?\n/)
      .map((item) => stripWrappingQuotes(item))
      .filter(Boolean),
    max_files: form.elements.max_files?.value ? Number(form.elements.max_files.value) : null,
    force: form.elements.force?.checked || false,
    compile: form.elements.compile?.checked || false,
    strict: form.elements.strict?.checked ?? true,
  };
}

function collectCompile(form) {
  return {
    max_docs: form.elements.max_docs?.value ? Number(form.elements.max_docs.value) : null,
    force: form.elements.force?.checked || false,
  };
}

function collectSearch(form) {
  return {
    query: form.elements.query?.value?.trim() || "",
    max_results: Number(form.elements.max_results?.value) || 5,
    compile: form.elements.compile?.checked || false,
  };
}

function collectAsk(form) {
  return {
    question: form.elements.question?.value?.trim() || "",
    top_k: Number(form.elements.top_k?.value) || 6,
    promote: form.elements.promote?.checked || false,
    retrieval_profile: form.elements.retrieval_profile?.value || null,
  };
}

function bindForm(formId, endpoint, collect) {
  const form = document.getElementById(formId);
  if (!form) {
    return;
  }

  const action = form.dataset.form;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const payload = collect(form);
    const label = operationLabels[action] || action;
    if (!validatePayload(action, payload, label)) {
      return;
    }
    runAction(endpoint, payload, action);
  });
}

function openDrawer(drawerId) {
  document.querySelectorAll(".drawer").forEach((drawer) => {
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
  });

  const drawer = document.getElementById(drawerId);
  if (!drawer) {
    return;
  }
  drawer.classList.add("is-open");
  drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  if (!drawer) {
    return;
  }
  drawer.classList.remove("is-open");
  drawer.setAttribute("aria-hidden", "true");
}

function bindDrawers() {
  document.querySelectorAll("[data-drawer-open]").forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.getAttribute("data-drawer-open");
      if (target) {
        openDrawer(target);
      }
    });
  });

  document.querySelectorAll("[data-drawer-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.getAttribute("data-drawer-close");
      if (target) {
        closeDrawer(target);
      }
    });
  });
}

function activatePanel(panelId) {
  document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active-panel"));
  document.querySelectorAll(".nav-item[data-nav-target]").forEach((button) => button.classList.remove("active"));

  const panel = document.getElementById(panelId);
  if (panel) {
    panel.classList.add("active-panel");
  }

  const button = document.querySelector(`.nav-item[data-nav-target="${panelId}"]`);
  if (button) {
    button.classList.add("active");
  }
}

function bindNavigation() {
  document.querySelectorAll(".nav-item[data-nav-target]").forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.getAttribute("data-nav-target");
      if (target) {
        activatePanel(target);
      }
    });
  });
}

function bindLogControls() {
  if (els.clearLogBtn && els.logStream) {
    els.clearLogBtn.addEventListener("click", () => {
      els.logStream.innerHTML = "";
    });
  }
}

function bindRefreshButtons() {
  if (els.refreshBtn) {
    els.refreshBtn.addEventListener("click", () => {
      refreshAll().catch((error) => {
        pushLog(`刷新失败：${error.message}`, "error");
      });
    });
  }

  const recommendationBtn = document.getElementById("refreshRecommendationBtn");
  if (recommendationBtn) {
    recommendationBtn.addEventListener("click", () => renderRecommendations(state.jobGroups));
  }
}

/* bootstrap */

async function bootstrap() {
  bindDrawers();
  bindNavigation();
  bindLogControls();
  bindRefreshButtons();

  bindForm("ingestForm", "ingest", collectIngest);
  bindForm("compileForm", "compile", collectCompile);
  bindForm("searchForm", "search", collectSearch);
  bindForm("askForm", "ask", collectAsk);

  renderEmptyCurrentResult();
  await refreshAll();
  pushLog("工作台已就绪。", "ok");

  window.setInterval(() => {
    if (!state.polling.size) {
      refreshAll().catch((error) => {
        pushLog(`自动刷新失败：${error.message}`, "error");
      });
    }
  }, 30000);
}

bootstrap().catch((error) => {
  pushLog(`启动失败：${error.message}`, "error");
  setProgress(100, "前端初始化失败", "error");
});
