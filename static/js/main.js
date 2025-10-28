/**
 * Main Application Module - Tab-based trading system
 * Handles BTC and ETH charts with independent time controls
 */

// Import functions from modules
import { getDatasetData } from './api.js';
import { initChart, renderChart } from './chart.js';
import { initOscillatorChart, renderOscillatorChart } from './oscillator.js';

// Application state
const appState = {
    activeTab: 'btc',              // Current active tab
    days: {
        btc: 30,                    // Default 1M for BTC
        eth: 30,                    // Default 1M for ETH
        gold: 30                    // Default 1M for Gold
    },
    chartData: {
        btc: null,
        eth: null,
        gold: null
    },
    chartsInitialized: {
        btc: false,
        eth: false,
        gold: false
    },
    colors: {
        btc: '#F7931A',             // Bitcoin orange
        eth: '#627EEA',             // Ethereum blue
        gold: '#FFD700'             // Gold yellow
    },
    // Oscillator state
    oscillatorData: {
        btc: {},
        eth: {},
        gold: {}
    },
    oscillatorsInitialized: {
        btc: false,
        eth: false,
        gold: false
    },
    selectedDatasets: {
        btc: ['rsi', 'macd', 'volume', 'dxy'],
        eth: ['rsi', 'macd', 'volume', 'dxy'],
        gold: ['rsi', 'macd', 'dxy']  // No volume for gold
    },
    datasetColors: {
        rsi: '#FF9500',
        macd: '#2196F3',
        volume: '#9C27B0',
        dxy: '#4CAF50'
    }
};

/**
 * Main application entry point
 */
async function main() {
    console.log('BTC Trading System initializing...');

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        await initialize();
    }
}

/**
 * Initialize the application
 */
async function initialize() {
    try {
        console.log('Initializing application...');

        // Setup tab switching
        setupTabs();

        // Setup time period controls
        setupTimeControls();

        // Setup oscillator controls
        setupOscillatorControls();

        // Initialize and load the default tab (BTC)
        await loadTab('btc');

        console.log('Application initialized successfully!');

    } catch (error) {
        console.error('Failed to initialize application:', error);
        showErrorMessage('btc', 'Failed to initialize application. Please refresh the page.');
    }
}

/**
 * Setup tab switching behavior
 */
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const tabName = button.dataset.tab;

            if (tabName === appState.activeTab) {
                return; // Already on this tab
            }

            // Update UI
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Update state
            appState.activeTab = tabName;

            // Load tab data
            await loadTab(tabName);
        });
    });
}

/**
 * Setup time period control buttons
 */
function setupTimeControls() {
    const timeButtons = document.querySelectorAll('.time-btn');

    timeButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const dataset = button.dataset.dataset;
            const days = parseInt(button.dataset.days);

            // Update active button for this dataset
            document.querySelectorAll(`.time-btn[data-dataset="${dataset}"]`).forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');

            // Update state and reload chart
            appState.days[dataset] = days;
            await loadChartData(dataset);
            await loadOscillatorData(dataset);
        });
    });
}

/**
 * Setup oscillator control event handlers
 */
function setupOscillatorControls() {
    // Setup dataset checkboxes
    document.querySelectorAll('.dataset-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', async () => {
            const asset = checkbox.dataset.asset;
            const datasetName = checkbox.dataset.dataset;

            // Update selected datasets
            if (checkbox.checked) {
                if (!appState.selectedDatasets[asset].includes(datasetName)) {
                    appState.selectedDatasets[asset].push(datasetName);
                }
            } else {
                appState.selectedDatasets[asset] = appState.selectedDatasets[asset].filter(
                    d => d !== datasetName
                );
            }

            // Reload oscillator data
            await loadOscillatorData(asset);
        });
    });
}

/**
 * Load a tab (initialize chart if needed, fetch and render data)
 * @param {string} dataset - Dataset name ('btc', 'eth', 'gold')
 */
