// ALL data comes from backend, NO hardcoded values

let updateInterval = null;
let startTime = null;
let wearChart = null;
let accuracyChart = null;
let csvWearChart = null;
let csvAccuracyChart = null;
let csvOpsChart = null;
let csvHealthChart = null;
let currentTestRun = null;
let testStartTime = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('startBtn').addEventListener('click', startSimulation);
    document.getElementById('stopBtn').addEventListener('click', stopSimulation);
    document.getElementById('resetBtn').addEventListener('click', resetSimulation);
    document.getElementById('exportBtn').addEventListener('click', exportData);
    document.getElementById('refreshCsvBtn').addEventListener('click', loadCsvList);
    document.getElementById('loadCsvBtn').addEventListener('click', loadSelectedCsv);
    document.getElementById('refreshCsvListBtn').addEventListener('click', loadCsvList);
    
    // Initialize charts
    initCharts();
    initCsvCharts();
    
    // Initial data fetch
    fetchStats();
    fetchTestResults();
    loadCsvList();
    
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

function initCsvCharts() {
    // CSV Wear chart
    const csvWearDiv = document.getElementById('csvWearChart');
    if (csvWearDiv) {
        csvWearChart = Plotly.newPlot(csvWearDiv, [{
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Wear Balance',
            line: {color: '#3b82f6', width: 2}
        }], {
            margin: {t: 20, r: 20, b: 40, l: 50},
            yaxis: {title: 'Balance %'}
        });
    }
    
    // CSV Accuracy chart
    const csvAccDiv = document.getElementById('csvAccuracyChart');
    if (csvAccDiv) {
        csvAccuracyChart = Plotly.newPlot(csvAccDiv, [{
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Accuracy',
            line: {color: '#8b5cf6', width: 2}
        }], {
            margin: {t: 20, r: 20, b: 40, l: 50},
            yaxis: {title: 'Accuracy %'}
        });
    }
    
    // CSV Ops chart
    const csvOpsDiv = document.getElementById('csvOpsChart');
    if (csvOpsDiv) {
        csvOpsChart = Plotly.newPlot(csvOpsDiv, [{
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Writes',
            line: {color: '#10b981', width: 2}
        }, {
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Reads',
            line: {color: '#f59e0b', width: 2}
        }], {
            margin: {t: 20, r: 20, b: 40, l: 50},
            yaxis: {title: 'Count'}
        });
    }
    
    // CSV Health chart
    const csvHealthDiv = document.getElementById('csvHealthChart');
    if (csvHealthDiv) {
        csvHealthChart = Plotly.newPlot(csvHealthDiv, [{
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'P3 Health',
            line: {color: '#ec4899', width: 2}
        }, {
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'P2 Health',
            line: {color: '#8b5cf6', width: 2}
        }], {
            margin: {t: 20, r: 20, b: 40, l: 50},
            yaxis: {title: 'Health %', range: [0, 100]}
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
    
    // Show test details panel
    showTestDetails(testName);
    
    testStartTime = Date.now();
    
    fetch(`/api/run-test/${testName}`)
        .then(response => response.json())
        .then(data => {
            updateTestStatus(testName, data);
            button.style.opacity = '1';
            
            // Show test details
            if (data.details) {
                displayTestDetails(testName, data);
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

function showTestDetails(testName) {
    const panel = document.getElementById('testDetailsPanel');
    const title = document.getElementById('testDetailsTitle');
    panel.style.display = 'block';
    
    let displayName = '';
    switch(testName) {
        case 'flash': displayName = 'Flash Simulation Test'; break;
        case 'adaptive': displayName = 'Patent 1: Adaptive Wear Test'; break;
        case 'predictive': displayName = 'Patent 2: Predictive Retirement Test'; break;
        case 'self_healing': displayName = 'Patent 3: Self-Healing Test'; break;
        case 'integration': displayName = 'Integration Test'; break;
        default: displayName = testName;
    }
    title.textContent = displayName;
    
    document.getElementById('testDetailsContent').innerHTML = `
        <div class="test-progress">
            <div class="progress-bar" id="testProgressBar" style="width: 0%;">0%</div>
        </div>
        <div class="test-stats">
            <div class="stat">Passed: <span id="testPassed">0</span></div>
            <div class="stat">Total: <span id="testTotal">0</span></div>
            <div class="stat">Time: <span id="testTime">0s</span></div>
        </div>
        <div class="test-steps" id="testSteps">Running tests...</div>
    `;
}

function closeTestDetails() {
    document.getElementById('testDetailsPanel').style.display = 'none';
}

function displayTestDetails(testName, data) {
    const details = data.details;
    if (!details) return;
    
    const passed = details.passed || 0;
    const total = details.total || 0;
    const percentage = total > 0 ? Math.round((passed / total) * 100) : 0;
    const elapsed = ((Date.now() - testStartTime) / 1000).toFixed(1);
    
    document.getElementById('testPassed').textContent = passed;
    document.getElementById('testTotal').textContent = total;
    document.getElementById('testTime').textContent = elapsed + 's';
    
    const progressBar = document.getElementById('testProgressBar');
    progressBar.style.width = percentage + '%';
    progressBar.textContent = percentage + '%';
    
    let stepsHtml = '<ul class="test-steps-list">';
    if (details.details && Array.isArray(details.details)) {
        details.details.forEach(step => {
            const status = step.includes('✅') ? 'passed' : (step.includes('❌') ? 'failed' : '');
            stepsHtml += `<li class="test-step ${status}">${step}</li>`;
        });
    }
    stepsHtml += '</ul>';
    
    document.getElementById('testSteps').innerHTML = stepsHtml;
}

function loadCsvList() {
    fetch('/api/csv-list')
        .then(response => response.json())
        .then(files => {
            const select = document.getElementById('csvFileSelect');
            select.innerHTML = '<option value="">Select CSV file...</option>';
            files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading CSV list:', error));
}

function loadSelectedCsv() {
    const select = document.getElementById('csvFileSelect');
    const filename = select.value;
    if (!filename) {
        alert('Please select a CSV file');
        return;
    }
    
    document.getElementById('lastCsvFile').textContent = filename;
    
    fetch(`/api/csv-data/${filename}`)
        .then(response => response.json())
        .then(data => {
            updateCsvDashboard(data);
        })
        .catch(error => console.error('Error loading CSV data:', error));
}

function updateCsvDashboard(data) {
    if (!data || !data.summary) return;
    
    // Update metrics
    document.getElementById('csvTotalPoints').textContent = data.summary.total_points || 0;
    document.getElementById('csvAvgWear').textContent = (data.summary.avg_wear_balance || 0).toFixed(1) + '%';
    document.getElementById('csvAvgAccuracy').textContent = (data.summary.avg_accuracy || 0).toFixed(1) + '%';
    document.getElementById('csvTotalWrites').textContent = data.summary.total_writes || 0;
    
    // Update summary text
    const summaryText = `
Total Data Points: ${data.summary.total_points}
Date Range: ${data.summary.start_date} to ${data.summary.end_date}
Total Writes: ${data.summary.total_writes}
Total Reads: ${data.summary.total_reads}
Total Erases: ${data.summary.total_erases}
Avg Wear Balance: ${data.summary.avg_wear_balance.toFixed(1)}%
Avg Accuracy: ${data.summary.avg_accuracy.toFixed(1)}%
Avg P3 Health: ${data.summary.avg_p3_health.toFixed(1)}%
Max Write Time: ${data.summary.max_write_time}μs
Min Write Time: ${data.summary.min_write_time}μs
    `;
    document.getElementById('csvSummaryText').textContent = summaryText;
    
    // Update charts
    if (data.charts && data.charts.timestamps) {
        // Wear chart
        if (csvWearChart && data.charts.wear_balance) {
            Plotly.update('csvWearChart', {
                x: [data.charts.timestamps],
                y: [data.charts.wear_balance]
            });
        }
        
        // Accuracy chart
        if (csvAccuracyChart && data.charts.accuracy) {
            Plotly.update('csvAccuracyChart', {
                x: [data.charts.timestamps],
                y: [data.charts.accuracy]
            });
        }
        
        // Ops chart
        if (csvOpsChart) {
            Plotly.update('csvOpsChart', {
                x: [data.charts.timestamps, data.charts.timestamps],
                y: [data.charts.writes || [], data.charts.reads || []]
            });
        }
        
        // Health chart
        if (csvHealthChart) {
            Plotly.update('csvHealthChart', {
                x: [data.charts.timestamps, data.charts.timestamps],
                y: [data.charts.p3_health || [], data.charts.p2_health || []]
            });
        }
    }
}