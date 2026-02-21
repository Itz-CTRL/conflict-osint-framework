// src/components/CasePage.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { RiskBadge, Card, SectionTitle, Alert, EmptyState, Spinner } from './UI';
import Sidebar from './Sidebar';
import NetworkGraph from './NetworkGraph';

export default function CasePage({ theme, sidebarOpen, onSidebarClose }) {
  const t = THEMES[theme];
  const { id } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) { navigate('/'); return; }
    (async () => {
      try {
        const res = await api.getInvestigation(id);
        setData(res);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id, navigate]);

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
      <Spinner size={40} color={t.accent} />
    </div>
  );

  if (error) return (
    <div style={{ padding: 32, maxWidth: 600, margin: '0 auto' }}>
      <Alert type="danger" theme={theme}>
        <strong>Failed to load report:</strong> {error}
      </Alert>
      <button onClick={() => navigate('/')} style={{ marginTop: 16, padding: '8px 20px', background: t.accentGrad, color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontFamily: "'Sora',sans-serif" }}>
        ← Back to Dashboard
      </button>
    </div>
  );

  // Parse investigation data
  const inv = data.investigation;
  const findings = data.findings || [];
  const analysisFinding = findings.find(f => f.platform === 'ANALYSIS');
  let fullData = {};
  if (analysisFinding?.data) {
    try { fullData = JSON.parse(analysisFinding.data); } catch {}
  }

  const analysis = fullData.analysis || {};
  const platformResults = fullData.platform_results || {};
  const reddit = fullData.reddit || {};
  const github = fullData.github || {};
  const platforms = platformResults.platforms || [];
  const riskLevel = analysis.risk_level || 'UNKNOWN';
  const networkData = data.network || {};

  return (
    <>
      {/* Sidebar Drawer (controlled by App) */}
      <Sidebar theme={theme} isOpen={sidebarOpen} onClose={onSidebarClose} />

      {/* Main Content */}
      <div className="animate-fadeIn" style={{ padding: '24px 20px', maxWidth: 1400, margin: '0 auto' }}>

      {/* Back Button at Top */}
      <button
        onClick={() => navigate('/')}
        style={{
          marginBottom: 20,
          padding: '10px 18px',
          background: t.surfaceAlt,
          border: `1px solid ${t.border}`,
          color: t.textMid,
          borderRadius: 8,
          cursor: 'pointer',
          fontFamily: "'Sora',sans-serif",
          fontWeight: 600,
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          transition: 'all 0.2s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = t.accent;
          e.currentTarget.style.color = '#fff';
          e.currentTarget.style.borderColor = t.accent;
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = t.surfaceAlt;
          e.currentTarget.style.color = t.textMid;
          e.currentTarget.style.borderColor = t.border;
        }}
      >
        ← Back to Investigations
      </button>

      {/* Header Banner */}
      <div style={{
        background: t.accentGrad,
        borderRadius: 16, padding: '24px 28px',
        marginBottom: 24,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16,
      }}>
        <div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: 'rgba(255,255,255,0.7)', letterSpacing: 2, marginBottom: 6 }}>
            INVESTIGATION REPORT #{inv.id}
          </div>
          <h1 style={{ fontFamily: "'Sora',sans-serif", fontSize: 26, fontWeight: 800, color: '#fff', margin: 0 }}>
            @{inv.username}
          </h1>
          <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: 'rgba(255,255,255,0.75)', marginTop: 4 }}>
            Created: {new Date(inv.created_at).toLocaleString()} · Status: {inv.status.toUpperCase()}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
          <RiskBadge level={riskLevel} theme={theme} />
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>
            Risk Score: {analysis.risk_score ?? '—'}/100
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 24 }}>
        <MetricCard
          label="THREAT LEVEL"
          value={riskLevel}
          color={riskLevel === 'HIGH' ? t.riskHigh : riskLevel === 'MEDIUM' ? t.riskMed : t.riskLow}
          theme={theme}
        />
        <MetricCard label="PLATFORMS FOUND" value={platformResults.found_count ?? '—'} color={t.riskLow} theme={theme} />
        <MetricCard label="PLATFORMS CHECKED" value={platformResults.total_checked ?? '—'} color={t.accent} theme={theme} />
      </div>

      {/* Platform Presence */}
      <Card theme={theme} style={{ padding: 24, marginBottom: 24 }}>
        <SectionTitle icon="📱" title="Platform Presence" theme={theme} />
        {platforms.length === 0 ? (
          <EmptyState message="No platform data available." theme={theme} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: 12 }}>
            {platforms.map((p, i) => (
              <PlatformCard key={i} platform={p} theme={theme} />
            ))}
          </div>
        )}
      </Card>

      {/* Behavior Analysis */}
      <Card theme={theme} style={{ padding: 24, marginBottom: 24 }}>
        <SectionTitle icon="🧠" title="Behavior Analysis" theme={theme} />
        <BehaviorSection analysis={analysis} theme={theme} />
      </Card>

      {/* Detailed Data: Reddit */}
      {reddit?.found && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 24 }}>
          <SectionTitle icon="🔴" title="Reddit Profile Details" theme={theme} />
          <RedditSection reddit={reddit} theme={theme} />
        </Card>
      )}

      {/* Detailed Data: GitHub */}
      {github?.found && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 24 }}>
          <SectionTitle icon="💻" title="GitHub Profile Details" theme={theme} />
          <GitHubSection github={github} theme={theme} />
        </Card>
      )}

      {/* Network Graph Visualization */}
      <Card theme={theme} style={{ padding: 24, marginBottom: 24 }}>
        <SectionTitle icon="🕸" title="Investigation Network Map" theme={theme} />
        <NetworkGraph networkData={networkData} theme={theme} />
      </Card>

      {/* Recommendations */}
      {analysis.recommendations?.length > 0 && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 24 }}>
          <SectionTitle icon="⚠" title="Investigator Recommendations" theme={theme} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {analysis.recommendations.map((rec, i) => (
              <Alert key={i} type="warning" theme={theme}>{rec}</Alert>
            ))}
          </div>
        </Card>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 32 }}>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: '11px 24px', background: t.accentGrad, color: '#fff', border: 'none',
            borderRadius: 10, cursor: 'pointer', fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14,
            boxShadow: `0 4px 16px ${t.accent}44`,
          }}
        >
          🔍 New Investigation
        </button>
        <button
          onClick={() => window.print()}
          style={{
            padding: '11px 24px', background: 'transparent',
            border: `1px solid ${t.border}`, color: t.textMid, borderRadius: 10,
            cursor: 'pointer', fontFamily: "'Sora',sans-serif", fontWeight: 600, fontSize: 14,
          }}
        >
          🖨 Print Report
        </button>
      </div>

      <footer style={{ textAlign: 'center', fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, letterSpacing: 2, paddingBottom: 24 }}>
        SOKO AERIAL OSINT · REPORT GENERATED: {new Date().toLocaleString().toUpperCase()} · PUBLIC DATA ONLY
      </footer>
      </div>
    </>
  );
}

