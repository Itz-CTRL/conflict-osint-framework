// src/components/Ticker.jsx
import { THEMES } from '../themes';

const ITEMS = [
  '⚠ LIVE MONITORING ACTIVE',
  '• Bawku Region — Elevated Misinformation Risk',
  '• Public Data Only — OSINT Framework',
  '• Platforms: Facebook · Instagram · TikTok · Reddit · GitHub · Twitter/X · YouTube · LinkedIn · Pinterest · Telegram',
  '• All findings are for research and educational purposes only',
  '• Handover to authorities upon confirmed threat',
];

export default function Ticker({ theme }) {
  const t = THEMES[theme];
  const text = ITEMS.join('    ');

  return (
    <div style={{
      background: t.tickerBg,
      borderBottom: `1px solid ${t.border}`,
      overflow: 'hidden',
      height: 28,
      display: 'flex',
      alignItems: 'center',
    }}>
      <div style={{
        animation: 'ticker 40s linear infinite',
        whiteSpace: 'nowrap',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 10,
        color: t.textSub,
        letterSpacing: 1,
        fontWeight: 600,
      }}>
        {text}&nbsp;&nbsp;&nbsp;&nbsp;{text}
      </div>
    </div>
  );
}
