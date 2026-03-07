// src/components/RiskScore.jsx
import { THEMES } from '../themes';

/**
 * SVG arc gauge for risk score (0–100).
 * Arc sweeps 270° from bottom-left (7-o'clock) to bottom-right (5-o'clock).
 */
export default function RiskScore({ score = 0, theme, showFactors, factors = [] }) {
  const t = THEMES[theme];
  const clamp = Math.max(0, Math.min(100, Math.round(score)));

  const color =
    clamp >= 67 ? t.riskHigh :
    clamp >= 34 ? t.riskMed  :
                  t.riskLow;

  const level =
    clamp >= 67 ? 'HIGH' :
    clamp >= 34 ? 'MEDIUM' :
                  'LOW';

  /* ── Arc maths ── */
  const cx = 100, cy = 100, r = 72;
  const START = -135;   // degrees (clock convention: 0=top, clockwise)
  const SWEEP = 270;    // total sweep

  const toXY = (deg) => ({
    x: cx + r * Math.sin(deg * Math.PI / 180),
    y: cy - r * Math.cos(deg * Math.PI / 180),
  });

  const arcD = (startDeg, endDeg) => {
    const s = toXY(startDeg);
    const e = toXY(endDeg);
    const span = ((endDeg - startDeg) + 360) % 360;
    const large = span > 180 ? 1 : 0;
    return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`;
  };

  const fillEnd = START + (clamp / 100) * SWEEP;

  /* ── Tick marks ── */
  const ticks = [0, 25, 50, 75, 100].map(v => {
    const deg = START + (v / 100) * SWEEP;
    const outer = toXY(deg);
    const inner = {
      x: cx + (r - 12) * Math.sin(deg * Math.PI / 180),
      y: cy - (r - 12) * Math.cos(deg * Math.PI / 180),
    };
    return { outer, inner, v };
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
      {/* Gauge */}
      <div style={{ position: 'relative' }}>
        <svg width={200} height={185} viewBox="0 0 200 200">
          {/* Glow filter */}
          <defs>
            <filter id="gaugeGlow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background arc */}
          <path
            d={arcD(START, START + SWEEP)}
            fill="none"
            stroke={t.borderLight}
            strokeWidth={14}
            strokeLinecap="round"
          />

          {/* Tick marks */}
          {ticks.map(({ outer, inner, v }) => (
            <line
              key={v}
              x1={inner.x.toFixed(2)}
              y1={inner.y.toFixed(2)}
              x2={outer.x.toFixed(2)}
              y2={outer.y.toFixed(2)}
              stroke={t.border}
              strokeWidth={2}
            />
          ))}

          {/* Score arc */}
          {clamp > 0 && (
            <path
              d={arcD(START, fillEnd)}
              fill="none"
              stroke={color}
              strokeWidth={14}
              strokeLinecap="round"
              filter="url(#gaugeGlow)"
              style={{ transition: 'stroke 0.4s' }}
            />
          )}

          {/* Score value */}
          <text
            x={cx}
            y={cy + 6}
            textAnchor="middle"
            fill={color}
            fontSize={40}
            fontFamily="'Sora',sans-serif"
            fontWeight="800"
            style={{ transition: 'fill 0.4s' }}
          >
            {clamp}
          </text>

          {/* /100 label */}
          <text
            x={cx}
            y={cy + 24}
            textAnchor="middle"
            fill={t.textMuted}
            fontSize={10}
            fontFamily="'JetBrains Mono',monospace"
            letterSpacing="2"
          >
            / 100
          </text>

          {/* LOW / HIGH labels */}
          <text x={18} y={168} fill={t.riskLow} fontSize={8} fontFamily="'JetBrains Mono',monospace" fontWeight="700">LOW</text>
          <text x={162} y={168} fill={t.riskHigh} fontSize={8} fontFamily="'JetBrains Mono',monospace" fontWeight="700">HIGH</text>
        </svg>
      </div>

      {/* Risk level badge */}
      <div style={{
        padding: '8px 24px',
        background: `${color}22`,
        border: `1px solid ${color}55`,
        borderRadius: 24,
        fontFamily: "'JetBrains Mono',monospace",
        fontWeight: 700,
        fontSize: 13,
        color,
        letterSpacing: 3,
        boxShadow: `0 0 16px ${color}33`,
      }}>
        {level} RISK
      </div>

      {/* Risk factor breakdown */}
      {showFactors && factors.length > 0 && (
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 10, color: t.textSub,
            letterSpacing: 2, marginBottom: 4,
          }}>
            RISK BREAKDOWN
          </div>
          {factors.map((f, i) => (
            <RiskFactor key={i} factor={f} theme={theme} />
          ))}
        </div>
      )}
    </div>
  );
}

function RiskFactor({ factor, theme }) {
  const t = THEMES[theme];
  const pct = Math.min(100, Math.max(0, factor.score || 0));
  const color =
    pct >= 67 ? t.riskHigh :
    pct >= 34 ? t.riskMed  :
                t.riskLow;
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.text }}>{factor.label}</span>
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color, fontWeight: 700 }}>
          {pct}
        </span>
      </div>
      <div style={{ width: '100%', height: 4, background: t.borderLight, borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: color, borderRadius: 2,
          transition: 'width 0.6s ease',
          boxShadow: `0 0 6px ${color}66`,
        }} />
      </div>
    </div>
  );
}
