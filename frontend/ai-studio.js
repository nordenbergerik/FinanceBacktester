const apiBaseUrl = window.BACKTEST_API_URL || 'http://localhost:8000';
const form = document.getElementById('strategy-form');
const statusMessage = document.getElementById('ai-status');

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const payload = {
        prompt: document.getElementById('strategyInput').value
    };

    statusMessage.textContent = 'Generating strategy...';

    try {
        const response = await fetch(`${apiBaseUrl}/api/backtests/generateStrategy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const strategy = await response.json();
        if (!response.ok) {
            throw new Error(strategy.detail || 'Could not generate the strategy.');
        }
        localStorage.setItem('generatedStrategy', JSON.stringify(strategy));
        statusMessage.textContent = 'Strategy generated. Open Configuration and click Run generated strategy.';
    } catch (error) {
        statusMessage.textContent = error.message;
    }
});