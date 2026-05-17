const API_BASE_URL = "/api";
const SESSION_STORAGE_KEY = "nura_session_id";

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
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
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

function getRiskLabel(riskLevel, score) {
    if (!riskLevel) {
        return "Sin evaluar";
    }
    return `${riskLevel.toUpperCase()} · ${formatDecimal(score)}`;
}

function setApiStatus(text, detail, status) {
    const statusEl = document.getElementById("api-status");
    const detailEl = document.getElementById("api-status-detail");
    if (!statusEl || !detailEl) {
        return;
    }

    statusEl.textContent = text;
    detailEl.textContent = detail;
    statusEl.dataset.state = status;
}

function updateSessionLabel() {
    const label = document.getElementById("session-id-label");
    if (label) {
        label.textContent = state.sessionId;
    }
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
        avatarHtml = `<div class="avatar nura-avatar">
                        <span class="node-mini node-pink"></span>
                        <span class="node-mini node-cyan"></span>
                        <span class="node-mini node-blue"></span>
                      </div>`;
    } else {
        avatarHtml = `<div class="avatar user-avatar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                      </div>`;
    }

    const formattedText = escapeHtml(text).replace(/\n/g, "</p><p>");
    const contentHtml = `<div class="msg-content"><p>${formattedText}</p></div>`;

    msgDiv.innerHTML = avatarHtml + contentHtml;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function openFilePicker() {
    const input = document.getElementById("data-upload");
    if (input) {
        input.click();
    }
}

function clearAnalysis() {
    state.analysis = null;

    const elSelectedFile = document.getElementById("selected-file-label");
    if(elSelectedFile) elSelectedFile.textContent = "Sin archivo";
    
    const elStatFile = document.getElementById("stat-file");
    if(elStatFile) elStatFile.textContent = "Esperando carga";
    
    const elStatRows = document.getElementById("stat-rows");
    if(elStatRows) elStatRows.textContent = "0";
    
    const elStatColumns = document.getElementById("stat-columns");
    if(elStatColumns) elStatColumns.textContent = "0";
    
    const elStatRisk = document.getElementById("stat-risk");
    if(elStatRisk) elStatRisk.textContent = "Sin evaluar";
    
    const elStatHealth = document.getElementById("stat-health-detail");
    if(elStatHealth) elStatHealth.textContent = "Salud de datos pendiente";
    
    const elUploadHint = document.getElementById("upload-hint");
    if(elUploadHint) elUploadHint.textContent = "Formatos soportados: `.csv`, `.xlsx`, `.xls`";
    
    const elInsightsList = document.getElementById("insights-list");
    if(elInsightsList) elInsightsList.innerHTML = "Carga un archivo para ver alertas, patrones y recomendaciones iniciales.";
    
    const elTrendsTable = document.getElementById("trends-table");
    if(elTrendsTable) elTrendsTable.innerHTML = "Aun no hay metricas disponibles para mostrar.";

    const insightsContainer = document.getElementById("insights-container");
    if(insightsContainer) insightsContainer.style.display = "none";
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

    container.innerHTML = `
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
    `;
}

function renderAnalysis(data) {
    state.analysis = data;

    const elSelectedFile = document.getElementById("selected-file-label");
    if(elSelectedFile) elSelectedFile.textContent = data.file_name || "Archivo procesado";
    
    const elStatFile = document.getElementById("stat-file");
    if(elStatFile) elStatFile.textContent = data.file_name || "Archivo listo";
    
    const elStatRows = document.getElementById("stat-rows");
    if(elStatRows) elStatRows.textContent = formatNumber(data.summary?.rows);
    
    const elStatColumns = document.getElementById("stat-columns");
    if(elStatColumns) elStatColumns.textContent = formatNumber(data.summary?.columns);
    
    const elStatRisk = document.getElementById("stat-risk");
    if(elStatRisk) elStatRisk.textContent = getRiskLabel(data.health?.risk_level, data.health?.health_score);
    
    const elStatHealth = document.getElementById("stat-health-detail");
    if(elStatHealth) elStatHealth.textContent = `Faltantes: ${formatNumber(data.summary?.total_missing)} · Duplicados: ${formatNumber(data.summary?.duplicate_rows)}`;
    
    const elUploadHint = document.getElementById("upload-hint");
    if(elUploadHint) elUploadHint.textContent = "Analisis generado. Ya puedes preguntar al chat por riesgos, patrones o recomendaciones.";

    const insightsContainer = document.getElementById("insights-container");
    if(insightsContainer && data.insights?.length) insightsContainer.style.display = "block";

    renderInsights(data.insights);
    renderTrends(data.trends);
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) {
        return;
    }

    addMessage(message, "user");
    input.value = "";

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

    const elSelectedFile = document.getElementById("selected-file-label");
    if (elSelectedFile) elSelectedFile.textContent = file.name;
    const elStatFile = document.getElementById("stat-file");
    if (elStatFile) elStatFile.textContent = file.name;
    
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
    updateSessionLabel();
    clearAnalysis();
    testAPI();
}

window.testAPI = testAPI;
window.sendMessage = sendMessage;
window.handleKeyPress = handleKeyPress;
window.handleFileUpload = handleFileUpload;
window.openFilePicker = openFilePicker;
window.clearAnalysis = clearAnalysis;
window.initializeDashboard = initializeDashboard;
