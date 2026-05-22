/**
 * KULIMA OS Pilot - Visual Coordination Map
 * ==========================================
 * 
 * Visual Coordination Map component for rendering flow graphs and coordination patterns.
 * 
 * INVARIANT ENFORCEMENT:
 * - Zero-PII: Visualizes aggregated patterns only (never individual data)
 * - Coordination > Identity: Shows collective patterns, not individual behaviors
 * - Semantic Guard: Designed for planning, not surveillance or profiling
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function CoordinationMap() {
  const [view, setView] = useState('flow-graph'); // flow-graph, time-evolution, zone-interaction
  const [activityFilter, setActivityFilter] = useState('all');
  const [zoneFilter, setZoneFilter] = useState('all');
  const [timeWindow, setTimeWindow] = useState('weekly');
  const [flowData, setFlowData] = useState(null);
  const [loading, setLoading] = useState(true);
  const svgRef = useRef(null);

  useEffect(() => {
    fetchFlowData();
  }, [activityFilter, zoneFilter, timeWindow]);

  const fetchFlowData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/visualization/flow-network?activity=${activityFilter}&zone=${zoneFilter}&time_window=${timeWindow}`);
      const data = await response.json();
      setFlowData(data.data);
    } catch (error) {
      console.error('Error fetching flow data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (flowData && svgRef.current) {
      renderFlowGraph();
    }
  }, [flowData, view]);

  const renderFlowGraph = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    svg.attr('width', width).attr('height', height);

    if (view === 'flow-graph' && flowData.nodes && flowData.edges) {
      // Render Flow Graph
      const simulation = d3.forceSimulation(flowData.nodes)
        .force('link', d3.forceLink(flowData.edges).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

      const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Draw edges
      const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(flowData.edges)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.strength_score || 1) * 2);

      // Draw nodes
      const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(flowData.nodes)
        .enter().append('circle')
        .attr('r', d => Math.sqrt(d.frequency || 1) * 10)
        .attr('fill', d => getNodeColor(d.activity_type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended));

      // Add hover tooltips
      node.append('title')
        .text(d => `${d.activity_type}\nZone: ${d.zone}\nFrequency: ${d.frequency}\nPersistence: ${d.persistence}\nConfidence: ${d.confidence_score}`);

      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
      });

    } else if (view === 'time-evolution' && flowData.time_series) {
      // Render Time Evolution Graph
      const margin = { top: 40, right: 40, bottom: 60, left: 60 };
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;

      const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      const x = d3.scaleTime()
        .domain(d3.extent(flowData.time_series, d => new Date(d.timestamp)))
        .range([0, innerWidth]);

      const y = d3.scaleLinear()
        .domain([0, d3.max(flowData.time_series, d => d.value)])
        .range([innerHeight, 0]);

      // X axis
      g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('transform', 'rotate(-45)')
        .style('text-anchor', 'end');

      // Y axis
      g.append('g')
        .call(d3.axisLeft(y));

      // Line
      const line = d3.line()
        .x(d => x(new Date(d.timestamp)))
        .y(d => y(d.value));

      g.append('path')
        .datum(flowData.time_series)
        .attr('fill', 'none')
        .attr('stroke', '#4CAF50')
        .attr('stroke-width', 2)
        .attr('d', line);

      // Points
      g.selectAll('.point')
        .data(flowData.time_series)
        .enter().append('circle')
        .attr('class', 'point')
        .attr('cx', d => x(new Date(d.timestamp)))
        .attr('cy', d => y(d.value))
        .attr('r', 4)
        .attr('fill', '#4CAF50')
        .append('title')
        .text(d => `Value: ${d.value}\nDate: ${d.timestamp}`);

    } else if (view === 'zone-interaction') {
      // Render Zone Interaction Map (placeholder for Phase 2)
      const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      g.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '20')
        .text('Zone Interaction Map (Phase 2)');
    }
  };

  const getNodeColor = (activityType) => {
    const colors = {
      'irrigation': '#4CAF50',
      'milling': '#FF9800',
      'cold_storage': '#2196F3',
      'welding': '#F44336',
      'trading': '#9C27B0'
    };
    return colors[activityType] || '#999';
  };

  const dragstarted = (event, d) => {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  };

  const dragged = (event, d) => {
    d.fx = event.x;
    d.fy = event.y;
  };

  const dragended = (event, d) => {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">Loading coordination map...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">Visual Coordination Map</h2>
        
        {/* View Selector */}
        <div className="mb-4">
          <label className="mr-4 font-semibold">View:</label>
          <select
            value={view}
            onChange={(e) => setView(e.target.value)}
            className="px-4 py-2 border rounded"
          >
            <option value="flow-graph">Flow Graph</option>
            <option value="time-evolution">Time Evolution</option>
            <option value="zone-interaction">Zone Interaction (Phase 2)</option>
          </select>
        </div>

        {/* Filters */}
        <div className="flex gap-4 mb-4">
          <div>
            <label className="mr-2 font-semibold">Activity:</label>
            <select
              value={activityFilter}
              onChange={(e) => setActivityFilter(e.target.value)}
              className="px-4 py-2 border rounded"
            >
              <option value="all">All Activities</option>
              <option value="irrigation">Irrigation</option>
              <option value="milling">Milling</option>
              <option value="cold_storage">Cold Storage</option>
              <option value="welding">Welding</option>
              <option value="trading">Trading</option>
            </select>
          </div>

          <div>
            <label className="mr-2 font-semibold">Zone:</label>
            <select
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="px-4 py-2 border rounded"
            >
              <option value="all">All Zones</option>
              <option value="MZUZU">Mzuzu</option>
              <option value="LILONGWE">Lilongwe</option>
              <option value="BLANTYRE">Blantyre</option>
              <option value="ZOMBA">Zomba</option>
            </select>
          </div>

          <div>
            <label className="mr-2 font-semibold">Time Window:</label>
            <select
              value={timeWindow}
              onChange={(e) => setTimeWindow(e.target.value)}
              className="px-4 py-2 border rounded"
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="seasonal">Seasonal</option>
            </select>
          </div>
        </div>
      </div>

      {/* Visualization */}
      <div className="border rounded-lg p-4 bg-white">
        <svg ref={svgRef}></svg>
      </div>

      {/* Legend */}
      <div className="mt-4 p-4 border rounded bg-gray-50">
        <h3 className="font-semibold mb-2">Legend</h3>
        <div className="flex gap-4 flex-wrap">
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full mr-2" style={{ backgroundColor: '#4CAF50' }}></div>
            <span>Irrigation</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full mr-2" style={{ backgroundColor: '#FF9800' }}></div>
            <span>Milling</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full mr-2" style={{ backgroundColor: '#2196F3' }}></div>
            <span>Cold Storage</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full mr-2" style={{ backgroundColor: '#F44336' }}></div>
            <span>Welding</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full mr-2" style={{ backgroundColor: '#9C27B0' }}></div>
            <span>Trading</span>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Hover over nodes to see metrics. Drag nodes to rearrange. Use filters to focus on specific activities or zones.
        </p>
      </div>
    </div>
  );
}
