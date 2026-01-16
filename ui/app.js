/**
 * Sentinel UI - Trace Inspector
 * 
 * Minimal JavaScript for trace list, detail view, and replay.
 */

const API_BASE = '/v1';
let currentTraceId = null;
let traces = [];

/**
 * Load traces from the API
 */
async function loadTraces() {
    const traceList = document.getElementById('traceList');
    traceList.innerHTML = `
        <li class="loading">
            <div class="spinner"></div>
            <p>Loading traces...</p>
        </li>
    `;

    try {
        const response = await fetch(`${API_BASE}/traces?limit=50`);
        const data = await response.json();

        traces = data.traces;
        document.getElementById('totalTraces').textContent = data.total;

        // Count today's traces
        const today = new Date().toISOString().split('T')[0];
        const todayCount = traces.filter(t => t.timestamp.startsWith(today)).length;
        document.getElementById('todayTraces').textContent = todayCount;

        renderTraceList();
    } catch (error) {
        traceList.innerHTML = `
            <li class="empty-state">
                <h3>Error loading traces</h3>
                <p>${error.message}</p>
            </li>
        `;
    }
}

/**
 * Render the trace list
 */
function renderTraceList() {
    const traceList = document.getElementById('traceList');

    if (traces.length === 0) {
        traceList.innerHTML = `
            <li class="empty-state">
                <h3>No traces yet</h3>
                <p>Make some LLM calls to see them here</p>
            </li>
        `;
        return;
    }

    traceList.innerHTML = traces.map(trace => {
        const time = new Date(trace.timestamp).toLocaleString();
        const preview = trace.request.messages?.[0]?.content?.substring(0, 50) || 'No message';
        const isActive = trace.trace_id === currentTraceId ? 'active' : '';

        return `
            <li class="trace-item ${isActive}" onclick="selectTrace('${trace.trace_id}')">
                <div class="trace-item-header">
                    <span class="trace-model">${trace.request.model}</span>
                    <span class="trace-time">${time}</span>
                </div>
                <div class="trace-preview">${escapeHtml(preview)}...</div>
                <div class="trace-meta">
                    <span>${trace.request.provider}</span>
                    <span>${trace.response.latency_ms}ms</span>
                    ${trace.replay_of ? '<span>↩ Replay</span>' : ''}
                </div>
            </li>
        `;
    }).join('');
}

/**
 * Select and show a trace
 */
async function selectTrace(traceId) {
    currentTraceId = traceId;
    const detail = document.getElementById('traceDetail');
    const replayBtn = document.getElementById('replayBtn');

    // Update active state in list
    renderTraceList();

    detail.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading trace details...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/traces/${traceId}`);
        const trace = await response.json();

        replayBtn.disabled = false;

        detail.innerHTML = `
            <div class="detail-section">
                <h3>Trace Info</h3>
                <div class="detail-content">
ID: ${trace.trace_id}
Timestamp: ${trace.timestamp}
Model: ${trace.request.model}
Provider: ${trace.request.provider}
Latency: ${trace.response.latency_ms}ms
${trace.replay_of ? `Replay of: ${trace.replay_of}` : ''}
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Parameters</h3>
                <div class="detail-content">${JSON.stringify(trace.request.parameters, null, 2)}</div>
            </div>
            
            <div class="detail-section">
                <h3>Messages</h3>
                ${trace.request.messages.map(msg => `
                    <div class="message ${msg.role}">
                        <div class="message-role">${msg.role}</div>
                        <div>${escapeHtml(msg.content)}</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="detail-section">
                <h3>Response</h3>
                <div class="detail-content">${escapeHtml(trace.response.text)}</div>
            </div>
            
            ${trace.response.usage ? `
                <div class="detail-section">
                    <h3>Token Usage</h3>
                    <div class="detail-content">${JSON.stringify(trace.response.usage, null, 2)}</div>
                </div>
            ` : ''}
        `;
    } catch (error) {
        detail.innerHTML = `
            <div class="empty-state">
                <h3>Error loading trace</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

/**
 * Replay the current trace
 */
async function replayTrace() {
    if (!currentTraceId) return;

    const replayBtn = document.getElementById('replayBtn');
    replayBtn.disabled = true;
    replayBtn.textContent = 'Replaying...';

    try {
        const response = await fetch(`${API_BASE}/replay/${currentTraceId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const result = await response.json();

        if (response.ok) {
            alert(`Replay successful!\nNew trace: ${result.new_trace_id}`);
            loadTraces();
            selectTrace(result.new_trace_id);
        } else {
            alert(`Replay failed: ${result.detail}`);
        }
    } catch (error) {
        alert(`Replay error: ${error.message}`);
    } finally {
        replayBtn.disabled = false;
        replayBtn.textContent = 'Replay';
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load traces on page load
document.addEventListener('DOMContentLoaded', loadTraces);
