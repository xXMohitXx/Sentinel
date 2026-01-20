/**
 * Sentinel UI - Failure-First Inspector (Phase 11)
 * 
 * DESIGN PRINCIPLE: When something breaks, Sentinel explains why faster than a human can.
 * 
 * - Opens in FAILED-ONLY mode by default
 * - Failure summary above everything
 * - Navigation between failed traces only
 * - No distractions during damage control
 */

const API_BASE = '/v1';
let currentTraceId = null;
let traces = [];
let failedTraces = [];
let currentFailedIndex = -1;
let currentFilter = 'failed'; // DEFAULT: Failed-only mode (Phase 11.1)
let visibleCount = 5;
const PAGE_SIZE = 5;

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    loadTraces();
});

/**
 * Load traces from the API
 */
async function loadTraces() {
    const traceList = document.getElementById('traceList');
    traceList.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/traces?limit=100`);
        const data = await response.json();

        traces = data.traces || [];
        failedTraces = traces.filter(t => t.verdict?.status === 'fail');
        visibleCount = PAGE_SIZE;

        updateStats();
        renderTraceList();

        // Phase 11.1: Auto-select first failed trace if exists
        if (failedTraces.length > 0 && currentFilter === 'failed') {
            selectTrace(failedTraces[0].trace_id);
        }
    } catch (error) {
        traceList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Error loading traces</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

/**
 * Update header stats
 */
function updateStats() {
    const failed = failedTraces.length;
    const passed = traces.filter(t => t.verdict?.status === 'pass').length;

    document.getElementById('failedCount').textContent = failed;
    document.getElementById('passedCount').textContent = passed;
    document.getElementById('totalCount').textContent = traces.length;
}

/**
 * Set filter and re-render
 */
function setFilter(filter, element) {
    currentFilter = filter;
    visibleCount = PAGE_SIZE;

    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }

    renderTraceList();

    // Auto-select first trace of new filter
    const filtered = getFilteredTraces();
    if (filtered.length > 0) {
        selectTrace(filtered[0].trace_id);
    }
}

/**
 * Get filtered traces
 */
function getFilteredTraces() {
    if (currentFilter === 'failed') {
        return failedTraces;
    } else if (currentFilter === 'passed') {
        return traces.filter(t => t.verdict?.status === 'pass');
    }
    return traces;
}

/**
 * Load more traces
 */
function loadMore() {
    visibleCount += PAGE_SIZE;
    renderTraceList();
}

/**
 * Render the trace list
 */
function renderTraceList() {
    const traceList = document.getElementById('traceList');
    const filteredTraces = getFilteredTraces();

    // Phase 11.1: Green banner when no failures
    if (currentFilter === 'failed' && filteredTraces.length === 0) {
        traceList.innerHTML = `
            <div class="success-banner">
                <div class="success-icon">✅</div>
                <h3>No regressions detected</h3>
                <p>All expectations are passing</p>
            </div>
        `;
        // Clear detail panel
        document.getElementById('traceDetail').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🛡️</div>
                <h3>All clear</h3>
                <p>No failed traces to inspect</p>
            </div>
        `;
        return;
    }

    if (filteredTraces.length === 0) {
        traceList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <h3>No traces</h3>
                <p>No traces match this filter</p>
            </div>
        `;
        return;
    }

    const visibleTraces = filteredTraces.slice(0, visibleCount);
    const hasMore = filteredTraces.length > visibleCount;

    let html = visibleTraces.map((trace, index) => {
        const time = formatTime(trace.timestamp);
        const preview = trace.request.messages?.[0]?.content?.substring(0, 50) || 'No message';
        const isActive = trace.trace_id === currentTraceId ? 'active' : '';

        let verdictClass = 'pending';
        let verdictIcon = '⏳';
        if (trace.verdict) {
            if (trace.verdict.status === 'pass') {
                verdictClass = 'pass';
                verdictIcon = '✓';
            } else {
                verdictClass = 'fail';
                verdictIcon = '✕';
            }
        }

        return `
            <div class="trace-item ${isActive} verdict-${verdictClass}" onclick="selectTrace('${trace.trace_id}')">
                <div class="trace-header">
                    <div class="verdict-badge ${verdictClass}">${verdictIcon}</div>
                    <span class="trace-model">${trace.request.model}</span>
                </div>
                <div class="trace-preview">${escapeHtml(preview)}...</div>
                <div class="trace-meta">
                    <span>⏱ ${trace.response.latency_ms}ms</span>
                    <span>🕐 ${time}</span>
                </div>
            </div>
        `;
    }).join('');

    if (hasMore) {
        const remaining = filteredTraces.length - visibleCount;
        html += `
            <button class="load-more-btn" onclick="loadMore()">
                Load More (${remaining} remaining)
            </button>
        `;
    }

    traceList.innerHTML = html;
}

/**
 * Navigate to previous failed trace (Phase 11.4)
 */
function prevFailedTrace() {
    if (failedTraces.length === 0) return;

    currentFailedIndex = Math.max(0, currentFailedIndex - 1);
    selectTrace(failedTraces[currentFailedIndex].trace_id);
}

/**
 * Navigate to next failed trace (Phase 11.4)
 */
function nextFailedTrace() {
    if (failedTraces.length === 0) return;

    currentFailedIndex = Math.min(failedTraces.length - 1, currentFailedIndex + 1);
    selectTrace(failedTraces[currentFailedIndex].trace_id);
}

/**
 * Select and show a trace
 */
async function selectTrace(traceId) {
    currentTraceId = traceId;

    // Update failed index
    currentFailedIndex = failedTraces.findIndex(t => t.trace_id === traceId);

    const detail = document.getElementById('traceDetail');
    const replayBtn = document.getElementById('replayBtn');
    const navBtns = document.getElementById('failNav');

    renderTraceList();

    detail.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/traces/${traceId}`);
        const trace = await response.json();

        replayBtn.disabled = false;

        // Update navigation buttons
        if (navBtns) {
            navBtns.style.display = failedTraces.length > 1 ? 'flex' : 'none';
            document.getElementById('prevBtn').disabled = currentFailedIndex <= 0;
            document.getElementById('nextBtn').disabled = currentFailedIndex >= failedTraces.length - 1;
            document.getElementById('failCounter').textContent =
                `${currentFailedIndex + 1} / ${failedTraces.length}`;
        }

        // Build the detail view
        let html = '';

        // Phase 11.2: FAILURE SUMMARY FIRST (above everything)
        if (trace.verdict) {
            const isPass = trace.verdict.status === 'pass';
            const severity = trace.verdict.severity?.toUpperCase() || '';

            if (!isPass) {
                // Large failure banner
                html += `
                    <div class="failure-banner">
                        <div class="failure-header">
                            <div class="failure-icon">❌</div>
                            <div class="failure-title">
                                <h2>REGRESSION DETECTED</h2>
                                <span class="severity severity-${trace.verdict.severity}">${severity}</span>
                            </div>
                        </div>
                        
                        <div class="violations-section">
                            <h4>Violations:</h4>
                            <ul class="violations-list">
                                ${trace.verdict.violations.map(v => `
                                    <li><span class="violation-bullet">•</span> ${escapeHtml(v)}</li>
                                `).join('')}
                            </ul>
                        </div>
                        
                        ${trace.replay_of ? `
                            <div class="golden-ref">
                                <h4>Golden Reference:</h4>
                                <div class="golden-info">
                                    <span>Trace ID: ${trace.replay_of.substring(0, 20)}...</span>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;

                // Phase 11.3: Inline diff for golden mismatches
                if (trace.replay_of) {
                    html += await renderDiff(trace);
                }
            } else {
                html += `
                    <div class="pass-banner">
                        <div class="pass-icon">✅</div>
                        <div>
                            <h3>PASSED</h3>
                            <p>All expectations met</p>
                        </div>
                    </div>
                `;
            }
        }

        // Trace details (below the failure summary)
        html += `
            <div class="trace-details">
                <div class="detail-section">
                    <h4 class="section-title">Request</h4>
                    <div class="trace-id">ID: ${trace.trace_id}</div>
                    <div class="model-info">${trace.request.model} (${trace.request.provider})</div>
                </div>
                
                <div class="detail-section">
                    <h4 class="section-title">Prompt</h4>
                    <div class="prompt-box">
                        ${trace.request.messages.map(msg => `
                            <div class="message ${msg.role}">
                                <span class="role">${msg.role}:</span>
                                <span class="content">${escapeHtml(msg.content)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4 class="section-title">Response</h4>
                    <div class="response-box">${escapeHtml(trace.response.text)}</div>
                </div>
                
                <div class="detail-section meta-section">
                    <div class="meta-grid">
                        <div class="meta-item">
                            <span class="meta-label">Latency</span>
                            <span class="meta-value">${trace.response.latency_ms}ms</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Timestamp</span>
                            <span class="meta-value">${formatTime(trace.timestamp)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        detail.innerHTML = html;

    } catch (error) {
        detail.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Error loading trace</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

/**
 * Render diff between golden and current output (Phase 11.3)
 */
async function renderDiff(trace) {
    try {
        const goldenResponse = await fetch(`${API_BASE}/traces/${trace.replay_of}`);
        const goldenTrace = await goldenResponse.json();

        const goldenText = goldenTrace.response.text;
        const currentText = trace.response.text;

        if (goldenText === currentText) {
            return ''; // No diff needed
        }

        return `
            <div class="diff-section">
                <h4 class="section-title">What Changed?</h4>
                <div class="diff-container">
                    <div class="diff-panel">
                        <div class="diff-header diff-old">
                            <span>Expected (Golden)</span>
                        </div>
                        <div class="diff-content">${escapeHtml(goldenText)}</div>
                    </div>
                    <div class="diff-panel">
                        <div class="diff-header diff-new">
                            <span>Actual (Current)</span>
                        </div>
                        <div class="diff-content">${escapeHtml(currentText)}</div>
                    </div>
                </div>
            </div>
        `;
    } catch {
        return '';
    }
}

/**
 * Replay the current trace
 */
async function replayTrace() {
    if (!currentTraceId) return;

    const replayBtn = document.getElementById('replayBtn');
    replayBtn.disabled = true;
    replayBtn.innerHTML = '🔁 Replaying...';

    try {
        const response = await fetch(`${API_BASE}/replay/${currentTraceId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Replay complete', 'success');
            loadTraces();
            setTimeout(() => selectTrace(result.new_trace_id), 500);
        } else {
            showNotification(`Replay failed: ${result.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        replayBtn.disabled = false;
        replayBtn.innerHTML = '🔁 Replay';
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Format timestamp
 */
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    const timeOpts = { hour: '2-digit', minute: '2-digit', hour12: true };

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return date.toLocaleTimeString('en-US', timeOpts);

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
        ', ' + date.toLocaleTimeString('en-US', timeOpts);
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// Phase 15: Graph Visualization
// =============================================================================

let currentView = 'traces'; // 'traces' or 'graph'
let executions = [];
let currentGraph = null;

/**
 * Switch between Traces and Graph views
 */
function switchView(view) {
    currentView = view;

    // Update tabs
    document.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-view="${view}"]`)?.classList.add('active');

    if (view === 'traces') {
        document.getElementById('tracesView').style.display = 'flex';
        document.getElementById('graphView').style.display = 'none';
    } else {
        document.getElementById('tracesView').style.display = 'none';
        document.getElementById('graphView').style.display = 'flex';
        loadExecutions();
    }
}

/**
 * Load all executions
 */
async function loadExecutions() {
    const container = document.getElementById('executionList');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/executions`);
        const data = await response.json();
        executions = data.executions || [];

        if (executions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📊</div>
                    <h3>No executions yet</h3>
                    <p>Run code with sentinel.execution() context</p>
                </div>
            `;
            return;
        }

        container.innerHTML = executions.map(id => `
            <div class="execution-item" onclick="loadGraph('${id}')">
                <span class="execution-id">${id.substring(0, 20)}...</span>
            </div>
        `).join('');

        // Auto-load first execution
        loadGraph(executions[0]);
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><p>Error: ${error.message}</p></div>`;
    }
}

/**
 * Load and render a specific execution graph
 */
async function loadGraph(executionId) {
    const graphContainer = document.getElementById('graphCanvas');
    graphContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/executions/${executionId}/graph`);
        const graph = await response.json();
        currentGraph = graph;

        renderGraph(graph);
    } catch (error) {
        graphContainer.innerHTML = `<div class="empty-state"><p>Error: ${error.message}</p></div>`;
    }
}

/**
 * Render the execution graph as a visual DAG
 */
function renderGraph(graph) {
    const container = document.getElementById('graphCanvas');

    if (!graph.nodes || graph.nodes.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Empty graph</p></div>';
        return;
    }

    // Calculate failed nodes and tainted (downstream) nodes
    const failedNodeIds = new Set(graph.nodes.filter(n => n.verdict_status === 'fail').map(n => n.node_id));
    const taintedNodeIds = new Set();

    // BFS to find tainted nodes
    failedNodeIds.forEach(failedId => {
        graph.edges.forEach(edge => {
            if (failedNodeIds.has(edge.from_node) || taintedNodeIds.has(edge.from_node)) {
                taintedNodeIds.add(edge.to_node);
            }
        });
    });

    // Build HTML for nodes
    let nodesHtml = '<div class="graph-nodes">';

    // Simple vertical layout (topological order)
    const nodeMap = {};
    graph.nodes.forEach(n => nodeMap[n.node_id] = n);

    graph.nodes.forEach((node, index) => {
        let statusClass = 'pending';
        let statusIcon = '⏳';

        if (node.verdict_status === 'fail') {
            statusClass = 'fail';
            statusIcon = '❌';
        } else if (node.verdict_status === 'pass') {
            statusClass = 'pass';
            statusIcon = '✅';
        }

        // Check if tainted
        const isTainted = taintedNodeIds.has(node.node_id);
        const taintedClass = isTainted ? 'tainted' : '';

        nodesHtml += `
            <div class="graph-node ${statusClass} ${taintedClass}" data-node="${node.node_id}">
                <div class="node-header">
                    <span class="node-status">${statusIcon}</span>
                    <span class="node-label">${escapeHtml(node.label || node.model)}</span>
                    ${isTainted ? '<span class="taint-badge">⚠️ TAINTED</span>' : ''}
                </div>
                <div class="node-meta">
                    <span class="node-model">${node.model || 'unknown'}</span>
                    <span class="node-latency">${node.latency_ms}ms</span>
                </div>
            </div>
        `;

        // Add edge arrow if not last node
        if (index < graph.nodes.length - 1) {
            nodesHtml += '<div class="graph-edge-arrow">↓</div>';
        }
    });

    nodesHtml += '</div>';

    // Graph summary
    const failCount = failedNodeIds.size;
    const taintCount = taintedNodeIds.size;

    let summaryHtml = `
        <div class="graph-summary">
            <div class="summary-item">
                <span class="summary-value">${graph.node_count}</span>
                <span class="summary-label">Nodes</span>
            </div>
            <div class="summary-item">
                <span class="summary-value">${graph.total_latency_ms}ms</span>
                <span class="summary-label">Total Latency</span>
            </div>
            ${failCount > 0 ? `
                <div class="summary-item fail">
                    <span class="summary-value">${failCount}</span>
                    <span class="summary-label">Failed</span>
                </div>
                <div class="summary-item tainted">
                    <span class="summary-value">${taintCount}</span>
                    <span class="summary-label">Tainted</span>
                </div>
            ` : `
                <div class="summary-item pass">
                    <span class="summary-value">✅</span>
                    <span class="summary-label">All Pass</span>
                </div>
            `}
        </div>
    `;

    container.innerHTML = summaryHtml + nodesHtml;
}
