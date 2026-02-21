// src/components/UI.jsx
import { THEMES } from '../themes';

/* ── Risk Badge ─────────────────────────────── */
export function RiskBadge({ level, theme }) {
  const t = THEMES[theme];
  const map = {
    HIGH:    { bg: t.riskHigh, label: 'HIGH' },
    MEDIUM:  { bg: t.riskMed,  label: 'MED'  },
    LOW:     { bg: t.riskLow,  label: 'LOW'  },
    UNKNOWN: { bg: t.textMuted, label: '—'   },
  };
  const r = map[level?.toUpperCase()] || map.UNKNOWN;
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
    pending:   { bg: t.textMuted, label: 'PENDING'  },
    failed:    { bg: t.riskHigh, label: 'FAILED'    },
  };
  const s = map[status?.toLowerCase()] || map.pending;
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
export function SectionTitle({ icon, title, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
      {icon && <span style={{ color: t.accent, fontSize: 16 }}>{icon}</span>}
      <span style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 15, color: t.text }}>{title}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(to right,${t.border},transparent)`, marginLeft: 8 }} />
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
