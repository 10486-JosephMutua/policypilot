import React from 'react';

const ARC_R = 52;
const CX = 70, CY = 70;
const START_ANGLE = -210;
const SWEEP = 240;

function polarToXY(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(cx, cy, r, startDeg, endDeg) {
  const s = polarToXY(cx, cy, r, startDeg);
  const e = polarToXY(cx, cy, r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
}

export default function ConfidenceGauge({ score = 0, label = 'Ambiguous', size = 140 }) {
  const pct   = Math.max(0, Math.min(1, score));
  const angle = START_ANGLE + SWEEP * pct;
  const trackPath  = describeArc(CX, CY, ARC_R, START_ANGLE, START_ANGLE + SWEEP);
  const fillPath   = describeArc(CX, CY, ARC_R, START_ANGLE, angle);
  const needle = polarToXY(CX, CY, ARC_R - 14, angle);

  const colour = label === 'Correct'   ? '#22c55e'
               : label === 'Incorrect' ? '#ef4444'
               :                         '#f59e0b';

  const pctDisplay = Math.round(pct * 100);

  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:4 }}>
      <svg width={size} height={size * 0.72} viewBox="0 0 140 100">
        {/* Track */}
        <path d={trackPath} fill="none" stroke="#1e2535" strokeWidth="10" strokeLinecap="round"/>
        {/* Fill */}
        <path d={fillPath}  fill="none" stroke={colour} strokeWidth="10" strokeLinecap="round"
              style={{ filter: `drop-shadow(0 0 6px ${colour}66)` }}/>
        {/* Needle dot */}
        <circle cx={needle.x} cy={needle.y} r="5" fill={colour}
                style={{ filter: `drop-shadow(0 0 4px ${colour})` }}/>
        {/* Score */}
        <text x={CX} y={CY + 14} textAnchor="middle"
              style={{ fontFamily:'DM Serif Display,serif', fontSize:26, fill:'#e8edf5' }}>
          {pctDisplay}%
        </text>
        {/* Label */}
        <text x={CX} y={CY + 28} textAnchor="middle"
              style={{ fontFamily:'Inter,sans-serif', fontSize:9, fill: colour, letterSpacing:1, textTransform:'uppercase' }}>
          {label}
        </text>
      </svg>
    </div>
  );
}