/* ── Sub-components ─────────────────────────── */

function MetricCard({ label, value, color, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{
      background: t.surface, border: `1px solid ${t.border}`,
      borderRadius: 14, padding: '20px 22px', textAlign: 'center',
    }}>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textSub, letterSpacing: 2, marginBottom: 10 }}>
        {label}
      </div>
      <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 36, fontWeight: 800, color }}>
        {value}
      </div>
    </div>
  );
}

function PlatformCard({ platform, theme }) {
  const t = THEMES[theme];
  const found = platform.found;
  return (
    <div style={{
      background: t.surfaceAlt,
      border: `2px solid ${found ? t.riskLow : t.border}`,
      borderRadius: 12, padding: 16,
      transition: 'transform 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      {/* Avatar */}
      {platform.profile_picture && (
        <div style={{ textAlign: 'center', marginBottom: 10 }}>
          <img
            src={platform.profile_picture}
            alt={`${platform.platform} avatar`}
            style={{ width: 60, height: 60, borderRadius: '50%', objectFit: 'cover', border: `2px solid ${t.riskLow}` }}
            onError={e => { e.target.style.display = 'none'; }}
          />
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13, color: t.text }}>
          {platform.platform}
        </span>
        <span style={{
          padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700,
          fontFamily: "'JetBrains Mono',monospace", letterSpacing: 1,
          background: found ? `${t.riskLow}22` : `${t.textMuted}22`,
          color: found ? t.riskLow : t.textMuted,
          border: `1px solid ${found ? t.riskLow : t.textMuted}44`,
        }}>
          {found ? '✓ FOUND' : '✗ NOT FOUND'}
        </span>
      </div>
      {found && platform.url && (
        <a
          href={platform.url}
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'block', textAlign: 'center', padding: '6px 0',
            background: `${t.accent}22`, color: t.textMid, borderRadius: 6,
            fontFamily: "'Sora',sans-serif", fontSize: 12, fontWeight: 600,
            textDecoration: 'none', border: `1px solid ${t.accent}33`,
          }}
        >
          🔗 View Profile
        </a>
      )}
    </div>
  );
}

