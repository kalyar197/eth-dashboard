// Indexed Chart Module - Displays normalized data all starting at baseline 100

// Chart State Management
let indexedChartState = {
    days: '365',
    activePlugins: [],
    datasets: {},
    metadata: {},
    currentZoom: null,
    commonStartDate: null,
    commonStartTimestamp: null
};

// Chart dimensions
const indexedMargin = {top: 30, right: 80, bottom: 50, left: 80};
let indexedWidth;
let indexedHeight;

// DOM elements
let indexedContainer;
let indexedTooltip;

// D3 elements
let indexedSvg;
let indexedG;
let indexedClip;
let indexedGridGroup;
let indexedLinesGroup;
let indexedXAxisGroup;
let indexedYAxisGroup;
let indexedCrosshairGroup;
let indexedBrushGroup;
let indexedOverlay;

// D3 scales and interactions
let indexedXScale;
let indexedYScale;
let indexedBrush;

// Crosshair elements
let indexedVerticalLine;
let indexedHorizontalLine;
let indexedCrosshairTextX;

/**
 * Initializes the indexed chart
 */
export function initIndexedChart(containerId, tooltipId) {
    indexedContainer = document.getElementById(containerId);
    indexedTooltip = d3.select(`#${tooltipId}`);

    // Calculate dimensions
    indexedWidth = Math.min(indexedContainer.clientWidth - indexedMargin.left - indexedMargin.right, 1200);
    indexedHeight = 550 - indexedMargin.top - indexedMargin.bottom;

    // Create SVG
    d3.select(`#${containerId}`).selectAll("svg").remove();
    indexedSvg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", indexedWidth + indexedMargin.left + indexedMargin.right)
        .attr("height", 580);

    indexedG = indexedSvg.append("g")
        .attr("transform", `translate(${indexedMargin.left},${indexedMargin.top})`);

    // Create clip path
    indexedClip = indexedG.append("defs").append("clipPath")
        .attr("id", "indexed-clip")
        .append("rect")
        .attr("width", indexedWidth)
        .attr("height", indexedHeight);

    // Groups for elements
    indexedGridGroup = indexedG.append("g").attr("class", "grid");
    indexedLinesGroup = indexedG.append("g").attr("clip-path", "url(#indexed-clip)");
    indexedXAxisGroup = indexedG.append("g").attr("transform", `translate(0,${indexedHeight})`);
    indexedCrosshairGroup = indexedG.append("g").attr("class", "crosshair");

    // Crosshair elements
    indexedVerticalLine = indexedCrosshairGroup.append("line")
        .attr("class", "crosshair-line")
        .attr("y1", 0)
        .attr("y2", indexedHeight)
        .style("display", "none");

    indexedHorizontalLine = indexedCrosshairGroup.append("line")
        .attr("class", "crosshair-line")
        .attr("x1", 0)
        .attr("x2", indexedWidth)
        .style("display", "none");

    indexedCrosshairTextX = indexedCrosshairGroup.append("text")
        .attr("class", "crosshair-text")
        .attr("y", indexedHeight + 15)
        .attr("text-anchor", "middle");

    // Scales
    indexedXScale = d3.scaleTime().range([0, indexedWidth]);
    indexedYScale = d3.scaleLinear().range([indexedHeight, 0]);

    // Brush for zoom
    indexedBrush = d3.brushX()
        .extent([[0, 0], [indexedWidth, indexedHeight]])
        .on("end", indexedBrushEnded);

    indexedBrushGroup = indexedG.append("g")
        .attr("class", "brush");

    // Overlay for mouse events
    indexedOverlay = indexedG.append("rect")
        .attr("class", "zoom-overlay")
        .attr("width", indexedWidth)
        .attr("height", indexedHeight)
        .on("mousemove", indexedMouseMove)
        .on("mouseout", indexedMouseOut)
        .call(indexedBrush);

    // Handle resize
    window.addEventListener('resize', handleIndexedResize);
}

/**
 * Updates the indexed chart with new data
 */
