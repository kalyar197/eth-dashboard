/**
 * Chart Module - Candlestick chart rendering for OHLCV data
 * Uses D3.js for visualization
 */

import { syncOscillatorZoom } from './oscillator.js';

// Chart state for each dataset
const chartInstances = {};

/**
 * Initialize a chart for a specific dataset
 * @param {string} containerId - DOM ID of the chart container
 * @param {string} dataset - Dataset name ('btc' or 'eth')
 * @param {string} color - Base color for the chart
 */
export function initChart(containerId, dataset, color) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    // Clear any existing content
    container.innerHTML = '';

    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const margin = { top: 20, right: 60, bottom: 40, left: 60 };
    const width = containerRect.width - margin.left - margin.right;
    const height = containerRect.height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', containerRect.width)
        .attr('height', containerRect.height);

    // Create main group
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create clip path for zoom
    g.append('defs').append('clipPath')
        .attr('id', `clip-${dataset}`)
        .append('rect')
        .attr('width', width)
        .attr('height', height);

    // Create groups for different elements
    const gridGroup = g.append('g').attr('class', 'grid');
    const candlesGroup = g.append('g').attr('class', 'candles').attr('clip-path', `url(#clip-${dataset})`);
    const overlaysGroup = g.append('g').attr('class', 'overlays').attr('clip-path', `url(#clip-${dataset})`);
    const xAxisGroup = g.append('g').attr('class', 'x-axis').attr('transform', `translate(0,${height})`);
    const yAxisGroup = g.append('g').attr('class', 'y-axis');

    // Crosshair elements
    const crosshairGroup = g.append('g').attr('class', 'crosshair').style('display', 'none');
    crosshairGroup.append('line').attr('class', 'crosshair-line crosshair-x');
    crosshairGroup.append('line').attr('class', 'crosshair-line crosshair-y');

    // Store chart instance
    chartInstances[dataset] = {
        svg,
        g,
        width,
        height,
        margin,
        color,
        gridGroup,
        candlesGroup,
        overlaysGroup,
        xAxisGroup,
        yAxisGroup,
        crosshairGroup,
        xScale: null,
        yScale: null,
        zoom: null,
        currentTransform: d3.zoomIdentity,
        overlayData: []  // Store overlay data for zoom updates
    };

    console.log(`Chart initialized for ${dataset}`);
}

/**
 * Render candlestick chart with OHLCV data and optional overlays
 * @param {string} dataset - Dataset name ('btc', 'eth', or 'gold')
 * @param {Array} data - OHLCV data [[timestamp, open, high, low, close, volume], ...]
 * @param {Array} overlays - Optional array of overlay datasets [{data: [[ts, value], ...], metadata: {...}}, ...]
 */
