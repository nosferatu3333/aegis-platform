const form = document.querySelector("#mission-form");
const taskInput = document.querySelector("#mission-task");
const analyzeButton = document.querySelector("#analyze-button");
const executeButton = document.querySelector("#execute-button");
const buttonLabel = analyzeButton.querySelector(".button-label");
const executeButtonLabel = executeButton.querySelector(".button-label");
const errorMessage = document.querySelector("#error-message");
const resultPanel = document.querySelector("#result-panel");
const executionPanel = document.querySelector("#execution-panel");
const validationPanel = document.querySelector("#validation-panel");
const governedButton = document.querySelector("#governed-button");
const governedButtonLabel = governedButton.querySelector(".button-label");
const governedPanel = document.querySelector("#governed-panel");
let latestAnalysis = null;

function setText(selector, value, fallback = "Not available") {
  const element = document.querySelector(selector);
  element.textContent =
    value === undefined || value === null || value === ""
      ? fallback
      : String(value);
}

function renderChips(containerSelector, values) {
  const container = document.querySelector(containerSelector);
  container.replaceChildren();

  if (!values || values.length === 0) {
    const empty = document.createElement("span");
    empty.className = "empty-value";
    empty.textContent = "None";
    container.append(empty);
    return;
  }

  values.forEach((value) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    container.append(chip);
  });
}

function renderWorkflow(steps) {
  const list = document.querySelector("#workflow-steps");
  const orderedSteps = [...(steps || [])].sort(
    (left, right) => left.order - right.order,
  );

  list.replaceChildren();
  setText("#workflow-count", `${orderedSteps.length} steps`);

  orderedSteps.forEach((step) => {
    const item = document.createElement("li");
    item.className = "workflow-step";

    const content = document.createElement("div");
    const title = document.createElement("h4");
    const description = document.createElement("p");
    const status = document.createElement("span");

    title.textContent = step.title;
    description.textContent = step.description;
    status.className = "step-status";
    status.textContent = step.status || "pending";

    content.append(title, description);
    item.append(content, status);
    list.append(item);
  });
}

function renderResult(payload) {
  latestAnalysis = payload;
  const intent = payload.intent || {};
  const capability = payload.capability || {};
  const secondaryIntents = intent.secondary_intents || [];

  setText("#pipeline-status", payload.status);
  setText("#original-task", payload.task);
  setText("#primary-intent", intent.primary_intent);
  setText("#complexity", intent.complexity);
  setText("#risk-level", intent.risk);
  setText("#selected-capability", capability.name || capability.capability_id);
  setText("#confidence", capability.confidence);
  setText("#score", capability.score);

  renderChips("#required-capabilities", intent.required_capabilities);
  renderChips("#secondary-intents", secondaryIntents);
  document.querySelector("#secondary-intents-group").hidden =
    secondaryIntents.length === 0;

  renderWorkflow(payload.workflow);
  document.querySelector("#raw-json").textContent = JSON.stringify(
    payload,
    null,
    2,
  );

  if (payload.status === "failed" && payload.metadata?.failure_reason) {
    errorMessage.textContent = payload.metadata.failure_reason;
    errorMessage.hidden = false;
  }

  resultPanel.hidden = false;
}

function renderExecution(receipt) {
  const steps = [...(receipt.steps || [])].sort(
    (left, right) => left.order - right.order,
  );
  const list = document.querySelector("#execution-steps");
  list.replaceChildren();

  setText("#execution-status", receipt.status);
  setText(
    "#receipt-summary",
    `${receipt.completed_steps} completed · ${receipt.failed_steps} failed`,
  );
  setText("#execution-count", `${steps.length} steps`);

  steps.forEach((step) => {
    const item = document.createElement("li");
    item.className = "workflow-step";
    const content = document.createElement("div");
    const title = document.createElement("h4");
    const output = document.createElement("p");
    const status = document.createElement("span");

    title.textContent = step.description;
    output.textContent =
      step.error || step.outputs?.message || "No simulated output.";
    status.className = "step-status";
    status.textContent = step.status;
    content.append(title, output);
    item.append(content, status);
    list.append(item);
  });

  document.querySelector("#execution-json").textContent = JSON.stringify(
    receipt,
    null,
    2,
  );
  executionPanel.hidden = false;
}

function renderValidation(validation) {
  const checks = validation.checks || [];
  const checkList = document.querySelector("#validation-checks");
  const evidenceList = document.querySelector("#validation-evidence");
  checkList.replaceChildren();
  evidenceList.replaceChildren();

  setText("#validation-status", validation.status);
  setText("#operation-outcome", validation.operation_outcome);
  setText("#validation-count", `${checks.length} checks`);

  checks.forEach((check) => {
    const item = document.createElement("li");
    item.className = "workflow-step";
    const content = document.createElement("div");
    const title = document.createElement("h4");
    const evidence = document.createElement("p");
    const status = document.createElement("span");

    title.textContent = check.name.replaceAll("_", " ");
    evidence.textContent = check.evidence;
    status.className = "step-status";
    status.textContent = check.status;
    content.append(title, evidence);
    item.append(content, status);
    checkList.append(item);

    const evidenceItem = document.createElement("li");
    evidenceItem.textContent = check.evidence;
    evidenceList.append(evidenceItem);
  });

  document.querySelector("#validation-json").textContent = JSON.stringify(
    validation,
    null,
    2,
  );
  validationPanel.hidden = false;
}


