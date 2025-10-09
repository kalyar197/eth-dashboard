// Chart State Management
let chartState = {
    days: '365',
    activePlugins: [],
    datasets: {},
    metadata: {},
    currentZoom: null
};

// Chart dimensions
const margin = {top: 30, right: 320, bottom: 50, left: 80};
let width;
let height;

// DOM elements
let container;
let tooltip;

// D3 elements
let svg;
let g;
let clip;
let gridGroup;
let linesGroup;
let xAxisGroup;
let yAxisGroups = {};
let crosshairGroup;
let brushGroup;
let overlay;

// D3 scales and interactions
let xScale;
const yScales = {};
let brush;

// Crosshair elements
let verticalLine;
let horizontalLine;
let crosshairTextX;

/**
 * Initializes the D3 chart with SVG elements, scales, and interaction layers
 * @param {string} containerId - ID of the container element for the chart
 * @param {string} tooltipId - ID of the tooltip element
 */
export function initChart(containerId, tooltipId) {
    // Get container and tooltip elements
    container = document.getElementById(containerId);
    tooltip = d3.select(`#${tooltipId}`);

    // Calculate initial dimensions
    width = Math.min(container.clientWidth - margin.left - margin.right, 1200);
    height = 550 - margin.top - margin.bottom;

    // Create SVG
    d3.select(`#${containerId}`).selectAll("svg").remove();
    svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", 580);

    g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Create clip path for zoom
    clip = g.append("defs").append("clipPath")
        .attr("id", "clip")
        .append("rect")
        .attr("width", width)
        .attr("height", height);

    // Groups for different elements
    gridGroup = g.append("g").attr("class", "grid");
    linesGroup = g.append("g").attr("clip-path", "url(#clip)");
    xAxisGroup = g.append("g").attr("transform", `translate(0,${height})`);
    crosshairGroup = g.append("g").attr("class", "crosshair");

    // Crosshair elements
    verticalLine = crosshairGroup.append("line")
        .attr("class", "crosshair-line")
        .attr("y1", 0)
        .attr("y2", height)
        .style("display", "none");

    horizontalLine = crosshairGroup.append("line")
        .attr("class", "crosshair-line")
        .attr("x1", 0)
        .attr("x2", width)
        .style("display", "none");

    crosshairTextX = crosshairGroup.append("text")
        .attr("class", "crosshair-text")
        .attr("y", height + 15)
        .attr("text-anchor", "middle");

    // Scales
    xScale = d3.scaleTime().range([0, width]);

    // Brush for zoom selection
    brush = d3.brushX()
        .extent([[0, 0], [width, height]])
        .on("end", brushended);

    brushGroup = g.append("g")
        .attr("class", "brush");

    // Overlay for mouse events
    overlay = g.append("rect")
        .attr("class", "zoom-overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mousemove", mousemove)
        .on("mouseout", mouseout)
        .call(brush);

    // Handle window resize
    window.addEventListener('resize', handleResize);
}

/**
 * Updates the chart with new data and renders it
 * @param {Array<string>} activePlugins - Array of active plugin names
 * @param {Object} datasets - Object containing dataset arrays keyed by plugin name
 * @param {Object} metadata - Object containing metadata for each dataset
 * @param {string} days - Time range string ('30', '90', '365', 'max')
 */
export function updateChart(activePlugins, datasets, metadata, days) {
    // Update chart state
    chartState.activePlugins = activePlugins;
    chartState.datasets = datasets;
    chartState.metadata = metadata;
    chartState.days = days;

    // If no plugins selected, clear the chart
    if (chartState.activePlugins.length === 0) {
        linesGroup.selectAll("*").remove();
        gridGroup.selectAll("*").remove();
        Object.values(yAxisGroups).forEach(g => g.style("display", "none"));
        return;
    }

    // Render the chart
    renderChart();
}

/**
 * Internal function that performs the actual D3 rendering
 */
