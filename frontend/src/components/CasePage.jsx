// src/components/CasePage.jsx
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import {
  Card, SectionTitle, TabBar, StatusBadge, RiskBadge,
  EmptyState, Alert, Spinner, DataTable, Pill, ProgressBar, Btn
} from './UI';
import Sidebar from './Sidebar';
import RiskScore from './RiskScore';
import ReportViewer from './ReportViewer';
import GraphView from './GraphView';

const TABS = [
  { key: 'overview',   icon: '◎', label: 'Overview'  },
  { key: 'usernames',  icon: '👤', label: 'Usernames' },
  { key: 'emails',     icon: '📧', label: 'Emails'    },
  { key: 'phone',      icon: '📞', label: 'Phone'     },
  { key: 'mentions',   icon: '💬', label: 'Mentions'  },
  { key: 'graph',      icon: '🕸', label: 'Graph'     },
  { key: 'risk',       icon: '⚠', label: 'Risk'      },
  { key: 'report',     icon: '📄', label: 'Report'    },
];

const POLL_INTERVAL = 3000;

export default function CasePage({ theme, sidebarOpen, onSidebarClose }) {
  const t = THEMES[theme];
  const { id: caseId } = useParams();
  const navigate = useNavigate();

  const [tab,       setTab]       = useState('overview');
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
      setCaseData(d);
      return d.status;
    } catch (e) {
      setError(`Failed to load case: ${e.message}`);
      return 'error';
    }
  }, [caseId]);

  /* ── Fetch full result (only once completed) ── */
  const fetchResult = useCallback(async () => {
    try {
      const [resResult, resGraph, resStats] = await Promise.all([
        api.getResult(caseId),
        api.getGraph(caseId),
        api.getGraphStats(caseId),
      ]);
      setResult(resResult);
      setGraphData(resGraph.graph || null);
      setGraphStats(resStats.statistics || null);
    } catch (e) {
      setError(`Failed to load results: ${e.message}`);
    }
  }, [caseId]);

  /* ── Polling loop for running scans ── */
  useEffect(() => {
    let pollTimer;
    let active = true;

    const init = async () => {
      setLoading(true);
      const status = await fetchStatus();
      setLoading(false);

      if (status === 'completed') {
        await fetchResult();
      } else if (status === 'running' || status === 'pending') {
        setPolling(true);
        const poll = async () => {
          if (!active) return;
          const s = await fetchStatus();
          if (s === 'completed') {
            setPolling(false);
            await fetchResult();
          } else if (s === 'running' || s === 'pending') {
            pollTimer = setTimeout(poll, POLL_INTERVAL);
          } else {
            setPolling(false);
          }
        };
        pollTimer = setTimeout(poll, POLL_INTERVAL);
      }
    };

    init();
    return () => {
      active = false;
      clearTimeout(pollTimer);
    };
  }, [caseId, fetchStatus, fetchResult]);

  /* ── Tab count helpers ── */
  const findings   = result?.data?.findings || [];
  const platforms  = findings.filter(f => f.found);
  const emails     = (result?.data?.analysis?.emails    || []);
  const mentions   = (result?.data?.analysis?.mentions  || []);

  const tabsWithCounts = TABS.map(tab => {
    const countMap = {
      usernames: platforms.length,
      emails:    emails.length,
      mentions:  mentions.length,
    };
    return { ...tab, count: countMap[tab.key] ?? undefined };
  });

  /* ── Loading state ── */
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 20 }}>
        <Spinner size={48} color={THEMES[theme].accent} />
        <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 14, color: THEMES[theme].textMuted }}>
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

  return (
    <>
      <Sidebar theme={theme} isOpen={sidebarOpen} onClose={onSidebarClose} />

      <div className="animate-fadeIn" style={{ padding: '24px 20px', maxWidth: 1400, margin: '0 auto' }}>

        {/* ── Case Header ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <button
                onClick={() => navigate('/')}
                style={{ background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', fontSize: 13, fontFamily: "'Sora',sans-serif" }}
              >
                ← Dashboard
              </button>
              <span style={{ color: t.textMuted, fontSize: 13 }}>/</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: t.textSub }}>
                {caseId}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <h1 style={{ fontFamily: "'Sora',sans-serif", fontWeight: 900, fontSize: 24, color: t.text, margin: 0 }}>
                @{caseData?.username || '—'}
              </h1>
              <StatusBadge status={caseData?.status} theme={theme} />
              <RiskBadge level={caseData?.risk_level} theme={theme} />
            </div>
          </div>

          {/* Risk score strip */}
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <div style={{
              padding: '12px 20px',
              background: t.surface,
              border: `1px solid ${t.border}`,
              borderRadius: 12,
              textAlign: 'center',
            }}>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, letterSpacing: 2 }}>RISK SCORE</div>
              <div style={{
                fontFamily: "'Sora',sans-serif", fontWeight: 900, fontSize: 28,
                color: (caseData?.risk_score || 0) >= 67 ? t.riskHigh :
                       (caseData?.risk_score || 0) >= 34 ? t.riskMed  : t.riskLow,
              }}>
                {caseData?.risk_score ?? '—'}
              </div>
            </div>
            <div style={{
              padding: '12px 20px',
              background: t.surface,
              border: `1px solid ${t.border}`,
              borderRadius: 12,
              textAlign: 'center',
            }}>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, letterSpacing: 2 }}>FINDINGS</div>
              <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 900, fontSize: 28, color: t.text }}>
                {caseData?.findings_count ?? '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Polling banner */}
        {polling && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '12px 18px', marginBottom: 16,
            background: `${t.riskMed}11`, border: `1px solid ${t.riskMed}33`,
            borderRadius: 10,
          }}>
            <Spinner size={16} color={t.riskMed} />
            <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.riskMed }}>
              Scan in progress — polling for results every {POLL_INTERVAL / 1000}s…
            </div>
          </div>
        )}

        {error && <Alert type="danger" theme={theme} style={{ marginBottom: 16 }}>{error}</Alert>}

        {/* ── Tab bar ── */}
        <TabBar tabs={tabsWithCounts} active={tab} onChange={setTab} theme={theme} />

        {/* ── Tab Content ── */}
        <div className="animate-fadeIn" key={tab}>

          {/* OVERVIEW */}
          {tab === 'overview' && (
            <OverviewTab caseData={caseData} result={result} graphStats={graphStats} theme={theme} />
          )}

          {/* USERNAMES / PLATFORMS */}
          {tab === 'usernames' && (
            <UsernamesTab findings={findings} theme={theme} />
          )}

          {/* EMAILS */}
          {tab === 'emails' && (
            <EmailsTab emails={emails} theme={theme} />
          )}

          {/* PHONE */}
          {tab === 'phone' && (
            <PhoneTab caseData={caseData} theme={theme} />
          )}

          {/* MENTIONS */}
          {tab === 'mentions' && (
            <MentionsTab mentions={mentions} theme={theme} />
          )}

          {/* GRAPH */}
          {tab === 'graph' && (
            <div>
              <SectionTitle icon="🕸" title="Network Graph" theme={theme} action={
                graphStats && (
                  <div style={{ display: 'flex', gap: 16 }}>
                    {[
                      ['Nodes', graphStats.total_nodes],
                      ['Edges', graphStats.total_edges],
                      ['Density', graphStats.density?.toFixed(3)],
                    ].map(([k, v]) => (
                      <div key={k} style={{ textAlign: 'center' }}>
                        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted }}>{k}</div>
                        <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>{v}</div>
                      </div>
                    ))}
                  </div>
                )
              } />
              <GraphView graphData={graphData} theme={theme} targetUsername={caseData?.username} />
            </div>
          )}

          {/* RISK */}
          {tab === 'risk' && (
            <RiskTab caseData={caseData} result={result} theme={theme} />
          )}

          {/* REPORT */}
          {tab === 'report' && (
            <ReportViewer caseId={caseId} theme={theme} caseData={caseData} />
          )}
        </div>
      </div>
    </>
  );
}

