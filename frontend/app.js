const appState = {
  workflowId: null,
  workflow: null,
  auditEvents: [],
  humanReviews: [],
  intakeResult: null,
};

const elements = {
  intakeMessage: document.querySelector("#intake-message"),
  analyzeRequest: document.querySelector("#analyze-intake-button"),
  intakeStatus: document.querySelector("#intake-status"),
  intakeResult: document.querySelector("#intake-result"),
  useContext: document.querySelector("#use-context"),
  contextPreview: document.querySelector("#context-preview"),
  customerId: document.querySelector("#customer-id"),
  orderId: document.querySelector("#order-id"),
  runButton: document.querySelector("#run-workflow"),
  loadCracked: document.querySelector("#load-cracked"),
  loadUnknown: document.querySelector("#load-unknown"),
  clearContext: document.querySelector("#clear-context"),
  clearIntake: document.querySelector("#clear-intake"),
  status: document.querySelector("#status-message"),
  result: document.querySelector("#workflow-result"),
  telemetry: document.querySelector("#telemetry-tiles"),
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
  if (value === "Not Ready" || value === "Clarification Required") {
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

function routerField(label, value, kind = "neutral") {
  const rendered = kind === "pill" ? pill(value) : escapeHtml(safeText(value));
  return `
    <div class="router-field">
      <div class="summary-label">${escapeHtml(label)}</div>
      <div class="summary-value">${rendered}</div>
    </div>
  `;
}

function optionalValue(element) {
  const value = element.value.trim();
  return value || null;
}

function getContextPayload() {
  if (!elements.useContext.checked) {
    return {
      customer_id: null,
      order_id: null,
    };
  }
  return {
    customer_id: optionalValue(elements.customerId),
    order_id: optionalValue(elements.orderId),
  };
}

function getWorkflowIdentifiers() {
  return {
    customer_id: appState.intakeResult?.customer_id || optionalValue(elements.customerId),
    order_id: appState.intakeResult?.order_id || optionalValue(elements.orderId),
  };
}

function hasRequiredContext() {
  const identifiers = getWorkflowIdentifiers();
  return Boolean(identifiers.customer_id && identifiers.order_id);
}

function updateRunWorkflowAvailability() {
  const messageReady = Boolean(elements.intakeMessage.value.trim());
  const routerReady = Boolean(appState.intakeResult?.can_start_workflow);
  const checkedContextReady = elements.useContext.checked
    && Boolean(optionalValue(elements.customerId))
    && Boolean(optionalValue(elements.orderId));
  elements.runButton.disabled = !(messageReady && (routerReady || checkedContextReady));
}

function updateContextPreview() {
  const context = getContextPayload();
  elements.contextPreview.innerHTML = `
    <div>
      <span class="summary-label">Context sent to router</span>
      <strong>Customer ID:</strong> ${escapeHtml(safeText(context.customer_id, "Not provided"))}
      <span class="context-divider">•</span>
      <strong>Order ID:</strong> ${escapeHtml(safeText(context.order_id, "Not provided"))}
    </div>
  `;
  updateRunWorkflowAvailability();
}

function resetRouterResult() {
  appState.intakeResult = null;
  renderIntakeResult();
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
    setStatus("Customer ID and Order ID are required to start the governed workflow.", true);
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
        customer_request: elements.intakeMessage.value,
        customer_id: identifiers.customer_id,
        order_id: identifiers.order_id,
      }),
    });

    appState.workflowId = result.workflow_id;
    await refreshWorkflowView(result.workflow_id);
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
  elements.analyzeRequest.textContent = "Analyzing...";
  setIntakeStatus("Analyzing request...");

  try {
    const result = await requestJson("/api/intake/route", {
      method: "POST",
      body: JSON.stringify({
        message: elements.intakeMessage.value,
        ...getContextPayload(),
      }),
    });

    appState.intakeResult = result;
    renderIntakeResult();

    if (result.customer_id && elements.useContext.checked) {
      elements.customerId.value = result.customer_id;
    }
    if (result.order_id && elements.useContext.checked) {
      elements.orderId.value = result.order_id;
    }
    updateContextPreview();

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
    elements.analyzeRequest.textContent = "Analyze Request";
    updateRunWorkflowAvailability();
  }
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
  elements.intakeResult.className = "intake-result router-grid";
  elements.intakeResult.innerHTML = [
    routerField("Intent", result.intent, "pill"),
    routerField("Confidence", result.confidence ?? "Not Available"),
    routerField("Product Type", result.product_type || "Not Available"),
    routerField("Product Issue", result.product_issue || "Not Available"),
    routerField("Damage Type", result.damage_type || "Not Available"),
    routerField("Requires Clarification", clarificationText(result), "pill"),
    routerField("Missing Fields", missingFields),
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

  const [auditResponse, reviewResponse] = await Promise.all([
    requestJson(`/api/workflows/${workflowId}/audit`),
    requestJson(`/api/workflows/${workflowId}/human-reviews`),
  ]);

  appState.auditEvents = sortEvents(auditResponse.events || []);
  appState.humanReviews = reviewResponse.reviews || [];

  renderDecisionSummary();
  renderTelemetryTiles();
  renderAiDraftingPanel();
  renderWorkflowTimeline();
  renderAuditReplay();
  renderHumanReviewPanel();
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

function loadCrackedScreenScenario() {
  elements.intakeMessage.value = "My laptop screen cracked after 9 months. Can I get a replacement?";
  elements.customerId.value = "cust_primary_001";
  elements.orderId.value = "ord_laptop_001";
  elements.useContext.checked = true;
  appState.intakeResult = null;
  renderIntakeResult();
  updateContextPreview();
  setStatus("Cracked screen scenario loaded with optional workflow context.");
}

function loadUnknownCustomerScenario() {
  elements.intakeMessage.value = "I need a replacement for my laptop.";
  elements.customerId.value = "UNKNOWN_CUSTOMER";
  elements.orderId.value = "ord_laptop_001";
  elements.useContext.checked = true;
  appState.intakeResult = null;
  renderIntakeResult();
  updateContextPreview();
  setStatus("Unknown customer scenario loaded with optional workflow context.");
}

function clearContext() {
  elements.customerId.value = "";
  elements.orderId.value = "";
  elements.useContext.checked = false;
  appState.intakeResult = null;
  renderIntakeResult();
  updateContextPreview();
  setStatus("Optional workflow context cleared.");
}

function clearIntake() {
  elements.intakeMessage.value = "";
  elements.customerId.value = "";
  elements.orderId.value = "";
  elements.useContext.checked = false;
  appState.intakeResult = null;
  renderIntakeResult();
  updateContextPreview();
  setStatus("Intake cleared.");
  setIntakeStatus("");
}

function initializeConsole() {
  if (!elements.analyzeRequest) {
    return;
  }
  renderTelemetryTiles();
  renderAiDraftingPanel();
  renderIntakeResult();
  updateContextPreview();
  elements.analyzeRequest.addEventListener("click", analyzeRequest);
  elements.runButton.addEventListener("click", startWorkflow);
  elements.loadCracked.addEventListener("click", loadCrackedScreenScenario);
  elements.loadUnknown.addEventListener("click", loadUnknownCustomerScenario);
  elements.clearContext.addEventListener("click", clearContext);
  elements.clearIntake.addEventListener("click", clearIntake);
  elements.useContext.addEventListener("change", () => {
    updateContextPreview();
    resetRouterResult();
  });
  elements.customerId.addEventListener("input", () => {
    updateContextPreview();
    resetRouterResult();
  });
  elements.orderId.addEventListener("input", () => {
    updateContextPreview();
    resetRouterResult();
  });
  elements.intakeMessage.addEventListener("input", resetRouterResult);
  elements.reviewForm.addEventListener("submit", submitHumanReview);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeConsole);
} else {
  initializeConsole();
}
