const state = {
  workflowId: null,
  workflow: null,
};

const elements = {
  request: document.querySelector("#customer-request"),
  customerId: document.querySelector("#customer-id"),
  orderId: document.querySelector("#order-id"),
  runButton: document.querySelector("#run-workflow"),
  loadCracked: document.querySelector("#load-cracked"),
  loadUnknown: document.querySelector("#load-unknown"),
  status: document.querySelector("#status-message"),
  result: document.querySelector("#workflow-result"),
  decision: document.querySelector("#decision-summary"),
  audit: document.querySelector("#audit-timeline"),
  reviewContent: document.querySelector("#review-content"),
  reviewForm: document.querySelector("#review-form"),
  reviewerId: document.querySelector("#reviewer-id"),
  reviewDecision: document.querySelector("#review-decision"),
  reviewReason: document.querySelector("#review-reason"),
  reviewResponse: document.querySelector("#review-response"),
};

function setLoading(isLoading) {
  elements.runButton.disabled = isLoading;
  elements.runButton.textContent = isLoading ? "Running..." : "Run Warranty Workflow";
}

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.className = isError ? "status-message error" : "status-message";
}

function safeValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

function badgeForDecision(value) {
  if (value === "allow") {
    return `<span class="badge badge-positive">${value}</span>`;
  }
  if (value === "block") {
    return `<span class="badge badge-warning">${value}</span>`;
  }
  if (value) {
    return `<span class="badge badge-review">${value}</span>`;
  }
  return "—";
}

function kv(label, value, options = {}) {
  const classes = options.wide ? "kv-item wide" : "kv-item";
  return `
    <div class="${classes}">
      <div class="kv-label">${label}</div>
      <div class="kv-value">${value}</div>
    </div>
  `;
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
  setLoading(true);
  setStatus("Running workflow...");
  elements.reviewResponse.innerHTML = "";

  try {
    const result = await requestJson("/api/workflows/start", {
      method: "POST",
      body: JSON.stringify({
        customer_request: elements.request.value,
        customer_id: elements.customerId.value,
        order_id: elements.orderId.value,
      }),
    });

    state.workflowId = result.workflow_id;
    await loadWorkflowState(result.workflow_id);
    await loadAuditTimeline(result.workflow_id);
    setStatus("Workflow completed.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setLoading(false);
  }
}

async function loadWorkflowState(workflowId) {
  const response = await requestJson(`/api/workflows/${workflowId}`);
  state.workflow = response.state;
  renderWorkflowResult(response.state);
  renderDecisionSummary(response.state);
  renderHumanReview(response.state);
}

async function loadAuditTimeline(workflowId) {
  const response = await requestJson(`/api/workflows/${workflowId}/audit`);
  renderAuditTimeline(response.events);
}

function renderWorkflowResult(workflow) {
  elements.result.className = "kv-grid";
  elements.result.innerHTML = [
    kv("workflow_id", safeValue(workflow.workflow_id)),
    kv("correlation_id", safeValue(workflow.correlation_id)),
    kv("workflow_status", safeValue(workflow.workflow_status)),
    kv("eligibility_status", safeValue(workflow.eligibility_status)),
    kv("guardrail_decision", badgeForDecision(workflow.guardrail_decision)),
    kv("replacement_request_id", safeValue(workflow.replacement_request_id)),
    kv("escalation_id", workflow.escalation_id ? `<span class="badge badge-review">${workflow.escalation_id}</span>` : "—"),
    kv("customer_response", safeValue(workflow.customer_response), { wide: true }),
  ].join("");
}

function renderDecisionSummary(workflow) {
  elements.decision.className = "decision-grid";
  elements.decision.innerHTML = [
    kv("Identity verified", safeValue(workflow.identity_verified)),
    kv("Order retrieved", safeValue(workflow.order_retrieved)),
    kv("Policy reference", safeValue(workflow.policy_reference)),
    kv("Eligibility status", safeValue(workflow.eligibility_status)),
    kv("Inventory available", safeValue(workflow.inventory_available)),
    kv("Guardrail decision", badgeForDecision(workflow.guardrail_decision)),
    kv("Escalation reason", safeValue(workflow.escalation_reason), { wide: true }),
  ].join("");
}

function renderAuditTimeline(events) {
  if (!events.length) {
    elements.audit.className = "timeline empty-state";
    elements.audit.textContent = "No audit events recorded.";
    return;
  }

  elements.audit.className = "timeline";
  elements.audit.innerHTML = events
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .map((event) => {
      return `
        <article class="timeline-row">
          <div>
            <div class="timeline-title">${safeValue(event.event_type)}</div>
            <div class="timeline-meta">${safeValue(event.timestamp)}</div>
          </div>
          <div class="timeline-meta">
            <div><strong>Node:</strong> ${safeValue(event.node_name)}</div>
            <div><strong>Tool:</strong> ${safeValue(event.tool_name)}</div>
            <div><strong>Policy:</strong> ${safeValue(event.policy_reference)}</div>
            <div><strong>Guardrail:</strong> ${safeValue(event.guardrail_decision)}</div>
          </div>
          <div class="timeline-reason">${safeValue(event.reason)}</div>
        </article>
      `;
    })
    .join("");
}

function renderHumanReview(workflow) {
  elements.reviewResponse.innerHTML = "";
  if (workflow.escalation_id) {
    elements.reviewContent.className = "review-card";
    elements.reviewContent.innerHTML = `
      <strong>Review needed:</strong> ${workflow.escalation_id}<br />
      ${safeValue(workflow.escalation_reason)}
    `;
    elements.reviewForm.classList.remove("hidden");
    return;
  }

  elements.reviewContent.className = "empty-state";
  elements.reviewContent.textContent = "No human review currently required.";
  elements.reviewForm.classList.add("hidden");
}

async function submitHumanReview(event) {
  event.preventDefault();
  if (!state.workflowId) {
    elements.reviewResponse.innerHTML = `<div class="error">Run a workflow first.</div>`;
    return;
  }

  try {
    const response = await requestJson(`/api/workflows/${state.workflowId}/human-review`, {
      method: "POST",
      body: JSON.stringify({
        reviewer_id: elements.reviewerId.value,
        decision: elements.reviewDecision.value,
        reason: elements.reviewReason.value,
      }),
    });

    elements.reviewResponse.innerHTML = `
      <div class="review-card">
        <strong>${response.status}</strong><br />
        ${response.message}
      </div>
    `;
    await loadWorkflowState(state.workflowId);
  } catch (error) {
    elements.reviewResponse.innerHTML = `<div class="error">${error.message}</div>`;
  }
}

function loadCrackedScreenScenario() {
  elements.request.value = "My laptop screen cracked after 9 months. Can I get a replacement?";
  elements.customerId.value = "cust_primary_001";
  elements.orderId.value = "ord_laptop_001";
  setStatus("Cracked screen scenario loaded.");
}

function loadUnknownCustomerScenario() {
  elements.request.value = "I need a replacement for my laptop.";
  elements.customerId.value = "UNKNOWN_CUSTOMER";
  elements.orderId.value = "ord_laptop_001";
  setStatus("Unknown customer scenario loaded.");
}

elements.runButton.addEventListener("click", startWorkflow);
elements.loadCracked.addEventListener("click", loadCrackedScreenScenario);
elements.loadUnknown.addEventListener("click", loadUnknownCustomerScenario);
elements.reviewForm.addEventListener("submit", submitHumanReview);