function canonicalToken(prefix) {
  const token = crypto.randomUUID().replaceAll("-", "");
  return `${prefix}_${token}`;
}

function canonicalCapabilityId(value) {
  const normalized = String(value || "demo")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return `cap_${normalized || "demo"}`;
}

function buildGovernedRequest() {
  if (!latestAnalysis || latestAnalysis.status !== "ready") {
    throw new Error("Analyze a supported mission before running the governed demo.");
  }

  const capability = latestAnalysis.capability || {};
  return {
    task: taskInput.value,
    interpretation_id: canonicalToken("int"),
    selection: {
      request_id: canonicalToken("req"),
      capability_id: canonicalCapabilityId(capability.capability_id || capability.name),
      capability_version: "0.1.0-demo",
      eligibility: "eligible",
      rationale: "Explicit browser demonstration selection derived from the visible analysis result.",
      health_state: "healthy",
      authority_requirement: "none",
      selection_id: canonicalToken("sel"),
    },
    selected_agent: capability.name || "Demonstration Agent",
    workflow_definition: (latestAnalysis.workflow || []).map(
      (step) => step.description || step.title,
    ),
    execute: true,
  };
}

function renderGoverned(payload) {
  const authority = payload.authority || {};
  const reconciliation = payload.reconciliation || {};

  setText("#governed-status", payload.status);
  setText(
    "#authority-outcome",
    authority.ready ? "allowed" : authority.denied ? "denied" : "paused",
  );
  setText("#governed-execution-performed", payload.execution_performed);
  setText("#reconciliation-outcome", reconciliation.outcome, "not produced");
  document.querySelector("#governed-json").textContent = JSON.stringify(
    payload,
    null,
    2,
  );
  governedPanel.hidden = false;
}

function describeError(payload, status) {
  if (payload && typeof payload.detail === "string") {
    return payload.detail;
  }

  if (payload && Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => item.msg || "Invalid request")
      .join("; ");
  }

  return `Mission analysis failed with status ${status}.`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  errorMessage.hidden = true;
  resultPanel.hidden = true;
  validationPanel.hidden = true;
  analyzeButton.disabled = true;
  buttonLabel.textContent = "Analyzing…";

  try {
    const response = await fetch(form.dataset.endpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({task: taskInput.value}),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(describeError(payload, response.status));
    }

    renderResult(payload);
    resultPanel.scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    errorMessage.textContent =
      error instanceof Error
        ? error.message
        : "Unable to analyze the mission.";
    errorMessage.hidden = false;
  } finally {
    analyzeButton.disabled = false;
    buttonLabel.textContent = "Analyze Mission";
  }
});

executeButton.addEventListener("click", async () => {
  errorMessage.hidden = true;
  resultPanel.hidden = true;
  executionPanel.hidden = true;
  validationPanel.hidden = true;
  executeButton.disabled = true;
  analyzeButton.disabled = true;
  executeButtonLabel.textContent = "Simulating…";

  try {
    const response = await fetch(executeButton.dataset.endpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({task: taskInput.value}),
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(describeError(payload, response.status));
    }

    renderResult(payload.analysis);
    renderExecution(payload.execution);
    renderValidation(payload.validation);
    validationPanel.scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    errorMessage.textContent =
      error instanceof Error
        ? error.message
        : "Unable to simulate execution.";
    errorMessage.hidden = false;
  } finally {
    executeButton.disabled = false;
    analyzeButton.disabled = false;
    executeButtonLabel.textContent = "Simulate Execution";
  }
});


governedButton.addEventListener("click", async () => {
  errorMessage.hidden = true;
  governedPanel.hidden = true;
  governedButton.disabled = true;
  analyzeButton.disabled = true;
  executeButton.disabled = true;
  governedButtonLabel.textContent = "Running…";

  try {
    const response = await fetch(governedButton.dataset.endpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(buildGovernedRequest()),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(describeError(payload, response.status));
    }
    renderGoverned(payload);
    governedPanel.scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    errorMessage.textContent =
      error instanceof Error ? error.message : "Unable to run governed demo.";
    errorMessage.hidden = false;
  } finally {
    governedButton.disabled = false;
    analyzeButton.disabled = false;
    executeButton.disabled = false;
    governedButtonLabel.textContent = "Run Governed Demo";
  }
});
