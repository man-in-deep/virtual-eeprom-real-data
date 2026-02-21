// ALL data comes from backend, NO hardcoded values

let updateInterval = null;
let startTime = null;
let wearChart = null;
let accuracyChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('startBtn').addEventListener('click', startSimulation);
    document.getElementById('stopBtn').addEventListener('click', stopSimulation);
    document.getElementById('resetBtn').addEventListener('click', resetSimulation);
    document.getElementById('exportBtn').addEventListener('click', exportData);
    
    // Initialize charts
    initCharts();
    
    // Initial data fetch
    fetchStats();
    fetchTestResults();
    
    // Start periodic updates
    startTime = Date.now();
    updateInterval = setInterval(fetchStats, 2000);
});

function initCharts() {
    // Wear balance chart
    const wearDiv = document.getElementById('wearChart');
    if (wearDiv) {
        wearChart = Plotly.newPlot(wearDiv, [{
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Wear Balance %',
            line: {color: '#3b82f6', width: 2}
        }], {
            margin: {t: 10, r: 10, b: 40, l: 50},
            yaxis: {range: [0, 100], title: 'Balance %'}
        });
    }
    
    // Accuracy chart
    const accDiv = document.getElementById('accuracyChart');
    if (accDiv) {
        accuracyChart = Plotly.newPlot(accDiv, [{
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Prediction Accuracy %',
            line: {color: '#8b5cf6', width: 2}
        }], {
            margin: {t: 10, r: 10, b: 40, l: 50},
            yaxis: {range: [0, 100], title: 'Accuracy %'}
        });
    }
}

function startSimulation() {
    fetch('/api/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'started') {
                document.getElementById('simStatus').textContent = 'Running';
                document.getElementById('simStatus').className = 'status-value running';
            }
        })
        .catch(error => console.error('Error starting simulation:', error));
}

function stopSimulation() {
    fetch('/api/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'stopped') {
                document.getElementById('simStatus').textContent = 'Stopped';
                document.getElementById('simStatus').className = 'status-value stopped';
            }
        })
        .catch(error => console.error('Error stopping simulation:', error));
}

function resetSimulation() {
    fetch('/api/reset', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'reset') {
                document.getElementById('dataPoints').textContent = '0';
                startTime = Date.now();
                fetchStats();
            }
        })
        .catch(error => console.error('Error resetting simulation:', error));
}

function exportData() {
    window.location.href = '/api/export-excel';
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStats(data);
            updateUptime();
        })
        .catch(error => console.error('Error fetching stats:', error));
}

function updateStats(data) {
    // Update data points
    document.getElementById('dataPoints').textContent = data.data_points || 0;
    
    // Update Patent 1 stats
    const p1 = data.patent1 || {};
    document.getElementById('p1-strategy').textContent = p1.current_strategy || 'AUTO';
    document.getElementById('p1-balance').textContent = (p1.wear_balance || 0).toFixed(1) + '%';
    
    const hot = p1.hot_blocks || 0;
    const warm = p1.warm_blocks || 0;
    const cold = p1.cold_blocks || 0;
    document.getElementById('p1-hot').textContent = `${hot}/${warm}/${cold}`;
    document.getElementById('p1-rate').textContent = (p1.write_rate || 0).toFixed(0) + '/hr';
    
    // Update Patent 2 stats
    const p2 = data.patent2 || {};
    document.getElementById('p2-accuracy').textContent = (p2.prediction_accuracy || 0).toFixed(1) + '%';
    document.getElementById('p2-failing').textContent = p2.failing_blocks_count || 0;
    document.getElementById('p2-health').textContent = (p2.avg_health || 100).toFixed(1) + '%';
    document.getElementById('p2-retired').textContent = p2.retired_blocks_count || 0;
    
    // Update Patent 3 stats
    const p3 = data.patent3 || {};
    document.getElementById('p3-health').textContent = (p3.current_health || 100).toFixed(1) + '%';
    
    const healSuccess = p3.heal_success || 0;
    const healAttempts = p3.heal_attempts || 0;
    const healRate = healAttempts > 0 ? (healSuccess * 100 / healAttempts) : 100;
    document.getElementById('p3-rate').textContent = healRate.toFixed(1) + '%';
    
    document.getElementById('p3-corruptions').textContent = p3.corruptions_detected || 0;
    document.getElementById('p3-time').textContent = (p3.avg_heal_time_us || 0).toFixed(0) + 'μs';
    
    // Update comparison
    updateComparison(data.comparison || {});
    
    // Update charts
    fetchHistory();
}