function renderChart() {
    // Get all data points for x domain
    const allData = Object.entries(chartState.datasets)
        .filter(([key, data]) => chartState.activePlugins.includes(key))
        .map(([key, data]) => {
            // Handle Bollinger Bands special case
            if (key === 'bollinger_bands' && data.middle) {
                return data.middle;
            }
            return data;
        })
        .flat();

    if (allData.length === 0) return;

    // Set up X scale
    const xDomain = d3.extent(allData, d => new Date(d[0]));
    xScale.domain(chartState.currentZoom || xDomain);

    // Group datasets by Y axis ID with proper ordering
    const axisSets = {};
    const axisOrder = [];

    // Define priority order for axes
    const axisPriority = {
        'price_usd': 0,
        'percentage': 1,
        'indicator': 2
    };

    chartState.activePlugins.forEach(key => {
        const meta = chartState.metadata[key];
        if (!meta) return;

        // Check if dataset has valid data
        const hasValidData = key === 'bollinger_bands'
            ? (chartState.datasets[key] && chartState.datasets[key].middle && chartState.datasets[key].middle.length > 0)
            : (chartState.datasets[key] && chartState.datasets[key].length > 0);

        if (!hasValidData) return;

        const axisId = meta.yAxisId || 'default';

        if (!axisSets[axisId]) {
            axisSets[axisId] = {
                datasets: [],
                metadata: meta,
                color: meta.color,
                priority: axisPriority[axisId] !== undefined ? axisPriority[axisId] : 999
            };
            axisOrder.push(axisId);
        }
        axisSets[axisId].datasets.push(key);
    });

    // Sort axes by priority
    axisOrder.sort((a, b) => axisSets[a].priority - axisSets[b].priority);

    // Clear and recreate axes
    Object.values(yAxisGroups).forEach(group => group.remove());

    // Clear reference lines
    linesGroup.selectAll(".reference-line, .reference-label").remove();

    // Create Y scales and axes with proper positioning
    let rightAxisOffset = 0;

    axisOrder.forEach((axisId, index) => {
        const axisInfo = axisSets[axisId];

        // Create scale
        let yDomain;
        if (axisInfo.metadata.yDomain) {
            // Use fixed domain if specified (e.g., RSI [0, 100])
            yDomain = axisInfo.metadata.yDomain;
        } else {
            // Calculate dynamic domain
            const axisData = [];
            axisInfo.datasets.forEach(key => {
                if (key === 'bollinger_bands' && chartState.datasets[key].middle) {
                    // For Bollinger Bands, include all three lines
                    axisData.push(...chartState.datasets[key].middle);
                    axisData.push(...chartState.datasets[key].upper);
                    axisData.push(...chartState.datasets[key].lower);
                } else if (chartState.datasets[key]) {
                    axisData.push(...chartState.datasets[key]);
                }
            });

            if (axisData.length > 0) {
                yDomain = d3.extent(axisData, d => d[1]);
                const padding = (yDomain[1] - yDomain[0]) * 0.05;
                yDomain = [yDomain[0] - padding, yDomain[1] + padding];
            } else {
                yDomain = [0, 100];
            }
        }

        yScales[axisId] = d3.scaleLinear()
            .domain(yDomain)
            .range([height, 0]);

        // Position axes properly
        let axisGroup;
        let axis;

        if (index === 0) {
            // First axis goes on the left
            axisGroup = g.append("g")
                .attr("class", `y-axis y-axis-${axisId}`)
                .attr("transform", `translate(0, 0)`);

            axis = d3.axisLeft(yScales[axisId]);

            // Add label on left
            axisGroup.append("text")
                .attr("class", "axis-label")
                .attr("transform", "rotate(-90)")
                .attr("y", -50)
                .attr("x", -height / 2)
                .attr("text-anchor", "middle")
                .text(axisInfo.metadata.yAxisLabel)
                .style("fill", axisInfo.color);
        } else {
            // Subsequent axes go on the right with offset
            axisGroup = g.append("g")
                .attr("class", `y-axis y-axis-${axisId}`)
                .attr("transform", `translate(${width + rightAxisOffset}, 0)`);

            axis = d3.axisRight(yScales[axisId]);

            // Add label on right
            axisGroup.append("text")
                .attr("class", "axis-label")
                .attr("transform", "rotate(90)")
                .attr("y", -40 - rightAxisOffset)
                .attr("x", height / 2)
                .attr("text-anchor", "middle")
                .text(axisInfo.metadata.yAxisLabel)
                .style("fill", axisInfo.color);

            // Increment offset for next right axis
            rightAxisOffset += 80; // Increased spacing between axes
        }

        yAxisGroups[axisId] = axisGroup;

        // Format axis based on type
        if (axisId === 'percentage') {
            axis.tickFormat(d => d + '%');
        } else if (axisId === 'price_usd') {
            axis.tickFormat(d => '$' + d3.format(',.0f')(d));
        }

        axisGroup.call(axis.ticks(6));

        // Add reference lines if specified (only once per axis type)
        if (axisInfo.metadata.referenceLines && index === axisOrder.indexOf(axisId)) {
            axisInfo.metadata.referenceLines.forEach(ref => {
                linesGroup.append("line")
                    .attr("class", "reference-line")
                    .attr("x1", 0)
                    .attr("x2", width)
                    .attr("y1", yScales[axisId](ref.value))
                    .attr("y2", yScales[axisId](ref.value))
                    .style("stroke", ref.color)
                    .style("stroke-dasharray", ref.strokeDasharray);

                linesGroup.append("text")
                    .attr("class", "reference-label")
                    .attr("x", width - 5)
                    .attr("y", yScales[axisId](ref.value) - 3)
                    .attr("text-anchor", "end")
                    .text(ref.label)
                    .style("fill", ref.color);
            });
        }
    });

    // Draw X axis
    xAxisGroup.call(d3.axisBottom(xScale)
        .tickFormat(d3.timeFormat("%b %d"))
        .ticks(width > 600 ? 8 : 5));

    // Draw grid
    gridGroup.selectAll("*").remove();
    if (Object.keys(yScales).length > 0) {
        const firstAxisId = axisOrder[0];
        if (yScales[firstAxisId]) {
            gridGroup.call(d3.axisLeft(yScales[firstAxisId])
                .tickSize(-width)
                .tickFormat("")
                .ticks(8));
        }
    }

    // Clear old lines
    linesGroup.selectAll(".line").remove();
    linesGroup.selectAll(".bb-band").remove();
    linesGroup.selectAll(".bb-area").remove();

    // Draw lines for each dataset
    chartState.activePlugins.forEach(plugin => {
        if (!chartState.datasets[plugin]) return;

        const meta = chartState.metadata[plugin];
        const yScale = yScales[meta.yAxisId || 'default'];

        if (!yScale) return;

        if (plugin === 'bollinger_bands') {
            // Handle Bollinger Bands specially
            const bbData = chartState.datasets[plugin];
            if (bbData.middle && bbData.middle.length > 0) {
                // Draw area between upper and lower bands
                const area = d3.area()
                    .x(d => xScale(new Date(d[0])))
                    .y0(d => yScale(d[1]))
                    .y1((d, i) => yScale(bbData.upper[i][1]));

                linesGroup.append("path")
                    .datum(bbData.lower)
                    .attr("class", "bb-area")
                    .attr("d", area)
                    .style("fill", meta.upperBandColor || '#4CAF50')
                    .style("opacity", 0.1);

                // Draw the three lines
                const lineGenerator = d3.line()
                    .x(d => xScale(new Date(d[0])))
                    .y(d => yScale(d[1]));

                // Upper band
                linesGroup.append("path")
                    .attr("class", "bb-band bb-upper")
                    .attr("d", lineGenerator(bbData.upper))
                    .style("stroke", meta.upperBandColor || '#4CAF50')
                    .style("stroke-width", 1)
                    .style("fill", "none")
                    .style("stroke-dasharray", "2,2");

                // Middle band
                linesGroup.append("path")
                    .attr("class", "bb-band bb-middle")
                    .attr("d", lineGenerator(bbData.middle))
                    .style("stroke", meta.color)
                    .style("stroke-width", 1.5)
                    .style("fill", "none");

                // Lower band
                linesGroup.append("path")
                    .attr("class", "bb-band bb-lower")
                    .attr("d", lineGenerator(bbData.lower))
                    .style("stroke", meta.lowerBandColor || '#F44336')
                    .style("stroke-width", 1)
                    .style("fill", "none")
                    .style("stroke-dasharray", "2,2");
            }
        } else if (chartState.datasets[plugin].length > 0) {
            // Draw regular line
            const line = d3.line()
                .x(d => xScale(new Date(d[0])))
                .y(d => yScale(d[1]));

            linesGroup.append("path")
                .datum(chartState.datasets[plugin])
                .attr("class", `line line-${plugin}`)
                .attr("d", line)
                .style("stroke", meta.color)
                .style("stroke-width", meta.strokeWidth || 2)
                .style("fill", "none");
        }
    });
}

