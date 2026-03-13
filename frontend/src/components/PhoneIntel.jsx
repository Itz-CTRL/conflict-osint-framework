// src/components/PhoneIntel.jsx
// Phone Intelligence UI — standalone lookup separate from investigations.
// Shows: normalized number, carrier, country, line type, breach presence.
import { useState, useRef, useEffect } from 'react';
import { COUNTRY_CODES } from './CountryCodePicker';
import { api } from '../utils/api';
import { THEMES } from '../themes';
import { Card, SectionTitle, Alert, Spinner, EmptyState, Pill } from './UI';

// ── Validation ─────────────────────────────────
function validatePhoneInput(phone) {
  if (!phone || !phone.trim()) return 'Phone number is required.';
  const digits = phone.replace(/\D/g, '');
  if (digits.length < 10) return 'Phone number must contain at least 10 digits.';
  if (digits.length > 15) return 'Phone number is too long (max 15 digits).';
  return null;
}

function normalizePhone(phone, countryObj) {
  const cleaned = phone.replace(/[^\d+]/g, '');
  if (cleaned.startsWith('+')) return cleaned;
  if (countryObj?.dial) {
    const dialCode = countryObj.dial.replace(/\D/g, '');
    const local = cleaned.replace(/^0+/, '');
    return `+${dialCode}${local}`;
  }
  return cleaned.length > 5 ? `+${cleaned}` : '';
}

function detectCountry(normalizedPhone) {
  if (!normalizedPhone?.startsWith('+')) return null;
  const match = normalizedPhone.match(/^\+(\d{1,4})/);
  if (!match) return null;
  return COUNTRY_CODES.find(c => c.dial === `+${match[1]}`) || null;
}

// ── Line type display ───────────────────────────
const LINE_TYPE_LABELS = {
  mobile:   { label: 'Mobile',   color: '#16a34a' },
  landline: { label: 'Landline', color: '#2563eb' },
  voip:     { label: 'VoIP',     color: '#9333ea' },
  toll_free:{ label: 'Toll-Free',color: '#0891b2' },
  premium:  { label: 'Premium',  color: '#d97706' },
  unknown:  { label: 'Unknown',  color: '#6b7280' },
};

