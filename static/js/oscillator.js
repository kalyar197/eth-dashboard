/**
 * Oscillator Chart Module
 * Renders multi-line oscillator charts with synchronized zoom to price charts
 */

// Store oscillator chart instances
const oscillatorInstances = {};

// Store breakdown chart instances
const breakdownInstances = {};

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
 * Initialize a breakdown oscillator chart (for individual normalized oscillators)
 * @param {string} containerId - ID of the container element
 * @param {string} asset - Asset name (btc, eth, gold)
 */
export function initBreakdownChart(containerId, asset) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    // Clear any existing content (keep zoom controls and info text)
    const existingZoomControls = container.querySelector('.zoom-controls');
    const existingInfoText = container.querySelector('.info-text');

    // Remove all children except zoom controls and info text
    Array.from(container.children).forEach(child => {
        if (!child.classList.contains('zoom-controls') && !child.classList.contains('info-text')) {
            child.remove();
        }
    });

    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const margin = { top: 30, right: 50, bottom: 40, left: 60 };  // Extra top margin for legend
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
        .attr('id', `clip-${asset}-breakdown`)
        .append('rect')
        .attr('width', width)
        .attr('height', height);

    // Create lines group (clipped)
    const linesGroup = g.append('g')
        .attr('clip-path', `url(#clip-${asset}-breakdown)`)
        .attr('class', 'lines-group');

    // Create zero line
    const zeroLine = g.append('line')
        .attr('class', 'reference-line')
        .attr('x1', 0)
        .attr('x2', width)
        .style('stroke', '#666')
        .style('stroke-width', 1)
        .style('stroke-dasharray', '3,3')
        .style('opacity', 0.3);

    // Create legend group (top-left)
    const legendGroup = svg.append('g')
        .attr('class', 'legend-group')
        .attr('transform', `translate(${margin.left + 10}, 10)`);

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
    breakdownInstances[asset] = {
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
        legendGroup,
        crosshairGroup,
        crosshairLineX,
        crosshairLineY,
        overlay,
        zoom: null,
        currentTransform: d3.zoomIdentity,
        lines: {}  // Will store individual oscillator lines
    };

    console.log(`Breakdown chart initialized for ${asset}`);
}

/**
 * Render oscillator chart with multiple datasets
 * @param {string} asset - Asset name
 * @param {Object} datasetsData - Object with dataset names as keys and data arrays as values
 * @param {Object} colors - Object mapping dataset names to colors
 */
export function renderOscillatorChart(asset, datasetsData, colors, compositeMode = false) {
    const chart = oscillatorInstances[asset];
    if (!chart) {
        console.error(`Oscillator chart not initialized for ${asset}`);
        return;
    }

    if (compositeMode) {
        console.log(`Rendering COMPOSITE oscillator chart for ${asset}`);
        renderCompositeOscillator(asset, datasetsData, colors);
    } else {
        console.log(`Rendering INDIVIDUAL oscillator chart for ${asset} with datasets:`, Object.keys(datasetsData));
        renderIndividualOscillator(asset, datasetsData, colors);
    }

    // Setup zoom and crosshair if not already setup
    if (!chart.zoom) {
        setupOscillatorZoom(asset);
        setupOscillatorCrosshair(asset);
    }

    console.log(`Oscillator chart rendered for ${asset}`);
}

/**
 * Render composite oscillator with regime background
 */
