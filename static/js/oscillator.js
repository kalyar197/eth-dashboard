/**
 * Oscillator Chart Module
 * Renders multi-line oscillator charts with synchronized zoom to price charts
 */

// Store oscillator chart instances
const oscillatorInstances = {};

/**
 * Initialize an oscillator chart
 * @param {string} containerId - ID of the container element
 * @param {string} asset - Asset name (btc, eth, gold)
 * @param {string} assetColor - Color for the zero line
 */
export function initOscillatorChart(containerId, asset, assetColor) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    // Clear any existing content
    container.innerHTML = '';

    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const margin = { top: 20, right: 50, bottom: 40, left: 60 };
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

    // Create scales
    const xScale = d3.scaleTime().range([0, width]);
    const yScale = d3.scaleLinear().range([height, 0]);

    // Create axes
    const xAxis = d3.axisBottom(xScale)
        .ticks(8)
        .tickFormat(d3.timeFormat('%b %d'));

    const yAxis = d3.axisLeft(yScale)
        .ticks(6);

    // Append axis groups
    const xAxisGroup = g.append('g')
        .attr('class', 'axis x-axis')
        .attr('transform', `translate(0,${height})`);

    const yAxisGroup = g.append('g')
        .attr('class', 'axis y-axis');

    // Create grid
    const xGrid = g.append('g')
        .attr('class', 'grid x-grid');

    const yGrid = g.append('g')
        .attr('class', 'grid y-grid');

    // Create clip path
    const clipPath = svg.append('defs')
        .append('clipPath')
        .attr('id', `clip-${asset}-oscillator`)
        .append('rect')
        .attr('width', width)
        .attr('height', height);

    // Create lines group (clipped)
    const linesGroup = g.append('g')
        .attr('clip-path', `url(#clip-${asset}-oscillator)`)
        .attr('class', 'lines-group');

    // Create zero line (represents asset price)
    const zeroLine = g.append('line')
        .attr('class', 'reference-line')
        .attr('x1', 0)
        .attr('x2', width)
        .style('stroke', assetColor)
        .style('stroke-width', 2)
        .style('stroke-dasharray', '5,5')
        .style('opacity', 0.5);

    // Create zero line label
    const zeroLabel = g.append('text')
        .attr('class', 'reference-label')
        .attr('x', width + 5)
        .attr('text-anchor', 'start')
        .style('fill', assetColor)
        .style('font-size', '11px')
        .text('0 (Price)');

    // Create crosshair elements
    const crosshairGroup = g.append('g')
        .attr('class', 'crosshair-group')
        .style('display', 'none');

    const crosshairLineX = crosshairGroup.append('line')
        .attr('class', 'crosshair-line')
        .attr('y1', 0)
        .attr('y2', height);

    const crosshairLineY = crosshairGroup.append('line')
        .attr('class', 'crosshair-line')
        .attr('x1', 0)
        .attr('x2', width);

    // Create overlay for mouse events
    const overlay = g.append('rect')
        .attr('class', 'zoom-overlay')
        .attr('width', width)
        .attr('height', height);

    // Store chart instance
    oscillatorInstances[asset] = {
        svg,
        g,
        margin,
        width,
        height,
        xScale,
        yScale,
        xAxis,
        yAxis,
        xAxisGroup,
        yAxisGroup,
        xGrid,
        yGrid,
        linesGroup,
        zeroLine,
        zeroLabel,
        crosshairGroup,
        crosshairLineX,
        crosshairLineY,
        overlay,
        zoom: null,
        currentTransform: d3.zoomIdentity,
        data: {}  // Will store dataset lines
    };

    console.log(`Oscillator chart initialized for ${asset}`);
}

/**
 * Render oscillator chart with multiple datasets
 * @param {string} asset - Asset name
 * @param {Object} datasetsData - Object with dataset names as keys and data arrays as values
 * @param {Object} colors - Object mapping dataset names to colors
 */
