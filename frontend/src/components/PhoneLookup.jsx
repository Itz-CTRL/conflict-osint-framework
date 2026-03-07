// src/components/PhoneLookup.jsx
import { useState } from 'react';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { Card, SectionTitle, Alert, Spinner, EmptyState, DataTable, Pill } from './UI';
import { useCaseContext } from '../contexts/CaseContext';
import RiskScore from './RiskScore';

export default function PhoneLookup({ theme }) {
  const t = THEMES[theme];
  const { addPhoneLookup, phoneHistory } = useCaseContext();

  const [phone, setPhone]   = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError]   = useState('');
  const [focused, setFocused] = useState(false);

  const handleLookup = async () => {
    const num = phone.trim();
    if (!num) { setError('Please enter a phone number.'); return; }
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await api.phoneScan(num);
      setResult(res.data || {});
      addPhoneLookup(res.data || {});
    } catch (e) {
      setError(`Lookup failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 900, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 20, color: t.text, margin: 0, marginBottom: 6 }}>
          📱 Phone Intelligence
        </h2>
        <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.textMuted, margin: 0 }}>
          Lookup carrier, country, timezone, social presence and risk score for any phone number.
        </p>
      </div>

      {/* Input */}
      <Card theme={theme} style={{ padding: 24, marginBottom: 20 }}>
        <SectionTitle icon="📡" title="Phone Number Lookup" theme={theme} />

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <input
            type="tel"
            value={phone}
            onChange={e => setPhone(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && handleLookup()}
            placeholder="+1 555 000 0000  |  Include country code"
            disabled={loading}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            style={{
              flex: 1, minWidth: 260,
              padding: '12px 16px',
              background: t.inputBg,
              border: `1px solid ${focused ? t.accent : t.border}`,
              borderRadius: 10,
              color: t.text,
              fontFamily: "'JetBrains Mono',monospace",
              fontSize: 15,
              outline: 'none',
              letterSpacing: 1,
              transition: 'border-color 0.2s, box-shadow 0.2s',
              boxShadow: focused ? `0 0 0 3px ${t.accent}22` : 'none',
            }}
          />
          <button
            onClick={handleLookup}
            disabled={loading}
            style={{
              padding: '12px 28px',
              background: loading ? t.border : t.accentGrad,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontFamily: "'Sora',sans-serif",
              fontWeight: 700,
              fontSize: 14,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: loading ? 'none' : `0 4px 20px ${t.accent}44`,
              whiteSpace: 'nowrap',
              transition: 'all 0.2s',
            }}
          >
            {loading ? <><Spinner size={16} /> Scanning...</> : '📡 Scan'}
          </button>
        </div>

        {error && <Alert type="danger" theme={theme}>{error}</Alert>}

        <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted, marginTop: 8 }}>
          Always include country code (e.g. +1 for US, +44 for UK, +233 for Ghana).
          Public intelligence only — no private data access.
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 48, gap: 16 }}>
          <Spinner size={32} color={t.accent} />
          <div>
            <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>
              Querying Intelligence Sources...
            </div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, marginTop: 4 }}>
              Carrier lookup · Geo-intelligence · Social presence scan
            </div>
          </div>
        </div>
      )}

      {/* Result */}
      {result && !loading && <PhoneResult data={result} theme={theme} />}

      {/* History */}
      {phoneHistory.length > 0 && !loading && (
        <Card theme={theme} style={{ padding: 24, marginTop: 20 }}>
          <SectionTitle icon="🕐" title="Recent Lookups" theme={theme} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {phoneHistory.map((h, i) => (
              <HistoryRow key={i} data={h} theme={theme} onSelect={() => setResult(h)} />
            ))}
          </div>
        </Card>
      )}

      {/* Empty */}
      {!result && !loading && phoneHistory.length === 0 && (
        <EmptyState icon="📱" message="Enter a phone number above to begin intelligence gathering." theme={theme} />
      )}
    </div>
  );
}

/* ── Phone Result ───────────────────────────── */
function PhoneResult({ data, theme }) {
  const t = THEMES[theme];

  const SOCIAL_COLORS = {
    WhatsApp: '#25D366',
    Telegram: '#0088CC',
    Signal:   '#3A76F0',
    Viber:    '#7360F2',
    LINE:     '#00C300',
  };

  const rows = [
    ['Number',       data.number],
    ['Country',      data.country || '—'],
    ['Country Code', data.country_code || '—'],
    ['Region',       data.region || '—'],
    ['Carrier',      data.carrier || '—'],
    ['Timezone',     data.timezone || '—'],
    ['Valid',        data.valid ? '✓ Yes' : '✗ No'],
    ['Confidence',   data.confidence !== undefined ? `${Math.round(data.confidence * 100)}%` : '—'],
  ].filter(r => r[1]);

  return (
    <div className="animate-slideDown" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 16, alignItems: 'start' }}>

        {/* Details */}
        <Card theme={theme} style={{ padding: 24 }}>
          <SectionTitle icon="📋" title="Intelligence Report" theme={theme} />

          <div style={{
            display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20,
            padding: '14px 16px',
            background: t.surfaceAlt,
            border: `1px solid ${t.border}`,
            borderRadius: 10,
          }}>
            <span style={{ fontSize: 24 }}>📱</span>
            <div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 16, fontWeight: 700, color: t.text, letterSpacing: 2 }}>
                {data.number}
              </div>
              <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, marginTop: 2 }}>
                {data.country || '—'} · {data.carrier || '—'}
              </div>
            </div>
          </div>

          <DataTable rows={rows} theme={theme} />

          {/* Social Presence */}
          <div style={{ marginTop: 20 }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 10 }}>
              SOCIAL PRESENCE
            </div>
            {data.social_presence?.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {data.social_presence.map(s => (
                  <Pill
                    key={s}
                    label={s}
                    color={SOCIAL_COLORS[s] || t.accent}
                    theme={theme}
                  />
                ))}
              </div>
            ) : (
              <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.textMuted }}>
                No social presence detected
              </div>
            )}
          </div>

          {/* Emails Found */}
          {data.emails_found?.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 10 }}>
                ASSOCIATED EMAILS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {data.emails_found.map((email, i) => (
                  <div key={i} style={{
                    padding: '8px 12px',
                    background: t.surfaceAlt,
                    border: `1px solid ${t.border}`,
                    borderRadius: 6,
                    fontFamily: "'JetBrains Mono',monospace",
                    fontSize: 12,
                    color: t.textSub,
                  }}>
                    📧 {email}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Risk Score */}
        <Card theme={theme} style={{ padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <SectionTitle icon="⚠" title="Risk Score" theme={theme} />
          <RiskScore score={data.risk_score || 0} theme={theme} />

          <div style={{ marginTop: 16, width: '100%' }}>
            <RiskFactorBar label="Social Exposure" score={(data.social_presence?.length || 0) * 25} theme={theme} />
            <RiskFactorBar label="Email Links" score={(data.emails_found?.length || 0) * 20} theme={theme} />
            <RiskFactorBar label="Base Risk" score={20} theme={theme} />
          </div>
        </Card>
      </div>
    </div>
  );
}

function RiskFactorBar({ label, score, theme }) {
  const t = THEMES[theme];
  const pct = Math.min(100, score);
  const color = pct >= 67 ? t.riskHigh : pct >= 34 ? t.riskMed : t.riskLow;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted }}>{label}</span>
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color, fontWeight: 700 }}>{pct}</span>
      </div>
      <div style={{ height: 4, background: t.borderLight, borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  );
}

function HistoryRow({ data, theme, onSelect }) {
  const t = THEMES[theme];
  const riskColor =
    (data.risk_score || 0) >= 67 ? t.riskHigh :
    (data.risk_score || 0) >= 34 ? t.riskMed  : t.riskLow;

  return (
    <div
      onClick={onSelect}
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto auto',
        gap: 16,
        alignItems: 'center',
        padding: '12px 0',
        borderBottom: `1px solid ${t.borderLight}`,
        cursor: 'pointer',
        transition: 'background 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = t.rowHover}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 13, color: t.text }}>{data.number}</div>
        <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted, marginTop: 2 }}>
          {data.country} · {data.carrier || '—'}
        </div>
      </div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: riskColor, fontWeight: 700 }}>
        Risk: {data.risk_score || 0}
      </div>
      <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted }}>→</span>
    </div>
  );
}
