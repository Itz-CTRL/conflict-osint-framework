// src/components/CasePage.jsx
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import {
  Card, SectionTitle, TabBar, StatusBadge, RiskBadge,
  EmptyState, Alert, Spinner, DataTable, Pill, ProgressBar, Btn
} from './UI';
import GraphView from './GraphView';
import SimpleGraph from './SimpleGraph';

const POLL_INTERVAL = 5000;

// Tabs shown for each scan type
const LIGHT_TABS = [
  { key: 'usernames', icon: '◉', label: 'Profiles' },
  { key: 'graph',     icon: '⬡', label: 'Graph'    },
];

const DEEP_TABS = [
  { key: 'overview',  icon: '◎', label: 'Overview'  },
  { key: 'usernames', icon: '◉', label: 'Profiles'  },
  { key: 'emails',    icon: '✉', label: 'Emails'    },
  { key: 'mentions',  icon: '◇', label: 'Mentions'  },
  { key: 'graph',     icon: '⬡', label: 'Graph'     },
  { key: 'risk',      icon: '⚠', label: 'Risk'      },
];

export default function CasePage({ theme }) {
  const t = THEMES[theme];
  const { id: caseId } = useParams();
  const navigate = useNavigate();

  const [tab,       setTab]       = useState(null); // set after we know scan type
  const [caseData,  setCaseData]  = useState(null);
  const [result,    setResult]    = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [graphStats,setGraphStats]= useState(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState('');
  const [polling,   setPolling]   = useState(false);

  /* ── Fetch case status ── */
  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.getStatus(caseId);
      const d = res.data || {};
      
      // Normalize backend status to frontend status for badge display
      const normalizedStatus = d.status?.includes('complete') ? 'completed' : d.status;
      const displayData = { ...d, status: normalizedStatus };
      
      setCaseData(displayData);
      return normalizedStatus;
    } catch (e) {
      setError(`Failed to load case: ${e.message}`);
      return 'error';
    }
  }, [caseId]);

  /* ── Fetch full result once completed ── */
  const fetchResult = useCallback(async () => {
    try {
      const [resResult, resGraph, resStats] = await Promise.all([
        api.getResult(caseId),
        api.getGraph(caseId).catch(() => ({ graph: null })),
        api.getGraphStats(caseId).catch(() => ({ statistics: null })),
      ]);
      setResult(resResult);
      setGraphData(resGraph.graph || null);
      setGraphStats(resStats.statistics || null);
    } catch (e) {
      setError(`Failed to load results: ${e.message}`);
    }
  }, [caseId]);

  /* ── Polling loop ── */
  useEffect(() => {
    let pollTimer;
    let active = true;

    // Check if a status indicates completion
    const isComplete = (status) => {
      return status === 'completed' || status === 'light_complete' || status === 'deep_complete';
    };

    // Check if a status indicates still running
    const isRunning = (status) => {
      return status === 'running' || status === 'pending' || status === 'created';
    };

    const init = async () => {
      setLoading(true);
      const status = await fetchStatus();
      setLoading(false);

      if (isComplete(status)) {
        await fetchResult();
      } else if (isRunning(status)) {
        setPolling(true);
        const poll = async () => {
          if (!active) return;
          const s = await fetchStatus();
          if (isComplete(s)) {
            setPolling(false);
            await fetchResult();
          } else if (isRunning(s)) {
            pollTimer = setTimeout(poll, POLL_INTERVAL);
          } else {
            setPolling(false);
          }
        };
        pollTimer = setTimeout(poll, POLL_INTERVAL);
      }
    };

    init();
    return () => { active = false; clearTimeout(pollTimer); };
  }, [caseId, fetchStatus, fetchResult]);

  /* ── Derived data ── */
  const scanType  = caseData?.scan_type || 'light';
  const findings  = result?.data?.findings || [];
  const platforms = findings.filter(f => f.found);
  const emails    = result?.data?.emails || [];
  const mentions  = result?.data?.mentions || [];

  /* ── Default tab after load ── */
  useEffect(() => {
    if (!tab && caseData) {
      setTab(scanType === 'deep' ? 'overview' : 'usernames');
    }
  }, [caseData, scanType, tab]);

  /* ── Build active tab list with counts ── */
  const baseTabs  = scanType === 'deep' ? DEEP_TABS : LIGHT_TABS;
  const activeTabs = baseTabs.map(tb => {
    const counts = { usernames: platforms.length, emails: emails.length, mentions: mentions.length };
    return counts[tb.key] !== undefined ? { ...tb, count: counts[tb.key] } : tb;
  });

  /* ── Loading state ── */
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 20 }}>
        <Spinner size={48} color={t.accent} />
        <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 14, color: t.textMuted }}>
          Loading investigation…
        </div>
      </div>
    );
  }

  /* ── Error state ── */
  if (error && !caseData) {
    return (
      <div style={{ padding: 40 }}>
        <Alert type="danger" theme={theme}>{error}</Alert>
        <Btn theme={theme} variant="secondary" onClick={() => navigate('/')} style={{ marginTop: 16 }}>
          ← Back to Dashboard
        </Btn>
      </div>
    );
  }

  const currentTab = tab || (scanType === 'deep' ? 'overview' : 'usernames');

  return (
    <div className="animate-fadeIn" style={{ padding: '24px 20px', maxWidth: 1200, margin: '0 auto' }}>

      {/* ── Case Header ── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <button
            onClick={() => navigate('/')}
            style={{ background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', fontSize: 13, fontFamily: "'Sora',sans-serif", padding: 0 }}
          >
            ← Dashboard
          </button>
          <span style={{ color: t.borderLight }}>·</span>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub }}>
            {caseId}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 900, fontSize: 22, color: t.text, margin: 0 }}>
              @{caseData?.username || '—'}
            </h1>
            <StatusBadge status={caseData?.status} theme={theme} />
            {caseData?.risk_level && <RiskBadge level={caseData.risk_level} theme={theme} />}
            <ScanTypePill scanType={scanType} theme={theme} />
          </div>

          {/* Stats strip */}
          <div style={{ display: 'flex', gap: 12 }}>
            {caseData?.risk_score !== undefined && (
              <MetaChip label="RISK SCORE" value={caseData.risk_score} color={
                caseData.risk_score >= 67 ? t.riskHigh :
                caseData.risk_score >= 34 ? t.riskMed  : t.riskLow
              } theme={theme} />
            )}
            <MetaChip label="PLATFORMS" value={platforms.length} theme={theme} />
            {scanType === 'deep' && emails.length > 0 && (
              <MetaChip label="EMAILS" value={emails.length} theme={theme} />
            )}
          </div>
        </div>
      </div>

      {/* Polling banner */}
      {polling && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '10px 16px', marginBottom: 16,
          background: `${t.riskMed}11`, border: `1px solid ${t.riskMed}33`, borderRadius: 8,
        }}>
          <Spinner size={14} color={t.riskMed} />
          <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.riskMed }}>
            Scan in progress — polling for results…
          </span>
        </div>
      )}

      {error && (
        <Alert type="danger" theme={theme} style={{ marginBottom: 16 }}>{error}</Alert>
      )}

      {/* ── Tab bar ── */}
      <TabBar tabs={activeTabs} active={currentTab} onChange={setTab} theme={theme} />

      {/* ── Tab Content ── */}
      <div className="animate-fadeIn" key={currentTab}>

        {/* OVERVIEW (deep only) */}
        {currentTab === 'overview' && scanType === 'deep' && (
          <OverviewTab caseData={caseData} result={result} graphStats={graphStats} theme={theme} />
        )}

        {/* USERNAMES / PROFILES */}
        {currentTab === 'usernames' && (
          <ProfilesTab findings={findings} theme={theme} />
        )}

        {/* EMAILS (deep only) */}
        {currentTab === 'emails' && (
          <EmailsTab emails={emails} theme={theme} />
        )}

        {/* MENTIONS (deep only) */}
        {currentTab === 'mentions' && (
          <MentionsTab mentions={mentions} theme={theme} />
        )}

        {/* GRAPH */}
        {currentTab === 'graph' && (
          <GraphTab
            scanType={scanType}
            findings={findings}
            targetUsername={caseData?.username}
            graphData={graphData}
            graphStats={graphStats}
            theme={theme}
          />
        )}

        {/* RISK (deep only) */}
        {currentTab === 'risk' && scanType === 'deep' && (
          <RiskTab caseData={caseData} result={result} theme={theme} />
        )}
      </div>
    </div>
  );
}

