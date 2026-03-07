// src/components/UI.jsx
import { THEMES } from '../themes';

/* ── Risk Badge ─────────────────────────────── */
export function RiskBadge({ level, theme }) {
  const t = THEMES[theme];
  const map = {
    HIGH:    { bg: t.riskHigh, label: 'HIGH' },
    MEDIUM:  { bg: t.riskMed,  label: 'MED'  },
    LOW:     { bg: t.riskLow,  label: 'LOW'  },
    MINIMAL: { bg: t.riskLow,  label: 'MIN'  },
    UNKNOWN: { bg: t.textMuted, label: '—'   },
  };
  const r = map[(level || '').toUpperCase()] || map.UNKNOWN;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      padding: '4px 14px', borderRadius: 6,
      background: r.bg, color: '#fff',
      fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
      letterSpacing: 1.5, minWidth: 62, textAlign: 'center',
      boxShadow: `0 0 10px ${r.bg}88`,
    }}>
      {r.label}
    </span>
  );
}

/* ── Status Badge ───────────────────────────── */
export function StatusBadge({ status, theme }) {
  const t = THEMES[theme];
  const map = {
    completed: { bg: t.riskLow,  label: 'COMPLETED' },
    running:   { bg: t.riskMed,  label: 'RUNNING'   },
    pending:   { bg: t.textMuted, label: 'PENDING'   },
    failed:    { bg: t.riskHigh, label: 'FAILED'     },
  };
  const s = map[(status || '').toLowerCase()] || map.pending;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      padding: '3px 12px', borderRadius: 20,
      background: `${s.bg}22`, color: s.bg,
      border: `1px solid ${s.bg}55`,
      fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
      letterSpacing: 1.5,
    }}>
      {s.label}
    </span>
  );
}

/* ── Spinner ────────────────────────────────── */
export function Spinner({ size = 18, color = '#fff' }) {
  return (
    <span className="spin" style={{
      display: 'inline-block',
      width: size, height: size,
      border: `2px solid ${color}33`,
      borderTopColor: color,
      borderRadius: '50%',
      flexShrink: 0,
    }} />
  );
}

/* ── Stat Card ──────────────────────────────── */
export function StatCard({ label, value, delta, positive, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{
      background: t.surface, border: `1px solid ${t.border}`,
      borderRadius: 14, padding: '18px 20px',
      transition: 'border-color 0.2s, transform 0.2s',
      cursor: 'default',
    }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = t.cardHoverBorder; e.currentTarget.style.transform = 'translateY(-2px)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = t.border; e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textSub, letterSpacing: 2, marginBottom: 8 }}>
        {label.toUpperCase()}
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
        <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 32, fontWeight: 800, color: t.text, lineHeight: 1 }}>
          {value}
        </span>
        {delta && (
          <span style={{ fontSize: 12, fontWeight: 700, color: positive ? t.riskLow : t.riskHigh, marginBottom: 3 }}>
            {delta}
          </span>
        )}
      </div>
    </div>
  );
}

/* ── Card shell ─────────────────────────────── */
export function Card({ children, theme, style = {} }) {
  const t = THEMES[theme];
  return (
    <div style={{
      background: t.surface,
      border: `1px solid ${t.border}`,
      borderRadius: 16,
      ...style,
    }}>
      {children}
    </div>
  );
}