export function renderChart(dataset, data, overlays = []) {
    const chart = chartInstances[dataset];
    if (!chart) {
        console.error(`Chart instance for ${dataset} not found`);
        return;
    }

    if (!data || data.length === 0) {
        console.warn(`No data to render for ${dataset}`);
        showChartMessage(dataset, 'No data available');
        return;
    }

    console.log(`Rendering ${data.length} candles for ${dataset}`);
    if (overlays && overlays.length > 0) {
        console.log(`Rendering ${overlays.length} overlay(s) for ${dataset}`);
    }

    // Store overlay data for zoom updates
    chart.overlayData = overlays || [];

    // Create scales
    chart.xScale = d3.scaleTime()
        .domain(d3.extent(data, d => new Date(d[0])))
        .range([0, chart.width]);

    // Find price range (considering high/low and overlay values)
    const prices = data.flatMap(d => [d[2], d[3]]); // high, low

    // Include overlay values in Y-domain calculation
    if (overlays && overlays.length > 0) {
        overlays.forEach(overlay => {
            if (overlay.data && overlay.data.length > 0) {
                const overlayValues = overlay.data.map(d => d[1]);
                prices.push(...overlayValues);
            }
        });
    }

    chart.yScale = d3.scaleLinear()
        .domain([d3.min(prices) * 0.98, d3.max(prices) * 1.02])
        .range([chart.height, 0]);

    // Create axes
    const xAxis = d3.axisBottom(chart.xScale)
        .ticks(8)
        .tickFormat(d3.timeFormat('%b %d'));

    const yAxis = d3.axisLeft(chart.yScale)
        .ticks(8)
        .tickFormat(d => `$${d.toLocaleString()}`);

    // Draw grid
    chart.gridGroup.selectAll('*').remove();
    chart.gridGroup.selectAll('.grid-line-x')
        .data(chart.xScale.ticks(8))
        .enter()
        .append('line')
        .attr('class', 'grid-line-x')
        .attr('x1', d => chart.xScale(d))
        .attr('x2', d => chart.xScale(d))
        .attr('y1', 0)
        .attr('y2', chart.height)
        .style('stroke', '#222')
        .style('stroke-dasharray', '2,2');

    chart.gridGroup.selectAll('.grid-line-y')
        .data(chart.yScale.ticks(8))
        .enter()
        .append('line')
        .attr('class', 'grid-line-y')
        .attr('x1', 0)
        .attr('x2', chart.width)
        .attr('y1', d => chart.yScale(d))
        .attr('y2', d => chart.yScale(d))
        .style('stroke', '#222')
        .style('stroke-dasharray', '2,2');

    // Calculate candle width based on data density
    const candleWidth = Math.max(2, Math.min(12, chart.width / data.length * 0.7));

    // Draw candlesticks
    chart.candlesGroup.selectAll('*').remove();

    // Draw wicks (high-low lines)
    chart.candlesGroup.selectAll('.wick')
        .data(data)
        .enter()
        .append('line')
        .attr('class', 'wick')
        .attr('x1', d => chart.xScale(new Date(d[0])))
        .attr('x2', d => chart.xScale(new Date(d[0])))
        .attr('y1', d => chart.yScale(d[2])) // high
        .attr('y2', d => chart.yScale(d[3])) // low
        .style('stroke', d => d[4] >= d[1] ? '#26a69a' : '#ef5350') // close >= open ? green : red
        .style('stroke-width', 1);

    // Draw candle bodies (open-close rectangles)
    chart.candlesGroup.selectAll('.candle')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'candle')
        .attr('x', d => chart.xScale(new Date(d[0])) - candleWidth / 2)
        .attr('y', d => chart.yScale(Math.max(d[1], d[4]))) // top of candle
        .attr('width', candleWidth)
        .attr('height', d => {
            const height = Math.abs(chart.yScale(d[1]) - chart.yScale(d[4]));
            return height < 1 ? 1 : height; // Minimum 1px for doji candles
        })
        .style('fill', d => d[4] >= d[1] ? '#26a69a' : '#ef5350') // close >= open ? green : red
        .style('stroke', d => d[4] >= d[1] ? '#26a69a' : '#ef5350')
        .style('stroke-width', 0.5);

    // Update axes
    chart.xAxisGroup.call(xAxis)
        .selectAll('text')
        .style('fill', '#888')
        .style('font-size', '11px');

    chart.yAxisGroup.call(yAxis)
        .selectAll('text')
        .style('fill', '#888')
        .style('font-size', '11px');

    // Style axis lines
    chart.xAxisGroup.selectAll('path, line').style('stroke', '#333');
    chart.yAxisGroup.selectAll('path, line').style('stroke', '#333');

    // Render overlays (moving averages, etc.)
    if (overlays && overlays.length > 0) {
        renderOverlays(dataset, overlays);
    }

    // Add zoom behavior
    setupZoom(dataset, data);

    // Add hover behavior
    setupCrosshair(dataset, data);
}

/**
 * Render overlay lines (moving averages, etc.) or dots (Parabolic SAR)
 * @param {string} dataset - Dataset name
 * @param {Array} overlays - Array of overlay datasets [{data: [[ts, value], ...], metadata: {...}}, ...]
 */
