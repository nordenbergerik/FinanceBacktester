const form = document.getElementById('backtest-form');
const submitButton = form.querySelector('button[type="submit"]');
const apiResults = document.getElementById('api-results');
const resultTitle = document.getElementById('result-title');
const resultStatus = document.getElementById('result-status');
const strategySelect = document.getElementById('strategy-select');
const strategyDescription = document.getElementById('strategy-description');

const apiBaseUrl = window.BACKTEST_API_URL || 'http://localhost:8000';

/**
 * Fetches the available backtest strategies from the API and populates the strategy dropdown.
 * It also stores each strategy's description for later display when the user changes selection.
 */
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

/**
 * Renders a completed backtest result in the UI by updating the title, status, metric cards,
 * and number of observations shown to the user.
 *
 * @param {Object} result - The backtest result payload returned by the API.
 */
function renderResults(result) {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');

    if (startDateInput && result.start_date) startDateInput.value = result.start_date;
    if (endDateInput && result.end_date) endDateInput.value = result.end_date;

    resultTitle.textContent = `${result.symbol} backtest results`;
    resultStatus.textContent = `${result.strategy} · ${result.start_date} to ${result.end_date}`;
    document.getElementById('api-metrics').innerHTML = Object.entries(result.metrics)
        .map(([name, value]) => `<div class="api-metric"><span>${name.replaceAll('_', ' ')}</span><strong>${Number(value).toFixed(4)}</strong></div>`)
        .join('');
    document.getElementById('price-count').textContent = `${result.dates.length} daily observations`;
    apiResults.hidden = false;
}

/**
 * Handles form submission by building the backtest payload, sending it to the API,
 * updating the UI while the request is running, and showing either the result or an error.
 *
 * @param {Event} event - The submit event triggered by the form.
 */
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

/**
 * Updates the strategy description text when the selected strategy changes.
 */
strategySelect.addEventListener('change', () => {
    const descriptions = JSON.parse(strategySelect.dataset.descriptions || '{}');
    strategyDescription.textContent = descriptions[strategySelect.value] || strategyDescription.textContent;
});

loadStrategies();