export function renderOscillatorChart(asset, datasetsData, colors) {
    const chart = oscillatorInstances[asset];
    if (!chart) {
        console.error(`Oscillator chart not initialized for ${asset}`);
        return;
    }

    console.log(`Rendering oscillator chart for ${asset} with datasets:`, Object.keys(datasetsData));

    // Store data in chart instance
    chart.data = datasetsData;
    chart.colors = colors;

    // Find data extent across all datasets
    let allTimestamps = [];
    let allValues = [];

    Object.values(datasetsData).forEach(data => {
        if (data && data.length > 0) {
            data.forEach(d => {
                allTimestamps.push(new Date(d[0]));
                allValues.push(d[1]);
            });
        }
    });

    if (allTimestamps.length === 0) {
        console.warn('No data to render in oscillator chart');
        return;
    }

    // Update scales
    const xExtent = d3.extent(allTimestamps);
    const yExtent = d3.extent(allValues);

    // Add padding to y extent
    const yPadding = (yExtent[1] - yExtent[0]) * 0.1;
    chart.xScale.domain(xExtent);
    chart.yScale.domain([yExtent[0] - yPadding, yExtent[1] + yPadding]);

    // Update axes
    chart.xAxisGroup.call(chart.xAxis.scale(chart.xScale));
    chart.yAxisGroup.call(chart.yAxis.scale(chart.yScale));

    // Update grids
    chart.xGrid
        .attr('transform', `translate(0,${chart.height})`)
        .call(d3.axisBottom(chart.xScale)
            .ticks(8)
            .tickSize(-chart.height)
            .tickFormat(''));

    chart.yGrid
        .call(d3.axisLeft(chart.yScale)
            .ticks(6)
            .tickSize(-chart.width)
            .tickFormat(''));

    // Update zero line position
    const zeroY = chart.yScale(0);
    chart.zeroLine.attr('y1', zeroY).attr('y2', zeroY);
    chart.zeroLabel.attr('y', zeroY);

    // Clear existing lines
    chart.linesGroup.selectAll('path').remove();

    // Create line generator
    const line = d3.line()
        .x(d => chart.xScale(new Date(d[0])))
        .y(d => chart.yScale(d[1]))
        .curve(d3.curveMonotoneX);

    // Draw lines for each dataset
    Object.entries(datasetsData).forEach(([datasetName, data]) => {
        if (!data || data.length === 0) return;

        const color = colors[datasetName] || '#888';

        chart.linesGroup.append('path')
            .datum(data)
            .attr('class', `line line-${datasetName}`)
            .attr('d', line)
            .style('stroke', color)
            .style('stroke-width', 2)
            .style('fill', 'none');
    });

    // Setup zoom and crosshair if not already setup
    if (!chart.zoom) {
        setupOscillatorZoom(asset);
        setupOscillatorCrosshair(asset);
    }

    console.log(`Oscillator chart rendered for ${asset}`);
}

/**
 * Setup zoom behavior for oscillator chart
 * @param {string} asset - Asset name
 */
function setupOscillatorZoom(asset) {
    const chart = oscillatorInstances[asset];
    if (!chart) return;

    chart.zoom = d3.zoom()
        .scaleExtent([0.5, 10])
        .translateExtent([[0, 0], [chart.width, chart.height]])
        .extent([[0, 0], [chart.width, chart.height]])
        .on('zoom', (event) => updateOscillatorZoom(asset, event.transform));

    chart.overlay.call(chart.zoom);
}

/**
 * Update oscillator chart with zoom transform
 * @param {string} asset - Asset name
 * @param {Object} transform - D3 zoom transform
 */
function updateOscillatorZoom(asset, transform) {
    const chart = oscillatorInstances[asset];
    if (!chart) return;

    chart.currentTransform = transform;

    // Create new scales with transform
    const newXScale = transform.rescaleX(chart.xScale);
    const newYScale = transform.rescaleY(chart.yScale);

    // Update axes
    chart.xAxisGroup.call(chart.xAxis.scale(newXScale));
    chart.yAxisGroup.call(chart.yAxis.scale(newYScale));

    // Update grids
    chart.xGrid.call(d3.axisBottom(newXScale)
        .ticks(8)
        .tickSize(-chart.height)
        .tickFormat(''));

    chart.yGrid.call(d3.axisLeft(newYScale)
        .ticks(6)
        .tickSize(-chart.width)
        .tickFormat(''));

    // Update zero line
    const zeroY = newYScale(0);
    chart.zeroLine.attr('y1', zeroY).attr('y2', zeroY);
    chart.zeroLabel.attr('y', zeroY);

    // Update lines
    const line = d3.line()
        .x(d => newXScale(new Date(d[0])))
        .y(d => newYScale(d[1]))
        .curve(d3.curveMonotoneX);

    Object.entries(chart.data).forEach(([datasetName, data]) => {
        chart.linesGroup.select(`.line-${datasetName}`)
            .attr('d', line);
    });
}

