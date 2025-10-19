/**
 * Main Application Module - Orchestrates the entire application
 * Connects API, UI, and Chart modules together
 */

// Import functions from all modules
import { getDatasets, getDatasetData, getIndexedData } from './api.js';
import { initChart, updateChart, getZoomControls } from './chart.js';
import { initIndexedChart, updateIndexedChart, getIndexedZoomControls } from './indexed-chart.js';
import { initializeControls } from './ui.js';

// Central application state
const appState = {
    days: '365',              // Current time range
    activePlugins: [],        // Currently selected plugins
    datasets: {},             // Cached dataset data (raw)
    metadata: {},             // Cached metadata for each dataset (raw)
    indexedDatasets: {},      // Cached indexed dataset data
    indexedMetadata: {},      // Cached metadata for indexed datasets
    isLoading: false          // Loading state flag
};

/**
 * Main application entry point
 */
async function main() {
    console.log('Financial Dashboard initializing...');

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            // Step 1: Initialize both chart structures
            console.log('Initializing charts...');
            initChart('chart-container', 'tooltip');
            initIndexedChart('indexed-chart-container', 'indexed-tooltip');

            // Step 2: Get zoom controls from both chart modules
            const zoomControls = getZoomControls();
            const indexedZoomControls = getIndexedZoomControls();

            // Step 3: Set up indexed chart zoom button handlers
            document.getElementById('indexed-reset-zoom').addEventListener('click', indexedZoomControls.resetZoom);
            document.getElementById('indexed-zoom-in').addEventListener('click', indexedZoomControls.zoomIn);
            document.getElementById('indexed-zoom-out').addEventListener('click', indexedZoomControls.zoomOut);

            // Step 4: Initialize UI controls with callbacks
            console.log('Initializing UI controls...');
            await initializeControls({
                getDatasets: getDatasets,
                onPluginChange: handlePluginChange,
                onDaysChange: handleDaysChange,
                zoomControls: zoomControls
            });

            console.log('Financial Dashboard initialized successfully!');

        } catch (error) {
            console.error('Failed to initialize application:', error);
            showErrorMessage('Failed to initialize application. Please refresh the page.');
        }
    });
}

/**
 * Handles plugin selection changes from the UI
 * @param {Array<string>} plugins - Array of selected plugin names
 */
async function handlePluginChange(plugins) {
    console.log('Plugin selection changed:', plugins);

    // Update application state
    appState.activePlugins = plugins;

    // If no plugins selected, clear both charts
    if (plugins.length === 0) {
        updateChart([], {}, {}, appState.days);
        updateIndexedChart([], {}, {}, appState.days);
        showInfoMessage('Select at least one dataset to display');
        return;
    }

    // Fetch and render data for selected plugins
    await fetchAndRenderData();
}

/**
 * Handles time range changes from the UI
 * @param {string} days - New time range ('30', '90', '365', 'max')
 */
async function handleDaysChange(days) {
    console.log('Time range changed to:', days);

    // Update application state
    appState.days = days;

    // Clear zoom when changing time range
    // (The chart will reset zoom automatically when new data is provided)

    // Fetch and render data with new time range
    await fetchAndRenderData();
}

/**
 * Fetches data for all active plugins and renders the chart
 */
