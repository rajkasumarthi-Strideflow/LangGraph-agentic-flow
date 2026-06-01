const appState = {
  workflowId: null,
  workflow: null,
  auditEvents: [],
  humanReviews: [],
  intakeResult: null,
  intakeSessionId: null,
  correlationId: null,
  intakeOriginalMessage: null,
  conversationMessages: [],
  observability: null,
  monitoringSummary: null,
  monitoringRuns: [],
  monitoringOutcomes: null,
};

const elements = {
  workflowConsoleTab: document.querySelector("#workflow-console-tab"),
  monitoringDashboardTab: document.querySelector("#monitoring-dashboard-tab"),
  workflowConsoleView: document.querySelector("#workflow-console-view"),
  monitoringDashboardView: document.querySelector("#monitoring-dashboard-view"),
  intakeMessage: document.querySelector("#intake-message"),
  analyzeRequest: document.querySelector("#analyze-intake-button"),
  replyIntake: document.querySelector("#reply-intake-button"),
  intakeStatus: document.querySelector("#intake-status"),
  intakeResult: document.querySelector("#intake-result"),
  conversationPanel: document.querySelector("#conversation-panel"),
  runButton: document.querySelector("#run-workflow"),
  loadMissing: document.querySelector("#load-missing"),
  loadCracked: document.querySelector("#load-cracked"),
  loadEligible: document.querySelector("#load-eligible"),
  loadUnknown: document.querySelector("#load-unknown"),
  loadInvalid: document.querySelector("#load-invalid"),
  clearIntake: document.querySelector("#clear-intake"),
  status: document.querySelector("#status-message"),
  result: document.querySelector("#workflow-result"),
  telemetry: document.querySelector("#telemetry-tiles"),
  observability: document.querySelector("#observability-tiles"),
  traceContext: document.querySelector("#trace-context-tiles"),
  aiDrafting: document.querySelector("#ai-drafting"),
  timeline: document.querySelector("#workflow-timeline"),
  auditReplay: document.querySelector("#audit-replay"),
  reviewContent: document.querySelector("#review-content"),
  reviewForm: document.querySelector("#review-form"),
  reviewerId: document.querySelector("#reviewer-id"),
  reviewDecision: document.querySelector("#review-decision"),
  reviewReason: document.querySelector("#review-reason"),
  reviewRecords: document.querySelector("#review-records"),
  reviewResponse: document.querySelector("#review-response"),
  monitorWorkflowType: document.querySelector("#monitor-workflow-type"),
  monitorOutcome: document.querySelector("#monitor-outcome"),
  monitorCorrelation: document.querySelector("#monitor-correlation"),
  monitorRefresh: document.querySelector("#monitor-refresh"),
  monitoringKpis: document.querySelector("#monitoring-kpis"),
  monitoringOutcomes: document.querySelector("#monitoring-outcomes"),
  monitoringRuns: document.querySelector("#monitoring-runs"),
  monitoringAuditDrilldown: document.querySelector("#monitoring-audit-drilldown"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeText(value, fallback = "Not Available") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
}

function dash(value) {
  return safeText(value, "—");
}

function setLoading(isLoading) {
  elements.runButton.disabled = isLoading;
  elements.runButton.textContent = isLoading ? "Running Workflow..." : "Run Governed Workflow";
}

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.className = isError ? "status-message error" : "status-message";
}

function setIntakeStatus(message, isError = false) {
  elements.intakeStatus.textContent = message;
  elements.intakeStatus.className = isError ? "status-message error" : "status-message";
}

function statusClass(kind, value) {
  if (kind === "guardrail") {
    if (value === "allow") return "status-positive";
    if (value === "block") return "status-warning";
    if (value === "escalate") return "status-review";
    if (value === "allowed_action") return "status-positive";
    if (value === "blocked") return "status-warning";
    if (value === "escalated") return "status-review";
    if (value === "failed") return "status-danger";
    if (value === "Allowed / Action Created") return "status-positive";
    if (value === "Blocked") return "status-warning";
    if (value === "Escalated") return "status-review";
    if (value === "Failed") return "status-danger";
  }

  if (kind === "eligibility") {
    if (value === "eligible") return "status-positive";
    if (value === "not_eligible") return "status-warning";
    if (value === "human_review_required" || value === "unknown") return "status-review";
  }

  if (kind === "workflow") {
    if (value === "completed") return "status-positive";
    if (value === "failed") return "status-danger";
  }

  if (kind === "review") {
    if (value === "Required") return "status-review";
    if (value.startsWith("Completed")) return "status-positive";
  }

  if (kind === "replacement" && value !== "Not Created") {
    return "status-positive";
  }

  if (kind === "llm") {
    if (value === "completed" || value === "passed") return "status-positive";
    if (value === "not_configured" || value === "disabled" || value === "Not Run") return "status-neutral";
    if (value === "failed") return "status-danger";
  }

  if (kind === "response") {
    if (value === "llm_validated") return "status-positive";
    if (value.includes("fallback")) return "status-warning";
  }

  if (value === "Ready to Start Governed Workflow" || value === "No Clarification Required") {
    return "status-positive";
  }
  if (value === "Not Ready" || value === "Clarification Required" || value === "Invalid identifier format") {
    return "status-warning";
  }

  return "status-neutral";
}

function pill(value, kind = "neutral", fallback = "Not Available") {
  const text = safeText(value, fallback);
  return `<span class="status-pill ${statusClass(kind, text)}">${escapeHtml(text)}</span>`;
}

function summaryCard(label, value, options = {}) {
  const classes = options.response ? "summary-card response-card" : "summary-card";
  const content = options.html ? value : escapeHtml(safeText(value, options.fallback));
  const valueClass = options.response ? "summary-value response-text" : "summary-value";

  return `
    <div class="${classes}">
      <div class="summary-label">${escapeHtml(label)}</div>
      <div class="${valueClass}">${content}</div>
    </div>
  `;
}

