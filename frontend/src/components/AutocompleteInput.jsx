// src/components/AutocompleteInput.jsx
/**
 * Debounced username input with live suggestion dropdown.
 * Calls /api/username_suggestions?q=<query> after 300ms pause.
 * Keyboard: ↑↓ navigate · Enter select · Escape close
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { THEMES } from '../themes';
import { api } from '../utils/api';

export default function AutocompleteInput({
  label,
  placeholder = 'e.g. johndoe, elonmusk',
  value,
  onChange,
  disabled,
  theme,
}) {
  const t = THEMES[theme];

  const [suggestions, setSuggestions] = useState([]);
  const [open,        setOpen]        = useState(false);
  const [cursor,      setCursor]      = useState(-1);
  const [fetching,    setFetching]    = useState(false);
  const [focused,     setFocused]     = useState(false);

  const inputRef    = useRef(null);
  const dropRef     = useRef(null);
  const debounceRef = useRef(null);

  /* ── Fetch suggestions ──────────────────────────────── */
  const fetchSuggestions = useCallback(async (q) => {
    if (q.length < 2) { setSuggestions([]); setOpen(false); return; }
    setFetching(true);
    try {
      const res = await api.usernameSuggestions(q);
      const list = res.suggestions || res.data || [];
      setSuggestions(list.slice(0, 10));
      setOpen(list.length > 0);
    } catch {
      // Silently ignore — autocomplete is a nicety, not required
      setSuggestions([]);
      setOpen(false);
    } finally {
      setFetching(false);
    }
  }, []);

  /* ── Debounce on value change ───────────────────────── */
  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (!value || value.length < 2) { setSuggestions([]); setOpen(false); return; }
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 300);
    return () => clearTimeout(debounceRef.current);
  }, [value, fetchSuggestions]);

  /* ── Click outside to close ────────────────────────── */
  useEffect(() => {
    const handler = (e) => {
      if (
        inputRef.current && !inputRef.current.contains(e.target) &&
        dropRef.current  && !dropRef.current.contains(e.target)
      ) {
        setOpen(false);
        setCursor(-1);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  /* ── Keyboard navigation ────────────────────────────── */
  const handleKeyDown = (e) => {
    if (!open || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setCursor(c => Math.min(c + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setCursor(c => Math.max(c - 1, 0));
    } else if (e.key === 'Enter' && cursor >= 0) {
      e.preventDefault();
      selectSuggestion(suggestions[cursor]);
    } else if (e.key === 'Escape') {
      setOpen(false);
      setCursor(-1);
    }
  };

  const selectSuggestion = (s) => {
    const val = typeof s === 'string' ? s : (s.username || s.label || s);
    onChange(val);
    setSuggestions([]);
    setOpen(false);
    setCursor(-1);
    inputRef.current?.blur();
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Label */}
      {label && (
        <label style={{
          display: 'block',
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 10, fontWeight: 700,
          color: t.textSub, letterSpacing: 1.5,
          marginBottom: 6, textTransform: 'uppercase',
        }}>
          {label} <span style={{ color: t.riskHigh }}>*</span>
        </label>
      )}

      {/* Input */}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={e => { onChange(e.target.value); setCursor(-1); }}
          onKeyDown={handleKeyDown}
          onFocus={() => { setFocused(true); if (suggestions.length) setOpen(true); }}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
          spellCheck={false}
          style={{
            width: '100%',
            padding: '11px 40px 11px 14px',
            background: t.inputBg,
            border: `1px solid ${focused ? t.accent : open ? t.accent + 'aa' : t.border}`,
            borderRadius: open ? '8px 8px 0 0' : 8,
            color: t.text,
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 14, letterSpacing: 0.5,
            outline: 'none',
            boxSizing: 'border-box',
            transition: 'border-color 0.2s, box-shadow 0.2s',
            boxShadow: focused ? `0 0 0 3px ${t.accent}22` : 'none',
            opacity: disabled ? 0.6 : 1,
          }}
        />

        {/* Loading indicator */}
        {fetching && (
          <span style={{
            position: 'absolute', right: 12,
            width: 14, height: 14,
            border: `2px solid ${t.accent}33`,
            borderTopColor: t.accent,
            borderRadius: '50%',
            animation: 'spin 0.7s linear infinite',
          }} />
        )}
        {/* Search icon when idle */}
        {!fetching && (
          <span style={{
            position: 'absolute', right: 12,
            fontSize: 13, color: t.textMuted,
            pointerEvents: 'none',
          }}>🔍</span>
        )}
      </div>

      {/* Dropdown */}
      {open && suggestions.length > 0 && (
        <div
          ref={dropRef}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0, right: 0,
            background: t.surface,
            border: `1px solid ${t.accent}88`,
            borderTop: 'none',
            borderRadius: '0 0 8px 8px',
            boxShadow: `0 8px 24px rgba(0,0,0,0.25)`,
            zIndex: 1000,
            overflow: 'hidden',
          }}
        >
          {suggestions.map((s, i) => {
            const label = typeof s === 'string' ? s : (s.username || s.label || String(s));
            const sub   = typeof s === 'object' ? (s.source || s.platform || '') : '';
            const isCursor = i === cursor;
            return (
              <div
                key={i}
                onMouseDown={(e) => { e.preventDefault(); selectSuggestion(s); }}
                onMouseEnter={() => setCursor(i)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '10px 14px',
                  background: isCursor ? `${t.accent}18` : 'transparent',
                  borderLeft: `3px solid ${isCursor ? t.accent : 'transparent'}`,
                  cursor: 'pointer',
                  transition: 'background 0.1s',
                }}
              >
                <span style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: `${t.accent}22`, border: `1px solid ${t.accent}44`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: "'Sora',sans-serif", fontSize: 11, fontWeight: 700, color: t.accent,
                  flexShrink: 0,
                }}>
                  {label[0]?.toUpperCase() || '?'}
                </span>
                <div style={{ minWidth: 0 }}>
                  <div style={{
                    fontFamily: "'Sora',sans-serif", fontSize: 13, fontWeight: 600,
                    color: isCursor ? t.accent : t.text,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    @{label}
                  </div>
                  {sub && (
                    <div style={{
                      fontFamily: "'JetBrains Mono',monospace",
                      fontSize: 9, color: t.textMuted, marginTop: 1,
                    }}>
                      {sub}
                    </div>
                  )}
                </div>
                {isCursor && (
                  <span style={{ marginLeft: 'auto', fontSize: 9, color: t.accent, fontFamily: "'JetBrains Mono',monospace" }}>
                    ↵
                  </span>
                )}
              </div>
            );
          })}
          <div style={{
            padding: '6px 14px',
            borderTop: `1px solid ${t.borderLight}`,
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 8, color: t.textMuted, letterSpacing: 1,
          }}>
            ↑ ↓ navigate · ↵ select · ESC close
          </div>
        </div>
      )}
    </div>
  );
}