function renderCompositeOscillator(asset, data, colors) {
    const chart = oscillatorInstances[asset];
    const compositeData = data.composite;
    const regimeData = data.regime;
    const metadata = data.metadata;

    if (!compositeData || !regimeData) {
        console.error('Missing composite or regime data');
        return;
    }

    // Store data
    chart.data = data;
    chart.colors = colors;

    // Find data extent
    const allTimestamps = compositeData.map(d => new Date(d[0]));
    const allValues = compositeData.map(d => d[1]);

    // Update scales
    const xExtent = d3.extent(allTimestamps);
    const yExtent = d3.extent(allValues);

    // Symmetrical y-domain around 0 for Z-scores
    const yMax = Math.max(Math.abs(yExtent[0]), Math.abs(yExtent[1]), 3.5);  // At least ±3.5σ
    chart.xScale.domain(xExtent);
    chart.yScale.domain([-yMax, yMax]);

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
            .ticks(8)
            .tickSize(-chart.width)
            .tickFormat(''));

    // Clear existing content
    chart.linesGroup.selectAll('*').remove();

    // 1. RENDER REGIME BACKGROUND (first, so it's behind everything)
    renderRegimeBackground(chart, regimeData, metadata.regime);

    // 2. RENDER REFERENCE LINES at ±2σ and ±3σ
    const referenceLines = [
        { value: 3, label: '+3σ', color: 'rgba(255, 59, 48, 0.5)' },
        { value: 2, label: '+2σ', color: 'rgba(255, 149, 0, 0.5)' },
        { value: -2, label: '-2σ', color: 'rgba(48, 209, 88, 0.5)' },
        { value: -3, label: '-3σ', color: 'rgba(50, 215, 75, 0.5)' }
    ];

    referenceLines.forEach(ref => {
        const y = chart.yScale(ref.value);
        chart.linesGroup.append('line')
            .attr('class', 'reference-line')
            .attr('x1', 0)
            .attr('x2', chart.width)
            .attr('y1', y)
            .attr('y2', y)
            .style('stroke', ref.color)
            .style('stroke-width', 1)
            .style('stroke-dasharray', '5,5')
            .style('opacity', 0.6);

        chart.linesGroup.append('text')
            .attr('class', 'reference-label')
            .attr('x', chart.width - 5)
            .attr('y', y - 3)
            .attr('text-anchor', 'end')
            .style('fill', ref.color)
            .style('font-size', '10px')
            .text(ref.label);
    });

    // Update zero line position
    const zeroY = chart.yScale(0);
    chart.zeroLine.attr('y1', zeroY).attr('y2', zeroY);
    chart.zeroLabel.attr('y', zeroY);

    // 3. RENDER COMPOSITE LINE
    const line = d3.line()
        .x(d => chart.xScale(new Date(d[0])))
        .y(d => chart.yScale(d[1]))
        .curve(d3.curveMonotoneX);

    chart.linesGroup.append('path')
        .datum(compositeData)
        .attr('class', 'line line-composite')
        .attr('d', line)
        .style('stroke', '#00D9FF')  // Cyan
        .style('stroke-width', 2.5)
        .style('fill', 'none');
}

/**
 * Render regime background shading
 */
function renderRegimeBackground(chart, regimeData, metadata) {
    if (!regimeData || regimeData.length === 0) return;

    const states = metadata.states;

    // Group consecutive timestamps with same regime
    const regimeSegments = [];
    let currentSegment = null;

    regimeData.forEach((d, i) => {
        const timestamp = d[0];
        const regime = d[1];

        if (!currentSegment || currentSegment.regime !== regime) {
            // Start new segment
            if (currentSegment) {
                regimeSegments.push(currentSegment);
            }
            currentSegment = {
                regime: regime,
                startTime: timestamp,
                endTime: timestamp
            };
        } else {
            // Extend current segment
            currentSegment.endTime = timestamp;
        }
    });

    // Push last segment
    if (currentSegment) {
        regimeSegments.push(currentSegment);
    }

    // Render background rectangles
    regimeSegments.forEach(segment => {
        const state = states[segment.regime];
        if (!state) return;

        const x1 = chart.xScale(new Date(segment.startTime));
        const x2 = chart.xScale(new Date(segment.endTime));
        const width = x2 - x1 || 2;  // Minimum width of 2px

        chart.linesGroup.insert('rect', ':first-child')  // Insert at beginning (background)
            .attr('class', `regime-background regime-${segment.regime}`)
            .attr('x', x1)
            .attr('y', 0)
            .attr('width', width)
            .attr('height', chart.height)
            .style('fill', state.color)
            .style('opacity', 1);
    });
}

/**
 * Render individual oscillators (original logic)
 */
