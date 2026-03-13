// src/components/NewInvestigation.jsx
// New investigation creation form.
// Validates all inputs using formValidation.js before calling the backend.
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { useCaseContext } from '../contexts/CaseContext';
import { Card, SectionTitle, Alert, Spinner, ProgressBar, InputField } from './UI';
import AutocompleteInput from './AutocompleteInput';
import CountryCodePicker from './CountryCodePicker';
import { validateUsername, validateEmail, validatePhone } from '../utils/formValidation';

const SCAN_PHASES = {
  light: [
    { at: 0,  label: 'Initialising scan engine…'        },
    { at: 15, label: 'Checking platform registrations…' },
    { at: 40, label: 'Validating profile metadata…'      },
    { at: 65, label: 'Running risk analysis…'            },
    { at: 85, label: 'Building network graph…'           },
    { at: 95, label: 'Finalising report…'                },
  ],
  deep: [
    { at: 0,  label: 'Initialising deep scan engine…'  },
    { at: 10, label: 'Cross-platform correlation…'      },
    { at: 25, label: 'Email harvesting…'                },
    { at: 40, label: 'Deep crawl initiated…'            },
    { at: 55, label: 'Behavioural analysis…'            },
    { at: 70, label: 'Network graph construction…'      },
    { at: 82, label: 'Threat correlation…'              },
    { at: 92, label: 'Generating report…'               },
    { at: 97, label: 'Finalising…'                      },
  ],
};

const SCAN_TYPES = [
  {
    key:      'light',
    icon:     '⚡',
    label:    'Light Scan',
    desc:     'Username search across major platforms. Quick risk score.',
    estimate: '~15 s',
  },
  {
    key:      'deep',
    icon:     '🔬',
    label:    'Deep Scan',
    desc:     'Full correlation, email harvest, network graph and report.',
    estimate: '~60–120 s',
  },
];