function telemetryCard(label, value, help, tone = "") {
  const toneClass = tone ? ` ${tone}` : "";
  return `
    <article class="telemetry-card${toneClass}">
      <div class="telemetry-label">${escapeHtml(label)}</div>
      <div class="telemetry-value">${value}</div>
      <div class="telemetry-help">${escapeHtml(help)}</div>
    </article>
  `;
}

function workflowTypeLabel(value) {
  const labels = {
    warranty_replacement: "Warranty Replacement",
  };
  return labels[value] || safeText(value);
}

function outcomeLabel(value) {
  const labels = {
    blocked: "Blocked",
    escalated: "Escalated",
    allowed_action: "Allowed / Action Created",
    completed_no_action: "Completed No Action",
    failed: "Failed",
    unknown: "Unknown",
  };
  return labels[value] || safeText(value);
}

function routerField(label, value, kind = "neutral") {
  const rendered = kind === "pill" ? pill(value) : escapeHtml(safeText(value));
  return `
    <div class="router-field">
      <div class="summary-label">${escapeHtml(label)}</div>
      <div class="summary-value">${rendered}</div>
    </div>
  `;
}

function getContextPayload() {
  return {
    customer_id: null,
    order_id: null,
  };
}

function getWorkflowIdentifiers() {
  return {
    customer_id: appState.intakeResult?.customer_id || null,
    order_id: appState.intakeResult?.order_id || null,
  };
}

function updateRunWorkflowAvailability() {
  const messageReady = Boolean(elements.intakeMessage.value.trim());
  const identifiers = getWorkflowIdentifiers();
  const routerReady = Boolean(appState.intakeResult?.can_start_workflow);
  const identifiersReady = Boolean(identifiers.customer_id && identifiers.order_id);
  elements.runButton.disabled = !(messageReady && routerReady && identifiersReady);
}

function resetWorkflowData() {
  appState.workflowId = null;
  appState.workflow = null;
  appState.auditEvents = [];
  appState.humanReviews = [];
  renderDecisionSummary();
  renderTelemetryTiles();
  renderAiDraftingPanel();
  renderWorkflowTimeline();
  renderAuditReplay();
  renderHumanReviewPanel();
}

function resetRouterResult() {
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  appState.intakeResult = null;
  elements.replyIntake.classList.add("hidden");
  renderConversation();
  renderIntakeResult();
  renderTraceContextTiles();
  updateRunWorkflowAvailability();
}

function routerReadinessText(result) {
  if (result.can_start_workflow) {
    return "Ready to Start Governed Workflow";
  }
  return "Not Ready";
}

function clarificationText(result) {
  return result.requires_clarification ? "Clarification Required" : "No Clarification Required";
}

function replacementAction(workflow) {
  if (!workflow) {
    return "Not Started";
  }
  return workflow?.replacement_request_id
    ? workflow.replacement_request_id
    : "Not Created";
}

function humanReviewStatus(workflow, reviews) {
  if (!workflow) {
    return "Not Started";
  }
  if (!workflow.escalation_id) {
    return "Not Required";
  }
  if (reviews.length > 0) {
    return `Completed (${reviews.length})`;
  }
  return "Required";
}

function sortEvents(events) {
  return [...events].sort((a, b) => {
    const left = new Date(a.timestamp).getTime();
    const right = new Date(b.timestamp).getTime();
    return left - right;
  });
}

function queryString(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      query.set(key, value);
    }
  });
  const rendered = query.toString();
  return rendered ? `?${rendered}` : "";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }
  return data;
}

