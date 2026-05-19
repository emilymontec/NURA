const APP_CONFIG = window.NURA_CONFIG || {};
const API_BASE_URL = APP_CONFIG.apiBaseUrl || "/api";
const LOGO_URL = APP_CONFIG.logoUrl || "/static/assets/logo.png";
const SESSION_STORAGE_KEY = "nura_session_id";
const CHAT_HISTORY_STORAGE_KEY = "nura_chat_history";

const state = {
    analysis: null,
    sessionId: getSessionId(),
};

function getSessionId() {
    const stored = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (stored) {
        return stored;
    }

    const sessionId = `nura-${Date.now()}`;
    window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    return sessionId;
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatInlineMarkdown(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

function formatMessageContent(text) {
    const safeText = escapeHtml(text || "");
    const lines = safeText.split("\n");
    const parts = [];
    let listItems = [];

    const flushList = () => {
        if (!listItems.length) {
            return;
        }
        parts.push(`<ul>${listItems.join("")}</ul>`);
        listItems = [];
    };

    for (const line of lines) {
        const trimmed = line.trim();

        if (!trimmed) {
            flushList();
            continue;
        }

        const bulletMatch = trimmed.match(/^[-*]\s+(.+)$/);
        if (bulletMatch) {
            listItems.push(`<li>${formatInlineMarkdown(bulletMatch[1])}</li>`);
            continue;
        }

        flushList();
        parts.push(`<p>${formatInlineMarkdown(trimmed)}</p>`);
    }

    flushList();
    return parts.join("");
}

function getStoredChatHistory() {
    try {
        const raw = window.localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        return [];
    }
}

function saveStoredChatHistory(items) {
    window.localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(items));
}

function buildChatHistoryTitle(entry) {
    if (entry.fileName && entry.fileName !== "Sin archivo") {
        return entry.fileName;
    }
    if (entry.firstPrompt) {
        return entry.firstPrompt;
    }
    return entry.sessionId;
}

function upsertChatHistoryEntry(patch) {
    const history = getStoredChatHistory();
    const index = history.findIndex((item) => item.sessionId === patch.sessionId);
    const previous = index >= 0 ? history[index] : null;
    const nextEntry = {
        sessionId: patch.sessionId,
        firstPrompt: patch.firstPrompt || previous?.firstPrompt || "Nueva conversacion",
        lastPreview: patch.lastPreview || previous?.lastPreview || "Sin mensajes aun.",
        fileName: patch.fileName !== undefined ? patch.fileName : previous?.fileName || "Sin archivo",
        updatedAt: patch.updatedAt || new Date().toISOString(),
    };

    if (index >= 0) {
        history[index] = nextEntry;
    } else {
        history.push(nextEntry);
    }

    history.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    saveStoredChatHistory(history.slice(0, 12));
    renderChatHistory();
}

function renderChatHistory() {
    const container = document.getElementById("chat-history-list");
    const countBadge = document.getElementById("history-count-badge");
    if (!container) {
        return;
    }

    const history = getStoredChatHistory();
    if (countBadge) {
        countBadge.textContent = String(history.length);
    }

    if (!history.length) {
        container.innerHTML = `<div class="history-empty">Aun no hay conversaciones guardadas.</div>`;
        return;
    }

    container.innerHTML = history
        .map((entry) => {
            const activeClass = entry.sessionId === state.sessionId ? " active" : "";
            const title = escapeHtml(buildChatHistoryTitle(entry));
            const preview = escapeHtml(entry.lastPreview || "Sin mensajes aun.");
            const meta = entry.sessionId === state.sessionId ? "Sesion actual" : "Sesion guardada";
            return `
                <div class="history-item${activeClass}">
                    <div class="history-item-title" title="${title}">${title}</div>
                    <div class="history-item-meta">${meta}</div>
                    <div class="history-item-preview">${preview}</div>
                </div>
            `;
        })
        .join("");
}

function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "0";
    }
    return new Intl.NumberFormat("es-ES").format(Number(value));
}

function formatDecimal(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "0.00";
    }
    return Number(value).toFixed(2);
}

function setText(id, value, title = null) {
    const element = document.getElementById(id);
    if (!element) {
        return;
    }

    element.textContent = value;
    if (title !== null) {
        element.title = title;
    }
}