function renderOverlays(dataset, overlays) {
    const chart = chartInstances[dataset];
    if (!chart || !overlays || overlays.length === 0) {
        return;
    }

    // Clear existing overlays
    chart.overlaysGroup.selectAll('*').remove();

    // Render each overlay
    overlays.forEach((overlay, index) => {
        if (!overlay.data || overlay.data.length === 0) {
            return;
        }

        const metadata = overlay.metadata || {};
        const renderType = metadata.renderType || 'line';
        const label = metadata.label || `Overlay ${index + 1}`;

        if (renderType === 'dots') {
            // Render as dots (e.g., Parabolic SAR)
            const dotRadius = metadata.dotRadius || 3;
            const dotColors = metadata.dotColors || { bullish: '#00D9FF', bearish: '#FF1493' };

            chart.overlaysGroup.selectAll(`.sar-dot-${index}`)
                .data(overlay.data)
                .enter()
                .append('circle')
                .attr('class', `sar-dot sar-dot-${index}`)
                .attr('cx', d => chart.xScale(new Date(d[0])))
                .attr('cy', d => chart.yScale(d[1]))
                .attr('r', dotRadius)
                .style('fill', d => {
                    // d[2] is trend: 1 = bullish (below price), -1 = bearish (above price)
                    const trend = d[2] || 1;
                    return trend === 1 ? dotColors.bullish : dotColors.bearish;
                })
                .style('stroke', 'none')
                .style('opacity', 0.85);

            console.log(`Rendered overlay dots: ${label} with ${overlay.data.length} points`);
        } else {
            // Render as line (default for SMA, etc.)
            const color = metadata.color || '#888';
            const strokeWidth = metadata.strokeWidth || 2;

            // Create line generator
            const line = d3.line()
                .x(d => chart.xScale(new Date(d[0])))
                .y(d => chart.yScale(d[1]))
                .curve(d3.curveLinear);

            // Draw the line
            chart.overlaysGroup.append('path')
                .datum(overlay.data)
                .attr('class', `overlay-line overlay-${index}`)
                .attr('d', line)
                .style('fill', 'none')
                .style('stroke', color)
                .style('stroke-width', strokeWidth)
                .style('opacity', 0.85);

            console.log(`Rendered overlay line: ${label} with ${overlay.data.length} points`);
        }
    });
}

/**
 * Setup zoom and pan behavior
 * @param {string} dataset - Dataset name
 * @param {Array} data - OHLCV data
 */
function setupZoom(dataset, data) {
    const chart = chartInstances[dataset];

    // Remove existing zoom overlay
    chart.g.selectAll('.zoom-overlay').remove();

    // Create zoom behavior
    chart.zoom = d3.zoom()
        .scaleExtent([0.5, 10])
        .translateExtent([[0, 0], [chart.width, chart.height]])
        .extent([[0, 0], [chart.width, chart.height]])
        .on('zoom', (event) => {
            chart.currentTransform = event.transform;
            updateZoom(dataset, data, event.transform);
            // Sync oscillator chart zoom
            syncOscillatorZoom(dataset, event.transform);
        });

    // Add zoom overlay
    chart.g.append('rect')
        .attr('class', 'zoom-overlay')
        .attr('width', chart.width)
        .attr('height', chart.height)
        .style('fill', 'none')
        .style('pointer-events', 'all')
        .call(chart.zoom);

    // Setup zoom controls
    setupZoomControls(dataset, data);
}

/**
 * Update chart with zoom transform
 * @param {string} dataset - Dataset name
 * @param {Array} data - OHLCV data
 * @param {Object} transform - D3 zoom transform
 */
function updateZoom(dataset, data, transform) {
    const chart = chartInstances[dataset];

    // Update scales with transform
    const newXScale = transform.rescaleX(chart.xScale);

    // Update axes
    const xAxis = d3.axisBottom(newXScale)
        .ticks(8)
        .tickFormat(d3.timeFormat('%b %d'));

    chart.xAxisGroup.call(xAxis)
        .selectAll('text')
        .style('fill', '#888');

    chart.xAxisGroup.selectAll('path, line').style('stroke', '#333');

    // Update candles position
    const candleWidth = Math.max(2, Math.min(12, chart.width / data.length * 0.7)) * transform.k;

    chart.candlesGroup.selectAll('.wick')
        .attr('x1', d => newXScale(new Date(d[0])))
        .attr('x2', d => newXScale(new Date(d[0])));

    chart.candlesGroup.selectAll('.candle')
        .attr('x', d => newXScale(new Date(d[0])) - candleWidth / 2)
        .attr('width', candleWidth);

    // Update overlay lines and dots position
    if (chart.overlayData && chart.overlayData.length > 0) {
        chart.overlayData.forEach((overlay, index) => {
            if (!overlay.data || overlay.data.length === 0) {
                return;
            }

            const metadata = overlay.metadata || {};
            const renderType = metadata.renderType || 'line';

            if (renderType === 'dots') {
                // Update dot positions (keep radius fixed at 3px)
                chart.overlaysGroup.selectAll(`.sar-dot-${index}`)
                    .attr('cx', d => newXScale(new Date(d[0])));
            } else {
                // Update line path
                const line = d3.line()
                    .x(d => newXScale(new Date(d[0])))
                    .y(d => chart.yScale(d[1]))
                    .curve(d3.curveLinear);

                chart.overlaysGroup.select(`.overlay-${index}`)
                    .datum(overlay.data)
                    .attr('d', line);
            }
        });
    }
}

