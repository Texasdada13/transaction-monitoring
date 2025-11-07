// dashboard.js - Fraud Detection Dashboard JavaScript

// Global state
let currentPeriod = 'month';
let refreshInterval = null;
let charts = {};

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializePeriodSelector();
    updateCurrentTime();
    loadControlRoomData();
    loadExecutiveSummaryData();

    // Start auto-refresh every 30 seconds
    refreshInterval = setInterval(() => {
        const activeTab = document.querySelector('.tab-panel.active').id;
        if (activeTab === 'control-room') {
            loadControlRoomData();
        } else {
            loadExecutiveSummaryData();
        }
    }, 30000);
});

// Tab Navigation
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

    // Update panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');

    // Load data for the active tab
    if (tabId === 'control-room') {
        loadControlRoomData();
    } else if (tabId === 'executive-summary') {
        loadExecutiveSummaryData();
    }
}

// Period Selector
function initializePeriodSelector() {
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentPeriod = button.getAttribute('data-period');
            periodButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            loadExecutiveSummaryData();
        });
    });
}

// Update Current Time
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    const now = new Date();
    timeElement.textContent = now.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    setTimeout(updateCurrentTime, 60000); // Update every minute
}

// Format Currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

// Format Number
function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

// Format Percentage
function formatPercentage(value) {
    return (value * 100).toFixed(1) + '%';
}

// ============================================================================
// CONTROL ROOM TAB
// ============================================================================

async function loadControlRoomData() {
    try {
        await Promise.all([
            loadRealTimeMetrics(),
            loadRiskDistribution(),
            loadTransactionFeed(),
            loadReviewQueue(),
            loadTriggeredRules()
        ]);
    } catch (error) {
        console.error('Error loading Control Room data:', error);
    }
}

