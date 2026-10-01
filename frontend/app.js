const topicEl = document.getElementById("topic");
const generateBtn = document.getElementById("generate");
const revalidateBtn = document.getElementById("revalidate");
const postEl = document.getElementById("post");
const postWrap = document.getElementById("post-wrap");
const postEditorShell = document.getElementById("post-editor-shell");
const linkPopover = document.getElementById("link-popover");
const linkPopoverUrl = document.getElementById("link-popover-url");
const linkPopoverVisit = document.getElementById("link-popover-visit");
const linkPopoverClose = document.getElementById("link-popover-close");
const postWordCount = document.getElementById("post-word-count");
const postCharCount = document.getElementById("post-char-count");
const editorStatus = document.getElementById("editor-status");
const toolBold = document.getElementById("tool-bold");
const toolItalic = document.getElementById("tool-italic");
const toolUnderline = document.getElementById("tool-underline");
const toolLink = document.getElementById("tool-link");
const toolClearFormat = document.getElementById("tool-clear-format");
const toolUndo = document.getElementById("tool-undo");
const toolRedo = document.getElementById("tool-redo");
const toolParagraph = document.getElementById("tool-paragraph");
const toolSelectAll = document.getElementById("tool-select-all");
const toolCopy = document.getElementById("tool-copy");

const FORMAT_TOOLS = [
  toolBold,
  toolItalic,
  toolUnderline,
  toolLink,
  toolClearFormat,
  toolUndo,
  toolRedo,
  toolParagraph,
  toolSelectAll,
  toolCopy,
];

const POST_PLACEHOLDER =
  "Enter a topic and run the gate to see editable draft copy here.";
const editHint = document.getElementById("edit-hint");
const decisionEl = document.getElementById("decision");
const decisionCard = document.getElementById("decision-card");
const decisionHint = document.getElementById("decision-hint");
const reasonsEl = document.getElementById("reasons");
const checksEl = document.getElementById("checks");
const validationCard = document.getElementById("validation-card");
const historyEl = document.getElementById("history");
const errorEl = document.getElementById("error");
const generatingPanel = document.getElementById("generating");
const generatingTitle = document.getElementById("generating-title");
const generatingSub = document.getElementById("generating-sub");
const pipelineSteps = document.getElementById("pipeline-steps");
const btnSpinner = generateBtn.querySelector(".btn-spinner");
const reasonsPanel = document.getElementById("reasons-panel");

const RULE_LABELS = {
  absolute_claim: "Absolute claim",
  competitor_mention: "Competitor mention",
  hard_sell: "Hard-sell language",
  exclamation_mark: "Formatting",
  emoji: "Formatting",
  all_caps_hype: "Formatting",
  empty_post: "Empty post",
  brand_voice_threshold: "Brand voice score",
  brand_voice_feedback: "Brand voice feedback",
  brand_voice_error: "Brand voice check",
  brand_voice_skipped: "Brand voice",
  generation_failed: "Generation",
};

const CHECK_LABELS = [
  "Non-negotiable rules",
  "Competitor check",
  "Hard-sell check",
  "Formatting",
  "Brand voice",
];

const PIPELINE_COPY = [
  { step: "draft", title: "Drafting post", sub: "LLM is writing on-brand copy…" },
  { step: "hard", title: "Hard rules", sub: "Checking claims, competitors, and formatting…" },
  { step: "voice", title: "Brand voice", sub: "Scoring warmth and tone…" },
  { step: "decide", title: "Final decision", sub: "Application code chooses publish, hold, or reject…" },
];

let pipelineTimer = null;
let pipelineIndex = 0;
let lastValidatedPost = "";
const GENERATING_FADE_MS = 420;
const postCard = document.querySelector(".card-post");

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getResultSections(includePost = true) {
  const sections = [];
  if (includePost && postCard) sections.push(postCard);
  sections.push(validationCard, decisionCard);
  return sections.filter(Boolean);
}

function dimResultSections(includePost = true) {
  getResultSections(includePost).forEach((el) => el.classList.add("is-content-dimmed"));
}

