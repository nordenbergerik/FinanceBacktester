const form = document.getElementById('backtest-form');
const apiResults = document.getElementById('api-results');
const resultTitle = document.getElementById('result-title');
const resultStatus = document.getElementById('result-status');
const resultSymbol = document.getElementById('result-symbol');
const strategySelect = document.getElementById('strategy-select');
const strategyDescription = document.getElementById('strategy-description');
const submitButtons = [...form.querySelectorAll('button[type="submit"]')];
const apiBaseUrl = window.BACKTEST_API_URL || 'http://localhost:8000';

function setApiStatus(connected) {
    const state = connected ? 'connected' : 'error';
    const label = connected ? 'API connected' : 'API unavailable';
    const status = document.getElementById('api-status');
    status.dataset.state = state;
    status.lastElementChild.textContent = label;

    const sidebarStatus = document.getElementById('sidebar-api-status');
    sidebarStatus.closest('.engine-status').dataset.state = state;
    sidebarStatus.textContent = connected ? 'Engine connected' : 'Engine unavailable';
}

async function checkApi() {
    try {
        const response = await fetch(`${apiBaseUrl}/health`);
        if (!response.ok) throw new Error(`API health check failed (${response.status}).`);
        setApiStatus(true);
    } catch (error) {
        setApiStatus(false);
    }
}

function showToday() {
    document.getElementById('today-date').textContent = new Intl.DateTimeFormat('en', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
    }).format(new Date());
}

async function loadStrategies() {
    try {
        const response = await fetch(`${apiBaseUrl}/api/backtests/strategies`);
        if (!response.ok) throw new Error(`Could not load strategies (${response.status}).`);

        const strategies = await response.json();
        if (!Array.isArray(strategies) || strategies.length === 0) {
            throw new Error('The API did not return any available strategies.');
        }

        const selectedStrategy = strategySelect.value;
        strategySelect.replaceChildren(...strategies.map((strategy) => {
            const option = document.createElement('option');
            option.value = strategy.id;
            option.textContent = strategy.name;
            return option;
        }));
        strategySelect.dataset.descriptions = JSON.stringify(
            Object.fromEntries(strategies.map((strategy) => [strategy.id, strategy.description]))
        );
        strategySelect.value = strategies.some((strategy) => strategy.id === selectedStrategy)
            ? selectedStrategy
            : strategies[0].id;
        updateStrategyDescription();
    } catch (error) {
        resultStatus.textContent = `Could not load strategies: ${error.message}`;
    }
}

function updateStrategyDescription() {
    const descriptions = JSON.parse(strategySelect.dataset.descriptions || '{}');
    strategyDescription.textContent = descriptions[strategySelect.value]
        || 'The selected strategy will be applied to the historical price series.';
}

function prettifyMetricName(name) {
    return name.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderMetrics(metrics) {
    const container = document.getElementById('api-metrics');
    container.replaceChildren(...Object.entries(metrics).map(([name, value]) => {
        const card = document.createElement('div');
        card.className = 'api-metric';

        const label = document.createElement('span');
        label.className = 'metric-label';
        label.textContent = prettifyMetricName(name);

        const number = Number(value);
        const metricValue = document.createElement('strong');
        metricValue.className = `metric-value${number < 0 ? ' negative' : ''}`;
        metricValue.textContent = Number.isFinite(number)
            ? number.toLocaleString(undefined, { maximumFractionDigits: 4 })
            : '—';

        card.append(label, metricValue);
        return card;
    }));
}

async function renderResults(result) {
    if (result.start_date) document.getElementById('start-date').value = result.start_date;
    if (result.end_date) document.getElementById('end-date').value = result.end_date;

    resultTitle.textContent = `${result.symbol} backtest`;
    resultStatus.textContent = `${result.strategy} · ${result.start_date} to ${result.end_date}`;
    resultSymbol.textContent = result.symbol;
    resultSymbol.hidden = false;
    document.getElementById('price-count').textContent =
        `${result.dates.length.toLocaleString()} daily observations`;
    renderMetrics(result.metrics);

    document.getElementById('empty-state').hidden = true;
    apiResults.hidden = false;
    const chart = document.getElementById('performance-chart');
    chart.classList.add('is-visible');

    try {
        if (!window.Plotly) throw new Error('Plotly did not load. Check your connection and refresh the page.');

        const layout = {
            ...result.performance_chart.layout,
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: '#ffffff',
            font: {
                ...result.performance_chart.layout.font,
                family: 'DM Sans, sans-serif',
                color: '#52645a'
            },
            margin: { l: 54, r: 24, t: 35, b: 48, ...result.performance_chart.layout.margin },
            xaxis: {
                ...result.performance_chart.layout.xaxis,
                gridcolor: '#eaf0eb',
                zerolinecolor: '#dce6dd'
            },
            yaxis: {
                ...result.performance_chart.layout.yaxis,
                gridcolor: '#eaf0eb',
                zerolinecolor: '#dce6dd'
            }
        };
        await Plotly.react('performance-chart', result.performance_chart.data, layout, {
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        });
    } catch (error) {
        resultStatus.textContent = `Backtest completed, but the chart could not be displayed: ${error.message}`;
    }
}

function getErrorMessage(body, status) {
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail)) {
        return body.detail.map((issue) => issue.msg || JSON.stringify(issue)).join(' ');
    }
    return `The backtest failed (${status}).`;
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const clickedButton = event.submitter || submitButtons[0];
    const action = clickedButton.value || 'runStrategy';
    const formData = new FormData(form);
    let strategy = formData.get('strategy');

    if (action === 'runGeneratedStrategy') {
        const savedStrategy = localStorage.getItem('generatedStrategy');
        if (!savedStrategy) {
            resultStatus.textContent = 'Generate a strategy in AI Studio before running it.';
            return;
        }

        try {
            strategy = JSON.parse(savedStrategy);
        } catch (error) {
            resultStatus.textContent = `Could not read the generated strategy: ${error.message}`;
            return;
        }
    }

    const payload = {
        symbol: formData.get('symbol').trim().toUpperCase(),
        start_date: formData.get('start-date'),
        end_date: formData.get('end-date'),
        cash: Number(formData.get('capital')),
        strategy
    };

    for (const button of submitButtons) {
        button.disabled = true;
        button.dataset.originalLabel = button.querySelector('span').textContent;
    }
    clickedButton.querySelector('span').textContent = 'Running backtest…';
    resultStatus.textContent = 'Loading historical data and calculating performance…';

    try {
        const response = await fetch(`${apiBaseUrl}/api/backtests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const body = await response.json();
        if (!response.ok) throw new Error(getErrorMessage(body, response.status));
        await renderResults(body);
    } catch (error) {
        resultStatus.textContent = error.message;
    } finally {
        for (const button of submitButtons) {
            button.disabled = false;
            button.querySelector('span').textContent = button.dataset.originalLabel;
            delete button.dataset.originalLabel;
        }
    }
});

strategySelect.addEventListener('change', updateStrategyDescription);

showToday();
checkApi();
loadStrategies();