/**
 * Handles brush end event for zoom selection
 */
function brushended(event) {
    if (!event.selection) return;

    const [x0, x1] = event.selection.map(xScale.invert);
    chartState.currentZoom = [x0, x1];

    brushGroup.call(brush.clear);
    renderChart();
}

/**
 * Resets zoom to show all data
 */
function resetZoom() {
    chartState.currentZoom = null;
    renderChart();
}

/**
 * Zooms in by 50%
 */
function zoomIn() {
    const domain = xScale.domain();
    const center = new Date((domain[0].getTime() + domain[1].getTime()) / 2);
    const range = domain[1].getTime() - domain[0].getTime();
    const newRange = range * 0.5;

    chartState.currentZoom = [
        new Date(center.getTime() - newRange / 2),
        new Date(center.getTime() + newRange / 2)
    ];
    renderChart();
}

/**
 * Zooms out by 100%
 */
function zoomOut() {
    const domain = xScale.domain();
    const center = new Date((domain[0].getTime() + domain[1].getTime()) / 2);
    const range = domain[1].getTime() - domain[0].getTime();
    const newRange = range * 2;

    chartState.currentZoom = [
        new Date(center.getTime() - newRange / 2),
        new Date(center.getTime() + newRange / 2)
    ];
    renderChart();
}