async function startWorkflow() {
  const identifiers = getWorkflowIdentifiers();
  if (!identifiers.customer_id || !identifiers.order_id) {
    setStatus(
      appState.intakeResult?.next_question
        || "Customer ID and Order ID are required to start the governed workflow.",
      true,
    );
    updateRunWorkflowAvailability();
    return;
  }

  setLoading(true);
  setStatus("Running governed workflow...");
  elements.reviewResponse.innerHTML = "";

  try {
    const result = await requestJson("/api/workflows/start", {
      method: "POST",
      body: JSON.stringify({
        customer_request: appState.intakeOriginalMessage || elements.intakeMessage.value,
        customer_id: identifiers.customer_id,
        order_id: identifiers.order_id,
        correlation_id: appState.correlationId,
      }),
    });

    appState.workflowId = result.workflow_id;
    await refreshWorkflowView(result.workflow_id);
    if (!elements.monitoringDashboardView.classList.contains("hidden")) {
      await refreshMonitoringDashboard();
    }
    setStatus("Workflow completed. State, audit events, and review records are current.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setLoading(false);
    updateRunWorkflowAvailability();
  }
}

async function analyzeRequest() {
  elements.analyzeRequest.disabled = true;
  elements.analyzeRequest.textContent = "Starting...";
  setIntakeStatus("Analyzing request...");

  try {
    const result = await requestJson("/api/intake/session/start", {
      method: "POST",
      body: JSON.stringify({
        message: elements.intakeMessage.value,
      }),
    });

    applyIntakeSession(result);

    setIntakeStatus(
      result.can_start_workflow
        ? "Ready to start the governed workflow."
        : result.requires_clarification
          ? "Clarification needed before workflow start."
          : "No workflow route selected.",
    );
  } catch (error) {
    setIntakeStatus(error.message, true);
  } finally {
    elements.analyzeRequest.disabled = false;
    elements.analyzeRequest.textContent = "Start Intake / Analyze Request";
    updateRunWorkflowAvailability();
  }
}

async function replyToIntake() {
  if (!appState.intakeSessionId) {
    setIntakeStatus("Start intake before replying.", true);
    return;
  }

  elements.replyIntake.disabled = true;
  elements.replyIntake.textContent = "Continuing...";
  setIntakeStatus("Updating intake session...");

  try {
    const result = await requestJson(`/api/intake/session/${appState.intakeSessionId}/reply`, {
      method: "POST",
      body: JSON.stringify({
        message: elements.intakeMessage.value,
      }),
    });

    applyIntakeSession(result);
    setIntakeStatus(
      result.can_start_workflow
        ? "Required facts collected. Ready to start the governed workflow."
        : result.requires_clarification
          ? "Clarification still needed before workflow start."
          : "No workflow route selected.",
    );
  } catch (error) {
    setIntakeStatus(error.message, true);
  } finally {
    elements.replyIntake.disabled = false;
    elements.replyIntake.textContent = "Reply / Continue";
    updateRunWorkflowAvailability();
  }
}

function applyIntakeSession(result) {
  if (appState.workflow?.correlation_id !== result.correlation_id) {
    resetWorkflowData();
  }
  appState.intakeSessionId = result.intake_session_id;
  appState.correlationId = result.correlation_id;
  appState.intakeOriginalMessage = result.original_message;
  appState.conversationMessages = result.conversation_messages || [];
  appState.intakeResult = result;
  renderConversation();
  renderIntakeResult();
  renderTraceContextTiles();
  updateReplyVisibility(result);
  updateRunWorkflowAvailability();
}

function updateReplyVisibility(result) {
  if (result.requires_clarification) {
    elements.replyIntake.classList.remove("hidden");
  } else {
    elements.replyIntake.classList.add("hidden");
  }
}

function renderConversation() {
  const messages = appState.conversationMessages;
  if (!messages.length) {
    elements.conversationPanel.className = "conversation-panel empty-state";
    elements.conversationPanel.textContent = "Start intake to see the conversation and clarification turns.";
    return;
  }

  elements.conversationPanel.className = "conversation-panel";
  elements.conversationPanel.innerHTML = messages
    .map((message) => `
      <article class="conversation-message ${escapeHtml(message.role)}">
        <div class="conversation-role">${escapeHtml(message.role)}</div>
        <div class="conversation-text">${escapeHtml(message.content)}</div>
        <div class="conversation-time">${escapeHtml(dash(message.timestamp))}</div>
      </article>
    `)
    .join("");
}

function renderIntakeResult() {
  const result = appState.intakeResult;
  if (!result) {
    elements.intakeResult.className = "intake-result empty-state";
    elements.intakeResult.textContent = "Analyze a message to see intent, missing facts, and workflow routing.";
    return;
  }

  const missingFields = result.missing_fields?.length
    ? result.missing_fields.join(", ")
    : "None";
  const invalidFields = result.invalid_fields?.length
    ? result.invalid_fields.join(", ")
    : "None";
  const identifierValidation = result.invalid_fields?.length
    ? "Invalid identifier format"
    : "Valid or not required";
  elements.intakeResult.className = "intake-result router-grid";
  elements.intakeResult.innerHTML = [
    routerField("Intent", result.intent, "pill"),
    routerField("Confidence", result.confidence ?? "Not Available"),
    routerField("Extracted Customer ID", result.customer_id || "Not provided"),
    routerField("Extracted Order ID", result.order_id || "Not provided"),
    routerField("Product Type", result.product_type || "Not Available"),
    routerField("Product Issue", result.product_issue || "Not Available"),
    routerField("Damage Type", result.damage_type || "Not Available"),
    routerField("Requires Clarification", clarificationText(result), "pill"),
    routerField("Missing Fields", missingFields),
    routerField("Invalid Fields", invalidFields),
    routerField("Identifier Validation", identifierValidation, "pill"),
    routerField("Routed Workflow", result.routed_workflow || "Not Routed"),
    routerField("Routing Status", result.routing_status, "pill"),
    routerField("Can Start Workflow", routerReadinessText(result), "pill"),
    routerField("Next Question", result.next_question || "None"),
    routerField("Error", result.error_message || "None"),
  ].join("");
}

async function refreshWorkflowView(workflowId) {
  const workflowResponse = await requestJson(`/api/workflows/${workflowId}`);
  appState.workflow = workflowResponse.state;
  appState.correlationId = workflowResponse.correlation_id || appState.workflow?.correlation_id || appState.correlationId;

  const [auditResponse, reviewResponse] = await Promise.all([
    requestJson(`/api/workflows/${workflowId}/audit`),
    requestJson(`/api/workflows/${workflowId}/human-reviews`),
  ]);

  appState.auditEvents = sortEvents(auditResponse.events || []);
  appState.correlationId = auditResponse.correlation_id || appState.correlationId;
  appState.humanReviews = reviewResponse.reviews || [];

  renderTraceContextTiles();
  renderDecisionSummary();
  renderTelemetryTiles();
  renderAiDraftingPanel();
  renderWorkflowTimeline();
  renderAuditReplay();
  renderHumanReviewPanel();
}

async function refreshObservabilityStatus() {
  try {
    appState.observability = await requestJson("/api/observability/status");
  } catch (error) {
    appState.observability = {
      provider: "langsmith",
      tracing_status: "not_configured",
      project: "decisiontrace-phase2",
      trace_url: null,
      trace_url_supported: false,
      error_message: error.message,
    };
  }
  renderObservabilityTiles();
  renderTraceContextTiles();
}

function showView(viewName) {
  const monitoring = viewName === "monitoring";
  elements.workflowConsoleView.classList.toggle("hidden", monitoring);
  elements.monitoringDashboardView.classList.toggle("hidden", !monitoring);
  elements.workflowConsoleTab.classList.toggle("active", !monitoring);
  elements.monitoringDashboardTab.classList.toggle("active", monitoring);
  if (monitoring) {
    refreshMonitoringDashboard();
  }
}

async function loadMonitoringFilterOptions() {
  try {
    const data = await requestJson("/api/monitoring/outcomes");
    appState.monitoringOutcomes = data;
    elements.monitorWorkflowType.innerHTML = [
      '<option value="">Select Workflow Type</option>',
      ...(data.workflow_types || []).map(
        (workflowType) => `<option value="${escapeHtml(workflowType)}">${escapeHtml(workflowTypeLabel(workflowType))}</option>`,
      ),
    ].join("");
    elements.monitorOutcome.innerHTML = [
      '<option value="">All Workflow Outcomes</option>',
      ...(data.outcomes || []).map(
        (outcome) => `<option value="${escapeHtml(outcome)}">${escapeHtml(outcomeLabel(outcome))}</option>`,
      ),
    ].join("");
  } catch (error) {
    elements.monitoringKpis.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
  }
}

function monitoringFilters() {
  return {
    workflow_type: elements.monitorWorkflowType.value,
    outcome: elements.monitorOutcome.value,
    correlation_id: elements.monitorCorrelation.value.trim(),
  };
}

async function refreshMonitoringDashboard() {
  const filters = monitoringFilters();
  if (!filters.workflow_type) {
    appState.monitoringSummary = null;
    appState.monitoringRuns = [];
    elements.monitoringKpis.className = "telemetry-grid empty-state";
    elements.monitoringKpis.textContent = "Select a workflow type to view monitoring metrics.";
    elements.monitoringOutcomes.className = "outcome-grid empty-state";
    elements.monitoringOutcomes.textContent = "Outcome breakdown appears after a workflow type is selected.";
    elements.monitoringRuns.className = "monitoring-runs empty-state";
    elements.monitoringRuns.textContent = "Recent runs appear after a workflow type is selected.";
    elements.monitoringAuditDrilldown.className = "audit-replay empty-state";
    elements.monitoringAuditDrilldown.textContent = "Select View Audit on a recent run to inspect persisted audit events.";
    return;
  }

  const summaryQuery = queryString({
    workflow_type: filters.workflow_type,
    outcome: filters.outcome,
  });
  const runsQuery = queryString({
    ...filters,
    limit: 25,
  });

  elements.monitorRefresh.disabled = true;
  elements.monitorRefresh.textContent = "Refreshing...";
  try {
    const [summary, runs] = await Promise.all([
      requestJson(`/api/monitoring/summary${summaryQuery}`),
      requestJson(`/api/monitoring/runs${runsQuery}`),
    ]);
    appState.monitoringSummary = summary;
    appState.monitoringRuns = runs.runs || [];
    renderMonitoringSummary();
    renderMonitoringRuns();
  } catch (error) {
    elements.monitoringKpis.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
  } finally {
    elements.monitorRefresh.disabled = false;
    elements.monitorRefresh.textContent = "Refresh";
  }
}

function renderMonitoringSummary() {
  const summary = appState.monitoringSummary;
  if (!summary) {
    elements.monitoringKpis.className = "telemetry-grid empty-state";
    elements.monitoringKpis.textContent = "Select a workflow type to view monitoring metrics.";
    elements.monitoringOutcomes.className = "outcome-grid empty-state";
    elements.monitoringOutcomes.textContent = "Outcome breakdown appears after a workflow type is selected.";
    return;
  }

  elements.monitoringKpis.className = "telemetry-grid";
  elements.monitoringKpis.innerHTML = [
    telemetryCard("Total Workflow Runs", escapeHtml(summary.total_workflow_runs), "Persisted workflow_runs records.", "audit"),
    telemetryCard("Completed Runs", escapeHtml(summary.completed_runs), "Runs with completed workflow status.", "positive"),
    telemetryCard("Blocked", escapeHtml(summary.blocked_count), "Policy or guardrail blocked outcomes.", "warning"),
    telemetryCard("Escalated", escapeHtml(summary.escalated_count), "Runs routed to human review.", "review"),
    telemetryCard("Allowed / Action Created", escapeHtml(summary.allowed_action_count), "Runs that created a governed action.", "positive"),
    telemetryCard("Replacement Requests", escapeHtml(summary.replacement_request_count), "Replacement request IDs present in final state.", "positive"),
    telemetryCard("LLM Drafts Completed", escapeHtml(summary.llm_drafting_completed_count), "Provider-backed LLM drafting completions.", "audit"),
    telemetryCard("LLM Validation Failures", escapeHtml(summary.llm_validation_failed_count), "Drafts rejected by deterministic validation.", summary.llm_validation_failed_count ? "warning" : ""),
    telemetryCard("Total Tokens", escapeHtml(summary.total_tokens), "Provider token usage from persisted final_state.", "audit"),
    telemetryCard("Audit Events", escapeHtml(summary.total_audit_events), "Persisted audit event count.", "audit"),
    telemetryCard("Tool Calls", escapeHtml(summary.total_tool_calls), "Audit events with tool_name populated.", "audit"),
  ].join("");

  const breakdown = summary.outcome_breakdown || {};
  elements.monitoringOutcomes.className = "outcome-grid";
  elements.monitoringOutcomes.innerHTML = Object.entries(breakdown)
    .map(([outcome, count]) => `
      <article class="outcome-card">
        <strong>${escapeHtml(count)}</strong>
        <span>${escapeHtml(outcomeLabel(outcome))}</span>
      </article>
    `)
    .join("");
}

function renderMonitoringRuns() {
  const runs = appState.monitoringRuns || [];
  if (!runs.length) {
    elements.monitoringRuns.className = "monitoring-runs empty-state";
    elements.monitoringRuns.textContent = "No workflow runs found.";
    return;
  }

  elements.monitoringRuns.className = "monitoring-runs monitoring-table-wrap";
  elements.monitoringRuns.innerHTML = `
    <table class="monitoring-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Workflow Type</th>
          <th>Correlation ID</th>
          <th>Workflow ID</th>
          <th>Outcome</th>
          <th>Guardrail</th>
          <th>LLM Status</th>
          <th>Tokens</th>
          <th>Audit Events</th>
          <th>Tool Calls</th>
          <th>Drilldown</th>
        </tr>
      </thead>
      <tbody>
        ${runs.map((run) => `
          <tr>
            <td>${escapeHtml(dash(run.updated_at || run.created_at))}</td>
            <td>${escapeHtml(workflowTypeLabel(run.workflow_type))}</td>
            <td>${escapeHtml(dash(run.correlation_id))}</td>
            <td>${escapeHtml(dash(run.workflow_id))}</td>
            <td>${pill(outcomeLabel(run.outcome), "guardrail")}</td>
            <td>${escapeHtml(dash(run.guardrail_decision))}</td>
            <td>${escapeHtml(dash(run.llm_drafting_status))}</td>
            <td>${escapeHtml(dash(run.llm_total_tokens))}</td>
            <td>${escapeHtml(dash(run.audit_event_count))}</td>
            <td>${escapeHtml(dash(run.tool_call_count))}</td>
            <td><button class="link-button" data-workflow-id="${escapeHtml(run.workflow_id)}" type="button">View Audit</button></td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
  elements.monitoringRuns.querySelectorAll("[data-workflow-id]").forEach((button) => {
    button.addEventListener("click", () => loadMonitoringAudit(button.dataset.workflowId));
  });
}

async function loadMonitoringAudit(workflowId) {
  elements.monitoringAuditDrilldown.className = "audit-replay empty-state";
  elements.monitoringAuditDrilldown.textContent = "Loading audit events...";
  try {
    const audit = await requestJson(`/api/workflows/${workflowId}/audit`);
    const events = sortEvents(audit.events || []);
    if (!events.length) {
      elements.monitoringAuditDrilldown.textContent = "No audit events found for this workflow.";
      return;
    }
    elements.monitoringAuditDrilldown.className = "audit-replay";
    elements.monitoringAuditDrilldown.innerHTML = events.map((event, index) => `
      <article class="replay-card">
        <div class="replay-header">
          <div>
            <div class="replay-title">${index + 1}. ${escapeHtml(dash(event.event_type))}</div>
            <div class="audit-meta">Correlation: ${escapeHtml(dash(event.correlation_id || audit.correlation_id))}</div>
          </div>
          ${event.guardrail_decision ? pill(event.guardrail_decision, "guardrail") : ""}
        </div>
        <div class="replay-body">
          <div><div class="meta-label">Node</div><div>${escapeHtml(dash(event.node_name))}</div></div>
          <div><div class="meta-label">Tool</div><div>${escapeHtml(dash(event.tool_name))}</div></div>
          <div><div class="meta-label">Reason</div><div>${escapeHtml(dash(event.reason))}</div></div>
        </div>
      </article>
    `).join("");
  } catch (error) {
    elements.monitoringAuditDrilldown.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
  }
}

function renderObservabilityTiles() {
  const status = appState.observability || {
    provider: "langsmith",
    tracing_status: "not_configured",
    project: "decisiontrace-phase2",
    trace_url: null,
    trace_url_supported: false,
  };
  const tracingLabel = status.tracing_status === "enabled"
    ? "LangSmith tracing enabled"
    : status.tracing_status === "disabled"
      ? "LangSmith tracing disabled"
      : "LangSmith not configured";
  const traceLink = status.trace_url
    ? `<a href="${escapeHtml(status.trace_url)}" target="_blank" rel="noreferrer">Open trace</a>`
    : "Not available yet";

  elements.observability.innerHTML = [
    telemetryCard(
      "Provider",
      escapeHtml(safeText(status.provider, "langsmith")),
      "Configured tracing provider.",
      "audit",
    ),
    telemetryCard(
      "Tracing Status",
      pill(tracingLabel, status.tracing_status === "enabled" ? "workflow" : "llm"),
      "Controlled by LANGSMITH_TRACING and LANGSMITH_API_KEY.",
      status.tracing_status === "enabled" ? "positive" : "",
    ),
    telemetryCard(
      "Project",
      escapeHtml(safeText(status.project, "decisiontrace-phase2")),
      "LangSmith project name when tracing is enabled.",
      "audit",
    ),
    telemetryCard(
      "Trace Link",
      traceLink,
      status.trace_url_supported
        ? "Real trace URLs are provided by the backend when available."
        : "Trace links will appear in a future enhancement.",
      "",
    ),
  ].join("");
}

function renderTraceContextTiles() {
  const status = appState.observability || {};
  const workflow = appState.workflow || {};
  const correlationId = appState.correlationId || workflow.correlation_id || "Not Available";
  const intakeSessionId = appState.intakeSessionId || "Not Available";
  const workflowId = appState.workflowId || workflow.workflow_id || "Not Available";
  const tracingStatus = safeText(status.tracing_status, "Not Configured");

  elements.traceContext.innerHTML = [
    telemetryCard(
      "Correlation ID",
      escapeHtml(correlationId),
      "Shared identifier connecting intake, workflow, audit, and trace metadata.",
      correlationId === "Not Available" ? "" : "audit",
    ),
    telemetryCard(
      "Intake Session ID",
      escapeHtml(intakeSessionId),
      "In-memory Phase 2 intake session identifier.",
      intakeSessionId === "Not Available" ? "" : "audit",
    ),
    telemetryCard(
      "Workflow ID",
      escapeHtml(workflowId),
      "Governed workflow run identifier.",
      workflowId === "Not Available" ? "" : "workflow",
    ),
    telemetryCard(
      "LangSmith Project",
      escapeHtml(safeText(status.project, "decisiontrace-phase2")),
      "Tracing project when LangSmith is configured.",
      "audit",
    ),
    telemetryCard(
      "Tracing Status",
      pill(tracingStatus, "llm"),
      "Real backend observability status; no trace links are faked.",
      tracingStatus === "enabled" ? "positive" : "",
    ),
  ].join("");
}

function renderDecisionSummary() {
  const workflow = appState.workflow;
  if (!workflow) {
    elements.result.className = "decision-summary empty-state";
    elements.result.textContent = "Run a workflow to see the decision.";
    return;
  }

  elements.result.className = "decision-summary";
  elements.result.innerHTML = [
    summaryCard("Workflow Status", pill(workflow.workflow_status, "workflow"), { html: true }),
    summaryCard("Eligibility", pill(workflow.eligibility_status, "eligibility"), { html: true }),
    summaryCard("Guardrail Decision", pill(workflow.guardrail_decision, "guardrail", "Not Evaluated"), { html: true }),
    summaryCard("Replacement Request", escapeHtml(replacementAction(workflow))),
    summaryCard("Escalation", workflow.escalation_id ? pill(workflow.escalation_id, "review") : pill("Not Required"), { html: true }),
    summaryCard("Policy Reference", workflow.policy_reference || "Not Available"),
    summaryCard("Workflow ID", workflow.workflow_id || "Not Available"),
    summaryCard("Correlation ID", workflow.correlation_id || "Not Available"),
    summaryCard("Customer Response", workflow.customer_response || "No customer response yet.", {
      response: true,
    }),
    summaryCard("Response Source", pill(workflow.final_response_source, "response", "deterministic"), { html: true }),
  ].join("");
}

function renderAiDraftingPanel() {
  const workflow = appState.workflow;
  if (!workflow) {
    elements.aiDrafting.className = "ai-grid empty-state";
    elements.aiDrafting.textContent = "Run a workflow to see LLM drafting status.";
    return;
  }

  const validationErrors = workflow.llm_validation_errors || [];
  elements.aiDrafting.className = "ai-grid";
  elements.aiDrafting.innerHTML = [
    summaryCard("Drafting Status", pill(workflow.llm_drafting_status, "llm", "Not Available"), { html: true }),
    summaryCard("Model Used", workflow.llm_model_name || "Not Configured"),
    summaryCard("Validation Status", pill(workflow.llm_validation_status, "llm", "Not Run"), { html: true }),
    summaryCard("Final Response Source", pill(workflow.final_response_source, "response", "deterministic"), { html: true }),
    summaryCard("Input Tokens", workflow.llm_input_tokens ?? "Not Available"),
    summaryCard("Output Tokens", workflow.llm_output_tokens ?? "Not Available"),
    summaryCard("Cached Tokens", workflow.llm_cached_tokens ?? "Not Available"),
    summaryCard("Total Tokens", workflow.llm_total_tokens ?? "Not Available"),
    summaryCard(
      "Validation Errors",
      validationErrors.length ? validationErrors.join("; ") : "None",
      { response: true },
    ),
  ].join("");
}

function renderTelemetryTiles() {
  const workflow = appState.workflow;
  const events = appState.auditEvents;
  const reviews = appState.humanReviews;
  const toolCalls = events.filter((event) => event.tool_name).length;
  const reviewStatus = humanReviewStatus(workflow, reviews);
  const replacement = replacementAction(workflow);
  const policyUsed = workflow?.policy_reference || "Not Available";

  elements.telemetry.innerHTML = [
    telemetryCard(
      "Workflow Status",
      pill(workflow?.workflow_status, "workflow", "Not Started"),
      "Final workflow status returned by the API.",
      workflow?.workflow_status === "completed" ? "positive" : "",
    ),
    telemetryCard(
      "Eligibility",
      pill(workflow?.eligibility_status, "eligibility", "Not Evaluated"),
      "Deterministic eligibility result from the workflow.",
      workflow?.eligibility_status === "not_eligible" ? "warning" : "",
    ),
    telemetryCard(
      "Guardrail Decision",
      pill(workflow?.guardrail_decision, "guardrail", "Not Evaluated"),
      "Action control outcome before replacement creation.",
      workflow?.guardrail_decision === "block" ? "warning" : workflow?.guardrail_decision === "allow" ? "positive" : workflow?.guardrail_decision === "escalate" ? "review" : "",
    ),
    telemetryCard(
      "Replacement Action",
      pill(replacement, "replacement"),
      "Created only when guardrails allow the action.",
      !workflow ? "" : replacement === "Not Created" ? "warning" : "positive",
    ),
    telemetryCard(
      "Policy Used",
      escapeHtml(policyUsed),
      "Current policy reference returned by policy retrieval.",
      "audit",
    ),
    telemetryCard(
      "Audit Events Count",
      escapeHtml(String(events.length)),
      "Persisted audit events for this workflow run.",
      "audit",
    ),
    telemetryCard(
      "Tool Calls Count",
      escapeHtml(String(toolCalls)),
      "Audit events with an associated tool_name.",
      "audit",
    ),
    telemetryCard(
      "Human Review Status",
      pill(reviewStatus, "review"),
      "Derived from escalation state and persisted reviews.",
      reviewStatus === "Required" ? "review" : reviewStatus.startsWith("Completed") ? "positive" : "",
    ),
  ].join("");
}

function timelineTone(event) {
  if (event.guardrail_decision === "block" || event.event_type === "eligibility_checked") {
    return "warning";
  }
  if (event.event_type === "human_escalation_created") {
    return "review";
  }
  if (event.event_type === "replacement_request_created" || event.event_type === "workflow_completed") {
    return "positive";
  }
  if (event.event_type === "llm_response_validation_passed") {
    return "positive";
  }
  if (event.event_type === "llm_response_validation_failed" || event.event_type === "llm_response_drafting_failed") {
    return "warning";
  }
  return "";
}

function renderWorkflowTimeline() {
  const events = appState.auditEvents;
  if (!events.length) {
    elements.timeline.className = "timeline empty-state";
    elements.timeline.textContent = "Audit events will appear after a workflow run.";
    return;
  }

  elements.timeline.className = "timeline";
  elements.timeline.innerHTML = events
    .map((event) => `
      <article class="timeline-row ${timelineTone(event)}">
        <div>
          <div class="timeline-title">${escapeHtml(dash(event.event_type))}</div>
          <div class="timeline-meta">${escapeHtml(dash(event.timestamp))}</div>
        </div>
        <div class="timeline-meta">
          <div><strong>Node:</strong> ${escapeHtml(dash(event.node_name))}</div>
          <div><strong>Tool:</strong> ${escapeHtml(dash(event.tool_name))}</div>
          <div><strong>Correlation:</strong> ${escapeHtml(dash(event.correlation_id))}</div>
          <div><strong>Policy:</strong> ${escapeHtml(dash(event.policy_reference))}</div>
          <div><strong>Guardrail:</strong> ${escapeHtml(dash(event.guardrail_decision))}</div>
        </div>
        <div class="timeline-reason">${escapeHtml(dash(event.reason))}</div>
      </article>
    `)
    .join("");
}

function auditMeaning(event) {
  const meanings = {
    workflow_started: "The workflow run was initialized with a workflow ID and correlation ID.",
    identity_verified: "Customer identity verification completed.",
    order_lookup_completed: "Order ownership and minimal order context were checked.",
    policy_retrieved: "The current warranty policy was retrieved for decisioning.",
    eligibility_checked: "Eligibility was evaluated against the current policy.",
    inventory_checked: "Replacement inventory availability was checked.",
    guardrail_decision: "The deterministic replacement action guardrail made a decision.",
    replacement_request_created: "A replacement request was created after guardrails allowed it.",
    human_escalation_created: "The workflow created a human escalation for review.",
    llm_response_drafting_skipped: "LLM drafting was skipped because it was disabled or not configured.",
    llm_response_drafted: "The LLM drafted response language from minimized approved workflow state.",
    llm_response_validation_passed: "The LLM draft passed deterministic response validation.",
    llm_response_validation_failed: "The LLM draft failed validation and deterministic fallback was used.",
    llm_response_drafting_failed: "The LLM drafting call failed and deterministic fallback was used.",
    customer_response_generated: "A customer-safe response was generated from workflow state.",
    workflow_completed: "The workflow completed successfully.",
    workflow_failed: "The workflow failed and recorded an audit event.",
  };
  return meanings[event.event_type] || "Workflow event recorded.";
}

function renderAuditReplay() {
  const events = appState.auditEvents;
  if (!events.length) {
    elements.auditReplay.className = "audit-replay empty-state";
    elements.auditReplay.textContent = "Run a workflow to inspect node, tool, policy, and guardrail evidence.";
    return;
  }

  elements.auditReplay.className = "audit-replay";
  elements.auditReplay.innerHTML = events
    .map((event, index) => {
      const output = JSON.stringify(event.output_summary || {}, null, 2);
      return `
        <article class="replay-card">
          <div class="replay-header">
            <div>
              <div class="replay-title">${index + 1}. ${escapeHtml(dash(event.event_type))}</div>
              <div class="audit-meta">${escapeHtml(auditMeaning(event))}</div>
            </div>
            ${event.guardrail_decision ? pill(event.guardrail_decision, "guardrail") : ""}
          </div>
          <div class="replay-body">
            <div>
              <div class="meta-label">Node</div>
              <div>${escapeHtml(dash(event.node_name))}</div>
            </div>
            <div>
              <div class="meta-label">Tool</div>
              <div>${escapeHtml(dash(event.tool_name))}</div>
            </div>
            <div>
              <div class="meta-label">Correlation</div>
              <div>${escapeHtml(dash(event.correlation_id))}</div>
            </div>
            <div>
              <div class="meta-label">Policy</div>
              <div>${escapeHtml(dash(event.policy_reference))}</div>
            </div>
            <div>
              <div class="meta-label">Reason</div>
              <div>${escapeHtml(dash(event.reason))}</div>
            </div>
            <pre class="replay-evidence">${escapeHtml(output)}</pre>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderHumanReviewPanel() {
  const workflow = appState.workflow;
  const reviews = appState.humanReviews;
  elements.reviewResponse.innerHTML = "";

  if (workflow?.escalation_id) {
    elements.reviewContent.className = "review-card";
    elements.reviewContent.innerHTML = `
      <strong>Escalation ID:</strong> ${escapeHtml(workflow.escalation_id)}<br />
      ${escapeHtml(safeText(workflow.escalation_reason, "Human review required."))}
    `;
    elements.reviewForm.classList.remove("hidden");
  } else {
    elements.reviewContent.className = "empty-state";
    elements.reviewContent.textContent = "No human review currently required.";
    elements.reviewForm.classList.add("hidden");
  }

  renderReviewRecords(reviews);
}

function renderReviewRecords(reviews) {
  if (!reviews.length) {
    elements.reviewRecords.innerHTML = "";
    return;
  }

  elements.reviewRecords.innerHTML = reviews
    .map((review) => `
      <article class="review-card">
        <strong>${escapeHtml(safeText(review.status, "recorded"))}</strong>
        <div class="audit-meta">
          Reviewer: ${escapeHtml(dash(review.reviewer_id))} · Decision: ${escapeHtml(dash(review.decision))}
        </div>
        <div>${escapeHtml(safeText(review.reason, "No reason provided."))}</div>
      </article>
    `)
    .join("");
}

async function submitHumanReview(event) {
  event.preventDefault();
  if (!appState.workflowId) {
    elements.reviewResponse.innerHTML = `<div class="error">Run a workflow first.</div>`;
    return;
  }

  try {
    const response = await requestJson(`/api/workflows/${appState.workflowId}/human-review`, {
      method: "POST",
      body: JSON.stringify({
        reviewer_id: elements.reviewerId.value,
        decision: elements.reviewDecision.value,
        reason: elements.reviewReason.value,
      }),
    });

    elements.reviewResponse.innerHTML = `
      <div class="review-card">
        <strong>${escapeHtml(response.status)}</strong><br />
        ${escapeHtml(response.message)}
      </div>
    `;
    await refreshWorkflowView(appState.workflowId);
  } catch (error) {
    elements.reviewResponse.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
  }
}

function loadMissingInfoScenario() {
  elements.intakeMessage.value = "My laptop screen cracked after 9 months. Can I get a replacement?";
  appState.intakeResult = null;
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  renderIntakeResult();
  renderConversation();
  renderTraceContextTiles();
  elements.replyIntake.classList.add("hidden");
  updateRunWorkflowAvailability();
  setStatus("Missing info scenario loaded. Analyze to see required customer and order details.");
  setIntakeStatus("");
}

function loadCrackedScreenScenario() {
  elements.intakeMessage.value = "My laptop screen cracked after 9 months. Can I get a replacement? Customer ID is cust_primary_001 and order ID is ord_laptop_001.";
  appState.intakeResult = null;
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  renderIntakeResult();
  renderConversation();
  renderTraceContextTiles();
  elements.replyIntake.classList.add("hidden");
  updateRunWorkflowAvailability();
  setStatus("Complete cracked screen scenario loaded. Analyze to extract identifiers.");
  setIntakeStatus("");
}

function loadEligibleManufacturingDefectScenario() {
  elements.intakeMessage.value = "My laptop stopped powering on after 6 months. Can I get a replacement? Customer ID is cust_primary_001 and order ID is ord_laptop_power_001.";
  appState.intakeResult = null;
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  renderIntakeResult();
  renderConversation();
  renderTraceContextTiles();
  elements.replyIntake.classList.add("hidden");
  updateRunWorkflowAvailability();
  setStatus("Eligible manufacturing defect scenario loaded. Analyze to extract identifiers.");
  setIntakeStatus("");
}

function loadUnknownCustomerScenario() {
  elements.intakeMessage.value = "I need a replacement for my laptop. Customer ID is cust_unknown_001 and order ID is ord_laptop_001.";
  appState.intakeResult = null;
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  renderIntakeResult();
  renderConversation();
  renderTraceContextTiles();
  elements.replyIntake.classList.add("hidden");
  updateRunWorkflowAvailability();
  setStatus("Unknown customer scenario loaded. Analyze to extract identifiers.");
  setIntakeStatus("");
}

function loadInvalidIdentifierScenario() {
  elements.intakeMessage.value = "My laptop screen cracked. Customer ID is UNKNOWN_CUSTOMER and order ID is ord_laptop_001.";
  appState.intakeResult = null;
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  renderIntakeResult();
  renderConversation();
  renderTraceContextTiles();
  elements.replyIntake.classList.add("hidden");
  updateRunWorkflowAvailability();
  setStatus("Invalid identifier scenario loaded. Analyze to see format validation.");
  setIntakeStatus("");
}

function clearIntake() {
  elements.intakeMessage.value = "";
  appState.intakeResult = null;
  appState.intakeSessionId = null;
  appState.correlationId = null;
  appState.intakeOriginalMessage = null;
  appState.conversationMessages = [];
  renderIntakeResult();
  renderConversation();
  renderTraceContextTiles();
  elements.replyIntake.classList.add("hidden");
  updateRunWorkflowAvailability();
  setStatus("Intake cleared.");
  setIntakeStatus("");
}

function initializeConsole() {
  if (!elements.analyzeRequest) {
    return;
  }
  renderTelemetryTiles();
  renderObservabilityTiles();
  renderTraceContextTiles();
  renderAiDraftingPanel();
  renderIntakeResult();
  renderConversation();
  renderMonitoringSummary();
  renderMonitoringRuns();
  updateRunWorkflowAvailability();
  refreshObservabilityStatus();
  loadMonitoringFilterOptions();
  elements.workflowConsoleTab.addEventListener("click", () => showView("workflow"));
  elements.monitoringDashboardTab.addEventListener("click", () => showView("monitoring"));
  elements.monitorRefresh.addEventListener("click", refreshMonitoringDashboard);
  elements.monitorWorkflowType.addEventListener("change", refreshMonitoringDashboard);
  elements.monitorOutcome.addEventListener("change", refreshMonitoringDashboard);
  elements.monitorCorrelation.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      refreshMonitoringDashboard();
    }
  });
  elements.analyzeRequest.addEventListener("click", analyzeRequest);
  elements.replyIntake.addEventListener("click", replyToIntake);
  elements.runButton.addEventListener("click", startWorkflow);
  elements.loadMissing.addEventListener("click", loadMissingInfoScenario);
  elements.loadCracked.addEventListener("click", loadCrackedScreenScenario);
  elements.loadEligible.addEventListener("click", loadEligibleManufacturingDefectScenario);
  elements.loadUnknown.addEventListener("click", loadUnknownCustomerScenario);
  elements.loadInvalid.addEventListener("click", loadInvalidIdentifierScenario);
  elements.clearIntake.addEventListener("click", clearIntake);
  elements.reviewForm.addEventListener("submit", submitHumanReview);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeConsole);
} else {
  initializeConsole();
}
