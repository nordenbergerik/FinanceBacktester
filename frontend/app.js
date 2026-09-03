const form = document.getElementById('backtest-form');
const submitButton = form.querySelector('button[type="submit"]');
const apiResults = document.getElementById('api-results');
const resultTitle = document.getElementById('result-title');
const resultStatus = document.getElementById('result-status');
const strategySelect = document.getElementById('strategy-select');
const strategyDescription = document.getElementById('strategy-description');

const apiBaseUrl = window.BACKTEST_API_URL || 'http://localhost:8000';

function loadStrategies() {
    fetch(`${apiBaseUrl}/api/backtests/strategies`)
        .then((response) => {
            if (!response.ok) throw new Error('Could not load strategies.');
            return response.json();
        })
        .then((strategies) => {
            strategySelect.innerHTML = strategies
                .map((strategy) => `<option value="${strategy.id}">${strategy.name}</option>`)
                .join('');
            strategyDescription.textContent = strategies[0]?.description || '';
            strategySelect.dataset.descriptions = JSON.stringify(
                Object.fromEntries(strategies.map((strategy) => [strategy.id, strategy.description]))
            );
        })
        .catch(() => { });
}

function renderResults(result) {
    resultTitle.textContent = `${result.symbol} backtest results`;
    resultStatus.textContent = `${result.strategy} · ${result.start_date} to ${result.end_date}`;
    document.getElementById('api-metrics').innerHTML = Object.entries(result.metrics)
        .map(([name, value]) => `<div class="api-metric"><span>${name.replaceAll('_', ' ')}</span><strong>${Number(value).toFixed(4)}</strong></div>`)
        .join('');
    document.getElementById('price-count').textContent = `${result.dates.length} daily observations`;
    apiResults.hidden = false;
}

form.addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
        symbol: formData.get('symbol'),
        start_date: formData.get('start-date'),
        end_date: formData.get('end-date'),
        cash: Number(formData.get('capital')),
        strategy: formData.get('strategy')
    };
    submitButton.disabled = true;
    submitButton.querySelector('span').textContent = 'Running backtest...';
    resultStatus.textContent = 'Loading data and calculating metrics...';
    fetch(`${apiBaseUrl}/api/backtests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(async (response) => {
            const body = await response.json();
            if (!response.ok) throw new Error(body.detail || 'The backtest failed.');
            return body;
        })
        .then(renderResults)
        .catch((error) => { resultStatus.textContent = error.message; })
        .finally(() => {
            submitButton.disabled = false;
            submitButton.querySelector('span').textContent = 'Run backtest';
        });
});

submitButton.disabled = false;
submitButton.querySelector('span').textContent = 'Run backtest';
strategySelect.addEventListener('change', () => {
    const descriptions = JSON.parse(strategySelect.dataset.descriptions || '{}');
    strategyDescription.textContent = descriptions[strategySelect.value] || strategyDescription.textContent;
});
loadStrategies();