export default function PhoneIntel({ theme }) {
  const t = THEMES[theme || 'dark'];

  const [phoneInput,      setPhoneInput]      = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [countrySearch,   setCountrySearch]   = useState('');
  const [showDrop,        setShowDrop]        = useState(false);
  const [detectedCountry, setDetectedCountry] = useState(null);
  const scanMode = 'light';
  const [isLoading,       setIsLoading]       = useState(false);
  const [progress,        setProgress]        = useState(0);
  const [result,          setResult]          = useState(null);
  const [error,           setError]           = useState('');

  const dropRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setShowDrop(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handlePhoneChange = (e) => {
    const val = e.target.value;
    setPhoneInput(val);
    setError('');
    const normalized = normalizePhone(val, null);
    setDetectedCountry(detectCountry(normalized));
  };

  const handleScan = async () => {
    const validationError = validatePhoneInput(phoneInput);
    if (validationError) { setError(validationError); return; }

    setIsLoading(true);
    setError('');
    setResult(null);
    setProgress(0);

    try {
      const countryObj = selectedCountry
        ? COUNTRY_CODES.find(c => c.name === selectedCountry)
        : detectedCountry;

      const normalized = normalizePhone(phoneInput, countryObj);
      if (!normalized) {
        setError('Could not format phone number. Please include the country code (e.g. +1, +44).');
        setIsLoading(false);
        return;
      }

      // Fake progress
      const interval = setInterval(() => {
        setProgress(p => p < 85 ? p + Math.random() * 18 : p);
      }, 350);

      const res = await api.phoneLookup(normalized, countryObj?.code || null, scanMode);

      clearInterval(interval);
      setProgress(100);

      if (res.status === 'success' && res.data) {
        setResult({
          ...res.data,
          normalizedPhone: normalized,
          scanMode,
          scannedAt: new Date().toLocaleString(),
        });
      } else {
        setError(res.message || 'Lookup failed. Please try again.');
      }
    } catch (err) {
      setError(`Scan error: ${err.message}`);
    } finally {
      setIsLoading(false);
      setTimeout(() => setProgress(0), 600);
    }
  };

  const handleClear = () => {
    setPhoneInput('');
    setSelectedCountry('');
    setCountrySearch('');
    setDetectedCountry(null);
    setResult(null);
    setError('');
    setProgress(0);
  };

  const handleExport = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `phone-intel-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredCountries = COUNTRY_CODES.filter(c =>
    c.name.toLowerCase().includes(countrySearch.toLowerCase()) ||
    c.dial.includes(countrySearch)
  );

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 860, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 24, paddingBottom: 20, borderBottom: `1px solid ${t.border}` }}>
        <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 20, color: t.text, margin: '0 0 6px 0' }}>
          Phone Intelligence
        </h2>
        <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.textMuted, margin: 0 }}>
          Lookup carrier, country, line type, and breach data for any phone number. Include country code for best results.
        </p>
      </div>

      {/* Input Panel */}
      <Card theme={theme} style={{ padding: 24, marginBottom: 20 }}>
        <SectionTitle icon="◉" title="Phone Lookup" theme={theme} />

        {/* Phone number input */}
        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle(t)}>Phone Number *</label>
          <input
            type="tel"
            value={phoneInput}
            onChange={handlePhoneChange}
            onKeyDown={e => e.key === 'Enter' && !isLoading && handleScan()}
            placeholder="+1 555 000 0000  ·  include country code"
            disabled={isLoading}
            style={inputStyle(t, isLoading)}
            onFocus={e => { e.target.style.borderColor = t.accent; e.target.style.boxShadow = `0 0 0 3px ${t.accent}22`; }}
            onBlur={e => { e.target.style.borderColor = t.border; e.target.style.boxShadow = 'none'; }}
          />
          {detectedCountry && !selectedCountry && (
            <div style={{ marginTop: 5, fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted }}>
              Detected: {detectedCountry.flag} {detectedCountry.name} ({detectedCountry.dial})
            </div>
          )}
        </div>

        {/* Country selector */}
        <div style={{ marginBottom: 16, position: 'relative' }} ref={dropRef}>
          <label style={labelStyle(t)}>Country (Optional — auto-detected from number)</label>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              value={selectedCountry || countrySearch}
              onChange={e => { setCountrySearch(e.target.value); setSelectedCountry(''); setShowDrop(true); }}
              onFocus={() => { setCountrySearch(''); setShowDrop(true); }}
              placeholder="Select country…"
              disabled={isLoading}
              style={{
                ...inputStyle(t, isLoading),
                borderBottomLeftRadius: showDrop ? 0 : 8,
                borderBottomRightRadius: showDrop ? 0 : 8,
                borderColor: showDrop ? t.accent : t.border,
              }}
            />
            {selectedCountry && (
              <button
                onClick={() => { setSelectedCountry(''); setCountrySearch(''); }}
                style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', fontSize: 14, padding: 0 }}
              >
                ✕
              </button>
            )}
            {showDrop && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, right: 0,
                maxHeight: 220, overflowY: 'auto',
                background: t.surface, border: `1px solid ${t.accent}55`,
                borderTop: 'none', borderRadius: '0 0 8px 8px',
                boxShadow: '0 8px 20px rgba(0,0,0,0.2)', zIndex: 100,
              }}>
                {filteredCountries.map(c => (
                  <div
                    key={c.code}
                    onClick={() => { setSelectedCountry(c.name); setCountrySearch(c.name); setShowDrop(false); }}
                    style={{
                      padding: '8px 14px', cursor: 'pointer',
                      display: 'flex', gap: 10, alignItems: 'center',
                      borderBottom: `1px solid ${t.borderLight}`,
                      background: selectedCountry === c.name ? `${t.accent}22` : 'transparent',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = `${t.accent}11`; }}
                    onMouseLeave={e => { e.currentTarget.style.background = selectedCountry === c.name ? `${t.accent}22` : 'transparent'; }}
                  >
                    <span style={{ fontSize: 16 }}>{c.flag}</span>
                    <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.text, flex: 1 }}>{c.name}</span>
                    <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted }}>{c.dial}</span>
                  </div>
                ))}
                {filteredCountries.length === 0 && (
                  <div style={{ padding: '10px 14px', fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, textAlign: 'center' }}>
                    No match
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 10 }}>
          <button
            onClick={handleScan}
            disabled={isLoading || !phoneInput.trim()}
            style={{
              padding: '12px',
              background: isLoading || !phoneInput.trim() ? t.border : t.accentGrad,
              color: '#fff', border: 'none', borderRadius: 8,
              fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14,
              cursor: isLoading || !phoneInput.trim() ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: isLoading ? 'none' : `0 4px 16px ${t.accent}44`,
              transition: 'all 0.2s',
            }}
          >
            {isLoading ? <><Spinner size={16} /> Scanning…</> : '◉ Start Scan'}
          </button>
          <button onClick={handleClear} disabled={isLoading} style={secondaryBtnStyle(t, isLoading)}>
            Clear
          </button>
          <button onClick={handleExport} disabled={!result || isLoading} style={secondaryBtnStyle(t, !result || isLoading)}>
            Export JSON
          </button>
        </div>

        {/* Progress bar */}
        {isLoading && progress > 0 && (
          <div style={{ marginTop: 14, height: 4, background: t.borderLight, borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', background: t.accentGrad, width: `${progress}%`, transition: 'width 0.3s', borderRadius: 2 }} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ marginTop: 14 }}>
            <Alert type="danger" theme={theme}>{error}</Alert>
          </div>
        )}
      </Card>

      {/* Result */}
      {result && !isLoading && <PhoneResult data={result} theme={theme} />}

      {/* Empty */}
      {!result && !isLoading && (
        <EmptyState
          icon="◉"
          message="Enter a phone number above to begin intelligence gathering."
          theme={theme}
        />
      )}
    </div>
  );
}

/* ── Phone Result ───────────────────────────── */
function PhoneResult({ data, theme }) {
  const t = THEMES[theme];

  const lineType = (data.line_type || data.type || 'unknown').toLowerCase();
  const lineInfo = LINE_TYPE_LABELS[lineType] || LINE_TYPE_LABELS.unknown;

  // Breach detection — backend may return breach_data, in_breach, or breaches array
  const inBreach = !!(
    data.in_breach ||
    data.breach_presence ||
    (Array.isArray(data.breach_data) && data.breach_data.length > 0) ||
    (Array.isArray(data.breaches)    && data.breaches.length    > 0)
  );
  const breachList = data.breach_data || data.breaches || [];

  const infoFields = [
    { label: 'NORMALIZED NUMBER', value: data.normalizedPhone || data.number },
    { label: 'COUNTRY',           value: data.country         },
    { label: 'COUNTRY CODE',      value: data.country_code    },
    { label: 'REGION',            value: data.region          },
    { label: 'CARRIER',           value: data.carrier         },
    { label: 'TIMEZONE',          value: data.timezone        },
    { label: 'VALID',             value: data.valid ? '✓ Yes' : '✗ No' },
  ].filter(f => f.value);

  return (
    <Card theme={theme} style={{ padding: 24 }}>
      <SectionTitle icon="◎" title="Intelligence Report" theme={theme} />

      {/* Number header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20,
        padding: '14px 16px', background: t.surfaceAlt,
        border: `1px solid ${t.border}`, borderRadius: 10,
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 18, fontWeight: 800, color: t.text, letterSpacing: 2 }}>
            {data.normalizedPhone || data.number}
          </div>
          <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, marginTop: 2 }}>
            {[data.country, data.carrier].filter(Boolean).join(' · ')}
          </div>
        </div>
        {/* Line type badge */}
        <span style={{
          padding: '4px 12px', borderRadius: 20,
          background: `${lineInfo.color}22`, color: lineInfo.color,
          border: `1px solid ${lineInfo.color}55`,
          fontFamily: "'JetBrains Mono',monospace", fontSize: 10, fontWeight: 700, letterSpacing: 1,
        }}>
          {lineInfo.label.toUpperCase()}
        </span>
        {/* Breach badge */}
        <span style={{
          padding: '4px 12px', borderRadius: 20,
          background: inBreach ? `${t.riskHigh}22` : `${t.riskLow}22`,
          color: inBreach ? t.riskHigh : t.riskLow,
          border: `1px solid ${inBreach ? t.riskHigh : t.riskLow}55`,
          fontFamily: "'JetBrains Mono',monospace", fontSize: 10, fontWeight: 700, letterSpacing: 1,
        }}>
          {inBreach ? '⚠ BREACH' : '✓ CLEAN'}
        </span>
      </div>

      {/* Info grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
        gap: 10, marginBottom: 20,
      }}>
        {infoFields.map(f => (
          <div key={f.label} style={{
            padding: '10px 12px', background: t.surfaceAlt,
            border: `1px solid ${t.border}`, borderRadius: 8,
          }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 8, color: t.textMuted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 4 }}>
              {f.label}
            </div>
            <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, fontWeight: 600, color: t.text, wordBreak: 'break-word' }}>
              {f.value}
            </div>
          </div>
        ))}
      </div>

      {/* Breach details */}
      {inBreach && breachList.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.riskHigh, letterSpacing: 2, marginBottom: 8, fontWeight: 700 }}>
            BREACH RECORDS
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {breachList.map((b, i) => (
              <Pill key={i} label={typeof b === 'string' ? b : b.source || b.name || 'breach'} color={t.riskHigh} theme={theme} />
            ))}
          </div>
        </div>
      )}

      {/* Social presence */}
      {data.social_presence?.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textSub, letterSpacing: 2, marginBottom: 8, fontWeight: 700 }}>
            SOCIAL PRESENCE
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {data.social_presence.map(s => (
              <Pill key={s} label={s} theme={theme} />
            ))}
          </div>
        </div>
      )}

      {/* Scan meta */}
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, letterSpacing: 1, marginTop: 8 }}>
        Scanned {data.scannedAt}
      </div>
    </Card>
  );
}

/* ── Shared styles ──────────────────────────── */
function labelStyle(t) {
  return {
    display: 'block',
    fontFamily: "'JetBrains Mono',monospace",
    fontSize: 10, fontWeight: 700,
    color: t.textSub, letterSpacing: 1.5,
    marginBottom: 7, textTransform: 'uppercase',
  };
}

function inputStyle(t, disabled) {
  return {
    width: '100%', padding: '11px 14px',
    background: t.inputBg, border: `1px solid ${t.border}`,
    borderRadius: 8, color: t.text,
    fontFamily: "'JetBrains Mono',monospace", fontSize: 14,
    outline: 'none', boxSizing: 'border-box',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    opacity: disabled ? 0.6 : 1, cursor: disabled ? 'not-allowed' : 'text',
    letterSpacing: 1,
  };
}

function secondaryBtnStyle(t, disabled) {
  return {
    padding: '12px',
    background: t.surfaceAlt, color: disabled ? t.textMuted : t.text,
    border: `1px solid ${t.border}`, borderRadius: 8,
    fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1, transition: 'all 0.15s',
  };
}