/**
 * Setup zoom control buttons
 * @param {string} dataset - Dataset name
 * @param {Array} data - OHLCV data
 */
function setupZoomControls(dataset, data) {
    const chart = chartInstances[dataset];
    const containerSelector = dataset === 'btc' ? '#btc-chart-container' : '#eth-chart-container';

    // Reset zoom
    d3.select(`${containerSelector} .reset-zoom`).on('click', () => {
        chart.svg.transition().duration(750).call(chart.zoom.transform, d3.zoomIdentity);
    });

    // Zoom in
    d3.select(`${containerSelector} .zoom-in`).on('click', () => {
        chart.svg.transition().duration(300).call(chart.zoom.scaleBy, 1.3);
    });

    // Zoom out
    d3.select(`${containerSelector} .zoom-out`).on('click', () => {
        chart.svg.transition().duration(300).call(chart.zoom.scaleBy, 0.77);
    });
}

/**
 * Setup crosshair hover behavior
 * @param {string} dataset - Dataset name
 * @param {Array} data - OHLCV data
 */
function setupCrosshair(dataset, data) {
    const chart = chartInstances[dataset];
    const tooltip = d3.select('#tooltip');

    chart.g.select('.zoom-overlay')
        .on('mousemove', function(event) {
            const [mx, my] = d3.pointer(event);

            // Transform mouse coordinates if zoomed
            const x = chart.currentTransform.invertX(mx);
            const dateAtMouse = chart.xScale.invert(x);

            // Find closest data point
            const bisect = d3.bisector(d => new Date(d[0])).left;
            const index = bisect(data, dateAtMouse);
            const d = data[index];

            if (d) {
                // Show crosshair
                chart.crosshairGroup.style('display', null);

                chart.crosshairGroup.select('.crosshair-x')
                    .attr('x1', mx)
                    .attr('x2', mx)
                    .attr('y1', 0)
                    .attr('y2', chart.height);

                chart.crosshairGroup.select('.crosshair-y')
                    .attr('x1', 0)
                    .attr('x2', chart.width)
                    .attr('y1', my)
                    .attr('y2', my);

                // Show tooltip
                const tooltipHTML = `
                    <div class="tooltip-header">${new Date(d[0]).toLocaleDateString()}</div>
                    <div class="tooltip-row">
                        <span>Open:</span>
                        <span class="tooltip-value">$${d[1].toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                    <div class="tooltip-row">
                        <span>High:</span>
                        <span class="tooltip-value">$${d[2].toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                    <div class="tooltip-row">
                        <span>Low:</span>
                        <span class="tooltip-value">$${d[3].toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                    <div class="tooltip-row">
                        <span>Close:</span>
                        <span class="tooltip-value">$${d[4].toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                    <div class="tooltip-row">
                        <span>Volume:</span>
                        <span class="tooltip-value">${d[5].toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                `;

                tooltip.html(tooltipHTML)
                    .classed('show', true)
                    .style('left', (event.pageX + 15) + 'px')
                    .style('top', (event.pageY - 15) + 'px');
            }
        })
        .on('mouseleave', () => {
            chart.crosshairGroup.style('display', 'none');
            tooltip.classed('show', false);
        });
}

/**
 * Show a message in the chart area
 * @param {string} dataset - Dataset name
 * @param {string} message - Message to display
 */
function showChartMessage(dataset, message) {
    const containerSelector = dataset === 'btc' ? '#btc-chart-container' : '#eth-chart-container';
    const container = document.querySelector(containerSelector);

    const messageDiv = document.createElement('div');
    messageDiv.className = 'loading';
    messageDiv.textContent = message;
    container.appendChild(messageDiv);
}