/**
 * Handles mouse move events for crosshair and tooltip
 */
function mousemove(event) {
    const [mouseX, mouseY] = d3.pointer(event);
    const date = xScale.invert(mouseX);

    // Update crosshair
    verticalLine
        .attr("x1", mouseX)
        .attr("x2", mouseX)
        .style("display", "block");

    horizontalLine
        .attr("y1", mouseY)
        .attr("y2", mouseY)
        .style("display", "block");

    crosshairTextX
        .attr("x", mouseX)
        .text(d3.timeFormat("%b %d, %Y")(date));

    // Find closest data points
    const tooltipData = [];

    chartState.activePlugins.forEach(key => {
        const data = chartState.datasets[key];
        if (!data) return;

        // Handle Bollinger Bands
        if (key === 'bollinger_bands' && data.middle) {
            const bisect = d3.bisector(d => new Date(d[0])).left;
            const i = bisect(data.middle, date, 1);
            const d0 = data.middle[i - 1];
            const d1 = data.middle[i];

            if (d0 && d1) {
                const closest = date - new Date(d0[0]) > new Date(d1[0]) - date ? d1 : d0;
                const closestIndex = data.middle.indexOf(closest);
                const meta = chartState.metadata[key];

                tooltipData.push({
                    label: 'BB Upper',
                    value: data.upper[closestIndex][1],
                    unit: meta.unit || '',
                    color: meta.upperBandColor || '#4CAF50',
                    date: new Date(closest[0])
                });

                tooltipData.push({
                    label: 'BB Middle',
                    value: data.middle[closestIndex][1],
                    unit: meta.unit || '',
                    color: meta.color,
                    date: new Date(closest[0])
                });

                tooltipData.push({
                    label: 'BB Lower',
                    value: data.lower[closestIndex][1],
                    unit: meta.unit || '',
                    color: meta.lowerBandColor || '#F44336',
                    date: new Date(closest[0])
                });
            }
        } else if (data.length > 0) {
            const bisect = d3.bisector(d => new Date(d[0])).left;
            const i = bisect(data, date, 1);
            const d0 = data[i - 1];
            const d1 = data[i];

            if (d0 && d1) {
                const closest = date - new Date(d0[0]) > new Date(d1[0]) - date ? d1 : d0;
                const meta = chartState.metadata[key];

                tooltipData.push({
                    label: meta.label,
                    value: closest[1],
                    unit: meta.unit || '',
                    color: meta.color,
                    date: new Date(closest[0])
                });
            }
        }
    });

    if (tooltipData.length > 0) {
        showTooltip(event, tooltipData);
    }
}

/**
 * Handles mouse out events to hide crosshair and tooltip
 */
function mouseout() {
    verticalLine.style("display", "none");
    horizontalLine.style("display", "none");
    tooltip.classed("show", false);
}

/**
 * Shows the tooltip with data at the current mouse position
 */
function showTooltip(event, data) {
    const [mouseX, mouseY] = d3.pointer(event);

    let html = `<div class="tooltip-header">${d3.timeFormat("%B %d, %Y")(data[0].date)}</div>`;

    data.forEach(d => {
        const formattedValue = d.unit === '$' ?
            `$${d.value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` :
            d.unit === '%' ?
            `${d.value.toFixed(2)}%` :
            d.value.toFixed(2);

        html += `
            <div class="tooltip-row">
                <span>
                    <span class="tooltip-color" style="background: ${d.color}"></span>
                    ${d.label}
                </span>
                <span class="tooltip-value">${formattedValue}</span>
            </div>
        `;
    });

    tooltip.html(html);

    const tooltipNode = tooltip.node();
    const rect = tooltipNode.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    let left = containerRect.left + margin.left + mouseX + 15;
    let top = containerRect.top + margin.top + mouseY - rect.height / 2;

    if (left + rect.width > window.innerWidth - 20) {
        left = containerRect.left + margin.left + mouseX - rect.width - 15;
    }

    tooltip
        .style("left", `${left}px`)
        .style("top", `${top}px`)
        .classed("show", true);
}

/**
 * Handles window resize events
 */
function handleResize() {
    width = Math.min(container.clientWidth - margin.left - margin.right, 1200);
    svg.attr("width", width + margin.left + margin.right);
    clip.attr("width", width);
    xScale.range([0, width]);

    // Update overlay and brush
    overlay.attr("width", width);
    brush.extent([[0, 0], [width, height]]);

    // Redraw
    renderChart();
}

/**
 * Returns zoom control functions for external use (e.g., button handlers)
 * @returns {Object} Object containing zoom control functions
 */
export function getZoomControls() {
    return {
        resetZoom,
        zoomIn,
        zoomOut
    };
}