export function updateIndexedChart(activePlugins, datasets, metadata, days) {
    indexedChartState.activePlugins = activePlugins;
    indexedChartState.metadata = metadata;
    indexedChartState.days = days;

    if (indexedChartState.activePlugins.length === 0) {
        indexedLinesGroup.selectAll("*").remove();
        indexedGridGroup.selectAll("*").remove();
        if (indexedYAxisGroup) indexedYAxisGroup.style("display", "none");
        // Clear baseline info
        d3.select('#indexed-chart-container').selectAll('.baseline-info').remove();
        return;
    }

    // Find common start date (latest start timestamp across all datasets)
    const startTimestamps = [];

    Object.entries(datasets).forEach(([key, data]) => {
        if (!indexedChartState.activePlugins.includes(key)) return;

        if (key === 'bollinger_bands' && data.middle) {
            if (data.middle.length > 0) startTimestamps.push(data.middle[0][0]);
        } else if (data.length > 0) {
            startTimestamps.push(data[0][0]);
        }
    });

    if (startTimestamps.length === 0) {
        indexedChartState.datasets = {};
        renderIndexedChart();
        return;
    }

    // Use the LATEST start timestamp (ensures all datasets have data)
    const commonStartTimestamp = Math.max(...startTimestamps);
    indexedChartState.commonStartTimestamp = commonStartTimestamp;
    indexedChartState.commonStartDate = new Date(commonStartTimestamp);

    // Re-index all datasets from the common start point
    indexedChartState.datasets = {};

    Object.entries(datasets).forEach(([key, data]) => {
        if (!indexedChartState.activePlugins.includes(key)) return;

        if (key === 'bollinger_bands' && data.middle) {
            // Re-index Bollinger Bands
            const reindexedBB = {
                upper: reindexFromTimestamp(data.upper, commonStartTimestamp),
                middle: reindexFromTimestamp(data.middle, commonStartTimestamp),
                lower: reindexFromTimestamp(data.lower, commonStartTimestamp)
            };
            indexedChartState.datasets[key] = reindexedBB;
        } else if (data.length > 0) {
            // Re-index regular data
            indexedChartState.datasets[key] = reindexFromTimestamp(data, commonStartTimestamp);
        }
    });

    renderIndexedChart();
}

/**
 * Re-indexes data from a specific timestamp
 */
function reindexFromTimestamp(data, startTimestamp, baseline = 100) {
    if (!data || data.length === 0) return [];

    // Filter to start from timestamp
    const filtered = data.filter(point => point[0] >= startTimestamp);

    if (filtered.length === 0) return [];

    // Get the first value as reference
    const firstValue = filtered[0][1];

    if (firstValue === 0) return filtered;

    // Re-index all values
    return filtered.map(point => [
        point[0],
        baseline * (point[1] / firstValue)
    ]);
}

/**
 * Renders the indexed chart
 */
function renderIndexedChart() {
    // Get all data points for X domain
    const allData = Object.entries(indexedChartState.datasets)
        .filter(([key, data]) => indexedChartState.activePlugins.includes(key))
        .map(([key, data]) => {
            // Handle Bollinger Bands
            if (key === 'bollinger_bands' && data.middle) {
                return data.middle;
            }
            return data;
        })
        .flat();

    if (allData.length === 0) return;

    // Display baseline information
    displayBaselineInfo();

    // Set X scale
    const xDomain = d3.extent(allData, d => new Date(d[0]));
    indexedXScale.domain(indexedChartState.currentZoom || xDomain);

    // Calculate Y domain from all indexed data
    // Since everything is indexed, we can use a dynamic range
    const allValues = allData.map(d => d[1]);
    const yMin = d3.min(allValues);
    const yMax = d3.max(allValues);
    const padding = (yMax - yMin) * 0.05;
    indexedYScale.domain([yMin - padding, yMax + padding]);

    // Create/update Y axis
    if (indexedYAxisGroup) indexedYAxisGroup.remove();

    indexedYAxisGroup = indexedG.append("g")
        .attr("class", "y-axis y-axis-indexed")
        .attr("transform", "translate(0, 0)");

    const yAxis = d3.axisLeft(indexedYScale).ticks(6);
    indexedYAxisGroup.call(yAxis);

    // Add Y axis label
    indexedYAxisGroup.append("text")
        .attr("class", "axis-label")
        .attr("transform", "rotate(-90)")
        .attr("y", -50)
        .attr("x", -indexedHeight / 2)
        .attr("text-anchor", "middle")
        .text("Indexed Value (Base 100)")
        .style("fill", "#4a9eff");

    // Draw X axis
    indexedXAxisGroup.call(d3.axisBottom(indexedXScale)
        .tickFormat(d3.timeFormat("%b %d"))
        .ticks(indexedWidth > 600 ? 8 : 5));

    // Draw grid
    indexedGridGroup.selectAll("*").remove();
    indexedGridGroup.call(d3.axisLeft(indexedYScale)
        .tickSize(-indexedWidth)
        .tickFormat("")
        .ticks(8));

    // Clear old lines
    indexedLinesGroup.selectAll(".line").remove();
    indexedLinesGroup.selectAll(".bb-band").remove();
    indexedLinesGroup.selectAll(".bb-area").remove();

    // Draw lines for each dataset
    indexedChartState.activePlugins.forEach(plugin => {
        if (!indexedChartState.datasets[plugin]) return;

        const meta = indexedChartState.metadata[plugin];

        if (plugin === 'bollinger_bands') {
            // Handle Bollinger Bands
            const bbData = indexedChartState.datasets[plugin];
            if (bbData.middle && bbData.middle.length > 0) {
                // Draw area
                const area = d3.area()
                    .x(d => indexedXScale(new Date(d[0])))
                    .y0(d => indexedYScale(d[1]))
                    .y1((d, i) => indexedYScale(bbData.upper[i][1]));

                indexedLinesGroup.append("path")
                    .datum(bbData.lower)
                    .attr("class", "bb-area")
                    .attr("d", area)
                    .style("fill", meta.upperBandColor || '#4CAF50')
                    .style("opacity", 0.1);

                // Draw lines
                const lineGenerator = d3.line()
                    .x(d => indexedXScale(new Date(d[0])))
                    .y(d => indexedYScale(d[1]));

                // Upper
                indexedLinesGroup.append("path")
                    .attr("class", "bb-band bb-upper")
                    .attr("d", lineGenerator(bbData.upper))
                    .style("stroke", meta.upperBandColor || '#4CAF50')
                    .style("stroke-width", 1)
                    .style("fill", "none")
                    .style("stroke-dasharray", "2,2");

                // Middle
                indexedLinesGroup.append("path")
                    .attr("class", "bb-band bb-middle")
                    .attr("d", lineGenerator(bbData.middle))
                    .style("stroke", meta.color)
                    .style("stroke-width", 1.5)
                    .style("fill", "none");

                // Lower
                indexedLinesGroup.append("path")
                    .attr("class", "bb-band bb-lower")
                    .attr("d", lineGenerator(bbData.lower))
                    .style("stroke", meta.lowerBandColor || '#F44336')
                    .style("stroke-width", 1)
                    .style("fill", "none")
                    .style("stroke-dasharray", "2,2");
            }
        } else if (indexedChartState.datasets[plugin].length > 0) {
            // Draw regular line
            const line = d3.line()
                .x(d => indexedXScale(new Date(d[0])))
                .y(d => indexedYScale(d[1]));

            indexedLinesGroup.append("path")
                .datum(indexedChartState.datasets[plugin])
                .attr("class", `line line-${plugin}`)
                .attr("d", line)
                .style("stroke", meta.color)
                .style("stroke-width", meta.strokeWidth || 2)
                .style("fill", "none");
        }
    });
}

