const apiBaseUrl = window.BACKTEST_API_URL || 'http://localhost:8000';
const form = document.getElementById('strategy-form');
const promptInput = document.getElementById('strategyInput');
const generateButton = document.getElementById('generateBtn');
const statusMessage = document.getElementById('ai-status');
const preview = document.getElementById('generated-preview');
const promptCount = document.getElementById('prompt-count');

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

function setStatus(message, state = 'success') {
    statusMessage.textContent = message;
    statusMessage.dataset.state = state;
}

function formatCondition(condition) {
    const parameters = Object.entries(condition.params || {})
        .filter(([, value]) => value !== null && value !== undefined)
        .map(([name, value]) => `${name.replaceAll('_', ' ')} ${value}`);
    const left = [condition.indicator, ...parameters].join(' ');
    const right = condition.target_type === 'indicator'
        ? condition.target_value
        : Number(condition.target_value).toLocaleString();
    return `${left} ${condition.operator} ${right}`;
}

function renderRuleGroup(containerId, group) {
    const container = document.getElementById(containerId);
    container.replaceChildren();

    if (!Array.isArray(group?.conditions) || group.conditions.length === 0) {
        const emptyRule = document.createElement('p');
        emptyRule.className = 'rule-list';
        emptyRule.textContent = 'No conditions were returned.';
        container.append(emptyRule);
        return;
    }

    const list = document.createElement('ul');
    list.className = 'rule-list';
    group.conditions.forEach((condition) => {
        const item = document.createElement('li');
        item.textContent = formatCondition(condition);
        list.append(item);
    });

    const logic = document.createElement('span');
    logic.className = 'condition-chip';
    logic.textContent = `Join conditions with ${group.logic || 'AND'}`;
    container.append(list, logic);
}

function renderStrategy(strategy) {
    document.getElementById('generated-name').textContent = strategy.name;
    document.getElementById('generated-description').textContent = strategy.description;
    renderRuleGroup('entry-rules', strategy.entry_rules);
    renderRuleGroup('exit-rules', strategy.exit_rules);
    preview.hidden = false;
}

function updatePromptCount() {
    promptCount.textContent = `${promptInput.value.length} / 1000`;
}

function errorMessage(body, status) {
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail)) {
        return body.detail.map((issue) => issue.msg || JSON.stringify(issue)).join(' ');
    }
    return `Could not generate the strategy (${status}).`;
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt) {
        setStatus('Describe a strategy before generating it.', 'error');
        promptInput.focus();
        return;
    }

    generateButton.disabled = true;
    generateButton.querySelectorAll('span')[1].textContent = 'Working on your strategy…';
    setStatus('Turning your idea into testable rules…', 'loading');

    try {
        const response = await fetch(`${apiBaseUrl}/api/backtests/generateStrategy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const strategy = await response.json();
        if (!response.ok) throw new Error(errorMessage(strategy, response.status));

        localStorage.setItem('generatedStrategy', JSON.stringify(strategy));
        renderStrategy(strategy);
        setStatus('Strategy generated and saved in this browser. Review the rules below before backtesting.');
        preview.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        setStatus(error.message, 'error');
    } finally {
        generateButton.disabled = false;
        generateButton.querySelectorAll('span')[1].textContent = 'Generate strategy';
    }
});

promptInput.addEventListener('input', updatePromptCount);

document.querySelectorAll('.suggestion-chip').forEach((button) => {
    button.addEventListener('click', () => {
        promptInput.value = button.dataset.prompt;
        updatePromptCount();
        promptInput.focus();
    });
});

try {
    const savedStrategy = localStorage.getItem('generatedStrategy');
    if (savedStrategy) {
        renderStrategy(JSON.parse(savedStrategy));
        setStatus('Your last generated strategy is saved in this browser.');
    }
} catch (error) {
    setStatus(`Could not read the saved strategy: ${error.message}`, 'error');
}

showToday();
checkApi();
updatePromptCount();