/* ── Section title ──────────────────────────── */
export function SectionTitle({ icon, title, theme, action }) {
  const t = THEMES[theme];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
      {icon && <span style={{ color: t.accent, fontSize: 16 }}>{icon}</span>}
      <span style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 15, color: t.text }}>{title}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(to right,${t.border},transparent)`, marginLeft: 8 }} />
      {action && action}
    </div>
  );
}

/* ── Empty state ────────────────────────────── */
export function EmptyState({ icon = '◎', message, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px', color: t.textMuted }}>
      <div style={{ fontSize: 36, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 14 }}>{message}</div>
    </div>
  );
}

/* ── Alert ──────────────────────────────────── */
export function Alert({ type = 'info', children, theme }) {
  const t = THEMES[theme];
  const colors = {
    info:    t.accent,
    success: t.riskLow,
    warning: t.riskMed,
    danger:  t.riskHigh,
  };
  const c = colors[type] || colors.info;
  return (
    <div style={{
      padding: '12px 16px', borderRadius: 10,
      background: `${c}18`, border: `1px solid ${c}44`,
      color: t.text, fontFamily: "'Sora',sans-serif", fontSize: 13,
      display: 'flex', gap: 10, alignItems: 'flex-start',
    }}>
      <span style={{ color: c, fontSize: 15, marginTop: 1 }}>
        {type === 'danger' ? '✖' : type === 'warning' ? '⚠' : type === 'success' ? '✓' : 'ℹ'}
      </span>
      <div>{children}</div>
    </div>
  );
}

/* ── Tab Bar ────────────────────────────────── */
export function TabBar({ tabs, active, onChange, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{
      display: 'flex',
      gap: 0,
      borderBottom: `1px solid ${t.border}`,
      marginBottom: 24,
      overflowX: 'auto',
      flexShrink: 0,
    }}>
      {tabs.map(tab => {
        const isActive = active === tab.key;
        return (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            style={{
              padding: '11px 20px',
              background: 'transparent',
              color: isActive ? t.accent : t.textMuted,
              border: 'none',
              borderBottom: `2px solid ${isActive ? t.accent : 'transparent'}`,
              cursor: 'pointer',
              fontFamily: "'Sora',sans-serif",
              fontWeight: isActive ? 700 : 500,
              fontSize: 13,
              whiteSpace: 'nowrap',
              transition: 'all 0.15s',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              flexShrink: 0,
            }}
            onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = t.text; }}
            onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = t.textMuted; }}
          >
            {tab.icon && <span style={{ fontSize: 14 }}>{tab.icon}</span>}
            {tab.label}
            {tab.count !== undefined && tab.count !== null && (
              <span style={{
                marginLeft: 4,
                padding: '1px 7px',
                background: isActive ? `${t.accent}33` : t.surfaceAlt,
                border: `1px solid ${isActive ? t.accent + '55' : t.border}`,
                borderRadius: 20,
                fontFamily: "'JetBrains Mono',monospace",
                fontSize: 9,
                color: isActive ? t.accent : t.textMuted,
              }}>
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* ── Progress Bar ───────────────────────────── */
export function ProgressBar({ value = 0, max = 100, color, theme, label, showPct = true }) {
  const t = THEMES[theme];
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const barColor = color || t.accent;
  return (
    <div style={{ width: '100%' }}>
      {(label || showPct) && (
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 6,
          fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted,
        }}>
          {label && <span>{label}</span>}
          {showPct && <span style={{ color: barColor }}>{Math.round(pct)}%</span>}
        </div>
      )}
      <div style={{
        width: '100%', height: 6, background: t.borderLight,
        borderRadius: 3, overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
          borderRadius: 3,
          transition: 'width 0.5s ease',
          boxShadow: `0 0 8px ${barColor}66`,
        }} />
      </div>
    </div>
  );
}

/* ── Input Field ────────────────────────────── */
export function InputField({ label, required, placeholder, value, onChange, type = 'text', disabled, theme }) {
  const t = THEMES[theme];
  return (
    <div>
      {label && (
        <label style={{
          display: 'block',
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 10, fontWeight: 700,
          color: t.textSub, letterSpacing: 1.5,
          marginBottom: 6,
          textTransform: 'uppercase',
        }}>
          {label}{required && <span style={{ color: t.riskHigh, marginLeft: 4 }}>*</span>}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        style={{
          width: '100%',
          padding: '11px 14px',
          background: t.inputBg,
          border: `1px solid ${t.border}`,
          borderRadius: 8,
          color: t.text,
          fontFamily: "'Sora',sans-serif",
          fontSize: 14,
          outline: 'none',
          boxSizing: 'border-box',
          transition: 'border-color 0.2s, box-shadow 0.2s',
          opacity: disabled ? 0.6 : 1,
        }}
        onFocus={e => {
          e.target.style.borderColor = t.accent;
          e.target.style.boxShadow = `0 0 0 3px ${t.accent}22`;
        }}
        onBlur={e => {
          e.target.style.borderColor = t.border;
          e.target.style.boxShadow = 'none';
        }}
      />
    </div>
  );
}

/* ── Button ─────────────────────────────────── */
export function Btn({ children, onClick, disabled, variant = 'primary', size = 'md', theme, style = {} }) {
  const t = THEMES[theme];
  const sizes = {
    sm: { padding: '7px 16px', fontSize: 12 },
    md: { padding: '11px 24px', fontSize: 14 },
    lg: { padding: '13px 30px', fontSize: 15 },
  };
  const variants = {
    primary: {
      background: disabled ? t.border : t.accentGrad,
      color: '#fff',
      border: 'none',
      boxShadow: disabled ? 'none' : `0 4px 20px ${t.accent}44`,
    },
    secondary: {
      background: 'transparent',
      color: t.textMid,
      border: `1px solid ${t.border}`,
      boxShadow: 'none',
    },
    danger: {
      background: `${t.riskHigh}22`,
      color: t.riskHigh,
      border: `1px solid ${t.riskHigh}44`,
      boxShadow: 'none',
    },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        ...sizes[size],
        ...variants[variant],
        borderRadius: 10,
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontFamily: "'Sora',sans-serif",
        fontWeight: 700,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        transition: 'all 0.2s',
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {children}
    </button>
  );
}

/* ── Data Table ─────────────────────────────── */
export function DataTable({ rows, theme }) {
  const t = THEMES[theme];
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <tbody>
        {rows.map(([key, val], i) => (
          <tr key={i} style={{ borderBottom: `1px solid ${t.borderLight}` }}>
            <td style={{
              padding: '10px 14px', width: '35%',
              fontFamily: "'JetBrains Mono',monospace", fontSize: 11,
              color: t.textMuted, fontWeight: 700, letterSpacing: 0.5,
            }}>{key}</td>
            <td style={{
              padding: '10px 14px',
              fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text,
              wordBreak: 'break-word',
            }}>{val}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/* ── Pill ───────────────────────────────────── */
export function Pill({ label, color, theme }) {
  const t = THEMES[theme];
  const c = color || t.accent;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '3px 12px', borderRadius: 20,
      background: `${c}22`, color: c,
      border: `1px solid ${c}44`,
      fontFamily: "'JetBrains Mono',monospace",
      fontSize: 10, fontWeight: 700, letterSpacing: 1,
    }}>
      {label}
    </span>
  );
}