/**
 * Brush end handler
 */
function indexedBrushEnded(event) {
    if (!event.selection) return;

    const [x0, x1] = event.selection.map(indexedXScale.invert);
    indexedChartState.currentZoom = [x0, x1];

    indexedBrushGroup.call(indexedBrush.clear);
    renderIndexedChart();
}

/**
 * Zoom controls
 */
function indexedResetZoom() {
    indexedChartState.currentZoom = null;
    renderIndexedChart();
}

function indexedZoomIn() {
    const domain = indexedXScale.domain();
    const center = new Date((domain[0].getTime() + domain[1].getTime()) / 2);
    const range = domain[1].getTime() - domain[0].getTime();
    const newRange = range * 0.5;

    indexedChartState.currentZoom = [
        new Date(center.getTime() - newRange / 2),
        new Date(center.getTime() + newRange / 2)
    ];
    renderIndexedChart();
}

function indexedZoomOut() {
    const domain = indexedXScale.domain();
    const center = new Date((domain[0].getTime() + domain[1].getTime()) / 2);
    const range = domain[1].getTime() - domain[0].getTime();
    const newRange = range * 2;

    indexedChartState.currentZoom = [
        new Date(center.getTime() - newRange / 2),
        new Date(center.getTime() + newRange / 2)
    ];
    renderIndexedChart();
}

/**
 * Mouse move handler
 */
function indexedMouseMove(event) {
    const [mouseX, mouseY] = d3.pointer(event);
    const date = indexedXScale.invert(mouseX);

    // Update crosshair
    indexedVerticalLine
        .attr("x1", mouseX)
        .attr("x2", mouseX)
        .style("display", "block");

    indexedHorizontalLine
        .attr("y1", mouseY)
        .attr("y2", mouseY)
        .style("display", "block");

    indexedCrosshairTextX
        .attr("x", mouseX)
        .text(d3.timeFormat("%b %d, %Y")(date));

    // Find closest data points
    const tooltipData = [];

    indexedChartState.activePlugins.forEach(key => {
        const data = indexedChartState.datasets[key];
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
                const meta = indexedChartState.metadata[key];

                tooltipData.push({
                    label: 'BB Upper (Indexed)',
                    value: data.upper[closestIndex][1],
                    unit: '',
                    color: meta.upperBandColor || '#4CAF50',
                    date: new Date(closest[0])
                });

                tooltipData.push({
                    label: 'BB Middle (Indexed)',
                    value: data.middle[closestIndex][1],
                    unit: '',
                    color: meta.color,
                    date: new Date(closest[0])
                });

                tooltipData.push({
                    label: 'BB Lower (Indexed)',
                    value: data.lower[closestIndex][1],
                    unit: '',
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
                const meta = indexedChartState.metadata[key];

                tooltipData.push({
                    label: meta.label,
                    value: closest[1],
                    unit: '',
                    color: meta.color,
                    date: new Date(closest[0])
                });
            }
        }
    });

    if (tooltipData.length > 0) {
        showIndexedTooltip(event, tooltipData);
    }
}