async function fetchAndRenderData() {
    if (appState.isLoading) {
        console.log('Already loading data, skipping...');
        return;
    }

    if (appState.activePlugins.length === 0) {
        console.log('No plugins selected, skipping data fetch');
        return;
    }

    appState.isLoading = true;
    setLoadingState(true);

    const errors = [];

    try {
        console.log(`Fetching data for ${appState.activePlugins.length} plugins...`);

        // Fetch both raw and indexed data for all active plugins in parallel
        const promises = appState.activePlugins.map(async plugin => {
            try {
                // Fetch raw data
                const rawResult = await getDatasetData(plugin, appState.days);

                // Fetch indexed data
                const indexedResult = await getIndexedData(plugin, appState.days, 100);

                // Check if data is empty
                if (!rawResult.data ||
                    (Array.isArray(rawResult.data) && rawResult.data.length === 0) ||
                    (typeof rawResult.data === 'object' && rawResult.data.middle && rawResult.data.middle.length === 0)) {
                    errors.push(`${rawResult.metadata?.label || plugin}: No data available`);
                }

                return { plugin, rawResult, indexedResult };
            } catch (error) {
                console.error(`Error fetching ${plugin}:`, error);
                errors.push(`${plugin}: Failed to load`);
                return {
                    plugin,
                    rawResult: { data: [], metadata: {} },
                    indexedResult: { data: [], metadata: {} }
                };
            }
        });

        const results = await Promise.all(promises);

        // Update application state with fetched data
        results.forEach(({ plugin, rawResult, indexedResult }) => {
            // Handle special case for Bollinger Bands in raw data
            if (plugin === 'bollinger_bands' && rawResult.data && typeof rawResult.data === 'object' && 'middle' in rawResult.data) {
                appState.datasets[plugin] = rawResult.data;
            } else {
                appState.datasets[plugin] = rawResult.data || [];
            }
            appState.metadata[plugin] = rawResult.metadata || {};

            // Handle special case for Bollinger Bands in indexed data
            if (plugin === 'bollinger_bands' && indexedResult.data && typeof indexedResult.data === 'object' && 'middle' in indexedResult.data) {
                appState.indexedDatasets[plugin] = indexedResult.data;
            } else {
                appState.indexedDatasets[plugin] = indexedResult.data || [];
            }
            appState.indexedMetadata[plugin] = indexedResult.metadata || {};
        });

        // Clear loading state
        setLoadingState(false);
        appState.isLoading = false;

        // Check if we have any valid data
        const hasData = Object.entries(appState.datasets).some(([key, d]) => {
            if (key === 'bollinger_bands') {
                return d.middle && d.middle.length > 0;
            }
            return d.length > 0;
        });

        if (!hasData) {
            showErrorMessage('No data available. This could be due to API rate limits or invalid API key. Check server console for details.');
        } else {
            // Render both charts with new data
            updateChart(
                appState.activePlugins,
                appState.datasets,
                appState.metadata,
                appState.days
            );

            updateIndexedChart(
                appState.activePlugins,
                appState.indexedDatasets,
                appState.indexedMetadata,
                appState.days
            );

            // Show any partial errors
            if (errors.length > 0) {
                showWarningMessage(errors.join(' " '));
            }
        }

    } catch (error) {
        console.error('Error fetching and rendering data:', error);
        setLoadingState(false);
        appState.isLoading = false;
        showErrorMessage('Failed to fetch data. Please ensure the Flask server is running on port 5000.');
    }
}

/**
 * Sets the loading state in the UI
 * @param {boolean} isLoading - Whether the application is loading
 */
function setLoadingState(isLoading) {
    const container = document.getElementById('chart-container');

    // Remove any existing loading messages
    const existingLoading = container.querySelectorAll('.loading');
    existingLoading.forEach(el => el.remove());

    if (isLoading) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'Loading data...';
        container.appendChild(loadingDiv);
    }
}

/**
 * Shows an error message
 * @param {string} message - Error message to display
 */
function showErrorMessage(message) {
    const container = document.getElementById('chart-container');

    // Remove any existing messages
    container.querySelectorAll('.loading, .error, .message').forEach(el => el.remove());

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 24px; margin-bottom: 10px;">�</div>
            <div>${message}</div>
        </div>
    `;
    container.appendChild(errorDiv);
}

/**
 * Shows a warning message (temporary, auto-dismisses)
 * @param {string} message - Warning message to display
 */
function showWarningMessage(message) {
    showMessage(message, 'warning');
}

/**
 * Shows an info message (temporary, auto-dismisses)
 * @param {string} message - Info message to display
 */
function showInfoMessage(message) {
    showMessage(message, 'info');
}

/**
 * Shows a temporary message that auto-dismisses
 * @param {string} message - Message to display
 * @param {string} type - Message type ('warning' or 'info')
 */
function showMessage(message, type = 'info') {
    const container = document.getElementById('chart-container');

    // Remove any existing temporary messages
    container.querySelectorAll('.message').forEach(el => el.remove());

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.style.position = 'absolute';
    messageDiv.style.top = '60px';
    messageDiv.style.left = '50%';
    messageDiv.style.transform = 'translateX(-50%)';
    messageDiv.style.padding = '8px 16px';
    messageDiv.style.background = type === 'warning' ? 'rgba(255, 149, 0, 0.2)' : 'rgba(98, 126, 234, 0.2)';
    messageDiv.style.border = `1px solid ${type === 'warning' ? '#FF9500' : '#627EEA'}`;
    messageDiv.style.borderRadius = '6px';
    messageDiv.style.color = type === 'warning' ? '#FF9500' : '#627EEA';
    messageDiv.style.fontSize = '12px';
    messageDiv.style.zIndex = '100';
    messageDiv.textContent = message;

    container.appendChild(messageDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.style.transition = 'opacity 0.5s';
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 500);
    }, 5000);
}

// Start the application
main();