function renderIndividualOscillator(asset, datasetsData, colors) {
    const chart = oscillatorInstances[asset];

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
    chart.linesGroup.selectAll('*').remove();

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

    // Also sync breakdown chart if it exists
    const breakdownChart = breakdownInstances[asset];
    if (breakdownChart && breakdownChart.zoom) {
        breakdownChart.overlay.call(breakdownChart.zoom.transform, newTransform);
    }
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
 * Render breakdown chart with individual normalized oscillators
 * @param {string} asset - Asset name
 * @param {Object} breakdownData - Object with oscillator names as keys containing data and metadata
 */
export function renderBreakdownChart(asset, breakdownData) {
    const chart = breakdownInstances[asset];
    if (!chart) {
        console.error(`Breakdown chart not initialized for ${asset}`);
        return;
    }

    console.log(`[Breakdown] Rendering breakdown chart for ${asset}`, breakdownData);

    // Extract all data points for domain calculation
    let allTimestamps = [];
    let allValues = [];

    Object.entries(breakdownData).forEach(([name, oscillatorData]) => {
        if (oscillatorData.data && oscillatorData.data.length > 0) {
            oscillatorData.data.forEach(d => {
                allTimestamps.push(d[0]);
                allValues.push(d[1]);
            });
        }
    });

    if (allTimestamps.length === 0) {
        console.warn(`[Breakdown] No data to render for ${asset}`);
        return;
    }

    // Update X scale domain
    const xExtent = d3.extent(allTimestamps);
    chart.xScale.domain(xExtent.map(ts => new Date(ts)));

    // Update Y scale domain (use same logic as composite - symmetrical around 0, minimum ±3.5)
    const yExtent = d3.extent(allValues);
    const yMax = Math.max(Math.abs(yExtent[0]), Math.abs(yExtent[1]), 3.5);
    chart.yScale.domain([-yMax, yMax]);

    // Update axes
    chart.xAxisGroup.call(chart.xAxis.scale(chart.xScale));
    chart.yAxisGroup.call(chart.yAxis.scale(chart.yScale));

    // Update grid
    chart.xGrid
        .call(d3.axisBottom(chart.xScale).tickSize(-chart.height).tickFormat(''))
        .attr('transform', `translate(0,${chart.height})`);

    chart.yGrid
        .call(d3.axisLeft(chart.yScale).tickSize(-chart.width).tickFormat(''));

    // Update zero line position
    chart.zeroLine.attr('y1', chart.yScale(0)).attr('y2', chart.yScale(0));

    // Line generator
    const lineGenerator = d3.line()
        .x(d => chart.xScale(new Date(d[0])))
        .y(d => chart.yScale(d[1]))
        .curve(d3.curveMonotoneX);

    // Clear existing lines
    chart.linesGroup.selectAll('path').remove();

    // Render each oscillator line
    Object.entries(breakdownData).forEach(([name, oscillatorData]) => {
        if (!oscillatorData.data || oscillatorData.data.length === 0) return;

        const color = oscillatorData.metadata.color || '#888';
        const label = oscillatorData.metadata.label || name.toUpperCase();

        // Draw line
        chart.linesGroup.append('path')
            .datum(oscillatorData.data)
            .attr('class', `line-${name}`)
            .attr('fill', 'none')
            .attr('stroke', color)
            .attr('stroke-width', 2)
            .attr('d', lineGenerator);

        // Store line info
        chart.lines[name] = {
            color,
            label,
            data: oscillatorData.data
        };

        console.log(`[Breakdown] Rendered ${name} line (${oscillatorData.data.length} points)`);
    });

    // Render legend
    renderBreakdownLegend(chart, chart.lines);

    console.log(`[Breakdown] Breakdown chart rendered for ${asset}`);
}

/**
 * Render legend for breakdown chart
 * @param {Object} chart - Chart instance
 * @param {Object} lines - Lines data with colors and labels
 */
function renderBreakdownLegend(chart, lines) {
    // Clear existing legend
    chart.legendGroup.selectAll('*').remove();

    // Create legend items
    const legendItems = Object.entries(lines).map(([name, info]) => ({
        name,
        color: info.color,
        label: info.label
    }));

    const itemWidth = 120;
    const itemHeight = 16;

    legendItems.forEach((item, i) => {
        const legendItem = chart.legendGroup.append('g')
            .attr('class', 'legend-item')
            .attr('transform', `translate(${i * itemWidth}, 0)`);

        // Color square
        legendItem.append('rect')
            .attr('width', 12)
            .attr('height', 12)
            .attr('fill', item.color);

        // Label
        legendItem.append('text')
            .attr('x', 16)
            .attr('y', 10)
            .attr('font-size', '11px')
            .attr('fill', '#ccc')
            .text(item.label);
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

/**
 * Get breakdown chart instance
 * @param {string} asset - Asset name
 * @returns {Object} Chart instance
 */
export function getBreakdownChart(asset) {
    return breakdownInstances[asset];
}
