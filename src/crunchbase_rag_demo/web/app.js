const questionInput = document.querySelector("#question");
const searchButton = document.querySelector("#searchButton");
const askButton = document.querySelector("#askButton");
const resultsNode = document.querySelector("#results");
const promptView = document.querySelector("#promptView");
const answerView = document.querySelector("#answerView");
const resultCount = document.querySelector("#resultCount");
const statusText = document.querySelector("#statusText");
const statusDot = document.querySelector(".status-dot");
const tabs = document.querySelectorAll(".tab");

let currentPrompt = "";

function setBusy(isBusy) {
  searchButton.disabled = isBusy;
  askButton.disabled = isBusy;
}

function setStatus(text, color = "#c77810") {
  statusText.textContent = text;
  statusDot.style.background = color;
}

function showView(id) {
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.view === id));
  document.querySelectorAll(".detail-view").forEach((view) => {
    view.classList.toggle("active", view.id === id);
  });
}

function renderResults(results) {
  resultCount.textContent = `${results.length} ${results.length === 1 ? "match" : "matches"}`;
  if (!results.length) {
    resultsNode.innerHTML = `<div class="empty">No matching records.</div>`;
    return;
  }

  const maxScore = Math.max(...results.map((item) => item.score), 0.01);
  resultsNode.innerHTML = results
    .map((item) => {
      const record = item.record;
      const width = Math.max(6, Math.round((item.score / maxScore) * 100));
      const meta = [record.category, record.location, record.founded].filter(Boolean).join(" / ");
      return `
        <article class="result-card">
          <div class="result-top">
            <h2>${escapeHtml(record.name)}</h2>
            <div class="score">${item.score.toFixed(3)}</div>
          </div>
          <div class="meta">${escapeHtml(meta || record.source)}</div>
          <p class="summary">${escapeHtml(record.summary || "No summary available.")}</p>
          <div class="bar" aria-hidden="true"><span style="--score-width: ${width}%"></span></div>
        </article>
      `;
    })
    .join("");
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

async function retrieve() {
  const question = questionInput.value.trim();
  if (!question) return;
  setBusy(true);
  setStatus("Retrieving local records");
  answerView.textContent = "";
  try {
    const payload = await postJson("/api/search", { question, top_k: 5 });
    currentPrompt = payload.prompt;
    renderResults(payload.results);
    promptView.textContent = payload.prompt;
    setStatus("Local retrieval ready", "#0f766e");
    showView("promptView");
  } catch (error) {
    setStatus("Retrieval failed", "#a13d2d");
    answerView.textContent = error.message;
    showView("answerView");
  } finally {
    setBusy(false);
  }
}

async function askCodex() {
  const question = questionInput.value.trim();
  if (!question) return;
  setBusy(true);
  setStatus("Asking Codex");
  answerView.textContent = "Waiting for Codex...";
  showView("answerView");
  try {
    const payload = await postJson("/api/ask", { question, top_k: 5 });
    currentPrompt = payload.prompt;
    renderResults(payload.results);
    promptView.textContent = payload.prompt;
    answerView.textContent = payload.answer;
    setStatus("Answer ready", "#0f766e");
  } catch (error) {
    setStatus("Codex call failed", "#a13d2d");
    answerView.textContent = error.message;
  } finally {
    setBusy(false);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => showView(tab.dataset.view));
});

searchButton.addEventListener("click", retrieve);
askButton.addEventListener("click", askCodex);
questionInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    askCodex();
  }
});

fetch("/api/status")
  .then((response) => response.json())
  .then((status) => {
    if (status.index_exists) {
      setStatus(status.codex_available ? "Index ready / Codex found" : "Index ready / Codex missing", "#0f766e");
    } else {
      setStatus(status.codex_available ? "Waiting for local index" : "Codex missing / waiting for index", "#0f766e");
    }
  })
  .catch(() => setStatus("Status unavailable", "#a13d2d"));