export default function NewInvestigation({ theme }) {
  const t = THEMES[theme];
  const navigate = useNavigate();
  const { startScan, updateProgress, completeScan } = useCaseContext();

  const [username,    setUsername]    = useState('');
  const [email,       setEmail]       = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [dialCode,    setDialCode]    = useState('+233');
  const [scanType,    setScanType]    = useState('light');
  const [loading,     setLoading]     = useState(false);
  const [progress,    setProgress]    = useState(0);
  const [phase,       setPhase]       = useState('');
  const [caseId,      setCaseId]      = useState(null);

  // Field-level validation errors
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitError, setSubmitError] = useState('');

  const timerRef = useRef(null);
  useEffect(() => () => clearInterval(timerRef.current), []);

  /* ── Validation ── */
  const validate = () => {
    const errors = {};

    const usernameCheck = validateUsername(username.trim());
    if (!usernameCheck.valid) errors.username = usernameCheck.error;

    if (email.trim()) {
      const emailCheck = validateEmail(email.trim());
      if (!emailCheck.valid) errors.email = emailCheck.error;
    }

    if (phoneNumber.trim()) {
      const phoneCheck = validatePhone(phoneNumber.trim(), dialCode);
      if (!phoneCheck.valid) errors.phone = phoneCheck.error;
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /* ── Progress simulation ── */
  const startFakeProgress = (type) => {
    const phases = SCAN_PHASES[type];
    let pct = 0;
    setProgress(0);
    setPhase(phases[0].label);
    timerRef.current = setInterval(() => {
      pct = Math.min(pct + (type === 'light' ? 2.5 : 1.2), 97);
      setProgress(pct);
      const curr = [...phases].reverse().find(p => pct >= p.at);
      if (curr) setPhase(curr.label);
      updateProgress(curr?.label || 'Processing…', pct, '');
    }, 800);
  };

  const stopProgress = () => {
    clearInterval(timerRef.current);
    setProgress(100);
    setPhase('Scan complete ✓');
    completeScan();
  };

  /* ── Submit ── */
  const handleSubmit = async () => {
    setSubmitError('');
    if (!validate()) return;

    setLoading(true);
    setCaseId(null);

    try {
      startScan(scanType);
      setPhase('Creating investigation case…');
      setProgress(2);

      const localNum = phoneNumber.trim().replace(/^0+/, '');
      const fullPhone = localNum ? `${dialCode}${localNum}` : null;

      const created = await api.createInvestigation(
        username.trim(),
        email.trim() || undefined,
        fullPhone || undefined,
        {}
      );
      const id = created.case_id;
      setCaseId(id);

      startFakeProgress(scanType);
      await api.startScan(id, scanType);
      stopProgress();

      setTimeout(() => navigate(`/case/${id}`), 800);
    } catch (e) {
      clearInterval(timerRef.current);
      setSubmitError(`Scan failed: ${e.message}`);
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 760, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 20, color: t.text, margin: '0 0 6px 0' }}>
          New Investigation
        </h2>
        <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.textMuted, margin: 0 }}>
          Enter a username to begin. Email and phone are optional — the backend will attempt auto-discovery.
        </p>
      </div>

      {/* Form */}
      <Card theme={theme} style={{ padding: 28, marginBottom: 20 }}>
        <SectionTitle icon="◎" title="Target Identification" theme={theme} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>

          {/* Username */}
          <div>
            <AutocompleteInput
              label="Username (Required)"
              placeholder="e.g. elonmusk, torvalds, spez"
              value={username}
              onChange={v => { setUsername(v); setFieldErrors(p => ({ ...p, username: undefined })); }}
              disabled={loading}
              theme={theme}
            />
            {fieldErrors.username && <FieldError msg={fieldErrors.username} t={t} />}
          </div>

          {/* Email */}
          <div>
            <InputField
              label="Email (Optional)"
              type="email"
              placeholder="Auto-discovered if not provided"
              value={email}
              onChange={v => { setEmail(v); setFieldErrors(p => ({ ...p, email: undefined })); }}
              disabled={loading}
              theme={theme}
            />
            {fieldErrors.email && <FieldError msg={fieldErrors.email} t={t} />}
          </div>

          {/* Phone */}
          <div>
            <label style={{
              display: 'block',
              fontFamily: "'JetBrains Mono',monospace", fontSize: 10, fontWeight: 700,
              color: t.textSub, letterSpacing: 1.5, marginBottom: 6, textTransform: 'uppercase',
            }}>
              Phone <span style={{ color: t.textMuted, fontWeight: 500, letterSpacing: 0 }}>(Optional)</span>
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <CountryCodePicker value={dialCode} onChange={setDialCode} disabled={loading} theme={theme} />
              <input
                type="tel"
                value={phoneNumber}
                onChange={e => {
                  setPhoneNumber(e.target.value.replace(/[^\d\s\-(). ]/g, ''));
                  setFieldErrors(p => ({ ...p, phone: undefined }));
                }}
                placeholder="24 000 0000"
                disabled={loading}
                style={{
                  flex: 1, padding: '11px 14px',
                  background: t.inputBg, border: `1px solid ${fieldErrors.phone ? t.riskHigh : t.border}`,
                  borderRadius: 8, color: t.text,
                  fontFamily: "'JetBrains Mono',monospace", fontSize: 14, letterSpacing: 1,
                  outline: 'none', opacity: loading ? 0.6 : 1,
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                }}
                onFocus={e => { e.target.style.borderColor = t.accent; e.target.style.boxShadow = `0 0 0 3px ${t.accent}22`; }}
                onBlur={e => { e.target.style.borderColor = fieldErrors.phone ? t.riskHigh : t.border; e.target.style.boxShadow = 'none'; }}
              />
            </div>
            {phoneNumber && !fieldErrors.phone && (
              <div style={{ marginTop: 4, fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, letterSpacing: 1 }}>
                Full: {dialCode}{phoneNumber.trim().replace(/^0+/, '')}
              </div>
            )}
            {fieldErrors.phone && <FieldError msg={fieldErrors.phone} t={t} />}
          </div>
        </div>

        {/* Scan depth */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, fontWeight: 700, color: t.textSub, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 10 }}>
            SCAN DEPTH
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {SCAN_TYPES.map(s => {
              const active = scanType === s.key;
              return (
                <button
                  key={s.key}
                  onClick={() => !loading && setScanType(s.key)}
                  disabled={loading}
                  style={{
                    padding: '16px 18px', textAlign: 'left',
                    background: active ? `${t.accent}18` : t.surfaceAlt,
                    border: `2px solid ${active ? t.accent : t.border}`,
                    borderRadius: 12, cursor: loading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s', opacity: loading ? 0.7 : 1,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 18 }}>{s.icon}</span>
                    <span style={{
                      padding: '2px 8px', borderRadius: 20,
                      background: active ? `${t.accent}22` : t.border,
                      border: `1px solid ${active ? t.accent + '44' : t.borderLight}`,
                      fontFamily: "'JetBrains Mono',monospace", fontSize: 9,
                      color: active ? t.accent : t.textMuted, fontWeight: 700,
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
                </button>
              );
            })}
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            width: '100%', padding: '14px',
            background: loading ? t.border : t.accentGrad,
            color: '#fff', border: 'none', borderRadius: 12,
            fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 15,
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
            boxShadow: loading ? 'none' : `0 6px 24px ${t.accent}44`,
            transition: 'all 0.2s',
          }}
        >
          {loading
            ? <><Spinner size={18} /> Running {scanType === 'deep' ? 'Deep' : 'Light'} Scan…</>
            : `Launch ${scanType === 'deep' ? 'Deep' : 'Light'} Scan`
          }
        </button>
      </Card>

      {/* Progress card */}
      {loading && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 20 }} className="animate-slideDown">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Spinner size={20} color={t.accent} />
            <div>
              <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>
                {scanType === 'deep' ? 'Deep Intelligence Scan' : 'Light Scan'} in Progress
              </div>
              {caseId && (
                <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, marginTop: 2 }}>
                  CASE: {caseId}
                </div>
              )}
            </div>
          </div>
          <ProgressBar value={progress} max={100} color={scanType === 'deep' ? t.riskMed : t.accent} theme={theme} />
          <div style={{ marginTop: 10, fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 0.5 }}>
            <span className="blink" style={{ color: t.accent, fontSize: 8, marginRight: 6 }}>●</span>
            {phase}
          </div>
          {scanType === 'deep' && (
            <div style={{ marginTop: 12, padding: '8px 12px', background: `${t.riskMed}11`, border: `1px solid ${t.riskMed}33`, borderRadius: 6 }}>
              <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.riskMed }}>
                Deep scan may take 60–120 seconds. Do not close this tab.
              </span>
            </div>
          )}
        </Card>
      )}

      {/* Submit errors */}
      {submitError && <Alert type="danger" theme={theme}>{submitError}</Alert>}
    </div>
  );
}

function FieldError({ msg, t }) {
  return (
    <div style={{ marginTop: 4, fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.riskHigh }}>
      {msg}
    </div>
  );
}
