// src/components/NewInvestigation.jsx
/**
 * New Investigation Creation Component
 * Features:
 * - Primary username input (required)
 * - Optional email/phone with auto-discovery
 * - Optional investigation filters (platform, location, account type, verification)
 * - Light/Deep scan depth selection
 * - Real-time progress tracking with phase messaging
 * - Responsive UI with Sora/JetBrains Mono fonts
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { useCaseContext } from '../contexts/CaseContext';
import { Card, SectionTitle, Alert, Spinner, ProgressBar, InputField } from './UI';
import AutocompleteInput from './AutocompleteInput';
import CountryCodePicker, { COUNTRY_CODES } from './CountryCodePicker';

const SCAN_PHASES = {
  light: [
    { at: 0,  label: 'Initialising scan engine...' },
    { at: 15, label: 'Checking platform registrations...' },
    { at: 40, label: 'Validating profile metadata...' },
    { at: 65, label: 'Running risk analysis...' },
    { at: 85, label: 'Building network graph...' },
    { at: 95, label: 'Finalising report...' },
  ],
  deep: [
    { at: 0,  label: 'Initialising deep scan engine...' },
    { at: 10, label: 'Cross-platform correlation...' },
    { at: 25, label: 'Email harvesting...' },
    { at: 40, label: 'Scrapy deep crawl initiated...' },
    { at: 55, label: 'Behavioural analysis...' },
    { at: 70, label: 'Network graph construction...' },
    { at: 82, label: 'Threat correlation...' },
    { at: 92, label: 'Generating report...' },
    { at: 97, label: 'Finalising...' },
  ],
};

const PLATFORMS = [
  'Twitter/X', 'Facebook', 'Instagram', 'TikTok', 'LinkedIn',
  'GitHub', 'YouTube', 'Reddit', 'Telegram', 'Pinterest',
  'Snapchat', 'WhatsApp', 'Discord', 'Twitch', 'Medium'
];

export default function NewInvestigation({ theme }) {
  const t = THEMES[theme];
  const navigate = useNavigate();
  const { startScan, updateProgress, completeScan } = useCaseContext();

  // Primary input
  const [username,    setUsername]    = useState('');
  const [email,       setEmail]       = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');         // local part
  const [dialCode,    setDialCode]    = useState('+233');     // Ghana default
  
  // Scan type
  const [scanType, setScanType] = useState('light'); // 'light' | 'deep'
  
  // Investigation filters
  const [platforms, setPlatforms] = useState([]);
  const [location, setLocation] = useState('');
  const [countrySearch, setCountrySearch] = useState('');
  const [showCountryDrop, setShowCountryDrop] = useState(false);
  const [accountType, setAccountType] = useState('');
  const [verified, setVerified] = useState(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState('');
  const [error, setError] = useState('');
  const [caseId, setCaseId] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  const timerRef = useRef(null);
  const countryDropRef = useRef(null);

  useEffect(() => () => clearInterval(timerRef.current), []);

  // Click outside country dropdown
  useEffect(() => {
    const handler = (e) => {
      if (countryDropRef.current && !countryDropRef.current.contains(e.target)) {
        setShowCountryDrop(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const startFakeProgress = (type) => {
    const phases = SCAN_PHASES[type];
    let pct = 0;
    setProgress(0);
    setPhase(phases[0].label);

    timerRef.current = setInterval(() => {
      pct = Math.min(pct + (type === 'light' ? 2.5 : 1.2), 97);
      setProgress(pct);
      const current = [...phases].reverse().find(p => pct >= p.at);
      if (current) setPhase(current.label);
      updateProgress(current?.label || 'Processing', pct, '');
    }, 800);
  };

  const stopProgress = () => {
    clearInterval(timerRef.current);
    setProgress(100);
    setPhase('Scan complete ✓');
    completeScan();
  };

  const handleSubmit = async () => {
    const name = username.trim();
    if (!name || name.length < 2) {
      setError('Username is required (minimum 2 characters).');
      return;
    }
    setError('');
    setLoading(true);
    setCaseId(null);

    try {
      // Start tracking scan
      startScan(scanType);

      // 1. Create investigation case
      setPhase('Creating investigation case...');
      setProgress(2);
      // Build full phone: dialCode + local number (strip leading 0 from local)
      const localNum = phoneNumber.trim().replace(/^0+/, '');
      const fullPhone = localNum ? `${dialCode}${localNum}` : null;

      const investigationData = {
        username: name,
        email: email.trim() || null,
        phone: fullPhone,
        filters: {
          platforms: platforms.length > 0 ? platforms : null,
          location: location || null,
          accountType: accountType || null,
          verified: verified
        }
      };

      const created = await api.createInvestigation(
        investigationData.username,
        investigationData.email || undefined,
        investigationData.phone || undefined,
        investigationData.filters
      );
      const id = created.case_id;
      setCaseId(id);

      // 2. Start fake progress
      startFakeProgress(scanType);

      // 3. Run the scan
      await api.startScan(id, scanType);

      // 4. Done
      stopProgress();

      setTimeout(() => navigate(`/case/${id}`), 800);
    } catch (e) {
      clearInterval(timerRef.current);
      setError(`Scan failed: ${e.message}`);
      setLoading(false);
      setProgress(0);
    }
  };

  const scanTypes = [
    {
      key: 'light',
      icon: '⚡',
      label: 'Light Scan',
      desc: 'Fast platform validation, quick risk score. Results in ~10–20 s.',
      estimate: '~15 sec',
    },
    {
      key: 'deep',
      icon: '🔬',
      label: 'Deep Scan',
      desc: 'Full correlation, email harvest, Scrapy crawl, graph + report.',
      estimate: '~60–120 sec',
    },
  ];

  const togglePlatform = (platform) => {
    setPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 820, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 20, color: t.text, margin: 0, marginBottom: 6 }}>
          🔍 New OSINT Investigation
        </h2>
        <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.textMuted, margin: 0 }}>
          Enter a username to begin. Email, phone, and filters are optional—the backend will auto-discover data if not provided.
        </p>
      </div>

      {/* Form */}
      <Card theme={theme} style={{ padding: 28, marginBottom: 20 }}>
        
        {/* Primary Target Section */}
        <SectionTitle icon="◎" title="Target Identification" theme={theme} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>

          {/* Username — autocomplete */}
          <AutocompleteInput
            label="Username (Required)"
            placeholder="e.g. elonmusk, torvalds, spez"
            value={username}
            onChange={setUsername}
            disabled={loading}
            theme={theme}
          />

          {/* Email */}
          <InputField
            label="Email (Optional)"
            type="email"
            placeholder="Auto-discovered if not provided"
            value={email}
            onChange={setEmail}
            disabled={loading}
            theme={theme}
          />

          {/* Phone — country code + number */}
          <div>
            <label style={{
              display: 'block',
              fontFamily: "'JetBrains Mono',monospace",
              fontSize: 10, fontWeight: 700,
              color: t.textSub, letterSpacing: 1.5,
              marginBottom: 6, textTransform: 'uppercase',
            }}>
              Phone <span style={{ color: t.textMuted, fontWeight: 500, letterSpacing: 0 }}>(Optional)</span>
            </label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
              <CountryCodePicker
                value={dialCode}
                onChange={setDialCode}
                disabled={loading}
                theme={theme}
              />
              <input
                type="tel"
                value={phoneNumber}
                onChange={e => {
                  // Only digits, spaces, dashes, parens
                  const v = e.target.value.replace(/[^\d\s\-().]/g, '');
                  setPhoneNumber(v);
                }}
                placeholder="24 000 0000"
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '11px 14px',
                  background: t.inputBg,
                  border: `1px solid ${t.border}`,
                  borderRadius: 8,
                  color: t.text,
                  fontFamily: "'JetBrains Mono',monospace",
                  fontSize: 14, letterSpacing: 1,
                  outline: 'none',
                  opacity: loading ? 0.6 : 1,
                  transition: 'border-color 0.2s, box-shadow 0.2s',
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
            {phoneNumber && (
              <div style={{
                marginTop: 4,
                fontFamily: "'JetBrains Mono',monospace",
                fontSize: 9, color: t.textMuted, letterSpacing: 1,
              }}>
                Full number: {dialCode}{phoneNumber.trim().replace(/^0+/, '')}
              </div>
            )}
          </div>

        </div>

        {/* Scan depth toggle */}
        <div style={{ marginBottom: 24 }}>
          <div style={{
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 10, fontWeight: 700,
            color: t.textSub, letterSpacing: 1.5,
            textTransform: 'uppercase',
            marginBottom: 10,
          }}>
            SCAN DEPTH
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {scanTypes.map(s => {
              const active = scanType === s.key;
              return (
                <button
                  key={s.key}
                  onClick={() => !loading && setScanType(s.key)}
                  disabled={loading}
                  style={{
                    padding: '16px 18px',
                    background: active ? `${t.accent}18` : t.surfaceAlt,
                    border: `2px solid ${active ? t.accent : t.border}`,
                    borderRadius: 12,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s',
                    opacity: loading ? 0.7 : 1,
                    boxShadow: active ? `0 0 16px ${t.accent}33` : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 20 }}>{s.icon}</span>
                    <span style={{
                      padding: '2px 8px',
                      background: active ? `${t.accent}22` : t.border,
                      border: `1px solid ${active ? t.accent + '44' : t.borderLight}`,
                      borderRadius: 20,
                      fontFamily: "'JetBrains Mono',monospace",
                      fontSize: 9,
                      color: active ? t.accent : t.textMuted,
                      fontWeight: 700,
                    }}>
                      {s.estimate}
                    </span>
                  </div>
                  <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: active ? t.accent : t.text, marginBottom: 4 }}>
                    {s.label}
                  </div>
                  <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, lineHeight: 1.5 }}>
                    {s.desc}
                  </div>
                  {active && (
                    <div style={{
                      marginTop: 10,
                      display: 'flex', alignItems: 'center', gap: 6,
                      fontFamily: "'JetBrains Mono',monospace", fontSize: 9,
                      color: t.accent, letterSpacing: 1,
                    }}>
                      <span style={{ fontSize: 8 }}>●</span> SELECTED
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Filters Toggle Button */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          disabled={loading}
          style={{
            width: '100%',
            padding: '10px',
            background: 'transparent',
            border: `1px dashed ${t.border}`,
            color: t.textMuted,
            borderRadius: 8,
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 11,
            cursor: 'pointer',
            marginBottom: 12,
            transition: 'all 0.2s',
            textDecoration: 'none',
          }}
        >
          {showFilters ? '▼ Filters (Optional)' : '▶ Filters (Optional)'}
          {(platforms.length > 0 || location || accountType || verified !== null) && (
            <span style={{ marginLeft: 8, color: t.accent }}>
              ({platforms.length + (location ? 1 : 0) + (accountType ? 1 : 0) + (verified !== null ? 1 : 0)} active)
            </span>
          )}
        </button>

        {/* Filters Section */}
        {showFilters && (
          <div style={{ marginBottom: 24, padding: '20px', background: `${t.surface}99`, border: `1px solid ${t.border}`, borderRadius: 12 }}>
            
            {/* Platform Filter */}
            <div style={{ marginBottom: 20 }}>
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 12, fontWeight: 700,
                color: t.text, marginBottom: 10,
              }}>
                🌐 Filter by Platform (Optional)
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {PLATFORMS.map(p => (
                  <button
                    key={p}
                    onClick={() => togglePlatform(p)}
                    style={{
                      padding: '6px 12px',
                      background: platforms.includes(p) ? t.accent : t.surfaceAlt,
                      border: `1px solid ${platforms.includes(p) ? t.accent : t.border}`,
                      color: platforms.includes(p) ? '#fff' : t.text,
                      borderRadius: 20,
                      fontFamily: "'Sora',sans-serif",
                      fontSize: 11,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    {platforms.includes(p) ? '✓ ' : ''}{p}
                  </button>
                ))}
              </div>
            </div>

            {/* Location Filter */}
            <div ref={countryDropRef} style={{ marginBottom: 20, position: 'relative' }}>
              <label style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 12, fontWeight: 700,
                color: t.text, display: 'block', marginBottom: 8,
              }}>
                📍 Location / Country (Optional)
              </label>
              
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={location || countrySearch}
                  onChange={(e) => {
                    const val = e.target.value;
                    setCountrySearch(val);
                    setLocation(val);
                    setShowCountryDrop(true);
                  }}
                  onFocus={() => setShowCountryDrop(true)}
                  placeholder="Type any country name (e.g. Ghana, Nigeria, USA)..."
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    background: t.surface,
                    border: `1px solid ${showCountryDrop ? t.accent : t.border}`,
                    borderRadius: 8,
                    color: t.text,
                    fontFamily: "'Sora',sans-serif",
                    fontSize: 12,
                    outline: 'none',
                    boxSizing: 'border-box',
                    transition: 'all 0.2s',
                  }}
                />
                
                {showCountryDrop && (
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0, right: 0,
                    maxHeight: 200,
                    overflowY: 'auto',
                    background: t.surface,
                    border: `1px solid ${t.accent}66`,
                    borderRadius: '0 0 8px 8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                    zIndex: 100,
                  }}>
                    {COUNTRY_CODES.filter(c => 
                      c.name.toLowerCase().includes((location || countrySearch).toLowerCase())
                    ).map(c => (
                      <div
                        key={c.code}
                        onClick={() => {
                          setLocation(c.name);
                          setCountrySearch(c.name);
                          setShowCountryDrop(false);
                        }}
                        style={{
                          padding: '8px 12px',
                          cursor: 'pointer',
                          fontFamily: "'Sora',sans-serif",
                          fontSize: 12,
                          color: t.text,
                          borderBottom: `1px solid ${t.borderLight}`,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = `${t.accent}11`}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <span>{c.flag}</span>
                        <span>{c.name}</span>
                      </div>
                    ))}
                    {COUNTRY_CODES.filter(c => 
                      c.name.toLowerCase().includes((location || countrySearch).toLowerCase())
                    ).length === 0 && (location || countrySearch) && (
                      <div style={{ padding: '8px 12px', fontSize: 11, color: t.textMuted }}>
                        Press enter to use "{location || countrySearch}"
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Account Type Filter */}
            <div style={{ marginBottom: 20 }}>
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 12, fontWeight: 700,
                color: t.text, marginBottom: 10,
              }}>
                👤 Account Type (Optional)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                {['personal', 'business', 'bot'].map(type => (
                  <button
                    key={type}
                    onClick={() => setAccountType(accountType === type ? '' : type)}
                    style={{
                      padding: '8px 12px',
                      background: accountType === type ? t.accent : t.surfaceAlt,
                      border: `1px solid ${accountType === type ? t.accent : t.border}`,
                      color: accountType === type ? '#fff' : t.text,
                      borderRadius: 8,
                      fontFamily: "'Sora',sans-serif",
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    {type === 'personal' && '👤 Personal'}
                    {type === 'business' && '🏢 Business'}
                    {type === 'bot' && '🤖 Bot'}
                  </button>
                ))}
              </div>
            </div>

            {/* Verified Toggle */}
            <div>
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 12, fontWeight: 700,
                color: t.text, marginBottom: 10,
              }}>
                ✓ Verification Status (Optional)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                {[
                  { key: null, label: 'Any' },
                  { key: true, label: '✓ Verified' },
                  { key: false, label: '✗ Not Verified' }
                ].map(v => (
                  <button
                    key={String(v.key)}
                    onClick={() => setVerified(verified === v.key ? null : v.key)}
                    style={{
                      padding: '8px 12px',
                      background: verified === v.key ? t.accent : t.surfaceAlt,
                      border: `1px solid ${verified === v.key ? t.accent : t.border}`,
                      color: verified === v.key ? '#fff' : t.text,
                      borderRadius: 8,
                      fontFamily: "'Sora',sans-serif",
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            background: loading ? t.border : t.accentGrad,
            color: '#fff',
            border: 'none',
            borderRadius: 12,
            fontFamily: "'Sora',sans-serif",
            fontWeight: 800,
            fontSize: 15,
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            boxShadow: loading ? 'none' : `0 6px 24px ${t.accent}55`,
            transition: 'all 0.2s',
            letterSpacing: 0.5,
          }}
        >
          {loading
            ? <><Spinner size={18} /> Running {scanType === 'deep' ? 'Deep' : 'Light'} Scan...</>
            : `🚀 Launch ${scanType === 'deep' ? 'Deep' : 'Light'} Scan`
          }
        </button>
      </Card>

      {/* Progress card (shown during scan) */}
      {loading && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 20 }} className="animate-slideDown">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Spinner size={20} color={t.accent} />
            <div>
              <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>
                {scanType === 'deep' ? 'Deep Intelligence Scan' : 'Light Scan'} in Progress
              </div>
              {caseId && (
                <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, marginTop: 2 }}>
                  CASE: {caseId}
                </div>
              )}
            </div>
          </div>

          <ProgressBar
            value={progress}
            max={100}
            color={scanType === 'deep' ? t.riskMed : t.accent}
            theme={theme}
          />

          <div style={{
            marginTop: 12,
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 11,
            color: t.textSub,
            letterSpacing: 0.5,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span className="blink" style={{ color: t.accent, fontSize: 8 }}>●</span>
            {phase}
          </div>

          {scanType === 'deep' && (
            <div style={{ marginTop: 12, padding: '10px 14px', background: `${t.riskMed}11`, border: `1px solid ${t.riskMed}33`, borderRadius: 8 }}>
              <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.riskMed }}>
                ⚠ Deep scan may take 60–120 seconds. Do not close this tab.
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Error */}
      {error && (
        <Alert type="danger" theme={theme}>{error}</Alert>
      )}

      {/* Info cards */}
      {!loading && (
        <>
          <Card theme={theme} style={{ padding: 20, marginBottom: 12 }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 12 }}>
              PLATFORM COVERAGE
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {PLATFORMS.map(p => (
                <span key={p} style={{
                  padding: '4px 12px',
                  background: t.surfaceAlt,
                  border: `1px solid ${t.border}`,
                  borderRadius: 20,
                  fontFamily: "'Sora',sans-serif",
                  fontSize: 11,
                  color: t.textMid,
                }}>{p}</span>
              ))}
            </div>
          </Card>

          <Card theme={theme} style={{ padding: 16 }}>
            <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted, lineHeight: 1.6 }}>
              <strong>Note:</strong> Email and phone fields are optional. If not provided, the backend will auto-discover them during the scan. Filters are also optional—a full search will be performed if filters are empty.
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