/* ── Scan Type Pill ─────────────────────────── */
function ScanTypePill({ scanType, theme }) {
  const t = THEMES[theme];
  const isDeep = scanType === 'deep';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 20,
      background: isDeep ? `${t.riskMed}22` : `${t.accent}22`,
      border: `1px solid ${isDeep ? t.riskMed : t.accent}55`,
      fontFamily: "'JetBrains Mono',monospace", fontSize: 9, fontWeight: 700,
      color: isDeep ? t.riskMed : t.accent, letterSpacing: 1.5,
    }}>
      {isDeep ? '🔬 DEEP' : '⚡ LIGHT'}
    </span>
  );
}

/* ── Meta Chip ──────────────────────────────── */
function MetaChip({ label, value, color, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{
      padding: '8px 16px', background: t.surface,
      border: `1px solid ${t.border}`, borderRadius: 10,
      textAlign: 'center', minWidth: 80,
    }}>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 8, color: t.textMuted, letterSpacing: 2, marginBottom: 2 }}>
        {label}
      </div>
      <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 800, fontSize: 22, color: color || t.text, lineHeight: 1 }}>
        {value ?? '—'}
      </div>
    </div>
  );
}

/* ── Graph Tab ──────────────────────────────── */
function GraphTab({ scanType, findings, targetUsername, graphData, graphStats, theme }) {
  const t = THEMES[theme];
  const found = findings.filter(f => f.found);

  if (scanType === 'light') {
    return (
      <div>
        <SectionTitle icon="⬡" title="Username-Platform Graph" theme={theme} />
        <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, marginBottom: 16, marginTop: -8 }}>
          Showing {found.length} platform{found.length !== 1 ? 's' : ''} where @{targetUsername} was found.
        </p>
        <SimpleGraph findings={findings} targetUsername={targetUsername} theme={theme} />
      </div>
    );
  }

  // Deep scan: use vis-network GraphView
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <SectionTitle icon="⬡" title="Network Graph" theme={theme} action={
          graphStats && (
            <div style={{ display: 'flex', gap: 16 }}>
              {[['Nodes', graphStats.total_nodes], ['Edges', graphStats.total_edges]].map(([k, v]) => (
                <div key={k} style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 8, color: t.textMuted }}>{k}</div>
                  <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>{v}</div>
                </div>
              ))}
            </div>
          )
        } />
      </div>
      <GraphView graphData={graphData} theme={theme} targetUsername={targetUsername} />
    </div>
  );
}

