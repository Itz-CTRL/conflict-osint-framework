// src/components/ThemeButton.jsx
import { useState, useRef, useEffect, useCallback } from 'react';
import { THEMES, THEME_ORDER } from '../themes';

export default function ThemeButton({ currentTheme, onTheme }) {
  const t = THEMES[currentTheme];
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ x: null, y: null }); // null = default bottom-right
  const dragging = useRef(false);
  const offset = useRef({ x: 0, y: 0 });
  const btnRef = useRef(null);

  // Init position bottom-right
  useEffect(() => {
    setPos({ x: window.innerWidth - 70, y: window.innerHeight - 70 });
  }, []);

  const onMouseDown = useCallback((e) => {
    if (e.button !== 0) return;
    dragging.current = true;
    const rect = btnRef.current.getBoundingClientRect();
    offset.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    e.preventDefault();
  }, []);

  const onMouseMove = useCallback((e) => {
    if (!dragging.current) return;
    const x = Math.max(0, Math.min(window.innerWidth - 52, e.clientX - offset.current.x));
    const y = Math.max(0, Math.min(window.innerHeight - 52, e.clientY - offset.current.y));
    setPos({ x, y });
  }, []);

  const onMouseUp = useCallback(() => { dragging.current = false; }, []);

  useEffect(() => {
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [onMouseMove, onMouseUp]);

  // Touch support
  const onTouchStart = useCallback((e) => {
    dragging.current = true;
    const touch = e.touches[0];
    const rect = btnRef.current.getBoundingClientRect();
    offset.current = { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
  }, []);

  const onTouchMove = useCallback((e) => {
    if (!dragging.current) return;
    const touch = e.touches[0];
    const x = Math.max(0, Math.min(window.innerWidth - 52, touch.clientX - offset.current.x));
    const y = Math.max(0, Math.min(window.innerHeight - 52, touch.clientY - offset.current.y));
    setPos({ x, y });
  }, []);

  if (pos.x === null) return null;

  return (
    <div
      style={{
        position: 'fixed',
        left: pos.x,
        top: pos.y,
        zIndex: 9999,
        userSelect: 'none',
      }}
    >
      {/* Palette panel */}
      {open && (
        <div
          className="animate-scaleIn"
          style={{
            position: 'absolute',
            bottom: 58,
            right: 0,
            background: t.surface,
            border: `1px solid ${t.border}`,
            borderRadius: 14,
            padding: '10px 8px',
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
            boxShadow: t.shadow,
            minWidth: 160,
          }}
        >
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textSub, letterSpacing: 2, padding: '2px 8px 6px', borderBottom: `1px solid ${t.border}` }}>
            SELECT THEME
          </div>
          {THEME_ORDER.map((key) => {
            const th = THEMES[key];
            return (
              <button
                key={key}
                onClick={() => { onTheme(key); setOpen(false); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px', borderRadius: 8,
                  border: currentTheme === key ? `1px solid ${t.accent}` : '1px solid transparent',
                  background: currentTheme === key ? `${t.accent}22` : 'transparent',
                  cursor: 'pointer', color: t.text,
                  fontFamily: "'Sora',sans-serif", fontSize: 13, fontWeight: 600,
                  textAlign: 'left', width: '100%',
                }}
              >
                {/* Color swatch */}
                <span style={{
                  width: 20, height: 20, borderRadius: 6,
                  background: th.accentGrad, flexShrink: 0,
                  border: `2px solid ${th.border}`,
                  boxShadow: `0 0 6px ${th.accent}66`,
                }} />
                {th.name}
              </button>
            );
          })}
        </div>
      )}

      {/* Main button */}
      <button
        ref={btnRef}
        onMouseDown={onMouseDown}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={() => { dragging.current = false; }}
        onClick={() => setOpen((o) => !o)}
        title="Change Theme"
        style={{
          width: 48, height: 48, borderRadius: '50%',
          background: t.accentGrad,
          border: `2px solid ${t.border}`,
          cursor: dragging.current ? 'grabbing' : 'grab',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, color: '#fff',
          boxShadow: `0 4px 20px ${t.accent}66, 0 0 0 2px ${t.surface}`,
          transition: 'box-shadow 0.2s',
        }}
      >
        🎨
      </button>
    </div>
  );
}