/**
 * Mouse out handler
 */
function indexedMouseOut() {
    indexedVerticalLine.style("display", "none");
    indexedHorizontalLine.style("display", "none");
    indexedTooltip.classed("show", false);
}

/**
 * Show tooltip
 */
function showIndexedTooltip(event, data) {
    const [mouseX, mouseY] = d3.pointer(event);

    let html = `<div class="tooltip-header">${d3.timeFormat("%B %d, %Y")(data[0].date)}</div>`;

    data.forEach(d => {
        const formattedValue = d.value.toFixed(2);

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

    indexedTooltip.html(html);

    const tooltipNode = indexedTooltip.node();
    const rect = tooltipNode.getBoundingClientRect();
    const containerRect = indexedContainer.getBoundingClientRect();

    let left = containerRect.left + indexedMargin.left + mouseX + 15;
    let top = containerRect.top + indexedMargin.top + mouseY - rect.height / 2;

    if (left + rect.width > window.innerWidth - 20) {
        left = containerRect.left + indexedMargin.left + mouseX - rect.width - 15;
    }

    indexedTooltip
        .style("left", `${left}px`)
        .style("top", `${top}px`)
        .classed("show", true);
}

/**
 * Display baseline date and elapsed time information
 */
function displayBaselineInfo() {
    if (!indexedChartState.commonStartDate) return;

    // Remove existing baseline info
    d3.select('#indexed-chart-container').selectAll('.baseline-info').remove();

    const now = new Date();
    const startDate = indexedChartState.commonStartDate;

    // Calculate elapsed time
    const totalDays = Math.floor((now - startDate) / (1000 * 60 * 60 * 24));
    const years = Math.floor(totalDays / 365);
    const remainingDays = totalDays % 365;
    const months = Math.floor(remainingDays / 30);
    const days = remainingDays % 30;

    // Format date
    const dateStr = startDate.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    // Build elapsed time string
    const elapsedParts = [];
    if (years > 0) elapsedParts.push(`${years} year${years > 1 ? 's' : ''}`);
    if (months > 0) elapsedParts.push(`${months} month${months > 1 ? 's' : ''}`);
    if (days > 0 || elapsedParts.length === 0) elapsedParts.push(`${days} day${days !== 1 ? 's' : ''}`);

    const elapsedStr = elapsedParts.join(', ');

    // Create info text element
    const infoDiv = d3.select('#indexed-chart-container')
        .append('div')
        .attr('class', 'baseline-info')
        .style('position', 'absolute')
        .style('top', '45px')
        .style('left', '20px')
        .style('font-size', '12px')
        .style('color', '#888')
        .style('background', 'rgba(26, 26, 26, 0.9)')
        .style('padding', '8px 12px')
        .style('border-radius', '6px')
        .style('border', '1px solid #333')
        .style('z-index', '10');

    infoDiv.html(`
        <div style="margin-bottom: 4px;">
            <strong style="color: #4a9eff;">Baseline Date:</strong> ${dateStr}
        </div>
        <div style="color: #aaa;">
            <strong style="color: #4a9eff;">Elapsed:</strong> ${elapsedStr}
        </div>
    `);
}

/**
 * Handle resize
 */
function handleIndexedResize() {
    indexedWidth = Math.min(indexedContainer.clientWidth - indexedMargin.left - indexedMargin.right, 1200);
    indexedSvg.attr("width", indexedWidth + indexedMargin.left + indexedMargin.right);
    indexedClip.attr("width", indexedWidth);
    indexedXScale.range([0, indexedWidth]);

    indexedOverlay.attr("width", indexedWidth);
    indexedBrush.extent([[0, 0], [indexedWidth, indexedHeight]]);

    renderIndexedChart();
}

/**
 * Export zoom controls
 */
export function getIndexedZoomControls() {
    return {
        resetZoom: indexedResetZoom,
        zoomIn: indexedZoomIn,
        zoomOut: indexedZoomOut
    };
}