function getRiskTone(riskLevel) {
    const level = String(riskLevel || "").toLowerCase();
    if (level.includes("alto")) {
        return "high";
    }
    if (level.includes("medio")) {
        return "medium";
    }
    if (level.includes("bajo")) {
        return "low";
    }
    return "neutral";
}

function setRiskValue(id, text, riskLevel) {
    const element = document.getElementById(id);
    if (!element) {
        return;
    }

    element.textContent = text;
    element.dataset.tone = getRiskTone(riskLevel);
}

function setDatasetState(label, variant = "neutral") {
    const badge = document.getElementById("dataset-state-badge");
    if (!badge) {
        return;
    }

    badge.textContent = label;
    badge.className = `mini-badge ${variant}`;
    const heroState = document.getElementById("hero-state");
    if (heroState) {
        heroState.textContent = label;
        heroState.className = `mini-badge ${variant}`;
    }
}

function updateHeroSummary({
    file = "Sin archivo",
    rows = "0",
    risk = "Sin evaluar",
    health = "Conversacion general disponible. Puedes preguntar sin subir archivos.",
    riskLevel = "",
} = {}) {
    setText("hero-file", file, file);
    setText("hero-rows", rows);
    setRiskValue("hero-risk", risk, riskLevel);
    setText("hero-summary-text", health);
}

function getRiskLabel(riskLevel, score) {
    if (!riskLevel) {
        return "Sin evaluar";
    }
    return `${riskLevel.toUpperCase()} · ${formatDecimal(score)}`;
}

function getBotAvatarMarkup() {
    return `<div class="avatar nura-avatar">
                <img src="${LOGO_URL}" alt="NURA" class="avatar-logo">
            </div>`;
}

function setApiStatus(text, detail, status) {
    const statusEl = document.getElementById("api-status");
    const detailEl = document.getElementById("api-status-detail");
    const statusCardEl = statusEl ? statusEl.closest(".status-card") : null;
    if (!statusEl || !detailEl || !statusCardEl) {
        return;
    }

    statusEl.textContent = text;
    detailEl.textContent = detail;
    statusEl.dataset.state = status;
    statusCardEl.classList.toggle("status-error", status === "error");
}

function updateSessionLabel() {
    const label = document.getElementById("session-id-label");
    if (label) {
        label.textContent = state.sessionId;
    }
    upsertChatHistoryEntry({
        sessionId: state.sessionId,
        updatedAt: new Date().toISOString(),
    });
}

async function testAPI() {
    setApiStatus("Comprobando...", "Validando conectividad del backend.", "loading");

    try {
        const response = await fetch(`${API_BASE_URL}/test/`);
        const data = await response.json();
        setApiStatus("Conectado", data.message || "Backend operativo.", "ok");
    } catch (error) {
        setApiStatus("Sin conexion", "No fue posible contactar al backend.", "error");
    }
}

function addMessage(text, sender, id = null) {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) {
        return;
    }

    const welcomeScreen = document.getElementById("welcome-screen-box");
    if (welcomeScreen) {
        welcomeScreen.style.display = "none";
    }

    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}-msg`;
    if (sender === "bot" && id && id.startsWith("typing")) {
        msgDiv.classList.add("loading");
    }
    if (id) {
        msgDiv.id = id;
    }

    let avatarHtml = "";
    if (sender === "bot") {
        avatarHtml = getBotAvatarMarkup();
    } else {
        avatarHtml = `<div class="avatar user-avatar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                      </div>`;
    }

    const contentHtml = `<div class="msg-content">${formatMessageContent(text)}</div>`;

    msgDiv.innerHTML = avatarHtml + contentHtml;
    chatBox.appendChild(msgDiv);
    setTimeout(() => { chatBox.scrollTop = chatBox.scrollHeight; }, 10);

    if (!id || !id.startsWith("typing")) {
        upsertChatHistoryEntry({
            sessionId: state.sessionId,
            firstPrompt: sender === "user" ? text : undefined,
            lastPreview: text,
            fileName: state.analysis?.file_name,
            updatedAt: new Date().toISOString(),
        });
    }
}

function usePrompt(prompt) {
    const input = document.getElementById("user-input");
    if (!input) {
        return;
    }

    input.value = prompt;
    autoResizeInput();
    input.focus();
}

function openFilePicker() {
    const input = document.getElementById("data-upload");
    if (input) {
        input.click();
    }
}

