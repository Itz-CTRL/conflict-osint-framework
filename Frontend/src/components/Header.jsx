// src/components/Header.jsx
import { useState, useEffect } from 'react';
import { THEMES } from '../themes';
import { api } from '../utils/api';

export default function Header({ theme, online }) {
  const t = THEMES[theme];
  const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const [time, setTime] = useState(now);

  useEffect(() => {
    const id = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header style={{
      background: t.navBg,
      borderBottom: `1px solid ${t.border}`,
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: 58,
      position: 'sticky',
      top: 0,
      zIndex: 200,
      backdropFilter: 'blur(12px)',
    }}>
      {/* Logo - Left side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 36, height: 36,
          background: t.accentGrad,
          borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18, fontWeight: 800, color: '#fff',
          boxShadow: `0 4px 16px ${t.accent}66`,
          flexShrink: 0,
        }}>◈</div>
        <div>
          <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 14, color: t.text, letterSpacing: 2 }}>
            SOKO AERIAL
          </div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 8, color: t.textSub, letterSpacing: 3, marginTop: -1 }}>
            OSINT FRAMEWORK
          </div>
        </div>
      </div>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        {/* Clock */}
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: t.textMuted, letterSpacing: 1 }}>
          {time}
        </div>

        {/* Backend status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div className="blink" style={{
            width: 7, height: 7, borderRadius: '50%',
            background: online ? t.riskLow : t.riskHigh,
            boxShadow: `0 0 8px ${online ? t.riskLow : t.riskHigh}`,
          }} />
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, letterSpacing: 1 }}>
            {online ? 'BACKEND ONLINE' : 'BACKEND OFFLINE'}
          </span>
        </div>

        {/* Role badge */}
        <div style={{
          padding: '4px 14px', borderRadius: 20,
          background: t.surfaceAlt, border: `1px solid ${t.border}`,
          fontFamily: "'Sora',sans-serif", fontSize: 12, fontWeight: 600,
          color: t.textMid, display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <span style={{ fontSize: 10 }}>▸</span> Analyst
        </div>
      </div>
    </header>
  );
}