/**
 * Synchronize oscillator zoom with price chart
 * Called by price chart when it zooms
 * @param {string} asset - Asset name
 * @param {Object} transform - Zoom transform from price chart
 */
export function syncOscillatorZoom(asset, transform) {
    const chart = oscillatorInstances[asset];
    if (!chart) return;

    // Only sync x-axis (time), not y-axis (different scales)
    const newTransform = d3.zoomIdentity
        .translate(transform.x, 0)
        .scale(transform.k);

    // Apply transform without triggering zoom event
    chart.overlay.call(chart.zoom.transform, newTransform);
}

/**
 * Setup crosshair for oscillator chart
 * @param {string} asset - Asset name
 */
function setupOscillatorCrosshair(asset) {
    const chart = oscillatorInstances[asset];
    if (!chart) return;

    const tooltip = d3.select('#tooltip');

    chart.overlay
        .on('mousemove', function(event) {
            const [mouseX, mouseY] = d3.pointer(event);

            // Use current transform for scales
            const newXScale = chart.currentTransform.rescaleX(chart.xScale);
            const newYScale = chart.currentTransform.rescaleY(chart.yScale);

            // Show crosshair
            chart.crosshairGroup.style('display', null);
            chart.crosshairLineX.attr('x1', mouseX).attr('x2', mouseX);
            chart.crosshairLineY.attr('y1', mouseY).attr('y2', mouseY);

            // Get date at mouse position
            const date = newXScale.invert(mouseX);

            // Find closest data points for all datasets
            let tooltipHTML = `<div class="tooltip-header">${d3.timeFormat('%Y-%m-%d')(date)}</div>`;

            Object.entries(chart.data).forEach(([datasetName, data]) => {
                if (!data || data.length === 0) return;

                // Binary search for closest point
                const bisect = d3.bisector(d => d[0]).left;
                const idx = bisect(data, date.getTime());

                if (idx > 0 && idx < data.length) {
                    const d0 = data[idx - 1];
                    const d1 = data[idx];
                    const closest = date.getTime() - d0[0] > d1[0] - date.getTime() ? d1 : d0;

                    const color = chart.colors[datasetName] || '#888';
                    const value = closest[1];

                    tooltipHTML += `
                        <div class="tooltip-row">
                            <span class="tooltip-color" style="background: ${color}"></span>
                            <span>${datasetName}</span>
                            <span class="tooltip-value">${value.toFixed(2)}</span>
                        </div>
                    `;
                }
            });

            // Position and show tooltip
            const containerRect = chart.svg.node().getBoundingClientRect();
            tooltip
                .style('left', (containerRect.left + mouseX + chart.margin.left + 10) + 'px')
                .style('top', (containerRect.top + mouseY + chart.margin.top + 10) + 'px')
                .classed('show', true)
                .html(tooltipHTML);
        })
        .on('mouseleave', function() {
            chart.crosshairGroup.style('display', 'none');
            tooltip.classed('show', false);
        });
}

/**
 * Reset oscillator zoom to default
 * @param {string} asset - Asset name
 */
export function resetOscillatorZoom(asset) {
    const chart = oscillatorInstances[asset];
    if (!chart) return;

    chart.overlay.call(chart.zoom.transform, d3.zoomIdentity);
}

/**
 * Get oscillator chart instance
 * @param {string} asset - Asset name
 * @returns {Object} Chart instance
 */
export function getOscillatorChart(asset) {
    return oscillatorInstances[asset];
}