function clearAnalysis() {
    state.analysis = null;

    setText("selected-file-label", "Sin archivo", "Sin archivo");
    setText("stat-file", "Esperando carga", "Esperando carga");
    setText("stat-rows", "0");
    setText("stat-columns", "0");
    setRiskValue("stat-risk", "Sin evaluar", "");
    setText("stat-health-detail", "Salud de datos pendiente");
    setText("hero-columns", "0");
    setText("hero-flow", "Chat general activo");
    updateHeroSummary();
    setDatasetState("Sin carga", "neutral");

    const appContainer = document.getElementById("app-container");
    if (appContainer) {
        appContainer.classList.remove("show-analytics");
    }

    const elUploadHint = document.getElementById("upload-hint");
    if (elUploadHint) {
        elUploadHint.textContent = "Sube archivos CSV o Excel para activar las analíticas avanzadas.";
    }

    const elInsightsList = document.getElementById("insights-list");
    if (elInsightsList) {
        elInsightsList.innerHTML = "Carga un archivo para ver alertas, patrones y recomendaciones iniciales.";
    }

    const elTrendsTable = document.getElementById("trends-table");
    if (elTrendsTable) {
        elTrendsTable.classList.remove("has-table");
        elTrendsTable.innerHTML = "Carga un dataset para ver indicadores numéricos y tendencias relevantes.";
    }

    const insightsContainer = document.getElementById("insights-container");
    if (insightsContainer) {
        insightsContainer.style.display = "none";
    }

    upsertChatHistoryEntry({
        sessionId: state.sessionId,
        fileName: "Sin archivo",
        updatedAt: new Date().toISOString(),
    });
}

function renderInsights(insights) {
    const container = document.getElementById("insights-list");
    if (!container) {
        return;
    }

    if (!insights || !insights.length) {
        container.innerHTML = "No se detectaron insights relevantes con el archivo actual.";
        return;
    }

    container.innerHTML = insights
        .map((insight) => `<article class="insight-item">${escapeHtml(insight)}</article>`)
        .join("");
}

function renderTrends(trends) {
    const container = document.getElementById("trends-table");
    if (!container) {
        return;
    }

    const entries = Object.entries(trends || {});
    if (!entries.length) {
        container.classList.remove("has-table");
        container.innerHTML = "El archivo no contiene columnas numericas suficientes para estimar tendencias.";
        return;
    }

    const rows = entries
        .map(([name, data]) => `
            <tr>
                <td>${escapeHtml(name)}</td>
                <td>${formatDecimal(data.mean)}</td>
                <td>${formatDecimal(data.min)}</td>
                <td>${formatDecimal(data.max)}</td>
                <td>${formatDecimal(data.trend)}</td>
            </tr>
        `)
        .join("");

    container.classList.add("has-table");
    container.innerHTML = `
        <div class="trend-table-wrapper">
        <table class="trend-table">
            <thead>
                <tr>
                    <th>Variable</th>
                    <th>Media</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Pendiente</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
        </div>
    `;
}