function updateComparison(comp) {
    const grid = document.getElementById('comparison');
    if (!grid) return;
    
    grid.innerHTML = `
        <div class="comparison-item">
            <h4>Without Patents</h4>
            <div class="comparison-stats">
                <div>Lifetime: <span id="without-lifetime">${(comp.without_lifetime || 0).toFixed(1)}</span> years</div>
                <div>Failure Rate: <span id="without-failure">${(comp.without_failure || 0).toFixed(1)}</span>%</div>
                <div>Data Loss Risk: <span id="without-risk">${(comp.without_risk || 0).toFixed(1)}</span>%</div>
            </div>
        </div>
        <div class="comparison-item">
            <h4>With Patents</h4>
            <div class="comparison-stats">
                <div>Lifetime: <span id="with-lifetime">${(comp.with_lifetime || 0).toFixed(1)}</span> years</div>
                <div>Failure Rate: <span id="with-failure">${(comp.with_failure || 0).toFixed(1)}</span>%</div>
                <div>Data Loss Risk: <span id="with-risk">${(comp.with_risk || 0).toFixed(1)}</span>%</div>
            </div>
        </div>
        <div class="comparison-item improvement">
            <h4>Improvement</h4>
            <div class="comparison-stats">
                <div id="improvement-lifetime">+${(comp.lifetime_improvement || 0).toFixed(1)}%</div>
                <div id="improvement-failure">-${(comp.failure_improvement || 0).toFixed(1)}%</div>
                <div id="improvement-risk">-${(comp.risk_improvement || 0).toFixed(1)}%</div>
            </div>
        </div>
    `;
}

function updateUptime() {
    if (startTime) {
        const uptime = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('uptime').textContent = uptime + 's';
    }
}

function fetchHistory() {
    // Fetch Patent 1 history for chart
    fetch('/api/history/patent1')
        .then(response => response.json())
        .then(data => {
            const values = data.map(d => d.wear_balance || 0);
            if (wearChart) {
                Plotly.update('wearChart', {
                    y: [values]
                });
            }
        })
        .catch(error => console.error('Error fetching patent1 history:', error));
    
    // Fetch Patent 2 history for chart
    fetch('/api/history/patent2')
        .then(response => response.json())
        .then(data => {
            const values = data.map(d => d.accuracy || 0);
            if (accuracyChart) {
                Plotly.update('accuracyChart', {
                    y: [values]
                });
            }
        })
        .catch(error => console.error('Error fetching patent2 history:', error));
}

function fetchTestResults() {
    fetch('/api/test-results')
        .then(response => response.json())
        .then(data => {
            updateTestStatus('flash', data.flash);
            updateTestStatus('adaptive', data.adaptive);
            updateTestStatus('predictive', data.predictive);
            updateTestStatus('healing', data.self_healing);
            updateTestStatus('integration', data.integration);
        })
        .catch(error => console.error('Error fetching test results:', error));
}

function updateTestStatus(testId, result) {
    const element = document.getElementById(`test-${testId}`);
    if (element && result) {
        element.textContent = result.status || '⚪ Not Run';
        if (result.status && result.status.includes('✅')) {
            element.className = 'test-status passed';
        } else if (result.status && result.status.includes('❌')) {
            element.className = 'test-status failed';
        } else if (result.status && result.status.includes('⏳')) {
            element.className = 'test-status running';
        } else {
            element.className = 'test-status';
        }
    }
}

function runTest(testName) {
    const button = event.currentTarget;
    button.style.opacity = '0.7';
    
    // Update status to running
    const element = document.getElementById(`test-${testName}`);
    if (element) {
        element.textContent = '⏳ Running...';
        element.className = 'test-status running';
    }
    
    fetch(`/api/run-test/${testName}`)
        .then(response => response.json())
        .then(data => {
            updateTestStatus(testName, data);
            button.style.opacity = '1';
            
            // Show test details in console for debugging
            if (data.details) {
                console.log(`Test ${testName} results:`, data.details);
            }
        })
        .catch(error => {
            console.error('Test error:', error);
            button.style.opacity = '1';
            
            // Update status to error
            if (element) {
                element.textContent = '❌ Error';
                element.className = 'test-status failed';
            }
        });
}