function fadeInResultSections(includePost = true) {
  getResultSections(includePost).forEach((el) => {
    el.classList.remove("is-content-dimmed");
    el.classList.add("is-fade-in");
  });
  setTimeout(() => {
    getResultSections(includePost).forEach((el) => el.classList.remove("is-fade-in"));
  }, 560);
}

function showGeneratingPanel() {
  generatingPanel.classList.remove("hidden", "is-leaving", "is-visible");
  requestAnimationFrame(() => {
    generatingPanel.classList.add("is-visible");
  });
}

async function hideGeneratingPanelAnimated() {
  if (generatingPanel.classList.contains("hidden")) return;
  generatingPanel.classList.remove("is-visible");
  generatingPanel.classList.add("is-leaving");
  generatingPanel.setAttribute("aria-busy", "false");
  await wait(GENERATING_FADE_MS);
  generatingPanel.classList.add("hidden");
  generatingPanel.classList.remove("is-leaving");
}

const editHistory = { stack: [""], index: 0, lock: false };
let activeLinkInEditor = null;
const PLAIN_URL_RE = /(https?:\/\/[^\s<>"']+)/gi;

function isEditorDisabled() {
  return postEl.getAttribute("contenteditable") === "false";
}

function setEditorDisabled(disabled) {
  postEl.setAttribute("contenteditable", disabled ? "false" : "true");
  postEl.classList.toggle("is-readonly", disabled);
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function plainTextToEditorHtml(text) {
  if (!text) return "";
  if (/[<][a-z]/i.test(text)) return text;
  return text
    .split(/\n\n+/)
    .map((block) => {
      const inner = escapeHtml(block.trim()).replace(/\n/g, "<br>");
      return inner ? `<p>${inner}</p>` : "";
    })
    .filter(Boolean)
    .join("");
}

function sanitizePostHtml(html) {
  const template = document.createElement("template");
  template.innerHTML = html;
  const allowed = new Set(["P", "BR", "B", "STRONG", "I", "EM", "U", "A", "DIV", "SPAN"]);

  const walk = (node) => {
    [...node.childNodes].forEach((child) => {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const el = child;
        if (!allowed.has(el.tagName)) {
          const frag = document.createDocumentFragment();
          while (el.firstChild) frag.appendChild(el.firstChild);
          el.replaceWith(frag);
          walk(frag);
          return;
        }
        if (el.tagName === "A") {
          const href = el.getAttribute("href") || "";
          if (!/^https?:\/\//i.test(href)) {
            el.replaceWith(...el.childNodes);
            return;
          }
          el.setAttribute("target", "_blank");
          el.setAttribute("rel", "noopener noreferrer");
          [...el.attributes].forEach((attr) => {
            if (!["href", "target", "rel"].includes(attr.name)) el.removeAttribute(attr.name);
          });
        } else {
          [...el.attributes].forEach((attr) => el.removeAttribute(attr.name));
        }
        walk(el);
      }
    });
  };

  walk(template.content);
  return template.innerHTML.trim();
}

function displayLinkLabel(href) {
  try {
    const u = new URL(href);
    const path = u.pathname === "/" ? "" : u.pathname;
    return `${u.hostname}${path}${u.search || ""}`;
  } catch {
    return href;
  }
}

function linkifyPlainUrlsInEditor() {
  const walker = document.createTreeWalker(postEl, NodeFilter.SHOW_TEXT);
  const toProcess = [];
  let node;
  while ((node = walker.nextNode())) {
    if (node.parentElement?.closest("a")) continue;
    if (PLAIN_URL_RE.test(node.textContent || "")) {
      toProcess.push(node);
    }
    PLAIN_URL_RE.lastIndex = 0;
  }

  toProcess.forEach((textNode) => {
    const text = textNode.textContent || "";
    PLAIN_URL_RE.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0;
    let match;
    while ((match = PLAIN_URL_RE.exec(text))) {
      if (match.index > last) {
        frag.appendChild(document.createTextNode(text.slice(last, match.index)));
      }
      const href = match[1];
      const a = document.createElement("a");
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "post-link";
      a.textContent = displayLinkLabel(href);
      frag.appendChild(a);
      last = match.index + href.length;
    }
    if (last < text.length) {
      frag.appendChild(document.createTextNode(text.slice(last)));
    }
    if (frag.childNodes.length) {
      textNode.replaceWith(frag);
    }
  });
}

function normalizeEditorLinks() {
  linkifyPlainUrlsInEditor();
  postEl.querySelectorAll("a[href]").forEach((anchor) => {
    const href = (anchor.getAttribute("href") || "").trim();
    if (!/^https?:\/\//i.test(href)) return;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    anchor.classList.add("post-link");
    anchor.setAttribute("title", `Open ${href}`);
    const visible = (anchor.textContent || "").replace(/\u00a0/g, " ").trim();
    if (!visible) {
      anchor.textContent = displayLinkLabel(href);
    }
  });
}

function hideLinkPopover() {
  if (activeLinkInEditor) {
    activeLinkInEditor.classList.remove("post-link-active");
    activeLinkInEditor = null;
  }
  linkPopover.classList.add("hidden");
}

function showLinkPopover(anchorEl) {
  const href = (anchorEl.getAttribute("href") || "").trim();
  if (!/^https?:\/\//i.test(href)) return;

  if (activeLinkInEditor && activeLinkInEditor !== anchorEl) {
    activeLinkInEditor.classList.remove("post-link-active");
  }
  activeLinkInEditor = anchorEl;
  anchorEl.classList.add("post-link-active");

  linkPopoverUrl.textContent = href;
  linkPopoverVisit.href = href;
  linkPopover.classList.remove("hidden");
  linkPopover.style.visibility = "hidden";

  const rect = anchorEl.getBoundingClientRect();
  const popRect = linkPopover.getBoundingClientRect();
  let top = rect.bottom + 8;
  let left = rect.left;
  if (top + popRect.height > window.innerHeight - 8) {
    top = Math.max(8, rect.top - popRect.height - 8);
  }
  left = Math.min(Math.max(8, left), window.innerWidth - popRect.width - 8);
  linkPopover.style.top = `${top}px`;
  linkPopover.style.left = `${left}px`;
  linkPopover.style.visibility = "";
}

function getPostPlainText() {
  return (postEl.innerText || "").replace(/\u00a0/g, " ").trim();
}

function getPostStorage() {
  if (!getPostPlainText()) return "";
  return sanitizePostHtml(postEl.innerHTML);
}

function syncPostEmptyState() {
  const empty = !getPostPlainText();
  postEl.dataset.empty = empty ? "true" : "false";
}

function countWords(text) {
  const t = text.trim();
  if (!t) return 0;
  return t.split(/\s+/).length;
}

function autoResizePost() {
  postEl.style.height = "auto";
  postEl.style.height = `${Math.max(postEl.scrollHeight, 220)}px`;
}

function updatePostStats() {
  const text = getPostPlainText();
  const words = countWords(text);
  postWordCount.textContent = `${words} word${words === 1 ? "" : "s"}`;
  postCharCount.textContent = `${text.length} character${text.length === 1 ? "" : "s"}`;
}

function updateEditorToolbar() {
  const enabled = !isEditorDisabled();
  for (const btn of FORMAT_TOOLS) {
    btn.disabled = !enabled;
  }
  if (enabled) {
    toolUndo.disabled = editHistory.index <= 0;
    toolRedo.disabled = editHistory.index >= editHistory.stack.length - 1;
  }
}

function resetEditHistory(value = "") {
  editHistory.stack = [value];
  editHistory.index = 0;
  updateEditorToolbar();
}

function pushEditHistory(value) {
  if (editHistory.lock) return;
  if (editHistory.stack[editHistory.index] === value) return;
  editHistory.stack = editHistory.stack.slice(0, editHistory.index + 1);
  editHistory.stack.push(value);
  editHistory.index = editHistory.stack.length - 1;
  if (editHistory.stack.length > 80) {
    editHistory.stack.shift();
    editHistory.index -= 1;
  }
  updateEditorToolbar();
}

function undoEdit() {
  if (editHistory.index <= 0 || isEditorDisabled()) return;
  editHistory.lock = true;
  editHistory.index -= 1;
  postEl.innerHTML = editHistory.stack[editHistory.index];
  editHistory.lock = false;
  normalizeEditorLinks();
  syncPostEmptyState();
  autoResizePost();
  updatePostStats();
  updateEditState();
}

function redoEdit() {
  if (editHistory.index >= editHistory.stack.length - 1 || isEditorDisabled()) return;
  editHistory.lock = true;
  editHistory.index += 1;
  postEl.innerHTML = editHistory.stack[editHistory.index];
  editHistory.lock = false;
  normalizeEditorLinks();
  syncPostEmptyState();
  autoResizePost();
  updatePostStats();
  updateEditState();
}

function onEditorInput() {
  syncPostEmptyState();
  pushEditHistory(getPostStorage());
  autoResizePost();
  updateEditState();
}

function execFormat(command, value = null) {
  if (isEditorDisabled()) return;
  postEl.focus();
  document.execCommand(command, false, value);
  onEditorInput();
}

function insertAtCursor(text) {
  if (isEditorDisabled()) return;
  postEl.focus();
  document.execCommand("insertText", false, text);
  onEditorInput();
}

function selectAllPost() {
  if (isEditorDisabled()) return;
  const range = document.createRange();
  range.selectNodeContents(postEl);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  postEl.focus();
}

function setEditorShellEnabled(enabled) {
  postEditorShell.classList.toggle("is-disabled", !enabled);
}

function clearPipelineAnimation() {
  if (pipelineTimer) {
    clearInterval(pipelineTimer);
    pipelineTimer = null;
  }
  pipelineIndex = 0;
  pipelineSteps.querySelectorAll(".pipeline-step").forEach((el) => {
    el.classList.remove("is-active", "is-done");
  });
}

function checkIconMarkup(state) {
  if (state === "running") {
    return '<span class="check-icon check-spinner" aria-hidden="true"></span>';
  }
  if (state === "sim-done") {
    return '<span class="check-icon pass check-pulse">✓</span>';
  }
  if (state === "pending") {
    return '<span class="check-icon pending-dot" aria-hidden="true">·</span>';
  }
  return '<span class="check-icon wait-icon" aria-hidden="true">○</span>';
}

function buildCheckRow(label, detail, state) {
  return `<div class="check-row">${checkIconMarkup(state)}<span class="check-copy">${label} — <strong class="check-detail">${detail}</strong></span></div>`;
}

function initValidationLoading() {
  checksEl.classList.remove("checks-empty");
  checksEl.classList.add("checks-loading");
  validationCard.classList.add("validation-active");
  checksEl.innerHTML = "";
  CHECK_LABELS.forEach((label, i) => {
    const li = document.createElement("li");
    li.className = "check-item is-wait";
    li.style.setProperty("--check-i", i);
    li.innerHTML = buildCheckRow(label, "Waiting", "wait");
    checksEl.appendChild(li);
  });
}

function updateValidationProgress(stepIndex) {
  const items = checksEl.querySelectorAll(".check-item");
  if (!items.length) return;

  items.forEach((li, i) => {
    li.classList.remove("is-wait", "is-pending", "is-running", "is-sim-done");
    let state = "wait";
    let detail = "Waiting";

    if (stepIndex === 0) {
      if (i === 0) {
        state = "pending";
        detail = "Queued…";
        li.classList.add("is-pending");
      } else {
        li.classList.add("is-wait");
      }
    } else if (stepIndex === 1) {
      if (i < 4) {
        state = "running";
        detail = "Checking…";
        li.classList.add("is-running");
      } else {
        li.classList.add("is-wait");
      }
    } else if (stepIndex === 2) {
      if (i < 4) {
        state = "sim-done";
        detail = "Checked";
        li.classList.add("is-sim-done");
      } else {
        state = "running";
        detail = "Scoring…";
        li.classList.add("is-running");
      }
    } else if (stepIndex === 3) {
      state = "running";
      detail = i === 4 ? "Scoring…" : "Confirming…";
      li.classList.add("is-running");
    }

    li.innerHTML = buildCheckRow(CHECK_LABELS[i], detail, state);
  });
}

function setPipelineStep(index) {
  const steps = pipelineSteps.querySelectorAll(".pipeline-step");
  steps.forEach((el, i) => {
    el.classList.toggle("is-done", i < index);
    el.classList.toggle("is-active", i === index);
  });
  const copy = PIPELINE_COPY[index];
  if (copy) {
    generatingTitle.textContent = copy.title;
    generatingSub.textContent = copy.sub;
  }
  updateValidationProgress(index);
}

function startPipelineAnimation(fromStep = 0) {
  pipelineIndex = fromStep;
  setPipelineStep(fromStep);
  pipelineTimer = setInterval(() => {
    pipelineIndex = Math.min(pipelineIndex + 1, PIPELINE_COPY.length - 1);
    setPipelineStep(pipelineIndex);
    if (pipelineIndex >= PIPELINE_COPY.length - 1) {
      clearInterval(pipelineTimer);
      pipelineTimer = null;
    }
  }, 1100);
}

function beginBusyUI({ revalidate = false } = {}) {
  clearPipelineAnimation();
  generatingPanel.classList.remove("hidden");
  generatingPanel.setAttribute("aria-busy", "true");
  generateBtn.disabled = true;
  revalidateBtn.disabled = true;
  setEditorDisabled(true);
  setEditorShellEnabled(false);
  updateEditorToolbar();

  if (revalidate) {
    generateBtn.querySelector(".btn-label").textContent = "Generate & Validate";
    btnSpinner.classList.add("hidden");
  } else {
    generateBtn.querySelector(".btn-label").textContent = "Brewing…";
    btnSpinner.classList.remove("hidden");
    postEditorShell.classList.add("is-loading");
    postEl.innerHTML = "";
    syncPostEmptyState();
    postEl.classList.add("muted");
  }

  decisionCard.classList.add("is-generating");
  decisionCard.classList.remove("state-publish", "state-hold", "state-reject");
  decisionEl.className = "decision decision-idle";
  decisionEl.textContent = "…";
  decisionHint.textContent = revalidate ? "Re-running checks on your edit…" : "Running the gate…";
  reasonsEl.innerHTML = "";
  reasonsPanel.classList.add("hidden");
  initValidationLoading();
}

function startGeneratingUI() {
  beginBusyUI({ revalidate: false });
  showGeneratingPanel();
  dimResultSections(true);
  startPipelineAnimation(0);
}

function startRevalidateUI() {
  beginBusyUI({ revalidate: true });
  dimResultSections(true);
  startPipelineAnimation(1);
}

function finishRunUI() {
  clearPipelineAnimation();
  generateBtn.querySelector(".btn-label").textContent = "Generate & Validate";
  btnSpinner.classList.add("hidden");
  postEditorShell.classList.remove("is-loading");
  decisionCard.classList.remove("is-generating");
  validationCard.classList.remove("validation-active");
  checksEl.classList.remove("checks-loading");
  generateBtn.disabled = false;
  if (getPostPlainText()) setEditorDisabled(false);
  pipelineSteps.querySelectorAll(".pipeline-step").forEach((el) => {
    el.classList.add("is-done");
    el.classList.remove("is-active");
  });
  updateEditState();
}

async function completeGeneratingTransition() {
  await hideGeneratingPanelAnimated();
  finishRunUI();
}

function setPostContent(text, { validated = false } = {}) {
  hideLinkPopover();
  if (text) {
    const html = sanitizePostHtml(plainTextToEditorHtml(text));
    postEl.innerHTML = html;
    normalizeEditorLinks();
    setEditorDisabled(false);
    postEl.classList.remove("muted");
    revalidateBtn.classList.remove("hidden");
    setEditorShellEnabled(true);
    const storage = getPostStorage();
    resetEditHistory(storage);
    if (validated) {
      lastValidatedPost = storage;
    }
  } else {
    postEl.innerHTML = "";
    setEditorDisabled(true);
    postEl.classList.add("muted");
    revalidateBtn.classList.add("hidden");
    lastValidatedPost = "";
    setEditorShellEnabled(false);
    resetEditHistory("");
  }
  syncPostEmptyState();
  autoResizePost();
  updatePostStats();
  updateEditState();
}

function updateEditState() {
  const storage = getPostStorage();
  const hasPost = storage.length > 0;
  const dirty = hasPost && storage !== (lastValidatedPost || "");
  revalidateBtn.disabled = !dirty || generateBtn.disabled;
  editHint.classList.toggle("hidden", !dirty);
  postEditorShell.classList.toggle("is-dirty", dirty);
  postEditorShell.classList.toggle("is-validated", hasPost && !dirty && !!lastValidatedPost);

  if (!hasPost && postEl.disabled) {
    editorStatus.textContent = "No draft yet";
    editorStatus.className = "editor-status muted";
  } else if (dirty) {
    editorStatus.textContent = "Unsaved edits — re-validate before publish";
    editorStatus.className = "editor-status editor-status-warn";
  } else if (lastValidatedPost) {
    editorStatus.textContent = "In sync with last validation";
    editorStatus.className = "editor-status editor-status-ok";
  } else {
    editorStatus.textContent = "Draft ready to edit";
    editorStatus.className = "editor-status muted";
  }

  updateEditorToolbar();
  updatePostStats();
}

function renderChecks(data, { animate = false } = {}) {
  checksEl.classList.remove("checks-empty", "checks-loading");
  checksEl.innerHTML = "";
  const hr = data.checks.hard_rules;
  const bv = data.checks.brand_voice;

  const items = [
    {
      ok: hr.passed,
      label: "Non-negotiable rules",
      detail: hr.passed ? "Passed" : "Failed",
    },
    {
      ok: !hr.violations.some((v) => v.rule === "competitor_mention"),
      label: "Competitor check",
      detail: hr.violations.some((v) => v.rule === "competitor_mention") ? "Failed" : "Passed",
    },
    {
      ok: !hr.violations.some((v) => v.rule === "hard_sell"),
      label: "Hard-sell check",
      detail: hr.violations.some((v) => v.rule === "hard_sell") ? "Failed" : "Passed",
    },
    {
      ok: !hr.violations.some((v) =>
        ["exclamation_mark", "emoji", "all_caps_hype"].includes(v.rule)
      ),
      label: "Formatting",
      detail: hr.violations.some((v) =>
        ["exclamation_mark", "emoji", "all_caps_hype"].includes(v.rule)
      )
        ? "Failed"
        : "Passed",
    },
    {
      ok: bv.passed,
      label: "Brand voice",
      detail:
        bv.score != null ? `${bv.score}/100` : bv.error ? "Unavailable" : "—",
      warn: bv.score != null && !bv.passed,
    },
  ];

  items.forEach((item, i) => {
    const li = document.createElement("li");
    li.className = "check-item";
    if (animate) {
      li.classList.add("check-reveal");
      li.style.animationDelay = `${i * 90}ms`;
    }
    const icon = item.ok ? "✓" : item.warn ? "!" : "✕";
    const cls = item.ok ? "pass" : item.warn ? "warn" : "fail";
    li.innerHTML = `<div class="check-row"><span class="check-icon ${cls}">${icon}</span><span>${item.label} — <strong>${item.detail}</strong></span></div>`;
    checksEl.appendChild(li);
  });
}

function ruleLabel(rule) {
  if (RULE_LABELS[rule]) return RULE_LABELS[rule];
  return rule.replace(/_/g, " ");
}

function normalizeReasonList(data) {
  let reasons = (data.reasons || []).map((r) => ({
    rule: r.rule || "reason",
    message: r.message || JSON.stringify(r),
  }));

  if (!reasons.length && data.checks?.hard_rules?.violations?.length) {
    reasons = data.checks.hard_rules.violations.map((v) => ({
      rule: v.rule,
      message: v.message,
    }));
  }
  return reasons;
}

function groupReasons(reasons) {
  const blocks = [];
  let feedbackBatch = [];

  const flushFeedback = () => {
    if (!feedbackBatch.length) return;
    blocks.push({ type: "feedback", title: "Brand voice feedback", items: [...feedbackBatch] });
    feedbackBatch = [];
  };

  for (const r of reasons) {
    if (r.rule === "brand_voice_feedback") {
      feedbackBatch.push(r.message);
      continue;
    }
    flushFeedback();
    blocks.push({ type: "single", title: ruleLabel(r.rule), message: r.message });
  }
  flushFeedback();
  return blocks;
}

function renderReasonBlock(block) {
  const el = document.createElement("article");
  el.className = "reason-block";

  const title = document.createElement("h3");
  title.className = "reason-block-title";
  title.textContent = block.title;

  el.appendChild(title);

  if (block.type === "feedback") {
    const ul = document.createElement("ul");
    ul.className = "reason-block-list";
    for (const item of block.items) {
      const li = document.createElement("li");
      li.textContent = item;
      ul.appendChild(li);
    }
    el.appendChild(ul);
  } else {
    const p = document.createElement("p");
    p.className = "reason-block-body";
    p.textContent = block.message;
    el.appendChild(p);
  }

  return el;
}

function renderReasons(data) {
  reasonsEl.innerHTML = "";
  reasonsPanel.classList.add("hidden");

  if (data.decision === "publish") return;

  const blocks = groupReasons(normalizeReasonList(data));
  if (!blocks.length) return;

  for (const block of blocks) {
    reasonsEl.appendChild(renderReasonBlock(block));
  }
  reasonsPanel.classList.remove("hidden");
}

function setDecision(decision) {
  decisionEl.className = "decision";
  decisionCard.classList.remove("state-publish", "state-hold", "state-reject", "is-generating");

  if (decision === "publish") {
    decisionEl.textContent = "PUBLISH";
    decisionEl.classList.add("decision-publish", "is-reveal");
    decisionCard.classList.add("state-publish");
    decisionHint.textContent = "All checks passed — safe to ship.";
  } else if (decision === "hold") {
    decisionEl.textContent = "HOLD";
    decisionEl.classList.add("decision-hold", "is-reveal");
    decisionCard.classList.add("state-hold");
    decisionHint.textContent = "Needs review — uncertainty or soft failure.";
  } else if (decision === "reject") {
    decisionEl.textContent = "REJECT";
    decisionEl.classList.add("decision-reject", "is-reveal");
    decisionCard.classList.add("state-reject");
    decisionHint.textContent = "Non-negotiable rule violation.";
  } else {
    decisionEl.textContent = "—";
    decisionEl.classList.add("decision-idle");
    decisionHint.textContent = "Waiting for a run";
  }
}

function applyGateResponse(data) {
  const draft = data.generated_post || data.post || getPostStorage();
  setPostContent(draft || "", { validated: true });
  renderChecks(data, { animate: true });
  setDecision(data.decision);
  renderReasons(data);
}

function badgeClass(decision) {
  if (decision === "publish") return "badge-publish";
  if (decision === "hold") return "badge-hold";
  return "badge-reject";
}

async function loadHistory() {
  try {
    const res = await fetch("/api/audit?limit=8");
    if (!res.ok) return;
    const rows = await res.json();
    historyEl.innerHTML = "";
    if (!rows.length) {
      historyEl.innerHTML = '<li class="history-placeholder muted">No decisions yet.</li>';
      return;
    }
    for (const row of rows) {
      const li = document.createElement("li");
      li.className = "history-item";
      const t = new Date(row.created_at).toLocaleString();
      li.innerHTML = `
        <span class="badge ${badgeClass(row.decision)}">${row.decision}</span>
        <span class="history-topic">${escapeHtml(row.topic.slice(0, 56))}${row.topic.length > 56 ? "…" : ""}</span>
        <span class="history-time">${t}</span>
      `;
      historyEl.appendChild(li);
    }
  } catch {
    historyEl.innerHTML = '<li class="muted">Could not load history.</li>';
  }
}

async function runGateRequest(url, body, { revalidate = false } = {}) {
  errorEl.classList.add("hidden");
  if (revalidate) {
    startRevalidateUI();
  } else {
    startGeneratingUI();
  }

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Request failed");
    }
    await completeGeneratingTransition();
    applyGateResponse(data);
    fadeInResultSections(true);
    await loadHistory();
  } catch (e) {
    await hideGeneratingPanelAnimated();
    finishRunUI();
    getResultSections(true).forEach((el) => el.classList.remove("is-content-dimmed", "is-fade-in"));
    errorEl.textContent = e.message || "Something went wrong.";
    errorEl.classList.remove("hidden");
    if (!revalidate) {
      setPostContent("");
      checksEl.classList.add("checks-empty");
      checksEl.innerHTML = '<li class="checks-placeholder muted">Checks appear after each run.</li>';
      setDecision(null);
    } else {
      updateEditState();
    }
  }
}

generateBtn.addEventListener("click", async () => {
  const topic = topicEl.value.trim();
  if (!topic) {
    errorEl.textContent = "Enter a topic.";
    errorEl.classList.remove("hidden");
    topicEl.focus();
    return;
  }
  await runGateRequest("/api/generate", { topic });
});

revalidateBtn.addEventListener("click", async () => {
  const topic = topicEl.value.trim();
  const post = getPostStorage();
  if (!topic) {
    errorEl.textContent = "Topic is required for audit context.";
    errorEl.classList.remove("hidden");
    topicEl.focus();
    return;
  }
  if (!post) {
    errorEl.textContent = "Nothing to validate.";
    errorEl.classList.remove("hidden");
    return;
  }
  await runGateRequest("/api/validate", { topic, post }, { revalidate: true });
});

postEl.addEventListener("input", onEditorInput);

postEl.addEventListener("click", (e) => {
  const anchor = e.target.closest("a[href]");
  if (!anchor || !postEl.contains(anchor)) return;
  e.preventDefault();
  showLinkPopover(anchor);
});

postEl.addEventListener("keydown", (e) => {
  if (e.key === "Escape") hideLinkPopover();
  const mod = e.metaKey || e.ctrlKey;
  if (mod && e.key === "z" && !e.shiftKey) {
    e.preventDefault();
    undoEdit();
    return;
  }
  if (mod && (e.key === "Z" || (e.key === "z" && e.shiftKey))) {
    e.preventDefault();
    redoEdit();
    return;
  }
  if (mod && e.key === "b") {
    e.preventDefault();
    execFormat("bold");
    return;
  }
  if (mod && e.key === "i") {
    e.preventDefault();
    execFormat("italic");
    return;
  }
  if (mod && e.key === "u") {
    e.preventDefault();
    execFormat("underline");
    return;
  }
  if (e.key === "Tab") {
    e.preventDefault();
    insertAtCursor("  ");
  }
});

toolBold.addEventListener("click", () => execFormat("bold"));
toolItalic.addEventListener("click", () => execFormat("italic"));
toolUnderline.addEventListener("click", () => execFormat("underline"));
toolLink.addEventListener("click", () => {
  const url = window.prompt("Link URL (https://…)", "https://");
  if (!url) return;
  execFormat("createLink", url.trim());
  normalizeEditorLinks();
});

linkPopoverClose.addEventListener("click", hideLinkPopover);
linkPopoverVisit.addEventListener("click", () => {
  hideLinkPopover();
});

document.addEventListener("click", (e) => {
  if (linkPopover.classList.contains("hidden")) return;
  if (linkPopover.contains(e.target)) return;
  if (e.target.closest("#post a[href]")) return;
  hideLinkPopover();
});
toolClearFormat.addEventListener("click", () => execFormat("removeFormat"));
toolUndo.addEventListener("click", undoEdit);
toolRedo.addEventListener("click", redoEdit);
toolParagraph.addEventListener("click", () => execFormat("insertParagraph"));
toolSelectAll.addEventListener("click", selectAllPost);
toolCopy.addEventListener("click", async () => {
  const text = getPostPlainText();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    editorStatus.textContent = "Copied to clipboard";
    editorStatus.className = "editor-status editor-status-ok";
    setTimeout(updateEditState, 1600);
  } catch {
    editorStatus.textContent = "Copy failed — select and copy manually";
    editorStatus.className = "editor-status editor-status-warn";
  }
});

topicEl.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    generateBtn.click();
  }
});

syncPostEmptyState();
updatePostStats();
updateEditorToolbar();

loadHistory();