function autoResizeInput() {
    const input = document.getElementById("user-input");
    if (!input) {
        return;
    }

    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

function renderAnalysis(data) {
    state.analysis = data;

    const fileName = data.file_name || "Archivo procesado";
    const rowCount = formatNumber(data.summary?.rows);
    const columnCount = formatNumber(data.summary?.columns);
    const riskLabel = getRiskLabel(data.health?.risk_level, data.health?.health_score);
    const healthSummary = `Faltantes: ${formatNumber(data.summary?.total_missing)} · Duplicados: ${formatNumber(data.summary?.duplicate_rows)}`;

    setText("selected-file-label", fileName, fileName);
    setText("stat-file", fileName, fileName);
    setText("stat-rows", rowCount);
    setText("stat-columns", columnCount);
    setRiskValue("stat-risk", riskLabel, data.health?.risk_level);
    setText("stat-health-detail", healthSummary);
    setText("hero-columns", columnCount);
    setText("hero-flow", "Analisis disponible");
    updateHeroSummary({
        file: fileName,
        rows: rowCount,
        risk: riskLabel,
        health: healthSummary,
        riskLevel: data.health?.risk_level,
    });
    setDatasetState("Listo", "success");

    const appContainer = document.getElementById("app-container");
    if (appContainer) {
        appContainer.classList.add("show-analytics");
    }

    const elUploadHint = document.getElementById("upload-hint");
    if (elUploadHint) {
        elUploadHint.textContent = "Análisis generado. Ya puedes preguntar al chat por riesgos, patrones o recomendaciones.";
    }

    const insightsContainer = document.getElementById("insights-container");
    if (insightsContainer && data.insights?.length) {
        insightsContainer.style.display = "block";
    }

    renderInsights(data.insights);
    renderTrends(data.trends);
    upsertChatHistoryEntry({
        sessionId: state.sessionId,
        fileName,
        lastPreview: `Dataset activo: ${fileName}`,
        updatedAt: new Date().toISOString(),
    });
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) {
        return;
    }

    addMessage(message, "user");
    input.value = "";
    autoResizeInput();

    const typingId = `typing-${Date.now()}`;
    addMessage("Analizando tu consulta...", "bot", typingId);

    try {
        const response = await fetch(`${API_BASE_URL}/chat/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_id: state.sessionId }),
        });
        const data = await response.json();

        const typingEl = document.getElementById(typingId);
        if (typingEl) {
            typingEl.remove();
        }

        if (response.ok && data.response) {
            addMessage(data.response, "bot");
            return;
        }

        addMessage(`Error: ${data.error || "No se pudo obtener respuesta del asistente."}`, "bot");
    } catch (error) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) {
            typingEl.remove();
        }
        addMessage("Error de conexion. Verifica que el backend este en ejecucion.", "bot");
    }
}

function handleKeyPress(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) {
        return;
    }

    const allowedExtensions = [".csv", ".xlsx", ".xls"];
    const extension = `.${file.name.split(".").pop().toLowerCase()}`;
    if (!allowedExtensions.includes(extension)) {
        addMessage("Formato no soportado. Usa archivos CSV o Excel.", "bot");
        event.target.value = "";
        return;
    }

    setText("selected-file-label", file.name, file.name);
    setText("stat-file", file.name, file.name);
    setText("hero-columns", "Calculando");
    setText("hero-flow", "Extrayendo señales");
    updateHeroSummary({
        file: file.name,
        rows: "Procesando",
        risk: "En calculo",
        health: "Estamos evaluando calidad, faltantes y tendencias.",
        riskLevel: "",
    });
    setDatasetState("Procesando", "neutral");
    
    addMessage(`Archivo cargado: ${file.name}`, "user");

    const typingId = `typing-${Date.now()}`;
    addMessage("Procesando archivo y calculando insights...", "bot", typingId);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", state.sessionId);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze/`, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        const typingEl = document.getElementById(typingId);
        if (typingEl) {
            typingEl.remove();
        }

        if (!response.ok) {
            addMessage(`Error al analizar el archivo: ${data.error || "Error desconocido."}`, "bot");
            return;
        }

        renderAnalysis(data);
        addMessage(
            `Analisis completado.\nArchivo: ${data.file_name}\nRegistros: ${data.summary.rows}\nColumnas: ${data.summary.columns}\nRiesgo: ${data.health.risk_level}\nSalud: ${formatDecimal(data.health.health_score)}`,
            "bot"
        );

        if (data.insights?.length) {
            addMessage(`Insights iniciales:\n- ${data.insights.join("\n- ")}`, "bot");
        }
    } catch (error) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) {
            typingEl.remove();
        }
        addMessage("No fue posible subir o analizar el archivo. Revisa el backend.", "bot");
    }

    event.target.value = "";
}

function initializeDashboard() {
    renderChatHistory();
    updateSessionLabel();
    clearAnalysis();
    testAPI();
    autoResizeInput();

    const input = document.getElementById("user-input");
    if (input && !input.dataset.autoresizeBound) {
        input.addEventListener("input", autoResizeInput);
        input.dataset.autoresizeBound = "true";
    }
}

function toggleAnalytics() {
    const container = document.getElementById("app-container");
    if (container) {
        container.classList.toggle("show-analytics");
    }
}

window.testAPI = testAPI;
window.sendMessage = sendMessage;
window.handleKeyPress = handleKeyPress;
window.handleFileUpload = handleFileUpload;
window.openFilePicker = openFilePicker;
window.clearAnalysis = clearAnalysis;
window.initializeDashboard = initializeDashboard;
window.usePrompt = usePrompt;
window.toggleAnalytics = toggleAnalytics;
