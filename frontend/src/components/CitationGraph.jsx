import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';

const NODE_COLORS = {
  query:  '#4f8ef7',
  answer: '#c9a84c',
  claim:  '#a78bfa',
  source: '#22c55e',
};
const NODE_RADIUS = { query: 20, answer: 18, claim: 12, source: 14 };

export default function CitationGraph({ graph }) {
  const svgRef = useRef(null);
  const { nodes = [], edges = [] } = graph || {};

  const simNodes = useMemo(() => nodes.map(n => ({ ...n })), [nodes]);
  const simLinks = useMemo(
    () => edges.map(e => ({ ...e, source: e.source, target: e.target })),
    [edges]
  );

  useEffect(() => {
    if (!svgRef.current || simNodes.length === 0) return;
    const el = svgRef.current;
    d3.select(el).selectAll('*').remove();

    const W = el.clientWidth || 700;
    const H = 380;

    const svg = d3.select(el)
      .attr('viewBox', `0 0 ${W} ${H}`)
      .style('background', 'transparent');

    const defs = svg.append('defs');
    // Arrow markers
    Object.entries(NODE_COLORS).forEach(([type, col]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('markerWidth', 8).attr('markerHeight', 8)
        .attr('refX', 16).attr('refY', 3)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,0 L0,6 L8,3 z')
        .attr('fill', col + '99');
    });

    const sim = d3.forceSimulation(simNodes)
      .force('link', d3.forceLink(simLinks).id(d => d.id).distance(100).strength(0.6))
      .force('charge', d3.forceManyBody().strength(-280))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide().radius(d => (NODE_RADIUS[d.type] || 12) + 18));

    const link = svg.append('g').selectAll('line')
      .data(simLinks).join('line')
      .attr('stroke', d => {
        const tgt = simNodes.find(n => n.id === (d.target?.id || d.target));
        return NODE_COLORS[tgt?.type] + '55' || '#333';
      })
      .attr('stroke-width', 1.5)
      .attr('marker-end', d => {
        const tgt = simNodes.find(n => n.id === (d.target?.id || d.target));
        return `url(#arrow-${tgt?.type || 'source'})`;
      });

    const node = svg.append('g').selectAll('g')
      .data(simNodes).join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end',   (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    node.append('circle')
      .attr('r', d => NODE_RADIUS[d.type] || 12)
      .attr('fill', d => NODE_COLORS[d.type] + '22')
      .attr('stroke', d => NODE_COLORS[d.type])
      .attr('stroke-width', 1.5);

    // Score ring for claim nodes
    node.filter(d => d.type === 'claim').append('circle')
      .attr('r', d => NODE_RADIUS[d.type] - 4)
      .attr('fill', d => {
        const s = d.data?.confidence || 0;
        return s >= 0.7 ? '#22c55e33' : s >= 0.35 ? '#f59e0b33' : '#ef444433';
      })
      .attr('stroke', 'none');

    node.append('text')
      .attr('dy', d => (NODE_RADIUS[d.type] || 12) + 12)
      .attr('text-anchor', 'middle')
      .attr('fill', d => NODE_COLORS[d.type])
      .attr('font-size', 9)
      .attr('font-family', 'IBM Plex Mono, monospace')
      .text(d => d.label?.substring(0, 22) + (d.label?.length > 22 ? '…' : ''));

    node.append('title').text(d => d.label);

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => sim.stop();
  }, [simNodes, simLinks]);

  if (!nodes.length) return null;

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
        {Object.entries(NODE_COLORS).map(([type, col]) => (
          <span key={type} style={{ display:'flex', alignItems:'center', gap:5, fontSize:11,
                                    color: col, fontFamily:'IBM Plex Mono,monospace', textTransform:'uppercase', letterSpacing:0.5 }}>
            <span style={{ width:8, height:8, borderRadius:'50%', background:col, display:'inline-block' }}/>
            {type}
          </span>
        ))}
      </div>
      <svg ref={svgRef} width="100%" style={{ minHeight: 380, border:'1px solid #1e2535', borderRadius:8 }}/>
    </div>
  );
}