/* ── Overview Tab ──────────────────────────── */
function OverviewTab({ caseData, result, graphStats, theme }) {
  const t = THEMES[theme];
  const analysis = result?.data?.analysis || {};

  const rows = [
    ['Case ID',        caseData?.id ?? '—'],
    ['Target',         `@${caseData?.username ?? '—'}`],
    ['Status',         caseData?.status ?? '—'],
    ['Risk Score',     `${caseData?.risk_score ?? '—'} / 100`],
    ['Risk Level',     caseData?.risk_level ?? '—'],
    ['Created',        caseData?.created_at ? new Date(caseData.created_at).toLocaleString() : '—'],
    ['Started',        caseData?.started_at ? new Date(caseData.started_at).toLocaleString() : '—'],
    ['Completed',      caseData?.completed_at ? new Date(caseData.completed_at).toLocaleString() : '—'],
    ['Platforms Checked', analysis.platforms_checked ?? '—'],
    ['Platforms Found',   analysis.platforms_found   ?? '—'],
  ].filter(r => r[1] !== '—');

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="◎" title="Case Details" theme={theme} />
        <DataTable rows={rows} theme={theme} />
      </Card>

      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="📊" title="Scan Summary" theme={theme} />
        {result ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <StatRow label="Platforms Found" value={analysis.platforms_found ?? 0} max={analysis.platforms_checked || 1} theme={theme} />
            {graphStats && (
              <>
                <StatRow label="Graph Nodes" value={graphStats.total_nodes} max={50} theme={theme} />
                <StatRow label="Graph Edges" value={graphStats.total_edges} max={100} theme={theme} />
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

function StatRow({ label, value, max, theme }) {
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

/* ── Usernames Tab ─────────────────────────── */
function UsernamesTab({ findings, theme }) {
  const t = THEMES[theme];

  const found    = findings.filter(f => f.found);
  const notFound = findings.filter(f => !f.found);

  if (findings.length === 0) {
    return <EmptyState icon="👤" message="No username data available." theme={theme} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Found platforms */}
      {found.length > 0 && (
        <Card theme={theme} style={{ padding: 24 }}>
          <SectionTitle icon="✓" title={`Active Profiles (${found.length})`} theme={theme} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
            {found.map((f, i) => (
              <PlatformCard key={i} finding={f} found theme={theme} />
            ))}
          </div>
        </Card>
      )}

      {/* Not found platforms */}
      {notFound.length > 0 && (
        <Card theme={theme} style={{ padding: 24 }}>
          <SectionTitle icon="✗" title={`Not Found (${notFound.length})`} theme={theme} />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {notFound.map((f, i) => (
              <span key={i} style={{
                padding: '6px 14px',
                background: t.surfaceAlt,
                border: `1px solid ${t.borderLight}`,
                borderRadius: 20,
                fontFamily: "'Sora',sans-serif",
                fontSize: 12, color: t.textMuted,
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

function PlatformCard({ finding, found, theme }) {
  const t = THEMES[theme];
  return (
    <a
      href={finding.profile_url}
      target="_blank"
      rel="noreferrer"
      style={{ textDecoration: 'none' }}
    >
      <div style={{
        padding: '14px 16px',
        background: t.surfaceAlt,
        border: `1px solid ${found ? t.riskLow + '44' : t.borderLight}`,
        borderRadius: 10,
        display: 'flex', alignItems: 'center', gap: 12,
        transition: 'border-color 0.15s, transform 0.15s',
        cursor: 'pointer',
      }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = t.accent; e.currentTarget.style.transform = 'translateY(-2px)'; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = found ? t.riskLow + '44' : t.borderLight; e.currentTarget.style.transform = 'translateY(0)'; }}
      >
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: `${t.riskLow}22`, border: `1px solid ${t.riskLow}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18, flexShrink: 0,
        }}>
          {PLATFORM_ICON[finding.platform] || '🌐'}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13, color: t.text }}>{finding.platform}</div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {finding.profile_url || finding.username}
          </div>
        </div>
        <div style={{ fontSize: 10, color: t.riskLow, fontWeight: 700 }}>→</div>
      </div>
    </a>
  );
}

const PLATFORM_ICON = {
  Facebook: '📘', Instagram: '📸', Twitter: '🐦', TikTok: '🎵',
  YouTube: '▶️', GitHub: '🐙', Reddit: '🟠', LinkedIn: '💼',
  Pinterest: '📌', Telegram: '✈️',
};

/* ── Emails Tab ────────────────────────────── */
function EmailsTab({ emails, theme }) {
  const t = THEMES[theme];

  if (!emails || emails.length === 0) {
    return <EmptyState icon="📧" message="No emails discovered during this investigation." theme={theme} />;
  }

  return (
    <Card theme={theme} style={{ padding: 24 }}>
      <SectionTitle icon="📧" title={`Emails Found (${emails.length})`} theme={theme} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {emails.map((email, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 14px',
            borderBottom: `1px solid ${t.borderLight}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 16 }}>📧</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 13, color: t.text }}>
                {typeof email === 'string' ? email : email.email || JSON.stringify(email)}
              </span>
            </div>
            {email.source && (
              <Pill label={email.source} theme={theme} />
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ── Phone Tab ─────────────────────────────── */
function PhoneTab({ caseData, theme }) {
  const t = THEMES[theme];

  if (!caseData?.phone) {
    return <EmptyState icon="📞" message="No phone number associated with this investigation." theme={theme} />;
  }

  return (
    <Card theme={theme} style={{ padding: 24 }}>
      <SectionTitle icon="📞" title="Phone Intelligence" theme={theme} />
      <DataTable
        rows={[
          ['Phone Number', caseData.phone],
          ['Status', 'Linked to investigation'],
        ]}
        theme={theme}
      />
      <div style={{ marginTop: 16 }}>
        <Alert type="info" theme={theme}>
          For full phone intelligence, use the <strong>Phone Intel</strong> tab on the Dashboard.
        </Alert>
      </div>
    </Card>
  );
}

/* ── Mentions Tab ──────────────────────────── */
function MentionsTab({ mentions, theme }) {
  const t = THEMES[theme];

  if (!mentions || mentions.length === 0) {
    return <EmptyState icon="💬" message="No web mentions found for this target." theme={theme} />;
  }

  return (
    <Card theme={theme} style={{ padding: 24 }}>
      <SectionTitle icon="💬" title={`Mentions (${mentions.length})`} theme={theme} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {mentions.map((m, i) => (
          <div key={i} style={{
            padding: '14px 0',
            borderBottom: `1px solid ${t.borderLight}`,
            display: 'flex', flexDirection: 'column', gap: 4,
          }}>
            <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text }}>
              {typeof m === 'string' ? m : m.text || m.content || JSON.stringify(m)}
            </div>
            {m.source && (
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted }}>
                Source: {m.source}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ── Risk Tab ──────────────────────────────── */
function RiskTab({ caseData, result, theme }) {
  const t = THEMES[theme];
  const analysis = result?.data?.analysis || {};
  const score    = caseData?.risk_score || 0;

  const factors = [
    { label: 'Platform Exposure',    score: Math.min(100, (analysis.platforms_found || 0) * 12) },
    { label: 'Social Footprint',     score: Math.min(100, (analysis.platforms_found || 0) * 8)  },
    { label: 'Data Availability',    score: Math.min(100, (analysis.findings_count  || 0) * 5)  },
    { label: 'Cross-Platform Match', score: score > 50 ? 70 : score > 25 ? 40 : 15             },
  ];

  const riskInfo = [
    { range: '0–33',  level: 'MINIMAL / LOW', color: t.riskLow,  desc: 'Limited public digital footprint. Low correlation risk.' },
    { range: '34–66', level: 'MEDIUM',        color: t.riskMed,  desc: 'Moderate exposure. Cross-platform presence detected.' },
    { range: '67–100',level: 'HIGH',          color: t.riskHigh, desc: 'High exposure. Multiple platform matches, elevated risk.' },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      {/* Gauge */}
      <Card theme={theme} style={{ padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <SectionTitle icon="⚠" title="Risk Assessment" theme={theme} />
        <RiskScore score={score} theme={theme} showFactors factors={factors} />
      </Card>

      {/* Risk legend */}
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="📊" title="Risk Matrix" theme={theme} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {riskInfo.map(r => (
            <div key={r.range} style={{
              padding: '14px 16px',
              background: `${r.color}11`,
              border: `1px solid ${r.color}33`,
              borderLeft: `4px solid ${r.color}`,
              borderRadius: 8,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: r.color, fontWeight: 700 }}>
                  {r.level}
                </span>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted }}>
                  Score {r.range}
                </span>
              </div>
              <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted }}>{r.desc}</div>
            </div>
          ))}
        </div>

        {/* Analysis details */}
        {analysis.threat_indicators && (
          <div style={{ marginTop: 20 }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 10 }}>
              THREAT INDICATORS
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
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