/* ── Profiles Tab ───────────────────────────── */
function ProfilesTab({ findings, theme }) {
  const t = THEMES[theme];
  const [expandedId, setExpandedId] = useState(null);

  const found    = findings.filter(f => f.found);
  const notFound = findings.filter(f => !f.found);

  if (!findings.length) {
    return <EmptyState icon="◉" message="No profile data available." theme={theme} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Found */}
      {found.length > 0 && (
        <Card theme={theme} style={{ padding: 24 }}>
          <SectionTitle icon="✓" title={`Active Profiles (${found.length})`} theme={theme} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 10 }}>
            {found.map((f, i) => (
              <ProfileCard
                key={i}
                finding={f}
                expanded={expandedId === i}
                onToggle={() => setExpandedId(expandedId === i ? null : i)}
                theme={theme}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Not found */}
      {notFound.length > 0 && (
        <Card theme={theme} style={{ padding: 20 }}>
          <SectionTitle icon="✗" title={`Not Found (${notFound.length})`} theme={theme} />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {notFound.map((f, i) => (
              <span key={i} style={{
                padding: '4px 12px',
                background: t.surfaceAlt, border: `1px solid ${t.borderLight}`,
                borderRadius: 20, fontFamily: "'Sora',sans-serif",
                fontSize: 11, color: t.textMuted,
              }}>
                {f.platform || '—'}
              </span>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

const PLATFORM_ICON = {
  Facebook: '📘', Instagram: '📸', Twitter: '🐦', TikTok: '🎵',
  YouTube: '▶️', GitHub: '🐙', Reddit: '🟠', LinkedIn: '💼',
  Pinterest: '📌', Telegram: '✈️', Snapchat: '👻', Discord: '🎮',
  Twitch: '🎮', Medium: '📝',
};

/* ── Profile Card ───────────────────────────── */
function ProfileCard({ finding, expanded, onToggle, theme }) {
  const t = THEMES[theme];
  return (
    <div
      onClick={onToggle}
      style={{
        padding: '14px 16px',
        background: t.surfaceAlt,
        border: `1.5px solid ${expanded ? t.accent : t.riskLow + '44'}`,
        borderRadius: 10,
        cursor: 'pointer',
        transition: 'border-color 0.15s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: `${t.riskLow}22`, border: `1px solid ${t.riskLow}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18, flexShrink: 0,
        }}>
          {PLATFORM_ICON[finding.platform] || '🌐'}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13, color: t.text }}>
            {finding.platform}
          </div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, marginTop: 2 }}>
            @{finding.username || '—'}
          </div>
        </div>
        <span style={{ fontSize: 11, color: t.textMuted }}>{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Expanded: profile info */}
      {expanded && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${t.borderLight}` }}>
          {finding.url ? (
            <a
              href={finding.url}
              target="_blank"
              rel="noreferrer"
              onClick={e => e.stopPropagation()}
              style={{
                display: 'block',
                fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.accent,
                textDecoration: 'none', wordBreak: 'break-all', letterSpacing: 0.3,
                marginBottom: 6,
              }}
            >
              {finding.url} →
            </a>
          ) : (
            <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted }}>No URL available</span>
          )}
          {finding.bio && (
            <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted, lineHeight: 1.5, marginTop: 4 }}>
              {finding.bio.length > 120 ? finding.bio.slice(0, 120) + '…' : finding.bio}
            </div>
          )}
          {finding.followers !== undefined && (
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textSub, marginTop: 6 }}>
              {finding.followers.toLocaleString()} followers
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Emails Tab ─────────────────────────────── */
function EmailsTab({ emails, theme }) {
  const t = THEMES[theme];
  if (!emails || !emails.length) {
    return <EmptyState icon="✉" message="No emails discovered during this investigation." theme={theme} />;
  }
  return (
    <Card theme={theme} style={{ padding: 24 }}>
      <SectionTitle icon="✉" title={`Emails Found (${emails.length})`} theme={theme} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {emails.map((email, i) => {
          const addr = typeof email === 'string' ? email : email.email || '';
          const confidence = email.confidence ? Math.round(email.confidence * 100) : null;
          const source = typeof email === 'object' ? email.source : null;
          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '11px 14px', borderBottom: `1px solid ${t.borderLight}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 13, color: t.text }}>
                  {addr}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {confidence && (
                  <span style={{
                    padding: '2px 8px', borderRadius: 4,
                    background: confidence >= 80 ? t.riskLow : confidence >= 60 ? t.riskMed : t.riskHigh,
                    color: '#fff', fontFamily: "'JetBrains Mono',monospace", fontSize: 10, fontWeight: 700,
                  }}>
                    {confidence}%
                  </span>
                )}
                {source && <Pill label={source} theme={theme} />}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

/* ── Mentions Tab ───────────────────────────── */
function MentionsTab({ mentions, theme }) {
  const t = THEMES[theme];
  if (!mentions || !mentions.length) {
    return <EmptyState icon="◇" message="No mentions found for this target." theme={theme} />;
  }
  return (
    <Card theme={theme} style={{ padding: 24 }}>
      <SectionTitle icon="◇" title={`Mentions (${mentions.length})`} theme={theme} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {mentions.map((m, i) => (
          <div key={i} style={{
            padding: '12px 0', borderBottom: `1px solid ${t.borderLight}`,
          }}>
            <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text, lineHeight: 1.5 }}>
              {typeof m === 'string' ? m : m.text || m.content || JSON.stringify(m)}
            </div>
            {m.source && (
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, marginTop: 4, letterSpacing: 0.5 }}>
                {m.source}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ── Overview Tab (deep only) ───────────────── */
function OverviewTab({ caseData, result, graphStats, theme }) {
  const analysis = result?.data?.analysis || {};
  const summary = result?.data?.summary || {};

  const rows = [
    ['Case ID',           caseData?.id],
    ['Target',            `@${caseData?.username}`],
    ['Scan Type',         caseData?.scan_type || 'light'],
    ['Status',            caseData?.status],
    ['Risk Score',        caseData?.risk_score !== undefined ? `${caseData.risk_score} / 100` : null],
    ['Created',           caseData?.created_at ? new Date(caseData.created_at).toLocaleString() : null],
    ['Completed',         caseData?.completed_at ? new Date(caseData.completed_at).toLocaleString() : null],
    ['Platforms Checked', analysis.platforms_checked || summary.total_profiles],
    ['Platforms Found',   analysis.platforms_found || summary.total_profiles],
    ['Breaches Found',    summary.total_breaches || analysis.breaches_found],
    ['Devices Found',     summary.devices_found],
  ].filter(r => r[1] != null);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="◎" title="Case Details" theme={theme} />
        <DataTable rows={rows} theme={theme} />
      </Card>
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="⬡" title="Scan Summary" theme={theme} />
        {result ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {(analysis.platforms_found !== undefined || summary.total_profiles) && (
              <ProgressRow label="Platforms Found" value={analysis.platforms_found || summary.total_profiles || 0} max={analysis.platforms_checked || 50} theme={theme} />
            )}
            {(summary.total_breaches !== undefined || graphStats) && (
              <ProgressRow label="Breaches" value={summary.total_breaches || 0} max={10} theme={theme} />
            )}
            {graphStats && (
              <>
                <ProgressRow label="Graph Nodes" value={graphStats.total_nodes || 0} max={50} theme={theme} />
                <ProgressRow label="Graph Edges" value={graphStats.total_edges || 0} max={100} theme={theme} />
              </>
            )}
          </div>
        ) : (
          <EmptyState icon="⏳" message="Scan results not yet available." theme={theme} />
        )}
      </Card>
    </div>
  );
}

function ProgressRow({ label, value, max, theme }) {
  const t = THEMES[theme];
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text }}>{label}</span>
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: t.accent, fontWeight: 700 }}>{value}</span>
      </div>
      <ProgressBar value={value} max={max} theme={theme} showPct={false} />
    </div>
  );
}

/* ── Risk Tab (deep only) ───────────────────── */
function RiskTab({ caseData, result, theme }) {
  const t = THEMES[theme];
  const analysis = result?.data?.analysis || {};
  const score    = caseData?.risk_score || 0;

  const riskBands = [
    { range: '0–33',   level: 'LOW',    color: t.riskLow,  desc: 'Limited public footprint. Low correlation risk.' },
    { range: '34–66',  level: 'MEDIUM', color: t.riskMed,  desc: 'Moderate exposure. Cross-platform presence detected.' },
    { range: '67–100', level: 'HIGH',   color: t.riskHigh, desc: 'High exposure. Multiple platform matches, elevated risk.' },
  ];

  const scoreColor = score >= 67 ? t.riskHigh : score >= 34 ? t.riskMed : t.riskLow;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      {/* Score */}
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="⚠" title="Risk Assessment" theme={theme} />
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 56, fontWeight: 800, color: scoreColor, lineHeight: 1 }}>
            {score}
          </div>
          <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, marginTop: 6 }}>
            Risk Score / 100
          </div>
          {caseData?.risk_level && (
            <div style={{ marginTop: 12 }}>
              <RiskBadge level={caseData.risk_level} theme={theme} />
            </div>
          )}
        </div>
        <div style={{ marginTop: 12 }}>
          <ProgressBar value={score} max={100} color={scoreColor} theme={theme} showPct />
        </div>
      </Card>

      {/* Risk Matrix */}
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="◎" title="Risk Matrix" theme={theme} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {riskBands.map(r => (
            <div key={r.range} style={{
              padding: '12px 14px',
              background: `${r.color}11`, border: `1px solid ${r.color}33`,
              borderLeft: `3px solid ${r.color}`, borderRadius: 6,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: r.color, fontWeight: 700 }}>
                  {r.level}
                </span>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted }}>
                  {r.range}
                </span>
              </div>
              <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted }}>{r.desc}</div>
            </div>
          ))}
        </div>
        {analysis.threat_indicators?.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textSub, letterSpacing: 2, marginBottom: 8 }}>
              THREAT INDICATORS
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {analysis.threat_indicators.map((ind, i) => (
                <Pill key={i} label={ind} color={t.riskMed} theme={theme} />
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