async function loadTab(dataset) {
    console.log(`Loading tab: ${dataset}`);

    // Initialize price chart if not already initialized
    if (!appState.chartsInitialized[dataset]) {
        const containerId = `${dataset}-chart-container`;
        const color = appState.colors[dataset];

        console.log(`Initializing price chart for ${dataset}`);
        initChart(containerId, dataset, color);
        appState.chartsInitialized[dataset] = true;
    }

    // Initialize oscillator chart if not already initialized
    if (!appState.oscillatorsInitialized[dataset]) {
        const containerId = `${dataset}-oscillator-container`;
        const color = appState.colors[dataset];

        console.log(`Initializing oscillator chart for ${dataset}`);
        initOscillatorChart(containerId, dataset, color);
        appState.oscillatorsInitialized[dataset] = true;
    }

    // Load price chart data
    await loadChartData(dataset);

    // Load oscillator data
    await loadOscillatorData(dataset);
}

/**
 * Fetch data and render chart for a dataset
 * @param {string} dataset - Dataset name ('btc' or 'eth')
 */
async function loadChartData(dataset) {
    const days = appState.days[dataset];

    console.log(`Fetching ${dataset} data for ${days} days...`);

    // Show loading state
    showLoadingMessage(dataset);

    try {
        // Fetch data from API
        const result = await getDatasetData(dataset, days);

        if (!result || !result.data || result.data.length === 0) {
            throw new Error('No data available');
        }

        console.log(`Received ${result.data.length} data points for ${dataset}`);

        // Store data in state
        appState.chartData[dataset] = result.data;

        // Render chart
        renderChart(dataset, result.data);

        // Clear loading message
        clearMessages(dataset);

    } catch (error) {
        console.error(`Error loading ${dataset} data:`, error);
        showErrorMessage(dataset, `Failed to load ${dataset.toUpperCase()} data. Please check server connection.`);
    }
}

/**
 * Fetch oscillator data and render oscillator chart
 * @param {string} asset - Asset name ('btc', 'eth', 'gold')
 */
async function loadOscillatorData(asset) {
    const days = appState.days[asset];
    const datasets = appState.selectedDatasets[asset].join(',');
    const normalizer = 'zscore';  // Always use zscore (regression divergence) normalizer

    if (!datasets) {
        console.log(`No datasets selected for ${asset} oscillator`);
        return;
    }

    console.log(`Fetching oscillator data for ${asset}: datasets=${datasets}, normalizer=${normalizer}, days=${days}`);

    try {
        // Fetch from API
        const url = `/api/oscillator-data?asset=${asset}&datasets=${datasets}&days=${days}&normalizer=${normalizer}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (!result || !result.datasets) {
            throw new Error('Invalid oscillator data received');
        }

        console.log(`Received oscillator data for ${asset}:`, Object.keys(result.datasets));

        // Store data in state
        appState.oscillatorData[asset] = result;

        // Prepare data for rendering
        const datasetsData = {};
        Object.entries(result.datasets).forEach(([datasetName, datasetInfo]) => {
            datasetsData[datasetName] = datasetInfo.data;
        });

        // Render oscillator chart
        renderOscillatorChart(asset, datasetsData, appState.datasetColors);

    } catch (error) {
        console.error(`Error loading oscillator data for ${asset}:`, error);
    }
}

/**
 * Show loading message in chart container
 * @param {string} dataset - Dataset name
 */
function showLoadingMessage(dataset) {
    const container = document.getElementById(`${dataset}-chart-container`);

    // Remove existing messages
    clearMessages(dataset);

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.textContent = `Loading ${dataset.toUpperCase()} data...`;
    container.appendChild(loadingDiv);
}

/**
 * Show error message in chart container
 * @param {string} dataset - Dataset name
 * @param {string} message - Error message
 */
function showErrorMessage(dataset, message) {
    const container = document.getElementById(`${dataset}-chart-container`);

    // Remove existing messages
    clearMessages(dataset);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 24px; margin-bottom: 10px;">⚠</div>
            <div>${message}</div>
        </div>
    `;
    container.appendChild(errorDiv);
}

/**
 * Clear all messages from chart container
 * @param {string} dataset - Dataset name
 */
function clearMessages(dataset) {
    const container = document.getElementById(`${dataset}-chart-container`);

    // Remove loading and error messages
    const messages = container.querySelectorAll('.loading, .error');
    messages.forEach(msg => msg.remove());
}

// Start the application
main();