// Real-time Metrics KPIs
async function loadRealTimeMetrics() {
    try {
        const response = await fetch('/api/dashboard/overview?time_window_hours=24');
        const data = await response.json();

        document.getElementById('txs-today').textContent = formatNumber(data.total_transactions);
        document.getElementById('alerts-flagged').textContent = data.flagged_count || 0;
        document.getElementById('manual-reviews').textContent = data.manual_review || 0;
        document.getElementById('fraud-prevented').textContent = formatCurrency(data.fraud_prevented_estimate || 0);
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

// Risk Distribution Chart
async function loadRiskDistribution() {
    try {
        const response = await fetch('/api/dashboard/risk-distribution');
        const data = await response.json();

        const ctx = document.getElementById('risk-gauge-chart');
        if (charts.riskGauge) {
            charts.riskGauge.destroy();
        }

        charts.riskGauge = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                datasets: [{
                    data: [data.low, data.medium, data.high],
                    backgroundColor: [
                        'rgba(39, 174, 96, 0.8)',
                        'rgba(243, 156, 18, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: false
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading risk distribution:', error);
    }
}

// Transaction Feed
async function loadTransactionFeed() {
    try {
        const response = await fetch('/api/dashboard/transaction-feed?limit=20');
        const data = await response.json();

        const feedContainer = document.getElementById('transaction-feed');
        feedContainer.innerHTML = '';

        if (data.length === 0) {
            feedContainer.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 2rem;">No recent transactions</p>';
            return;
        }

        data.forEach(tx => {
            const item = document.createElement('div');
            item.className = `transaction-item risk-${tx.risk_level}`;
            item.onclick = () => showTransactionDetails(tx);

            const rulesText = tx.triggered_rules.length > 0
                ? tx.triggered_rules.map(r => r.name).join(', ')
                : 'No rules triggered';

            item.innerHTML = `
                <div class="tx-header">
                    <span class="tx-employee">${tx.employee_name}</span>
                    <span class="tx-amount">${formatCurrency(tx.amount)}</span>
                </div>
                <div class="tx-meta">
                    <span>ID: ${tx.transaction_id}</span>
                    <span>Type: ${tx.transaction_type}</span>
                    <span>Account: ${tx.account_number}</span>
                    <span>${new Date(tx.timestamp).toLocaleString()}</span>
                </div>
                <div class="tx-risk">
                    <span class="risk-badge ${tx.risk_level}">${tx.risk_level.toUpperCase()}</span>
                    <span>Risk Score: ${tx.risk_score}</span>
                    <span style="margin-left: auto;">Status: ${tx.verification_status}</span>
                </div>
                <div style="font-size: 0.8rem; color: #7f8c8d; margin-top: 0.5rem;">
                    Rules: ${rulesText}
                </div>
            `;

            feedContainer.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading transaction feed:', error);
    }
}

// Refresh Transaction Feed (manual)
function refreshTransactionFeed() {
    loadTransactionFeed();
}

// Manual Review Queue
async function loadReviewQueue() {
    try {
        const response = await fetch('/api/dashboard/review-queue');
        const data = await response.json();

        document.getElementById('queue-count').textContent = `${data.length} item${data.length !== 1 ? 's' : ''}`;

        const queueContainer = document.getElementById('review-queue');
        queueContainer.innerHTML = '';

        if (data.length === 0) {
            queueContainer.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 1rem;">No items in queue</p>';
            return;
        }

        data.forEach(item => {
            const queueItem = document.createElement('div');
            queueItem.className = 'queue-item';

            const rulesText = item.triggered_rules.slice(0, 3).join(', ');
            const moreRules = item.triggered_rules.length > 3 ? ` +${item.triggered_rules.length - 3} more` : '';

            queueItem.innerHTML = `
                <div class="queue-item-header">
                    <span>${item.transaction_id}</span>
                    <span class="queue-risk-score">${item.risk_score.toFixed(2)}</span>
                </div>
                <div class="queue-details">
                    Amount: ${formatCurrency(item.amount)} | Type: ${item.transaction_type}
                </div>
                <div class="queue-rules">
                    Triggered: ${rulesText}${moreRules}
                </div>
                <div class="queue-actions">
                    <button class="btn-small btn-success" onclick="reviewAction(${item.assessment_id}, 'reviewed')">
                        Reviewed
                    </button>
                    <button class="btn-small btn-warning" onclick="reviewAction(${item.assessment_id}, 'escalated')">
                        Escalate
                    </button>
                </div>
            `;

            queueContainer.appendChild(queueItem);
        });
    } catch (error) {
        console.error('Error loading review queue:', error);
    }
}

// Review Action Handler
async function reviewAction(assessmentId, action) {
    try {
        const response = await fetch('/api/dashboard/review-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                assessment_id: assessmentId,
                action: action,
                comment: ''
            })
        });

        if (response.ok) {
            // Reload the queue
            await loadReviewQueue();
            await loadRealTimeMetrics();
        } else {
            console.error('Failed to process review action');
        }
    } catch (error) {
        console.error('Error processing review action:', error);
    }
}

// Top Triggered Rules
async function loadTriggeredRules() {
    try {
        const response = await fetch('/api/dashboard/top-rules?limit=10');
        const data = await response.json();

        const rulesContainer = document.getElementById('triggered-rules');
        rulesContainer.innerHTML = '';

        if (data.length === 0) {
            rulesContainer.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 1rem;">No rules triggered</p>';
            return;
        }

        data.forEach(rule => {
            const ruleItem = document.createElement('div');
            ruleItem.className = 'rule-item';

            ruleItem.innerHTML = `
                <div class="rule-info">
                    <div class="rule-name">${rule.name}</div>
                    <div class="rule-description">${rule.description || 'No description'}</div>
                </div>
                <div class="rule-count">${rule.count}</div>
            `;

            rulesContainer.appendChild(ruleItem);
        });
    } catch (error) {
        console.error('Error loading triggered rules:', error);
    }
}

// Transaction Details Modal
function showTransactionDetails(tx) {
    const modal = document.getElementById('transaction-modal');
    const modalBody = document.getElementById('modal-body');

    const rulesHtml = tx.triggered_rules.length > 0
        ? tx.triggered_rules.map(r => `
            <div style="padding: 0.5rem; background: #ecf0f1; border-radius: 4px; margin-bottom: 0.5rem;">
                <strong>${r.name}</strong> (Weight: ${r.weight})<br>
                <span style="font-size: 0.875rem; color: #7f8c8d;">${r.description}</span>
            </div>
        `).join('')
        : '<p>No rules triggered</p>';

    modalBody.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <strong>Transaction ID:</strong> ${tx.transaction_id}<br>
            <strong>Employee:</strong> ${tx.employee_name} (${tx.employee_id})<br>
            <strong>Amount:</strong> ${formatCurrency(tx.amount)}<br>
            <strong>Type:</strong> ${tx.transaction_type}<br>
            <strong>Account:</strong> ${tx.account_number}<br>
            <strong>Timestamp:</strong> ${new Date(tx.timestamp).toLocaleString()}<br>
            <strong>Risk Score:</strong> ${tx.risk_score} (${tx.risk_level.toUpperCase()})<br>
            <strong>Decision:</strong> ${tx.decision}<br>
            <strong>Status:</strong> ${tx.verification_status}
        </div>
        <div>
            <strong>Triggered Rules:</strong>
            <div style="margin-top: 0.5rem;">${rulesHtml}</div>
        </div>
    `;

    modal.classList.add('active');
}

// Close Modal
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('close-modal') || e.target.classList.contains('modal')) {
        document.getElementById('transaction-modal').classList.remove('active');
    }
});

// ============================================================================
// EXECUTIVE SUMMARY TAB
// ============================================================================

async function loadExecutiveSummaryData() {
    try {
        await Promise.all([
            loadExecutiveKPIs(),
            loadRiskDistributionPie(),
            loadTrendsChart(),
            loadRiskContributors()
        ]);
    } catch (error) {
        console.error('Error loading Executive Summary data:', error);
    }
}

// Executive KPIs
async function loadExecutiveKPIs() {
    try {
        const response = await fetch(`/api/dashboard/kpis?period=${currentPeriod}`);
        const data = await response.json();

        document.getElementById('exec-total-txs').textContent = formatNumber(data.total_transactions);
        document.getElementById('exec-flagged').textContent = formatNumber(data.flagged_transactions);
        document.getElementById('exec-flagged-rate').textContent = `${formatPercentage(data.flagged_rate)} flagged`;
        document.getElementById('exec-confirmed').textContent = formatNumber(data.confirmed_frauds);
        document.getElementById('exec-fraud-value').textContent = formatCurrency(data.fraud_prevented_value) + ' blocked';
        document.getElementById('exec-review-cost').textContent = formatCurrency(data.review_cost);
        document.getElementById('exec-net-savings').textContent = formatCurrency(data.net_savings);
        document.getElementById('exec-fpr').textContent = formatPercentage(data.false_positive_rate);
        document.getElementById('exec-sla').textContent = formatPercentage(data.sla_compliance);

        // Color code based on thresholds
        const fprElement = document.getElementById('exec-fpr');
        if (data.false_positive_rate > 0.15) {
            fprElement.style.color = '#e74c3c';
        } else {
            fprElement.style.color = '#27ae60';
        }

        const slaElement = document.getElementById('exec-sla');
        if (data.sla_compliance < 0.95) {
            slaElement.style.color = '#e74c3c';
        } else {
            slaElement.style.color = '#27ae60';
        }
    } catch (error) {
        console.error('Error loading executive KPIs:', error);
    }
}

// Risk Distribution Pie Chart
async function loadRiskDistributionPie() {
    try {
        const response = await fetch('/api/dashboard/risk-distribution');
        const data = await response.json();

        const ctx = document.getElementById('risk-distribution-chart');
        if (charts.riskDistribution) {
            charts.riskDistribution.destroy();
        }

        charts.riskDistribution = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                datasets: [{
                    data: [data.low, data.medium, data.high],
                    backgroundColor: [
                        'rgba(39, 174, 96, 0.8)',
                        'rgba(243, 156, 18, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading risk distribution pie:', error);
    }
}

// Trends Chart
async function loadTrendsChart() {
    try {
        const response = await fetch('/api/dashboard/metrics/trends?days=7');
        const data = await response.json();

        const ctx = document.getElementById('trends-chart');
        if (charts.trends) {
            charts.trends.destroy();
        }

        charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                datasets: [
                    {
                        label: 'Total Transactions',
                        data: data.map(d => d.total),
                        borderColor: 'rgba(52, 152, 219, 1)',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Flagged Transactions',
                        data: data.map(d => d.flagged),
                        borderColor: 'rgba(243, 156, 18, 1)',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'High Risk',
                        data: data.map(d => d.high_risk),
                        borderColor: 'rgba(231, 76, 60, 1)',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading trends chart:', error);
    }
}

// Risk Contributors
async function loadRiskContributors() {
    try {
        const response = await fetch('/api/dashboard/top-rules?limit=5');
        const data = await response.json();

        const contributorsContainer = document.getElementById('risk-contributors');
        contributorsContainer.innerHTML = '';

        if (data.length === 0) {
            contributorsContainer.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 1rem;">No data available</p>';
            return;
        }

        data.forEach((rule, index) => {
            const contributorItem = document.createElement('div');
            contributorItem.className = 'contributor-item';

            contributorItem.innerHTML = `
                <div class="contributor-rank">#${index + 1}</div>
                <div class="contributor-info">
                    <div class="contributor-name">${rule.name}</div>
                    <div class="contributor-description">${rule.description || 'No description'}</div>
                </div>
                <div class="contributor-count">${rule.count}</div>
            `;

            contributorsContainer.appendChild(contributorItem);
        });
    } catch (error) {
        console.error('Error loading risk contributors:', error);
    }
}
