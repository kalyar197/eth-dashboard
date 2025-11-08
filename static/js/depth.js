/**
 * Depth Chart Module - Multi-timeframe candlestick chart rendering
 * Renders 1m, 15m, 1h, and 4h timeframes with variable time depths
 * Uses D3.js for visualization, reuses patterns from chart.js
 */

// Depth chart state
let depthChartInstance = null;

/**
 * Initialize depth chart
 * @param {string} containerId - DOM ID of the chart container
 */
export function initDepthChart(containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Depth chart container ${containerId} not found`);
        return;
    }

    // Clear any existing content
    container.innerHTML = '';

    // Re-add zoom controls
    const zoomControls = document.createElement('div');
    zoomControls.className = 'zoom-controls';
    zoomControls.innerHTML = `
        <button class="zoom-btn reset-zoom-depth" title="Reset Zoom">↺</button>
        <button class="zoom-btn zoom-in-depth" title="Zoom In">+</button>
        <button class="zoom-btn zoom-out-depth" title="Zoom Out">−</button>
    `;
    container.appendChild(zoomControls);

    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const margin = { top: 20, right: 60, bottom: 40, left: 60 };
    const width = containerRect.width - margin.left - margin.right;
    const height = containerRect.height - margin.top - margin.bottom;

    // Create SVG with viewBox for responsive scaling
    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', containerRect.width)
        .attr('height', containerRect.height)
        .attr('viewBox', `0 0 ${containerRect.width} ${containerRect.height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');

    // Create main group
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create clip path for zoom
    g.append('defs').append('clipPath')
        .attr('id', 'clip-depth')
        .append('rect')
        .attr('width', width)
        .attr('height', height);

    // Create groups for different elements
    const gridGroup = g.append('g').attr('class', 'grid');
    const candlesGroup = g.append('g').attr('class', 'candles').attr('clip-path', 'url(#clip-depth)');
    const xAxisGroup = g.append('g').attr('class', 'x-axis').attr('transform', `translate(0,${height})`);
    const yAxisGroup = g.append('g').attr('class', 'y-axis');

    // Crosshair elements
    const crosshairGroup = g.append('g').attr('class', 'crosshair').style('display', 'none');
    crosshairGroup.append('line').attr('class', 'crosshair-line crosshair-x');
    crosshairGroup.append('line').attr('class', 'crosshair-line crosshair-y');

    // Store chart instance
    depthChartInstance = {
        svg,
        g,
        width,
        height,
        margin,
        gridGroup,
        candlesGroup,
        xAxisGroup,
        yAxisGroup,
        crosshairGroup,
        xScale: null,
        yScale: null,
        zoom: null,
        currentTransform: d3.zoomIdentity
    };

    console.log('Depth chart initialized');
}

/**
 * Render depth chart with OHLCV data
 * @param {Array} data - OHLCV data [[timestamp, open, high, low, close, volume], ...]
 */
export function renderDepthChart(data) {
    const chart = depthChartInstance;
    if (!chart) {
        console.error('Depth chart instance not found');
        return;
    }

    if (!data || data.length === 0) {
        console.warn('No data to render for depth chart');
        showDepthMessage('No data available');
        return;
    }

    console.log(`Rendering ${data.length} candles for depth chart`);

    // Create scales
    chart.xScale = d3.scaleTime()
        .domain(d3.extent(data, d => new Date(d[0])))
        .range([0, chart.width]);

    // Find price range (considering high/low)
    const prices = data.flatMap(d => [d[2], d[3]]); // high, low

    chart.yScale = d3.scaleLinear()
        .domain([d3.min(prices) * 0.98, d3.max(prices) * 1.02])
        .range([chart.height, 0]);

    // Create axes
    const xAxis = d3.axisBottom(chart.xScale)
        .ticks(8)
        .tickFormat(d3.timeFormat('%b %d %H:%M'));

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

    // Clear existing candlesticks
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

    // Add zoom behavior
    setupDepthZoom(data);

    // Add hover behavior
    setupDepthCrosshair(data);
}

/**
 * Setup zoom and pan behavior
 * @param {Array} data - OHLCV data
 */
function setupDepthZoom(data) {
    const chart = depthChartInstance;

    // Remove existing zoom overlay
    chart.g.selectAll('.zoom-overlay').remove();

    // Create zoom behavior
    chart.zoom = d3.zoom()
        .scaleExtent([0.5, 10])
        .translateExtent([[0, 0], [chart.width, chart.height]])
        .extent([[0, 0], [chart.width, chart.height]])
        .on('zoom', (event) => {
            chart.currentTransform = event.transform;
            updateDepthZoom(data, event.transform);
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
    setupDepthZoomControls(data);
}

/**
 * Update chart with zoom transform
 * @param {Array} data - OHLCV data
 * @param {Object} transform - D3 zoom transform
 */
function updateDepthZoom(data, transform) {
    const chart = depthChartInstance;

    // Update scales with transform
    const newXScale = transform.rescaleX(chart.xScale);

    // Update axes
    const xAxis = d3.axisBottom(newXScale)
        .ticks(8)
        .tickFormat(d3.timeFormat('%b %d %H:%M'));

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
}

/**
 * Setup zoom control buttons
 * @param {Array} data - OHLCV data
 */
function setupDepthZoomControls(data) {
    const chart = depthChartInstance;

    // Reset zoom
    d3.select('.reset-zoom-depth').on('click', () => {
        chart.svg.transition().duration(750).call(chart.zoom.transform, d3.zoomIdentity);
    });

    // Zoom in
    d3.select('.zoom-in-depth').on('click', () => {
        chart.svg.transition().duration(300).call(chart.zoom.scaleBy, 1.3);
    });

    // Zoom out
    d3.select('.zoom-out-depth').on('click', () => {
        chart.svg.transition().duration(300).call(chart.zoom.scaleBy, 0.77);
    });
}

/**
 * Setup crosshair hover behavior
 * @param {Array} data - OHLCV data
 */
function setupDepthCrosshair(data) {
    const chart = depthChartInstance;
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
                    <div class="tooltip-header">${new Date(d[0]).toLocaleString()}</div>
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
 * Show a message in the depth chart area
 * @param {string} message - Message to display
 */
function showDepthMessage(message) {
    const container = document.getElementById('depth-chart-container');

    // Clear existing content
    container.innerHTML = '';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'loading';
    messageDiv.textContent = message;
    container.appendChild(messageDiv);
}

/**
 * Show loading message
 */
export function showDepthLoading() {
    showDepthMessage('Loading depth chart data...');
}

/**
 * Show error message
 * @param {string} message - Error message
 */
export function showDepthError(message) {
    const container = document.getElementById('depth-chart-container');

    // Clear existing content
    container.innerHTML = '';

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