function BehaviorSection({ analysis, theme }) {
  const t = THEMES[theme];
  const flags = analysis.behavior_flags || [];
  const keywords = analysis.keyword_hits || [];
  const presence = analysis.platform_presence || {};
  const findings = analysis.findings || [];

  if (!flags.length && !keywords.length && !findings.length) {
    return <Alert type="success" theme={theme}>No suspicious behavior detected in available data.</Alert>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Platform summary */}
      {presence.found_on?.length > 0 && (
        <Alert type="info" theme={theme}>
          Account found on <strong>{presence.count}</strong> of {presence.platforms_checked} platforms: {presence.found_on.join(', ')}.
        </Alert>
      )}

      {/* Flags */}
      {flags.length > 0 && (
        <div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 8 }}>
            SUSPICIOUS INDICATORS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {flags.map((f, i) => (
              <div key={i} style={{
                padding: '10px 14px', borderRadius: 8,
                background: `${t.riskMed}18`, border: `1px solid ${t.riskMed}44`,
                fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text,
                display: 'flex', gap: 10, alignItems: 'flex-start',
              }}>
                <span style={{ color: t.riskMed }}>⚠</span>{f}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Keyword hits */}
      {keywords.length > 0 && (
        <div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 8 }}>
            CONFLICT KEYWORDS DETECTED
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {keywords.map((kw, i) => (
              <div key={i} style={{
                padding: '10px 14px', borderRadius: 8,
                background: `${t.riskHigh}15`, border: `1px solid ${t.riskHigh}33`,
                fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text,
              }}>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, color: t.riskHigh, fontSize: 11 }}>
                  {kw.keyword.toUpperCase()}
                </span>
                <span style={{ color: t.textMuted, marginLeft: 8, fontSize: 11 }}>
                  via {kw.platform}
                </span>
                <div style={{ color: t.textMuted, fontSize: 12, marginTop: 4, fontStyle: 'italic' }}>
                  "{kw.context}"
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional findings */}
      {findings.length > 0 && (
        <div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 8 }}>
            ADDITIONAL FINDINGS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {findings.map((f, i) => (
              <Alert key={i} type="info" theme={theme}>{f}</Alert>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RedditSection({ reddit, theme }) {
  const t = THEMES[theme];
  return (
    <div>
      {reddit.profile_picture && (
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <img src={reddit.profile_picture} alt="Reddit avatar"
            style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover', border: `3px solid ${t.riskHigh}` }}
            onError={e => { e.target.style.display = 'none'; }}
          />
        </div>
      )}
      <DataTable rows={[
        ['Username', `@${reddit.username}`],
        ['Total Karma', (reddit.karma || 0).toLocaleString()],
        ['Account Created', reddit.account_age || '—'],
        ['Email Verified', reddit.verified ? '✓ Yes' : '✗ No'],
      ]} theme={theme} />
      {reddit.recent_posts?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub, letterSpacing: 2, marginBottom: 8 }}>
            RECENT POSTS & COMMENTS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {reddit.recent_posts.map((post, i) => (
              <div key={i} style={{
                background: t.surfaceAlt, border: `1px solid ${t.border}`,
                borderRadius: 10, padding: 14,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textSub }}>r/{post.subreddit}</span>
                  <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted }}>{post.created} · {post.score} pts</span>
                </div>
                <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text, margin: 0 }}>{post.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function GitHubSection({ github, theme }) {
  const t = THEMES[theme];
  const rows = [
    github.name    && ['Name', github.name],
    ['Username', `@${github.username}`],
    github.bio     && ['Bio', github.bio],
    github.location && ['Location', github.location],
    github.email   && ['Email', github.email],
    github.company && ['Company', github.company],
    ['Public Repos', github.public_repos],
    ['Followers', (github.followers || 0).toLocaleString()],
    ['Following', (github.following || 0).toLocaleString()],
    ['Account Created', github.account_age || '—'],
    github.twitter_linked && ['Linked Twitter', `@${github.twitter_linked}`],
  ].filter(Boolean);

  return (
    <div>
      {github.profile_picture && (
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <img src={github.profile_picture} alt="GitHub avatar"
            style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover', border: `3px solid ${t.accent}` }}
            onError={e => { e.target.style.display = 'none'; }}
          />
        </div>
      )}
      <DataTable rows={rows} theme={theme} />
    </div>
  );
}

function DataTable({ rows, theme }) {
  const t = THEMES[theme];
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <tbody>
        {rows.map(([key, val], i) => (
          <tr key={i} style={{ borderBottom: `1px solid ${t.borderLight}` }}>
            <td style={{
              padding: '10px 14px', width: '35%',
              fontFamily: "'JetBrains Mono',monospace", fontSize: 11,
              color: t.textMuted, fontWeight: 700, letterSpacing: 0.5,
            }}>{key}</td>
            <td style={{
              padding: '10px 14px',
              fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.text,
            }}>{val}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
