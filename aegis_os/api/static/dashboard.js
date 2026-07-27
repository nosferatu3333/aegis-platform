const form = document.querySelector("#mission-form");
const taskInput = document.querySelector("#mission-task");
const analyzeButton = document.querySelector("#analyze-button");
const executeButton = document.querySelector("#execute-button");
const buttonLabel = analyzeButton.querySelector(".button-label");
const executeButtonLabel = executeButton.querySelector(".button-label");
const errorMessage = document.querySelector("#error-message");
const resultPanel = document.querySelector("#result-panel");
const executionPanel = document.querySelector("#execution-panel");

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
    executionPanel.scrollIntoView({behavior: "smooth", block: "start"});
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
